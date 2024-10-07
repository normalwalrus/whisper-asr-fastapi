import gradio as gr
import requests
import json
import ast
import librosa
import logging

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO
)

SAMPLE_RATE = 16000

def get_entry_from_response(response, key = 'transcription'):
    
    '''
    Gets the entry from a string that mimics a dictionary
    '''
    
    dictionary_data = json.loads(response)
    
    return dictionary_data[key]

def transcribe(audio_array):
    '''
    Transcribe the audio file with Whisper model container loaded using FastAPI
    '''

    SERVICE_URL = "http://asr-service:8080/v1/transcribe"
    
    audio = audio_array.tolist()
    audio_bytes = json.dumps({"array": audio})
    
    response = requests.post(SERVICE_URL, audio_bytes)
    response = response.content.decode()
    
    transcription = get_entry_from_response(response=response)
    
    return transcription

def vad(audio_file):
    '''
    Get the segments of speech in an audio file and returns a list of dictionaries
    '''
    SERVICE_URL = "http://vad-service:8081/detect"

    audio_bytes = {"file": open(audio_file, "rb")}
    response = requests.post(SERVICE_URL, files=audio_bytes)
    response = response.content.decode()
    
    segments = get_entry_from_response(response=response, key='speech_timestamps')
    segments = ast.literal_eval(segments)
    
    return segments


def main(audio, with_vad):
    '''
    Function to combine both VAD and ASR service.
    This also reads the audio file to feed into the asr_service.
    '''
    
    audio_array, _ = librosa.load(path=audio, sr=SAMPLE_RATE, mono=True)
    
    if with_vad:
        segments = vad(audio)
    else:
        segments = [{'start':0, 'end':len(audio_array)}]
        
    final_transcription = ''
    
    for segment in segments:
        start_frame = segment['start']
        end_frame = segment['end']
        
        split_audio = audio_array[start_frame:end_frame]
   
        transcription = transcribe(split_audio)
        
        start_time = start_frame/SAMPLE_RATE
        end_time = end_frame/SAMPLE_RATE
        
        segment_string = f'[{start_time} - {end_time}] : {transcription}\n'
        final_transcription += segment_string
    
    return final_transcription

inputs = [gr.Audio(type='filepath', label = 'Audio'),
          gr.Checkbox(label='VAD')]


demo = gr.Interface(
    fn=main,
    inputs=inputs,
    outputs=["text"],
)

demo.launch()