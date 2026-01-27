#!/usr/bin/env python
# coding: utf-8

# ## Load cleaned datasets

# In[9]:


import pandas as pd

all_datasets_df = pd.read_csv('data/final_120_sampled_medical_datasets.csv')
print('Loaded all datasets merged:', len(all_datasets_df))

# # select first 2 for testing
# all_datasets_df = all_datasets_df.head(2)


# ## Phi-4 Model

# In[10]:


import os
import requests
import torch
from PIL import Image
import soundfile
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig

# import datasets
from datasets import load_dataset
import torchcodec
import os
from tqdm import tqdm


# In[11]:


# Load model and processor
model_path = "kumapo/Phi-4-multimodal-instruct"
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    device_map="cuda", 
    torch_dtype="auto", 
    trust_remote_code=True,
    _attn_implementation='eager',
).cuda()
generation_config = GenerationConfig.from_pretrained(model_path)


# In[12]:


user_prompt = '<|user|>'
assistant_prompt = '<|assistant|>'
prompt_suffix = '<|end|>'
speech_prompt = "Based on the attached audio, generate a comprehensive text transcription of the spoken content."

def transcribe_file_chunked(audio_path, chunk_seconds=30, max_new_tokens=500):
    if not os.path.exists(audio_path):
        return f'FILE_NOT_FOUND: {audio_path}'
    try:
        data, sr = soundfile.read(audio_path)  # (numpy array, sample_rate)
        # ensure mono (if stereo, average channels)
        if data.ndim > 1:
            data = data.mean(axis=1)
        total_samples = data.shape[0]
        chunk_samples = int(chunk_seconds * sr)
        if chunk_samples <= 0:
            return "ERROR: invalid chunk_seconds"
        segments = []
        for start in range(0, total_samples, chunk_samples):
            seg = data[start : start + chunk_samples]
            if seg.size == 0:
                continue
            segments.append((seg, sr))
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        texts = []
        for i, seg in enumerate(segments):
            prompt = f'{user_prompt}<|audio_1|>{speech_prompt}{prompt_suffix}{assistant_prompt}'
            inputs = processor(text=prompt, audios=[seg], return_tensors='pt').to(device)
            generate_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                generation_config=generation_config,
                use_cache=False,
                min_length=1,
                top_p=1.0,
                repetition_penalty=1.0,
                length_penalty=1.0,
                temperature=1.0,
                do_sample=False,
                num_beams=1,
            )
            # slice off prompt tokens
            generate_ids = generate_ids[:, inputs['input_ids'].shape[1] : ]
            resp = processor.batch_decode(
                generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0].strip()
            texts.append(resp)
            # cleanup to reduce peak memory
            try:
                del inputs, generate_ids
            except Exception:
                pass
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        # join segment transcriptions (you can change separator)
        return " ".join(t for t in texts if t)
    except Exception as e:
        return f'ERROR: {e}'

audio_path = all_datasets_df['audio_file'].tolist()
all_datasets_df['Phi-4-ASR'] = [transcribe_file_chunked(path, chunk_seconds=30, max_new_tokens=500) for path in tqdm(audio_path, desc='Transcribing Audio')]


# ## Whisper ASR Model

# In[7]:


import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from datasets import load_dataset


# use a device id for pipeline (int) and a torch device string for .to()
torch_device = "cuda:0" if torch.cuda.is_available() else "cpu"
device_id = 0 if torch.cuda.is_available() else -1
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
# move the model to the proper device
model.to(torch_device)

processor = AutoProcessor.from_pretrained(model_id)

# create the pipeline; we keep model/tokenizer/feature_extractor explicit
# note: pass device as int (0 for cuda, -1 for cpu) to the pipeline
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device_id,
    generate_kwargs={
        'max_new_tokens': 256,
        'num_beams': 1,
        'do_sample': False,
        'repetition_penalty': 1.0,
        'language': 'english'
    }
)


# In[8]:


# Run Whisper ASR on all audio files in the dataframe for both doctor and patient
def run_whisper_asr(audio_paths, desc):
    responses = []
    for audio_path in tqdm(audio_paths, desc=desc):
        try:
            result = pipe(
                audio_path, 
                return_timestamps=True, 
                chunk_length_s=30,
                generate_kwargs={'language': 'english'}
            )
            responses.append(result.get("text", ""))
        except Exception as e:
            responses.append(f'ERROR: {e}')
    return responses

# primock_datasets['Whisper-ASR-Doctor'] = run_whisper_asr(primock_datasets['doctor_audio_path'].tolist(), 'Whisper Doctor Transcribing')
# primock_datasets['Whisper-ASR-Patient'] = run_whisper_asr(primock_datasets['patient_audio_path'].tolist(), 'Whisper Patient Transcribing')
all_datasets_df['Whisper-ASR'] = run_whisper_asr(all_datasets_df['audio_file'].tolist(), 'Whisper Audio Transcribing')


# In[ ]:


# save results to csv
all_datasets_df.to_csv('results/whisper_phi4_asr_results_all.csv', index=False)

