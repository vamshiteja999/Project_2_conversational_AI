# Sentiment Analysis Application

## Overview

This application is a comprehensive sentiment analysis tool that leverages Google Cloud services to analyze the sentiment of both text and speech inputs. It provides a user-friendly interface for sentiment analysis, text-to-speech conversion, and speech-to-text transcription.

## Features

1. **Text Sentiment Analysis**: Analyze the sentiment of user-provided text input.
2. **Speech Sentiment Analysis**: Convert speech to text and analyze its sentiment.
3. **Text-to-Speech Conversion**: Convert text input to speech.
4. **Speech-to-Text Conversion**: Transcribe audio input to text.
5. **Result Storage**: Save analysis results with unique IDs for future reference.
6. **History Tracking**: Retrieve past analysis results.
7. **Audio Playback**: Play back previously recorded audio inputs.

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **External Services**: Google Cloud Natural Language API, Google Cloud Speech-to-Text API, Google Cloud Text-to-Speech API

## Setup and Installation

1. Clone the repository.
2. Install the required Python packages:
   ```
   pip install fastapi uvicorn google-cloud-speech google-cloud-language google-cloud-texttospeech
   ```
3. Set up a Google Cloud project and enable the necessary APIs (Natural Language, Speech-to-Text, Text-to-Speech).
4. Download your Google Cloud credentials JSON file and set the path in the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

## Usage

1. Start the FastAPI server:
   ```
   python main.py
   ```
2. Open a web browser and navigate to `http://localhost:8000`.
3. Use the interface to input text or record speech for analysis.

## API Endpoints

- `POST /analyze-text`: Analyze sentiment of text input
- `POST /text-to-speech`: Convert text to speech
- `POST /speech-to-text`: Convert speech to text
- `POST /analyze-speech`: Analyze sentiment of speech input
- `GET /get-history`: Retrieve analysis history
- `GET /get-audio/{filename}`: Retrieve a specific audio file
- `GET /get-result/{result_id}`: Retrieve a specific analysis result

## Key Components

1. **FastAPI Application**: Handles HTTP requests and routes them to appropriate functions.
2. **Google Cloud Clients**: Interface with Google Cloud services for AI-powered analysis and conversions.
3. **Utility Functions**: 
   - `analyze_sentiment()`: Processes text through Google's Natural Language API
   - `interpret_sentiment()`: Classifies sentiment based on score
   - `save_result()`: Stores analysis results
   - `text_to_speech()`: Converts text to speech using Google's Text-to-Speech API
   - `speech_to_text()`: Transcribes audio using Google's Speech-to-Text API

## Data Storage

- Analysis results are stored as JSON files in the `sentiment_results` directory.
- Audio files are stored in the `audio_files` directory.

## Error Handling

The application includes comprehensive error handling and logging:
- Input validation to ensure non-empty text and audio inputs
- Proper error responses for various scenarios (e.g., file not found, API errors)
- Logging of errors and important events for debugging

## Security Considerations

- Ensure that your Google Cloud credentials are kept secure and not exposed publicly.
- Implement proper authentication and authorization if deploying this application in a production environment.

## Future Improvements

1. Implement user authentication for personalized history tracking.
2. Add support for multiple languages in sentiment analysis and speech processing.
3. Enhance the UI with more detailed sentiment visualizations.
4. Implement batch processing for large volumes of text or audio files.

## Contributing

Contributions to improve the application are welcome. Please follow the standard fork-and-pull request workflow.

