"""
API module for ASR service.

This module provides the FastAPI application for performing ASR.
"""

import io
import logging
import os
import json

import soundfile as sf
import numpy as np
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.status import HTTP_200_OK
from typing import List

from asr_inference_service.model import ASRModelForInference
from asr_inference_service.schemas import ASRResponse, HealthResponse

SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 8080

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO
)

app = FastAPI()
model = ASRModelForInference(
    model_dir=os.environ["PRETRAINED_MODEL_DIR"],
    sample_rate=int(os.environ["SAMPLE_RATE"]),
)

class AudioData(BaseModel):
    array: list

@app.get("/", status_code=HTTP_200_OK)
async def read_root():
    """Root Call"""
    return {"message": "This is an ASR service."}


@app.get("/health")
async def read_health() -> HealthResponse:
    """
    Check if the API endpoint is available.

    This endpoint is used by Docker to check the health of the container.
    """
    return {"status": "HEALTHY"}


@app.post("/v1/transcribe", response_model=ASRResponse)
async def transcribe(data: Request):
    """Function call to takes in an audio file as bytes, and executes model inference"""
    data = await data.json()
    
    print(len(data['array']))
    
    transcription = model.infer(data['array'], 16000)
    
    return {"transcription": str(transcription)}

def start():
    """Launched with `start` at root level"""
    uvicorn.run(
        "asr_inference_service.main:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=False,
    )


if __name__ == "__main__":
    start()
