# ASR Inference Service (HF Whisper)

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Static Badge](https://img.shields.io/badge/package_version-0.1.0-blue)
![Static Badge](https://img.shields.io/badge/torch_version-2.3.1-green)
![Static Badge](https://img.shields.io/badge/transformers_version-4.42.3-green)
![Static Badge](https://img.shields.io/badge/model-openai/whisper--small-green)

### Overview

This repository contains an ASR service that utilises Whisper implemented with HuggingFace.

## Initial Setup - RHEL

You will need to have a Red Hat account and its corresponding registry service token to pull the RHEL images. It is recommended you create one, since they hold some of the base images we will be building our docker environments with.

Link to create a registry service account token: https://access.redhat.com/terms-based-registry/

After setting up your token, use the token to login into the Red Hat docker registry. There should be a _docker-login bash script_ provided in the Red Hat registry service portal which you can copy and paste into your terminal.

## Initial Setup - Model Weights

Download the model weights into the `pretrained_models` directory.

```bash
cd pretrained_models
git clone https://huggingface.co/openai/whisper-small

# delete unnecessary bloats from the .git hidden directory
rm -R .git
# you only neeed to keep a model of a single filetype (we keeping only the safetensors)
rm pytorch_model.bin tf_model.h5 flax_model.msgpack
```

## Setup - Overall App (VAD + ASR + Gradio)

To set up the docker container, use the `docker-compose.dev.yaml` file. This setups a docker container with the poetry configurations/requirements file and python virtual environment initialised.

You will be mounting both the:

- code directory whisper asr inference (/asr_inference_service)
- code directory silero vad (/vad)
- code directory gradio app (/app)
- model weights (/pretrained_models)

```bash
# build the image
docker-compose -f docker-compose.dev.yaml build
# start up the container
docker-compose -f docker-compose.dev.yaml up
```

## Setup - VAD

If you want to troubleshoot the Voice Activity Detector(VAD), you can build and run only that component of the docker-compose.

```bash
# build the image
docker-compose -f docker-compose.dev.yaml build vad-service
# start up the container
docker-compose -f docker-compose.dev.yaml up vad-service
```

### About VAD

The VAD is implemented using silero-vad version 5.1. It takes in a filepath as inputs and would output a list of dictionaries, with each dictionary representing 1 segment of speech. Each segment will have a 'start' and 'end' value demarking the time (in frames).

The VAD is currrently set to detect a minimum of 1 second of no speech before spliting the audio.

Within the docker environment, port 8081 is exposed.

#### VAD Endpoints

Example request with `Python`:

```python
import requests
SERVICE_URL = "http://localhost:8001/detect"
FILENAME = "examples/audio.wav"

audio_bytes = {"file": open(FILENAME, "rb")}
response = requests.post(SERVICE_URL, files=audio_bytes)

print(response.content.decode())
```

## Setup - ASR

If you want to troubleshoot the Voice Activity Detector(VAD), you can build and run only that component of the docker-compose.

```bash
# build the image
docker-compose -f docker-compose.dev.yaml build vad-service
# start up the container
docker-compose -f docker-compose.dev.yaml up vad-service
```

### About ASR-inference

The ASR-inference is implemented using Whisper-small (https://huggingface.co/openai/whisper-small). It takes in a numpy array of an audio file as inputs and would output a string, which is the transcription of the audio.

As of now, the transcriptions are all forced to English.

Within the docker environment, port 8001 is exposed.

#### ASR Endpoints

Example request with `Python`:

```python
import requests
import librosa
import json

SAMPLE_RATE = 16000
SERVICE_URL = "http://localhost:8000/v1/transcribe"
FILENAME = "examples/trump_full1.wav"

audio, _ = librosa.load(path=FILENAME, sr = SAMPLE_RATE, mono=True)
audio = audio.tolist()
print(len(audio))

audio_bytes = json.dumps({"array": audio})
response = requests.post(SERVICE_URL, audio_bytes)
response.content.decode()
```
