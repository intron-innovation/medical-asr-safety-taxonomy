#!/usr/bin/env python3
"""
Extract errors from ASR reconstructed text with unique error IDs.
This generates unique identifiers for each error occurrence, allowing
multiple annotations of the same error text at different positions.
"""

import re
import uuid
from typing import List, Dict, Tuple


class ErrorExtractor:
    """Extract and assign unique IDs to each error occurrence."""

    # Matches inline NER tags produced by the medical-entity tagging pipeline,
    # e.g. "[PROBLEM: difficulty in urinating]" inside human_transcript_ner.
    _NER_TAG_PATTERN = re.compile(r'\[([A-Z_]+):\s*([^\]]+)\]')

    @staticmethod
    def build_medical_vocab(human_transcript_ner: str) -> set:
        """
        Build a lowercase word-token vocabulary from every NER-tagged medical
        entity span in the human transcript (PROBLEM, MEDICINE, ANATOMICAL_STRUCTURE,
        etc). Used to decide which auto-detected ASR errors are medically relevant
        and therefore actually require annotator attention.

        Args:
            human_transcript_ner: human transcript with inline [TYPE: span] tags

        Returns:
            Set of lowercase word tokens drawn from all tagged entity spans.
        """
        vocab = set()
        if not human_transcript_ner:
            return vocab
        for match in ErrorExtractor._NER_TAG_PATTERN.finditer(human_transcript_ner):
            entity_text = match.group(2)
            vocab.update(re.findall(r"[a-zA-Z']+", entity_text.lower()))
        return vocab

    @staticmethod
    def _words_overlap_medical_vocab(words, medical_vocab) -> bool:
        """
        Check whether any word overlaps the medical vocabulary, either exactly
        or via a shared word-stem (e.g. "urinal"/"urinary" both share a stem
        with "urinating"). ASR errors are frequently morphological variants of
        the reference word rather than exact matches, so a pure set-membership
        check misses many real medical corrections.
        """
        for word in words:
            if word in medical_vocab:
                return True
            if len(word) < 4:
                continue
            for vocab_word in medical_vocab:
                if len(vocab_word) < 4:
                    continue
                prefix_len = min(5, len(word), len(vocab_word))
                if word[:prefix_len] == vocab_word[:prefix_len]:
                    return True
        return False

    @staticmethod
    def _is_medical_error(error_type: str, error_content: str, medical_vocab: set) -> bool:
        """Check whether an error's text overlaps the medical entity vocabulary."""
        if not medical_vocab:
            return False
        if error_type == 'SUB' and '->' in error_content:
            before, after = error_content.split('->', 1)
            words = re.findall(r"[a-zA-Z']+", before.lower())
            words += re.findall(r"[a-zA-Z']+", after.lower())
        else:
            words = re.findall(r"[a-zA-Z']+", error_content.lower())
        return ErrorExtractor._words_overlap_medical_vocab(words, medical_vocab)

    @staticmethod
    def extract_errors(asr_text: str, human_transcript_ner: str = None) -> List[Dict]:
        """
        Extract all errors from ASR reconstructed text with unique IDs.
        
        Args:
            asr_text: ASR reconstructed text with error annotations
                     e.g., "hello [DEL:world] [INS:foo] [SUB:bar->baz]"
            human_transcript_ner: optional human transcript with inline NER tags
                     (e.g. "[PROBLEM: difficulty in urinating]"), used to flag
                     which errors are medically relevant via is_medical.
        
        Returns:
            List of dicts containing:
                - error_id: Unique UUID for this error occurrence
                - error_type: DEL, SUB, or INS
                - error_match: Full error text including brackets
                - error_text: Content inside brackets
                - position: Position in the text
                - start_idx: Start index in original text
                - end_idx: End index in original text
                - is_medical: True if the error's text overlaps a tagged medical
                     entity in human_transcript_ner (annotators are only
                     required to annotate is_medical=True errors)
        """
        errors = []
        medical_vocab = ErrorExtractor.build_medical_vocab(human_transcript_ner)
        
        # Pattern to match [TYPE:content] or [TYPE:before->after]
        pattern = r'\[([A-Z]+):([^\]]+)\]'
        
        for match in re.finditer(pattern, asr_text):
            error_type = match.group(1)  # DEL, SUB, INS
            error_content = match.group(2)  # content inside brackets
            error_match = match.group(0)  # full match including brackets
            
            error_id = str(uuid.uuid4())  # Generate unique ID for this occurrence
            
            errors.append({
                'error_id': error_id,
                'error_type': error_type,
                'error_match': error_match,
                'error_text': error_content,
                'position': len(errors),  # Sequential position for this occurrence
                'start_idx': match.start(),
                'end_idx': match.end(),
                'is_medical': ErrorExtractor._is_medical_error(error_type, error_content, medical_vocab)
            })
        
        return errors
    
    @staticmethod
    def enrich_annotation_data(data_list: List[Dict]) -> List[Dict]:
        """
        Add error extraction to annotation data.
        
        Args:
            data_list: List of annotation data items from JSON
        
        Returns:
            Enriched data with errors field containing extracted errors
        """
        for item in data_list:
            if 'asr_reconstructed' in item:
                errors = ErrorExtractor.extract_errors(
                    item['asr_reconstructed'],
                    item.get('human_transcript_ner')
                )
                item['errors'] = errors
                item['error_count'] = len(errors)
        
        return data_list


def create_error_id_mapping(asr_text: str) -> Dict[str, str]:
    """
    Create a mapping from (error_type, error_text, occurrence) to error_id.
    This is useful for consistent error identification across different runs.
    
    Args:
        asr_text: ASR reconstructed text
    
    Returns:
        Dict mapping (error_type, error_text, occurrence_index) to error_id
    """
    mapping = {}
    error_counts = {}
    
    pattern = r'\[([A-Z]+):([^\]]+)\]'
    
    for match in re.finditer(pattern, asr_text):
        error_type = match.group(1)
        error_content = match.group(2)
        key = (error_type, error_content)
        
        # Track occurrence number for this error text
        occurrence = error_counts.get(key, 0)
        error_counts[key] = occurrence + 1
        
        mapping[key + (occurrence,)] = str(uuid.uuid4())
    
    return mapping


if __name__ == '__main__':
    # Test example
    test_text = "hello [DEL:world] [INS:okay] world [DEL:okay] [INS:okay] test"
    
    print("Testing Error Extraction")
    print("=" * 60)
    print(f"Input: {test_text}")
    print(f"\nExtracted errors:")
    
    errors = ErrorExtractor.extract_errors(test_text)
    for i, error in enumerate(errors, 1):
        print(f"\n{i}. Error ID: {error['error_id']}")
        print(f"   Type: {error['error_type']}")
        print(f"   Text: {error['error_text']}")
        print(f"   Full Match: {error['error_match']}")
        print(f"   Position: {error['position']}")
        print(f"   String Index: [{error['start_idx']}:{error['end_idx']}]")
    
    print(f"\nTotal errors found: {len(errors)}")
