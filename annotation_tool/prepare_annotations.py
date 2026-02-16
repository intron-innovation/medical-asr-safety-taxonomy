"""
Prepare ASR data for annotation interface.

This script takes the processed ASR results from your notebook and exports them
in JSON format that can be loaded into the annotation_interface.html tool.

Usage:
    python prepare_annotations.py --input <excel_file> --output <json_file> --model <model_name>

Example:
    python prepare_annotations.py --input selected_sessions_normalized.xlsx --output annotation_data.json --model whisper
"""

import pandas as pd
import json
import argparse
from pathlib import Path


def prepare_annotation_data(excel_file: str, model: str, output_file: str = None) -> str:
    """
    Prepare annotation data from processed ASR results.
    
    Parameters:
    -----------
    excel_file : str
        Path to the Excel file with processed results (selected_sessions_normalized.xlsx)
    model : str
        ASR model name (whisper, phi4, parakeet, granite)
    output_file : str, optional
        Output JSON file path. If None, uses '<model>_annotation_data.json'
    
    Returns:
    --------
    str
        Path to the created JSON file
    """
    
    if output_file is None:
        output_file = f"{model}_annotation_data.json"
    
    print(f"Loading data from {excel_file}...")
    df = pd.read_excel(excel_file, engine='openpyxl')
    
    # Validate required columns
    required_cols = {
        'utterance_id': 'utterance_id',
        'human': 'human-transcript',
        'asr': f'{model}_reconstructed_ref',
        'asr_transcript': f'{model}-asr'
    }
    
    for col_key, col_name in required_cols.items():
        if col_name not in df.columns:
            raise ValueError(f"Required column '{col_name}' not found in Excel file")
    
    # Prepare data
    annotation_data = []
    
    for idx, row in df.iterrows():
        entry = {
            'utterance_id': str(row['utterance_id']),
            'human_transcript': str(row['human-transcript']) if pd.notna(row['human-transcript']) else "",
            'asr_reconstructed': str(row[f'{model}_reconstructed_ref']) if pd.notna(row[f'{model}_reconstructed_ref']) else "",
            'asr_transcript': str(row[f'{model}-asr']) if pd.notna(row[f'{model}-asr']) else "",
            'model': model,
            'wer': float(row[f'norm_{model}_asr_wer']) if pd.notna(row[f'norm_{model}_asr_wer']) else None,
            'index': idx
        }
        annotation_data.append(entry)
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotation_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Successfully prepared {len(annotation_data)} utterances")
    print(f"   Saved to: {output_file}")
    print(f"\n📖 Next Steps:")
    print(f"   1. Open annotation_interface.html in your web browser")
    print(f"   2. Click '📁 Load JSON File' and select {output_file}")
    print(f"   3. Start annotating errors by clicking on highlighted text")
    print(f"   4. Click '💾 Export Annotations' when done to save your work")
    
    return output_file


def prepare_primock_annotation_data(excel_file: str, output_file: str = None) -> str:
    """
    Prepare annotation data from primock merged results.
    
    Parameters:
    -----------
    excel_file : str
        Path to the Excel file with primock merged results
    output_file : str, optional
        Output JSON file path. If None, uses 'primock_annotation_data.json'
    
    Returns:
    --------
    str
        Path to the created JSON file
    """
    
    if output_file is None:
        output_file = "primock_annotation_data.json"
    
    print(f"Loading data from {excel_file}...")
    df = pd.read_excel(excel_file, engine='openpyxl')
    
    # Validate required columns
    required_cols = ['conversation_id', 'turns', 'doctor_utterances', 'patient_utterances',
                     'whisper_doctor_reconstructed_human', 'whisper_patient_reconstructed_human']
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in Excel file")
    
    # Prepare data (both doctor and patient)
    annotation_data = []
    
    for idx, row in df.iterrows():
        # Doctor utterance
        doc_entry = {
            'conversation_id': str(row['conversation_id']),
            'turns': int(row['turns']) if pd.notna(row['turns']) else 0,
            'speaker': 'doctor',
            'human_transcript': str(row['doctor_utterances']) if pd.notna(row['doctor_utterances']) else "",
            'asr_reconstructed': str(row['whisper_doctor_reconstructed_human']) if pd.notna(row['whisper_doctor_reconstructed_human']) else "",
            'asr_transcript': str(row['whisper_doctor_asr_transcript']) if pd.notna(row['whisper_doctor_asr_transcript']) else "",
            'index': idx * 2
        }
        annotation_data.append(doc_entry)
        
        # Patient utterance
        pat_entry = {
            'conversation_id': str(row['conversation_id']),
            'turns': int(row['turns']) if pd.notna(row['turns']) else 0,
            'speaker': 'patient',
            'human_transcript': str(row['patient_utterances']) if pd.notna(row['patient_utterances']) else "",
            'asr_reconstructed': str(row['whisper_patient_reconstructed_human']) if pd.notna(row['whisper_patient_reconstructed_human']) else "",
            'asr_transcript': str(row['whisper_patient_asr_transcript']) if pd.notna(row['whisper_patient_asr_transcript']) else "",
            'index': idx * 2 + 1
        }
        annotation_data.append(pat_entry)
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotation_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Successfully prepared {len(annotation_data)} utterances (doctor + patient)")
    print(f"   Saved to: {output_file}")
    print(f"\n📖 Next Steps:")
    print(f"   1. Open annotation_interface.html in your web browser")
    print(f"   2. Click '📁 Load JSON File' and select {output_file}")
    print(f"   3. Start annotating errors by clicking on highlighted text")
    print(f"   4. Click '💾 Export Annotations' when done to save your work")
    
    return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Prepare ASR data for annotation interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare Whisper ASR data
  python prepare_annotations.py --input all_result_processed.xlsx --model whisper
  
  # Prepare Phi-4 ASR data with custom output file
  python prepare_annotations.py --input all_result_processed.xlsx --model phi4 --output custom_output.json
  
  # Prepare Primock data
  python prepare_annotations.py --primock primock_result_separate_sheets.xlsx
        """
    )
    
    parser.add_argument('--input', type=str, default='all_result_processed.xlsx',
                        help='Path to input Excel file (default: all_result_processed.xlsx)')
    parser.add_argument('--model', type=str, choices=['whisper', 'phi4', 'parakeet', 'granite'],
                        default='whisper',
                        help='ASR model to prepare (default: whisper)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output JSON file path (default: {model}_annotation_data.json)')
    parser.add_argument('--primock', type=str, default=None,
                        help='Prepare Primock data from this Excel file')
    
    args = parser.parse_args()
    
    if args.primock:
        prepare_primock_annotation_data(args.primock, args.output)
    else:
        prepare_annotation_data(args.input, args.model, args.output)
