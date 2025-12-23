"""
Process annotation results and merge them back into your DataFrame.

This script takes the exported annotations from the annotation interface and
merges them back into your processed ASR results.

Usage:
    python process_annotations.py --annotations <json_file> --original <excel_file> --output <output_file>

Example:
    python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from collections import defaultdict


def process_annotations(annotations_file: str, original_excel: str, output_excel: str = None) -> pd.DataFrame:
    """
    Process annotations and merge them back into the original DataFrame.
    
    Parameters:
    -----------
    annotations_file : str
        Path to the exported annotations JSON file
    original_excel : str
        Path to the original processed Excel file
    output_excel : str, optional
        Output Excel file path. If None, creates 'results_with_annotations.xlsx'
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with annotations merged in
    """
    
    print(f"Loading annotations from {annotations_file}...")
    with open(annotations_file, 'r', encoding='utf-8') as f:
        annotations_data = json.load(f)
    
    print(f"Loading original data from {original_excel}...")
    df = pd.read_excel(original_excel, engine='openpyxl')
    
    # Create annotation lookup tables
    error_annotations = defaultdict(list)  # utterance_id -> list of error annotations
    
    for utt_idx, errors in annotations_data['annotations'].items():
        for error in errors:
            error_annotations[error['utterance_id']].append(error)
    
    # Create summary columns
    df['error_taxonomy_annotations'] = df['utterance_id'].apply(
        lambda uid: error_annotations.get(str(uid), [])
    )
    
    df['error_annotation_summary'] = df['utterance_id'].apply(
        lambda uid: create_summary(error_annotations.get(str(uid), []))
    )
    
    # Create detailed annotation columns
    df['deletion_annotations'] = df['utterance_id'].apply(
        lambda uid: get_errors_by_type(error_annotations.get(str(uid), []), 'DEL')
    )
    df['substitution_annotations'] = df['utterance_id'].apply(
        lambda uid: get_errors_by_type(error_annotations.get(str(uid), []), 'SUB')
    )
    df['insertion_annotations'] = df['utterance_id'].apply(
        lambda uid: get_errors_by_type(error_annotations.get(str(uid), []), 'INS')
    )
    
    # Save to Excel with annotations
    if output_excel is None:
        output_excel = 'results_with_annotations.xlsx'
    
    df.to_excel(output_excel, index=False, engine='openpyxl')
    
    # Print statistics
    print("\n" + "="*60)
    print("ANNOTATION PROCESSING SUMMARY")
    print("="*60)
    print(f"Total annotations processed: {annotations_data['total_annotations']}")
    print(f"Total utterances: {len(df)}")
    print(f"Annotated utterances: {df['error_annotation_summary'].apply(lambda x: x['total_errors'] > 0).sum()}")
    
    # Error type breakdown
    error_types = {'DEL': 0, 'SUB': 0, 'INS': 0}
    taxonomy_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    
    for utt_idx, errors in annotations_data['annotations'].items():
        for error in errors:
            error_types[error['error_type']] += 1
            for tax in error['taxonomy']:
                taxonomy_counts[tax] += 1
            severity_counts[error['severity']] += 1
    
    print("\n📊 Error Type Breakdown:")
    for err_type, count in sorted(error_types.items()):
        print(f"  {err_type}: {count}")
    
    print("\n🏷️ Taxonomy Distribution:")
    for tax, count in sorted(taxonomy_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / annotations_data['total_annotations']) * 100
        print(f"  {tax}: {count} ({pct:.1f}%)")
    
    print("\n⚠️ Severity Distribution:")
    severity_labels = {0: 'None', 1: 'Minor', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Critical'}
    for severity in range(6):
        count = severity_counts.get(severity, 0)
        pct = (count / annotations_data['total_annotations']) * 100 if annotations_data['total_annotations'] > 0 else 0
        print(f"  {severity} ({severity_labels[severity]}): {count} ({pct:.1f}%)")
    
    print(f"\n✅ Results saved to: {output_excel}")
    print("="*60)
    
    return df


def create_summary(errors: list) -> dict:
    """Create a summary of annotations for an utterance."""
    if not errors:
        return {'total_errors': 0, 'average_severity': 0, 'taxonomy_tags': []}
    
    total = len(errors)
    avg_severity = sum(e.get('severity', 0) for e in errors) / total if total > 0 else 0
    
    taxonomy_set = set()
    for error in errors:
        taxonomy_set.update(error.get('taxonomy', []))
    
    return {
        'total_errors': total,
        'average_severity': round(avg_severity, 2),
        'taxonomy_tags': sorted(list(taxonomy_set))
    }


def get_errors_by_type(errors: list, error_type: str) -> list:
    """Get all errors of a specific type with their annotations."""
    return [
        {
            'text': e.get('error_match', ''),
            'taxonomy': e.get('taxonomy', []),
            'severity': e.get('severity', 0)
        }
        for e in errors if e.get('error_type') == error_type
    ]


def create_annotation_report(annotations_file: str, output_csv: str = None) -> pd.DataFrame:
    """
    Create a detailed CSV report of all annotations.
    
    Parameters:
    -----------
    annotations_file : str
        Path to the exported annotations JSON file
    output_csv : str, optional
        Output CSV file path
    
    Returns:
    --------
    pd.DataFrame
        Detailed annotation report
    """
    
    print(f"\nCreating detailed annotation report from {annotations_file}...")
    
    with open(annotations_file, 'r', encoding='utf-8') as f:
        annotations_data = json.load(f)
    
    rows = []
    for utt_idx, errors in annotations_data['annotations'].items():
        for error in errors:
            rows.append({
                'utterance_id': error['utterance_id'],
                'error_type': error['error_type'],
                'error_text': error['error_match'],
                'taxonomy': '; '.join(error['taxonomy']),
                'severity': error['severity'],
                'timestamp': error.get('timestamp', 'N/A')
            })
    
    df_report = pd.DataFrame(rows)
    
    if output_csv is None:
        output_csv = 'annotation_report.csv'
    
    df_report.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"✅ Report saved to: {output_csv}")
    
    return df_report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process annotation results and merge back into DataFrame',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process annotations and merge with original data
  python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx
  
  # Process with custom output file
  python process_annotations.py --annotations asr_annotations_1234567890.json --original all_result_processed.xlsx --output my_results.xlsx
  
  # Create detailed report
  python process_annotations.py --annotations asr_annotations_1234567890.json --report
        """
    )
    
    parser.add_argument('--annotations', type=str, required=True,
                        help='Path to exported annotations JSON file')
    parser.add_argument('--original', type=str, default='all_result_processed.xlsx',
                        help='Path to original processed Excel file')
    parser.add_argument('--output', type=str, default=None,
                        help='Output Excel file path')
    parser.add_argument('--report', action='store_true',
                        help='Also create a detailed CSV report')
    parser.add_argument('--report-output', type=str, default='annotation_report.csv',
                        help='Output CSV report file path')
    
    args = parser.parse_args()
    
    # Process annotations
    df = process_annotations(args.annotations, args.original, args.output)
    
    # Create report if requested
    if args.report:
        create_annotation_report(args.annotations, args.report_output)
