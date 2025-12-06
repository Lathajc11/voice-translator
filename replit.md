# Voice Translator & Assistant

## Overview

A comprehensive voice translation and AI assistant application built with FastAPI and powered by Groq's AI models. The application provides a modern web interface for voice-to-text translation, AI conversations, grammar correction, text summarization, and dictionary lookup with support for 23 languages.

## User Preferences

Preferred communication style: Simple, everyday language.

## Features

### Core Modes
- **Translator Mode**: Translate speech or text between 23 languages with pronunciation guides
- **Assistant Mode**: Ask questions and get AI-powered answers in any language
- **Conversation Mode**: Two-way translation for real-time conversations
- **Grammar Fix Mode**: Correct grammar, spelling, and punctuation errors
- **Summarize Mode**: Condense long text into concise summaries
- **Dictionary Mode**: Look up word definitions with pronunciations

### Supported Languages
English, Chinese, Hindi, Japanese, French, Russian, Italian, Spanish, German, Korean, Arabic, Portuguese, Dutch, Turkish, Thai, Vietnamese, Polish, Greek, Swedish, Hebrew, Indonesian, Ukrainian, Czech

### UI Features
- Dark/Light theme toggle with persistence
- Translation history with local storage
- Favorites/bookmarks for saving translations
- Copy to clipboard functionality
- Share button (Web Share API)
- Export translations as text file
- Character and word count display
- Voice speed and pitch controls
- Keyboard shortcuts (Ctrl+R, Ctrl+Enter, Ctrl+L, Ctrl+T)

## System Architecture

### Backend Framework
- **FastAPI**: Modern async Python web framework
- **Uvicorn**: ASGI server running on port 5000

### AI Integration
- **Groq API**: High-performance AI inference
  - `whisper-large-v3`: Speech-to-text transcription
  - `llama-3.1-8b-instant`: Translation, chat, grammar, summarization, dictionary

### API Endpoints
- `GET /` - Health check
- `GET /ui` - Web interface
- `POST /speech-to-text` - Audio transcription
- `POST /translate-text` - Translation with pronunciation and language detection
- `POST /ask-assistant` - AI assistant with translation
- `POST /fix-grammar` - Grammar correction
- `POST /summarize` - Text summarization
- `POST /dictionary` - Word definitions with IPA pronunciation
- `POST /detect-language` - Language detection

### Frontend Architecture
- Single-file HTML/CSS/JS embedded in FastAPI
- CSS custom properties for theming
- localStorage for persistence (history, favorites, theme)
- Web Speech API for text-to-speech playback

## External Dependencies

### Third-Party Services
- **Groq AI Platform**: Primary AI service
  - Authentication: API key-based (GROQ_API_KEY)

### Python Packages
- fastapi
- groq
- python-multipart
- uvicorn

## Environment Variables
- `GROQ_API_KEY`: Required for Groq AI services

## Deployment
- Ready for production deployment
- Workflow: "Start application" (uvicorn main:app --host 0.0.0.0 --port 5000)
