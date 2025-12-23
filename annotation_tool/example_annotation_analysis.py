"""
Example: Working with Annotated Results in Pandas/Jupyter

This shows how to load and analyze the annotated results after 
processing annotations back through process_annotations.py
"""

import pandas as pd
import json
from collections import Counter

# Load your annotated results
df = pd.read_excel('results_with_annotations.xlsx')

# ============================================================================
# BASIC EXPLORATION
# ============================================================================

print("Dataset shape:", df.shape)
print("Columns:", df.columns.tolist())

# How many errors total?
total_errors = df['error_annotation_summary'].apply(lambda x: x['total_errors']).sum()
print(f"Total errors annotated: {total_errors}")

# How many utterances have errors?
annotated_utterances = (df['error_annotation_summary'].apply(lambda x: x['total_errors']) > 0).sum()
print(f"Utterances with errors: {annotated_utterances} / {len(df)}")

# ============================================================================
# ERROR STATISTICS
# ============================================================================

# Get average severity across all errors
severity_scores = []
for annotations in df['error_taxonomy_annotations']:
    for error in annotations:
        severity_scores.append(error['severity'])

print(f"\nAverage severity: {sum(severity_scores) / len(severity_scores):.2f}")
print(f"Severity distribution:")
for severity in range(6):
    count = severity_scores.count(severity)
    pct = (count / len(severity_scores)) * 100
    print(f"  Level {severity}: {count} ({pct:.1f}%)")

# ============================================================================
# TAXONOMY ANALYSIS
# ============================================================================

# Which taxonomy categories are most common?
taxonomy_counter = Counter()
for annotations in df['error_taxonomy_annotations']:
    for error in annotations:
        for tax in error.get('taxonomy', []):
            taxonomy_counter[tax] += 1

print("\nTaxonomy distribution:")
for tax, count in taxonomy_counter.most_common():
    pct = (count / sum(taxonomy_counter.values())) * 100
    print(f"  {tax}: {count} ({pct:.1f}%)")

# ============================================================================
# ERROR TYPE ANALYSIS
# ============================================================================

# How many of each error type?
error_types = Counter()
for annotations in df['error_taxonomy_annotations']:
    for error in annotations:
        error_types[error['error_type']] += 1

print("\nError types:")
for err_type in ['DEL', 'SUB', 'INS']:
    count = error_types.get(err_type, 0)
    pct = (count / sum(error_types.values())) * 100
    print(f"  {err_type}: {count} ({pct:.1f}%)")

# ============================================================================
# FILTERING & ANALYSIS
# ============================================================================

# Find all CRITICAL errors (severity 5)
critical_errors = []
for idx, row in df.iterrows():
    for error in row['error_taxonomy_annotations']:
        if error['severity'] == 5:
            critical_errors.append({
                'utterance_id': row['utterance_id'],
                'error_type': error['error_type'],
                'error_text': error['error_match'],
                'taxonomy': error['taxonomy']
            })

print(f"\nCritical errors (severity 5): {len(critical_errors)}")
for error in critical_errors[:5]:  # Show first 5
    print(f"  {error['utterance_id']}: {error['error_text']}")

# ============================================================================
# MODEL COMPARISON (if you annotated multiple models)
# ============================================================================

# Example: Compare Whisper vs other models
whisper_df = pd.read_excel('results_with_annotations.xlsx')
phi4_df = pd.read_excel('results_with_annotations.xlsx')  # if you annotated phi4

whisper_total_errors = whisper_df['error_annotation_summary'].apply(
    lambda x: x['total_errors']
).sum()

print(f"\nWhisper total errors: {whisper_total_errors}")

# ============================================================================
# EXPORT FILTERED RESULTS
# ============================================================================

# Export only critical errors to CSV
critical_df = pd.DataFrame(critical_errors)
critical_df.to_csv('critical_errors.csv', index=False)
print(f"\nCritical errors exported to: critical_errors.csv")

# ============================================================================
# MEDICATION ERRORS (Domain-Specific Analysis)
# ============================================================================

medication_errors = []
for idx, row in df.iterrows():
    for error in row['error_taxonomy_annotations']:
        if 'Medication' in error.get('taxonomy', []):
            medication_errors.append({
                'utterance_id': row['utterance_id'],
                'error': error['error_match'],
                'severity': error['severity'],
                'error_type': error['error_type']
            })

print(f"\nMedication-related errors: {len(medication_errors)}")
medication_severity = [e['severity'] for e in medication_errors]
print(f"  Average severity: {sum(medication_severity) / len(medication_severity):.2f}")
print(f"  High/Critical (4-5): {len([s for s in medication_severity if s >= 4])}")

# ============================================================================
# PLOTTING (if you have matplotlib/seaborn)
# ============================================================================

try:
    import matplotlib.pyplot as plt
    
    # Severity distribution histogram
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Histogram
    ax1.hist(severity_scores, bins=6, color='steelblue', edgecolor='black')
    ax1.set_xlabel('Severity Score')
    ax1.set_ylabel('Count')
    ax1.set_title('Error Severity Distribution')
    ax1.set_xticks(range(6))
    
    # Taxonomy pie chart
    taxonomy_data = dict(taxonomy_counter.most_common())
    ax2.pie(taxonomy_data.values(), labels=taxonomy_data.keys(), autopct='%1.1f%%')
    ax2.set_title('Error Taxonomy Distribution')
    
    plt.tight_layout()
    plt.savefig('annotation_analysis.png', dpi=150, bbox_inches='tight')
    print("\nCharts saved to: annotation_analysis.png")
    
except ImportError:
    print("\n(Install matplotlib to generate charts)")

# ============================================================================
# DETAILED ERROR REPORT
# ============================================================================

print("\n" + "="*70)
print("SAMPLE ANNOTATED ERRORS (First 5)")
print("="*70)

for idx, row in df.iterrows():
    if not row['error_taxonomy_annotations']:
        continue
    
    for i, error in enumerate(row['error_taxonomy_annotations']):
        if i >= 5:  # Only show first 5 total
            break
        
        print(f"\nUtterance: {row['utterance_id']}")
        print(f"  Error Type: {error['error_type']}")
        print(f"  Text: {error['error_match']}")
        print(f"  Taxonomy: {', '.join(error['taxonomy'])}")
        print(f"  Severity: {error['severity']}")

# ============================================================================
# INTER-ANNOTATOR AGREEMENT (if you have multiple annotators)
# ============================================================================

# Load another annotator's results
df_annotator2 = pd.read_excel('results_with_annotations_annotator2.xlsx')

# Compare severity scores for same errors
agreement_count = 0
disagreement_count = 0

for idx in range(len(df)):
    ann1_severity = [e['severity'] for e in df.iloc[idx]['error_taxonomy_annotations']]
    ann2_severity = [e['severity'] for e in df_annotator2.iloc[idx]['error_taxonomy_annotations']]
    
    if ann1_severity == ann2_severity:
        agreement_count += 1
    else:
        disagreement_count += 1

print(f"\nAnnotator agreement: {agreement_count} / {len(df)} utterances match")

# ============================================================================
# SAVE ANALYSIS SUMMARY
# ============================================================================

summary = {
    'total_annotated_errors': total_errors,
    'total_utterances': len(df),
    'utterances_with_errors': annotated_utterances,
    'average_severity': sum(severity_scores) / len(severity_scores),
    'error_type_breakdown': dict(error_types),
    'taxonomy_breakdown': dict(taxonomy_counter),
    'critical_errors_count': len(critical_errors),
    'medication_errors_count': len(medication_errors)
}

with open('annotation_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n✅ Analysis summary saved to: annotation_summary.json")
