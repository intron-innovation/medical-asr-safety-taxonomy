#!/usr/bin/env python3
"""
AudioFlamingo 3 ASR Inference on Medical Dataset
Loads existing results with Whisper ASR and adds AudioFlamingo 3 transcriptions

Usage: Run from your AudioFlamingo 3 environment:
cd /orange/ufdatastudios/c.okocha/audio-flamingo-audio_flamingo_3
source bin/activate  # or conda activate if using conda
cd /orange/ufdatastudios/c.okocha/medical-asr-safety-taxonomy
python audioflamingo3_inference.py
"""

import os
import sys
import torch
import pandas as pd
import soundfile
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Disable problematic imports before any llava imports
os.environ['DS_SKIP_CUDA_CHECK'] = '1'
os.environ['TRITON_DISABLE_LINE_INFO'] = '1'
os.environ['DISABLE_TRITON'] = '1'

# Add AudioFlamingo 3 environment path - CRITICAL for llava imports
AUDIOFLAMINGO3_ENV_PATH = "/orange/ufdatastudios/c.okocha/audio-flamingo-audio_flamingo_3"
if AUDIOFLAMINGO3_ENV_PATH not in sys.path:
    sys.path.insert(0, AUDIOFLAMINGO3_ENV_PATH)

# Import llava library (used by AudioFlamingo 3 local)
import llava
from llava import conversation as clib
from llava.media import Sound
from transformers import GenerationConfig

def load_existing_results():
    """Load existing results CSV with Whisper ASR results"""
    try:
        # Try to load existing results first
        results_df = pd.read_csv('results/phi_4_asr_results_all.csv')
        print(f'Loaded existing results with {len(results_df)} samples')
        return results_df
    except FileNotFoundError:
        # Fallback to original dataset if results don't exist
        print('Results file not found, loading original dataset...')
        original_df = pd.read_csv('data/final_120_sampled_medical_datasets.csv')
        print(f'Loaded original dataset with {len(original_df)} samples')
        return original_df

def setup_audioflamingo3():
    """Initialize AudioFlamingo 3 LOCAL model using llava library"""
    print("Loading AudioFlamingo 3 LOCAL model...")
    
    # Use LOCAL model path (matching your working setup)
    model_path = "/orange/ufdatastudios/c.okocha/audio-flamingo-audio_flamingo_3/audio-flamingo-3"
    
    # Load model using llava (matching working script pattern)
    model = llava.load(model_path)
    
    # Set up generation config if available
    generation_config_path = os.path.join(model_path, 'llm')
    if os.path.exists(os.path.join(generation_config_path, 'generation_config.json')):
        model.generation_config = GenerationConfig.from_pretrained(generation_config_path)
    
    # Initialize conversation mode (use "auto" like working script)
    conv_mode = "auto"
    clib.default_conversation = clib.conv_templates[conv_mode].copy()
    
    print(f"Model loaded from: {model_path}")
    print("Model loaded successfully!")
    return model, model_path

def transcribe_audio_flamingo3(audio_path, model, model_path, chunk_seconds=30, max_new_tokens=500):
    """
    Transcribe audio file using AudioFlamingo 3 LOCAL model with llava library
    Following the pattern from your working scripts
    """
    if not os.path.exists(audio_path):
        return f'FILE_NOT_FOUND: {audio_path}'
    
    try:
        # Create prompt list as in working script
        prompt_list = []
        media = Sound(audio_path)
        prompt_list.append(media)
        prompt_list.append("Transcribe the input speech.")
        
        # Generate transcription using the correct method from working script
        response = model.generate_content(
            prompt_list,
            response_format=None,
            generation_config=model.generation_config
        )
        
        # Extract and return text response
        if response and len(str(response).strip()) > 0:
            return str(response).strip()
        else:
            return "ERROR: Empty response"
            
    except Exception as e:
        return f'ERROR: {e}'

def run_audioflamingo3_inference(df, model, model_path):
    """Run AudioFlamingo 3 inference on all audio files"""
    print("Running AudioFlamingo 3 LOCAL inference...")
    
    audio_paths = df['audio_file'].tolist()
    transcriptions = []
    
    for audio_path in tqdm(audio_paths, desc='AudioFlamingo 3 Transcribing'):
        transcription = transcribe_audio_flamingo3(
            audio_path, model, model_path,
            chunk_seconds=30, max_new_tokens=500
        )
        transcriptions.append(transcription)
    
    return transcriptions

def main():
    """Main execution function"""
    print("=" * 60)
    print("AudioFlamingo 3 Medical ASR Inference")
    print("=" * 60)
    
    # Load existing results
    df = load_existing_results()
    
    # Check if AudioFlamingo 3 results already exist
    if 'AudioFlamingo3-ASR' in df.columns:
        print("AudioFlamingo 3 results already exist. Skipping inference...")
        print(f"Results saved in: results/audioflamingo3_asr_results.csv")
        return
    
    # Setup AudioFlamingo 3
    model, model_path = setup_audioflamingo3()
    
    # Run inference
    transcriptions = run_audioflamingo3_inference(df, model, model_path)
    
    # Add results to dataframe
    df['AudioFlamingo3-ASR'] = transcriptions
    
    # Save results
    output_path = 'results/audioflamingo3_asr_results.csv'
    os.makedirs('results', exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Total samples processed: {len(transcriptions)}")
    
    # Show summary
    error_count = sum(1 for t in transcriptions if t.startswith('ERROR') or t.startswith('FILE_NOT_FOUND'))
    success_count = len(transcriptions) - error_count
    
    print(f"Successful transcriptions: {success_count}")
    print(f"Failed transcriptions: {error_count}")
    
    if success_count > 0:
        print("\nFirst successful transcription sample:")
        for i, t in enumerate(transcriptions):
            if not (t.startswith('ERROR') or t.startswith('FILE_NOT_FOUND')):
                print(f"Audio: {df.iloc[i]['audio_file']}")
                print(f"AudioFlamingo 3: {t[:200]}...")
                break
    
    print("\nDataframe columns:")
    print(df.columns.tolist())

if __name__ == "__main__":
    main()