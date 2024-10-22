import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.cloud import texttospeech, speech, language_v1
import io
import os
import base64
import uuid
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "expanded-symbol-436721-q7-1c5b7ff0d4be.json"
RESULTS_DIR = "sentiment_results"
AUDIO_DIR = "audio_files"

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

app = FastAPI()

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize clients
tts_client = texttospeech.TextToSpeechClient()
speech_client = speech.SpeechClient()
language_client = language_v1.LanguageServiceClient()

# Pydantic models
class SentimentResponse(BaseModel):
    sentiment: str
    score: float
    magnitude: float
    result_id: str

class TextToSpeechResponse(BaseModel):
    audio: str

class SpeechToTextResponse(BaseModel):
    transcript: str
    audio_filename: str

class AnalyzeSpeechRequest(BaseModel):
    transcript: str
    audio_filename: str

# Utility functions
def analyze_sentiment(text_content: str):
    document = language_v1.Document(content=text_content, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = language_client.analyze_sentiment(request={'document': document})
    return response

def interpret_sentiment(score: float) -> str:
    if score > 0.25:
        return "Positive"
    elif score < -0.25:
        return "Negative"
    else:
        return "Neutral"

from datetime import datetime

def save_result(text: str, sentiment: str, score: float, magnitude: float, audio_filename: str = None) -> str:
    result_id = str(uuid.uuid4())
    result = {
        "id": result_id,
        "text": text,
        "sentiment": sentiment,
        "score": score,
        "magnitude": magnitude,
        "audio_filename": audio_filename,
        "date": datetime.now().isoformat()  # Add this line
    }

    filename = os.path.join(RESULTS_DIR, f"{result_id}.json")
    with open(filename, 'w') as f:
        json.dump(result, f)

    return result_id

def text_to_speech(text: str) -> str:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    return base64.b64encode(response.audio_content).decode('utf-8')


# Routes
@app.get("/")
async def read_index():
    return FileResponse('static/index2.html')

@app.post("/analyze-text", response_model=SentimentResponse)
async def analyze_text_endpoint(text: str = Form(...)):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    response = analyze_sentiment(text)
    sentiment = interpret_sentiment(response.document_sentiment.score)

    result_id = save_result(
        text,
        sentiment,
        response.document_sentiment.score,
        response.document_sentiment.magnitude
    )

    return SentimentResponse(
        sentiment=sentiment,
        score=response.document_sentiment.score,
        magnitude=response.document_sentiment.magnitude,
        result_id=result_id
    )

@app.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech_endpoint(text: str = Form(...)):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    audio_base64 = text_to_speech(text)
    return TextToSpeechResponse(audio=audio_base64)

def speech_to_text(audio_content: bytes):
    if not audio_content:
        logger.error("No audio content provided")
        raise ValueError("No audio content provided")

    if len(audio_content) < 100:  # Arbitrary small size to check for essentially empty files
        logger.error(f"Audio content too small: {len(audio_content)} bytes")
        raise ValueError("Audio content too small, possibly corrupted")

    audio = speech.RecognitionAudio(content=audio_content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="en-US"
    )

    try:
        logger.info(f"Sending request to Google Speech-to-Text API. Audio content size: {len(audio_content)} bytes")
        response = speech_client.recognize(config=config, audio=audio)
        logger.info(f"Received response from Google Speech-to-Text API: {response}")
    except Exception as e:
        logger.error(f"Error in speech recognition: {str(e)}")
        raise ValueError(f"Error in speech recognition: {str(e)}")

    if not response.results:
        logger.warning("No speech detected in the audio")
        raise ValueError("No speech detected in the audio")

    transcript = response.results[0].alternatives[0].transcript

    audio_filename = f"{str(uuid.uuid4())}.webm"
    with open(os.path.join(AUDIO_DIR, audio_filename), 'wb') as f:
        f.write(audio_content)

    logger.info(f"Speech-to-text conversion successful. Transcript: {transcript}")
    return transcript, audio_filename

@app.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text_endpoint(file: UploadFile = File(...)):
    if not file:
        logger.error("No file provided")
        raise HTTPException(status_code=400, detail="No file provided")

    audio_content = await file.read()
    if not audio_content:
        logger.error("Empty audio file")
        raise HTTPException(status_code=400, detail="Empty audio file")

    logger.info(f"Received audio file: {file.filename}, Size: {len(audio_content)} bytes")

    try:
        transcript, audio_filename = speech_to_text(audio_content)
    except ValueError as e:
        logger.error(f"Error in speech-to-text conversion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return SpeechToTextResponse(transcript=transcript, audio_filename=audio_filename)

@app.post("/analyze-speech", response_model=SentimentResponse)
async def analyze_speech_endpoint(request: AnalyzeSpeechRequest):
    if not request.transcript:
        raise HTTPException(status_code=400, detail="No transcript provided")

    sentiment_response = analyze_sentiment(request.transcript)
    sentiment = interpret_sentiment(sentiment_response.document_sentiment.score)

    result_id = save_result(
        request.transcript,
        sentiment,
        sentiment_response.document_sentiment.score,
        sentiment_response.document_sentiment.magnitude,
        request.audio_filename
    )

    return SentimentResponse(
        sentiment=sentiment,
        score=sentiment_response.document_sentiment.score,
        magnitude=sentiment_response.document_sentiment.magnitude,
        result_id=result_id
    )

@app.get("/get-history")
async def get_history():
    history = []
    for filename in os.listdir(RESULTS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(RESULTS_DIR, filename), 'r') as f:
                history.append(json.load(f))
    return history

@app.get("/get-audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/webm")
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/get-result/{result_id}")
async def get_result_endpoint(result_id: str):
    try:
        with open(os.path.join(RESULTS_DIR, f"{result_id}.json"), 'r') as f:
            result = json.load(f)
        return JSONResponse(content=result)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Result not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)