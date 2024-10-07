"""ASR Inference Model Class"""

import logging
from time import perf_counter

import librosa
import numpy as np
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO
)

DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
logging.info("Running on device: %s", DEVICE)


class ASRModelForInference:
    """Base class for ASR model for inference"""

    def __init__(self, model_dir: str, sample_rate: int = 16000):
        """
        Inputs:
            model_dir (str): path to model directory
            sample_rate (int): the target sample rate in which the model accepts
        """

        self.init_model(model_dir)
        self.target_sr = sample_rate

    def init_model(self, model_dir: str):
        """Method to initialise model on class initialisation

        Inputs:
            model_dir (str): path to model directory
        """

        logging.info("Loading model...")
        model_load_start = perf_counter()

        self.processor = WhisperProcessor.from_pretrained(model_dir)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_dir)
        self.model.to(DEVICE)
        self.model.config.forced_decoder_ids = None
        self.model.eval()
        
        #################### Set to English and Transcription task ###############
        LANGUAGE = 'English'
        TASK = 'transcribe'
        self.model.config.forced_decoder_ids = self.processor.tokenizer.get_decoder_prompt_ids(
            language=LANGUAGE, task=TASK
            )
        self.model.config.suppress_tokens = []
        self.model.generation_config.forced_decoder_ids = self.processor.tokenizer.get_decoder_prompt_ids(
            language=LANGUAGE, task=TASK
            )
        self.model.generation_config.suppress_tokens = []
        ##########################################################################
        
        model_load_end = perf_counter()
        logging.info(
            "Model loaded. Elapsed time: %s", model_load_end - model_load_start
        )

    def load_audio(self, audio_filepath: str) -> np.ndarray:
        """Method to load an audio filepath to generate a waveform, it automatically
        standardises the waveform to the target sample rate and channel

        Inputs:
            audio_filepath (str): path to the audio file

        Returns:
            waveform (np.ndarray) of shape (T,)
        """

        waveform, _ = librosa.load(audio_filepath, sr=self.target_sr, mono=True)

        return waveform

    def infer(self, waveform: np.ndarray, input_sr: int) -> str:
        """Method to run inference on a waveform to generate a transcription

        Inputs:
            waveform (np.ndarray): Takes in waveform of shape (T,)
            input_sr (int): Sample rate of input waveform

        Returns:
            transcription (str): Output text generated by the ASR model
        """
        inference_start = perf_counter()

        if input_sr != self.target_sr:
            waveform = librosa.resample(
                waveform, orig_sr=input_sr, target_sr=self.target_sr
            )
            

        # pad input values and return pt tensor
        input_features = self.processor(
            waveform, sampling_rate=self.target_sr, return_tensors="pt"
        ).input_features
        input_features = input_features.to(DEVICE)

        with torch.no_grad():
            predicted_ids = self.model.generate(input_features)
            
        transcription = self.processor.batch_decode(
            predicted_ids, skip_special_tokens=True
        )[0]
        print(transcription)

        inference_end = perf_counter()
        logging.info(
            "Model inference triggered. Elapsed time: %s",
            inference_end - inference_start,
        )

        return transcription#.strip()


if __name__ == "__main__":
    pass