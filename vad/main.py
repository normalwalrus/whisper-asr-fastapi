import io
import logging

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from starlette.status import HTTP_200_OK
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

from schemas import ASRResponse, HealthResponse

SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 8081

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO
)

app = FastAPI()
model = load_silero_vad()

@app.get("/", status_code=HTTP_200_OK)
async def read_root():
    """Root Call"""
    return {"message": "This is a VAD service."}


@app.get("/health")
async def read_health() -> HealthResponse:
    """
    Check if the API endpoint is available.

    This endpoint is used by Docker to check the health of the container.
    """
    return {"status": "HEALTHY"}


@app.post("/detect", response_model=ASRResponse)
async def detect(file: UploadFile = File(...)):
    """Function call to takes in an audio file as bytes, and executes model inference"""

    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="File uploaded is not a wav file.")

    # Receive the audio bytes from the request
    audio_bytes = file.file.read()
    print(io.BytesIO(audio_bytes))

    # load with soundfile, data will be a numpy array
    wav = read_audio(io.BytesIO(audio_bytes))
    speech_timestamps = get_speech_timestamps(wav, 
                                              model, 
                                              threshold=0.8,
                                              min_silence_duration_ms=1000)

    return {"speech_timestamps": str(speech_timestamps)}


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
