# AI Voice Note Pro

AI Voice Note Pro is a Streamlit app for turning spoken notes, uploaded audio, and text-based documents into clear summaries and downloadable voice recaps.

It combines local speech transcription with AI-assisted summarization, multilingual output, and simple export tools in one interface.

## Features

- Live voice recording with automatic stop after silence
- Stop and cancel controls during recording
- Audio upload support for `mp3`, `wav`, `m4a`, and `ogg`
- Document upload support for `txt` and text-based `pdf`
- Automatic transcription with Whisper
- AI-assisted summarization with provider support for:
  - Groq
  - OpenAI
- Multilingual summary targeting:
  - English
  - Hindi
  - Marathi
  - Tamil
  - Urdu
- Voice summary generation with downloadable MP3 output
- Summary export and transcription export

## Tech Stack

- Python
- Streamlit
- Whisper (`openai-whisper`)
- OpenAI-compatible client SDK
- Groq or OpenAI for summary generation
- gTTS for text-to-speech
- PyPDF for PDF text extraction

## Project Structure

```text
ai-voice-project/
├── main_app.py
├── run.py
├── requirements.txt
├── .env
├── src/
│   └── core/
│       ├── audio_recorder.py
│       ├── document_reader.py
│       ├── summarize.py
│       ├── transcribe.py
│       └── tts_engine.py
└── test_ffmpeg_whisper.py
```

## How It Works

### 1. Record or Upload

You can:

- Record live audio from your microphone
- Upload an audio file
- Upload a TXT or PDF document

### 2. Transcribe or Extract Text

- Audio is transcribed locally using Whisper
- Documents are read directly and their text is used as the source content

### 3. Generate Summary

The app sends the source text to the configured AI provider and generates:

- Summary
- Key moments
- Action items
- Deadlines
- Decisions

### 4. Generate Voice Summary

The generated summary can be converted into speech and downloaded as an MP3 file.

## Setup

### 1. Clone the project

```bash
git clone <your-repo-url>
cd ai-voice-project
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create or update `.env`:

```env
# Choose one provider
GROQ_API_KEY=your_groq_api_key
# or
OPENAI_API_KEY=your_openai_api_key

# Optional model overrides
GROQ_MODEL=llama-3.1-8b-instant
OPENAI_MODEL=gpt-4o-mini
```

Important:

- Do not commit `.env`
- Keep API keys private
- If both keys exist, the app may prefer the configured provider logic in code

## Run the App

```bash
python run.py
```

Then open the local Streamlit URL in your browser, usually:

```text
http://localhost:8501
```

## Usage Guide

### Live Recording

1. Open the `Record` tab
2. Click `Start Recording`
3. Speak naturally
4. The app stops after you pause, or you can stop/cancel manually
5. The app transcribes the recording automatically

### Audio Upload

1. Open the `Upload` tab
2. Upload an audio file
3. Click `Transcribe Uploaded Audio`

### Document Upload

1. Open the `Upload` tab
2. Upload a `txt` or `pdf` file
3. Click `Extract Document Text`
4. Generate summary from the extracted text

### Summary Generation

1. Open the `Summary` tab
2. Select the summary type
3. Click `Generate Summary`

### Voice Summary

1. After a summary is generated, click `Generate Human-Like Voice`
2. Listen in the browser
3. Download the generated MP3

## Supported Languages

The app currently supports target summary and voice output in:

- English
- Hindi
- Marathi
- Tamil
- Urdu

Language quality depends on:

- transcription quality
- AI provider output quality
- availability of provider quota or billing

## Requirements

You may also need:

- A working microphone for live recording
- FFmpeg available on your system for audio handling
- Internet access for AI summarization and gTTS voice generation

## Known Notes

- Whisper on CPU may show:
  - `FP16 is not supported on CPU; using FP32 instead`
  - This is a warning, not a failure
- Text extraction from scanned PDFs may fail if the PDF does not contain selectable text
- AI summary quality depends on your configured provider and available quota
- Live recording UI depends on local audio device access

## Security

- Never commit `.env`
- Never expose API keys in screenshots, commits, issues, or chat
- Rotate any key that has been shared publicly

## Future Improvements

- OCR support for scanned PDFs
- DOCX upload support
- Rich recording UI with timer and waveform
- Better fallback behavior when AI providers are unavailable
- More polished multilingual handling

## License

Add your preferred license here before publishing publicly.
