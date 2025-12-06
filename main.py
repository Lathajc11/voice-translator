from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
import urllib.parse
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Voice translator backend is running (Groq-powered)",
    }


@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌐</text></svg>">
  <title>AI Voice Translator & Assistant</title>
  <style>
    :root {
      --bg-primary: #0d1117;
      --bg-secondary: #161b22;
      --bg-tertiary: #21262d;
      --border-color: #30363d;
      --accent-blue: #1f6feb;
      --accent-blue-light: #58a6ff;
      --accent-green: #238636;
      --accent-green-light: #3fb950;
      --accent-red: #da3633;
      --accent-purple: #8b5cf6;
      --accent-orange: #f97316;
      --text-primary: #ffffff;
      --text-secondary: #8b949e;
      --text-muted: #6e7681;
    }
    
    .light-theme {
      --bg-primary: #ffffff;
      --bg-secondary: #f6f8fa;
      --bg-tertiary: #eaeef2;
      --border-color: #d0d7de;
      --text-primary: #1f2328;
      --text-secondary: #656d76;
      --text-muted: #8c959f;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 0;
      background: var(--bg-primary);
      font-family: 'Segoe UI', Arial, sans-serif;
      color: var(--text-primary);
      min-height: 100vh;
      transition: all 0.3s ease;
    }

    .app-container {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    .header {
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      padding: 15px 25px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }

    .header h1 {
      margin: 0;
      font-size: 22px;
      color: var(--accent-blue-light);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .header-controls {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    .theme-toggle {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 16px;
    }

    .main-content {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .left-panel {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      max-width: 700px;
    }

    .right-panel {
      width: 350px;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .panel-header {
      padding: 15px;
      border-bottom: 1px solid var(--border-color);
      font-weight: bold;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .panel-content {
      flex: 1;
      overflow-y: auto;
      padding: 10px;
    }

    .card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 15px;
    }

    .card-title {
      font-size: 14px;
      font-weight: bold;
      color: var(--text-secondary);
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .mode-tabs {
      display: flex;
      gap: 5px;
      margin-bottom: 15px;
      flex-wrap: wrap;
    }

    .mode-tab {
      padding: 10px 16px;
      border: 1px solid var(--border-color);
      background: var(--bg-tertiary);
      color: var(--text-primary);
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
    }

    .mode-tab:hover {
      border-color: var(--accent-blue);
    }

    .mode-tab.active {
      background: var(--accent-blue);
      border-color: var(--accent-blue);
      color: white;
    }

    select, textarea, input[type="text"] {
      width: 100%;
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      padding: 10px 12px;
      border-radius: 8px;
      font-size: 14px;
      transition: border-color 0.2s;
    }

    select:focus, textarea:focus, input[type="text"]:focus {
      outline: none;
      border-color: var(--accent-blue);
    }

    textarea {
      resize: vertical;
      min-height: 80px;
    }

    .language-row {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 15px;
    }

    .language-row select {
      flex: 1;
    }

    .swap-btn {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      width: 40px;
      height: 40px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .swap-btn:hover {
      background: var(--accent-blue);
      border-color: var(--accent-blue);
    }

    .btn {
      padding: 12px 20px;
      font-size: 14px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
    }

    .btn-primary {
      background: var(--accent-blue);
      color: white;
      box-shadow: 0 0 15px rgba(31, 111, 235, 0.3);
    }

    .btn-primary:hover {
      box-shadow: 0 0 25px rgba(31, 111, 235, 0.5);
    }

    .btn-primary.recording {
      background: var(--accent-red);
      animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 15px rgba(218, 54, 51, 0.3); }
      50% { box-shadow: 0 0 25px rgba(218, 54, 51, 0.6); }
    }

    .btn-success {
      background: var(--accent-green);
      color: white;
    }

    .btn-success:hover {
      background: var(--accent-green-light);
    }

    .btn-danger {
      background: var(--accent-red);
      color: white;
    }

    .btn-secondary {
      background: var(--bg-tertiary);
      color: var(--text-primary);
      border: 1px solid var(--border-color);
    }

    .btn-secondary:hover {
      border-color: var(--accent-blue);
    }

    .btn-icon {
      padding: 8px;
      min-width: 36px;
      justify-content: center;
    }

    .btn-group {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 12px;
    }

    .result-box {
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 15px;
      margin-top: 15px;
      position: relative;
    }

    .result-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .result-text {
      font-size: 16px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .result-text.original {
      color: var(--accent-blue-light);
    }

    .result-text.translated {
      color: var(--accent-green-light);
    }

    .result-actions {
      display: flex;
      gap: 8px;
      margin-top: 10px;
    }

    .result-actions button {
      padding: 6px 10px;
      font-size: 12px;
    }

    .pronunciation {
      font-size: 14px;
      color: var(--accent-purple);
      font-style: italic;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px dashed var(--border-color);
    }

    .detected-lang {
      display: inline-block;
      background: var(--accent-purple);
      color: white;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      margin-left: 8px;
    }

    .stats {
      display: flex;
      gap: 15px;
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 8px;
    }

    .voice-controls {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }

    .slider-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .slider-group label {
      font-size: 12px;
      color: var(--text-secondary);
    }

    .slider-group input[type="range"] {
      width: 80px;
    }

    .slider-group span {
      font-size: 12px;
      color: var(--accent-blue-light);
      min-width: 35px;
    }

    .status-bar {
      padding: 10px 15px;
      background: var(--bg-tertiary);
      border-radius: 8px;
      font-size: 13px;
      color: var(--accent-blue-light);
      margin-top: 15px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .status-bar.error {
      color: var(--accent-red);
      background: rgba(218, 54, 51, 0.1);
    }

    .status-bar.success {
      color: var(--accent-green-light);
      background: rgba(35, 134, 54, 0.1);
    }

    .history-item {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      cursor: pointer;
      transition: border-color 0.2s;
    }

    .history-item:hover {
      border-color: var(--accent-blue);
    }

    .history-item.favorite {
      border-left: 3px solid var(--accent-orange);
    }

    .history-original {
      font-size: 13px;
      color: var(--accent-blue-light);
      margin-bottom: 5px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .history-translated {
      font-size: 13px;
      color: var(--accent-green-light);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .history-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 8px;
      font-size: 11px;
      color: var(--text-muted);
    }

    .history-actions {
      display: flex;
      gap: 5px;
    }

    .history-actions button {
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      padding: 2px 5px;
      font-size: 14px;
    }

    .history-actions button:hover {
      color: var(--accent-blue-light);
    }

    .tab-buttons {
      display: flex;
      border-bottom: 1px solid var(--border-color);
    }

    .tab-btn {
      flex: 1;
      padding: 12px;
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      font-size: 13px;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
    }

    .tab-btn:hover {
      color: var(--text-primary);
    }

    .tab-btn.active {
      color: var(--accent-blue-light);
      border-bottom-color: var(--accent-blue);
    }

    .keyboard-hint {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 10px;
    }

    .keyboard-hint kbd {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
    }

    .search-link {
      margin-top: 15px;
    }

    .search-link a {
      color: var(--accent-blue-light);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .search-link a:hover {
      text-decoration: underline;
    }

    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--text-muted);
    }

    .empty-state-icon {
      font-size: 48px;
      margin-bottom: 15px;
    }

    .conversation-container {
      display: none;
    }

    .conversation-container.active {
      display: block;
    }

    .conversation-messages {
      max-height: 300px;
      overflow-y: auto;
      margin-bottom: 15px;
    }

    .conv-message {
      padding: 10px 15px;
      border-radius: 12px;
      margin-bottom: 10px;
      max-width: 85%;
    }

    .conv-message.left {
      background: var(--bg-tertiary);
      margin-right: auto;
    }

    .conv-message.right {
      background: var(--accent-blue);
      color: white;
      margin-left: auto;
    }

    .conv-lang {
      font-size: 11px;
      opacity: 0.7;
      margin-bottom: 4px;
    }

    @media (max-width: 900px) {
      .main-content {
        flex-direction: column;
      }
      .right-panel {
        width: 100%;
        border-left: none;
        border-top: 1px solid var(--border-color);
        max-height: 300px;
      }
      .left-panel {
        max-width: 100%;
      }
    }

    .hidden {
      display: none !important;
    }

    .toast {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      z-index: 1000;
      animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
      from { transform: translateX(100px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  </style>
</head>
<body>
<div class="app-container">
  <header class="header">
    <h1>AI Voice Translator & Assistant</h1>
    <div class="header-controls">
      <button class="theme-toggle" id="themeToggle" title="Toggle theme (Ctrl+T)">dark</button>
      <button class="btn btn-secondary" id="exportBtn" title="Export translations">Export</button>
    </div>
  </header>

  <div class="main-content">
    <div class="left-panel">
      <div class="card">
        <div class="card-title">Mode</div>
        <div class="mode-tabs">
          <button class="mode-tab active" data-mode="translator">Translator</button>
          <button class="mode-tab" data-mode="assistant">Assistant</button>
          <button class="mode-tab" data-mode="conversation">Conversation</button>
          <button class="mode-tab" data-mode="grammar">Grammar Fix</button>
          <button class="mode-tab" data-mode="summarize">Summarize</button>
          <button class="mode-tab" data-mode="dictionary">Dictionary</button>
        </div>

        <div class="card-title">Languages</div>
        <div class="language-row">
          <select id="sourceLang">
            <option value="auto">Auto Detect</option>
            <option value="english">English</option>
            <option value="chinese">Chinese</option>
            <option value="hindi">Hindi</option>
            <option value="japanese">Japanese</option>
            <option value="french">French</option>
            <option value="russian">Russian</option>
            <option value="italian">Italian</option>
            <option value="spanish">Spanish</option>
            <option value="german">German</option>
            <option value="korean">Korean</option>
            <option value="arabic">Arabic</option>
            <option value="portuguese">Portuguese</option>
            <option value="dutch">Dutch</option>
            <option value="turkish">Turkish</option>
            <option value="thai">Thai</option>
            <option value="vietnamese">Vietnamese</option>
            <option value="polish">Polish</option>
            <option value="greek">Greek</option>
            <option value="swedish">Swedish</option>
            <option value="hebrew">Hebrew</option>
            <option value="indonesian">Indonesian</option>
            <option value="ukrainian">Ukrainian</option>
            <option value="czech">Czech</option>
          </select>
          <button class="swap-btn" id="swapLangs" title="Swap languages">&#8644;</button>
          <select id="targetLang">
            <option value="chinese">Chinese</option>
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="japanese">Japanese</option>
            <option value="french">French</option>
            <option value="russian">Russian</option>
            <option value="italian">Italian</option>
            <option value="spanish">Spanish</option>
            <option value="german">German</option>
            <option value="korean">Korean</option>
            <option value="arabic">Arabic</option>
            <option value="portuguese">Portuguese</option>
            <option value="dutch">Dutch</option>
            <option value="turkish">Turkish</option>
            <option value="thai">Thai</option>
            <option value="vietnamese">Vietnamese</option>
            <option value="polish">Polish</option>
            <option value="greek">Greek</option>
            <option value="swedish">Swedish</option>
            <option value="hebrew">Hebrew</option>
            <option value="indonesian">Indonesian</option>
            <option value="ukrainian">Ukrainian</option>
            <option value="czech">Czech</option>
          </select>
        </div>
      </div>

      <div class="card" id="mainInputCard">
        <div class="card-title">Input</div>
        <textarea id="inputText" placeholder="Type or speak your text here..." rows="4"></textarea>
        <div class="stats" id="inputStats">
          <span id="charCount">0 characters</span>
          <span id="wordCount">0 words</span>
        </div>
        
        <div class="btn-group">
          <button class="btn btn-primary" id="recordBtn" title="Start recording (Ctrl+R)">
            <span>Start Recording</span>
          </button>
          <button class="btn btn-success" id="processBtn" title="Process text (Ctrl+Enter)">
            <span>Process</span>
          </button>
          <button class="btn btn-secondary" id="clearBtn" title="Clear (Ctrl+L)">Clear</button>
        </div>

        <div class="keyboard-hint">
          <kbd>Ctrl+R</kbd> Record &nbsp; <kbd>Ctrl+Enter</kbd> Process &nbsp; <kbd>Ctrl+L</kbd> Clear &nbsp; <kbd>Ctrl+T</kbd> Theme
        </div>
      </div>

      <div class="card conversation-container" id="conversationCard">
        <div class="card-title">Conversation Mode</div>
        <p style="font-size: 13px; color: var(--text-secondary);">
          Have a two-way conversation. Record in either language and get translations for both sides.
        </p>
        <div class="conversation-messages" id="convMessages"></div>
        <div class="btn-group">
          <button class="btn btn-primary" id="convRecordLeft">
            <span id="convLeftLabel">Record (Source)</span>
          </button>
          <button class="btn btn-success" id="convRecordRight">
            <span id="convRightLabel">Record (Target)</span>
          </button>
          <button class="btn btn-secondary" id="convClear">Clear Conversation</button>
        </div>
      </div>

      <div id="resultsSection">
        <div class="result-box" id="originalBox">
          <div class="result-label">
            <span>Original <span class="detected-lang" id="detectedLang" style="display:none;"></span></span>
          </div>
          <div class="result-text original" id="originalText"></div>
        </div>

        <div class="result-box" id="translatedBox">
          <div class="result-label">
            <span>Result</span>
          </div>
          <div class="result-text translated" id="translatedText"></div>
          <div class="pronunciation" id="pronunciation" style="display:none;"></div>
          <div class="result-actions">
            <button class="btn btn-secondary btn-icon" id="copyBtn" title="Copy to clipboard">Copy</button>
            <button class="btn btn-secondary btn-icon" id="speakBtn" title="Speak result">Speak</button>
            <button class="btn btn-secondary btn-icon" id="favoriteBtn" title="Add to favorites">Save</button>
            <button class="btn btn-secondary btn-icon" id="shareBtn" title="Share">Share</button>
          </div>
        </div>

        <div class="search-link" id="searchLink" style="display:none;"></div>
      </div>

      <div class="card">
        <div class="card-title">Voice Settings</div>
        <div class="voice-controls">
          <div class="slider-group">
            <label>Speed:</label>
            <input type="range" id="rateSlider" min="0.5" max="2" step="0.1" value="1">
            <span id="rateLabel">1.0x</span>
          </div>
          <div class="slider-group">
            <label>Pitch:</label>
            <input type="range" id="pitchSlider" min="0.5" max="2" step="0.1" value="1">
            <span id="pitchLabel">1.0</span>
          </div>
          <button class="btn btn-secondary btn-icon" id="stopVoiceBtn" title="Stop voice">Stop</button>
        </div>
      </div>

      <div class="status-bar" id="statusBar">Ready</div>
    </div>

    <div class="right-panel">
      <div class="tab-buttons">
        <button class="tab-btn active" data-tab="history">History</button>
        <button class="tab-btn" data-tab="favorites">Favorites</button>
      </div>
      <div class="panel-header">
        <span id="panelTitle">Recent Translations</span>
        <button class="btn btn-secondary" id="clearHistoryBtn" style="padding: 5px 10px; font-size: 12px;">Clear</button>
      </div>
      <div class="panel-content" id="historyPanel">
        <div class="empty-state" id="emptyHistory">
          <div class="empty-state-icon">clock</div>
          <p>No translations yet</p>
        </div>
        <div id="historyList"></div>
      </div>
      <div class="panel-content hidden" id="favoritesPanel">
        <div class="empty-state" id="emptyFavorites">
          <div class="empty-state-icon">star</div>
          <p>No favorites saved</p>
        </div>
        <div id="favoritesList"></div>
      </div>
    </div>
  </div>
</div>

<script>
const BACKEND_BASE = window.location.origin;

const LANGUAGES = {
  english:    { name: "English",    tts: "en-US" },
  chinese:    { name: "Chinese",    tts: "zh-CN" },
  hindi:      { name: "Hindi",      tts: "hi-IN" },
  japanese:   { name: "Japanese",   tts: "ja-JP" },
  french:     { name: "French",     tts: "fr-FR" },
  russian:    { name: "Russian",    tts: "ru-RU" },
  italian:    { name: "Italian",    tts: "it-IT" },
  spanish:    { name: "Spanish",    tts: "es-ES" },
  german:     { name: "German",     tts: "de-DE" },
  korean:     { name: "Korean",     tts: "ko-KR" },
  arabic:     { name: "Arabic",     tts: "ar-SA" },
  portuguese: { name: "Portuguese", tts: "pt-BR" },
  dutch:      { name: "Dutch",      tts: "nl-NL" },
  turkish:    { name: "Turkish",    tts: "tr-TR" },
  thai:       { name: "Thai",       tts: "th-TH" },
  vietnamese: { name: "Vietnamese", tts: "vi-VN" },
  polish:     { name: "Polish",     tts: "pl-PL" },
  greek:      { name: "Greek",      tts: "el-GR" },
  swedish:    { name: "Swedish",    tts: "sv-SE" },
  hebrew:     { name: "Hebrew",     tts: "he-IL" },
  indonesian: { name: "Indonesian", tts: "id-ID" },
  ukrainian:  { name: "Ukrainian",  tts: "uk-UA" },
  czech:      { name: "Czech",      tts: "cs-CZ" }
};

let currentMode = "translator";
let recording = false;
let mediaRecorder = null;
let chunks = [];
let history = JSON.parse(localStorage.getItem("translationHistory") || "[]");
let favorites = JSON.parse(localStorage.getItem("translationFavorites") || "[]");
let voiceRate = 1.0;
let voicePitch = 1.0;
let currentTab = "history";
let conversationMessages = [];

const inputText = document.getElementById("inputText");
const originalText = document.getElementById("originalText");
const translatedText = document.getElementById("translatedText");
const statusBar = document.getElementById("statusBar");
const recordBtn = document.getElementById("recordBtn");
const processBtn = document.getElementById("processBtn");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");
const speakBtn = document.getElementById("speakBtn");
const favoriteBtn = document.getElementById("favoriteBtn");
const shareBtn = document.getElementById("shareBtn");
const stopVoiceBtn = document.getElementById("stopVoiceBtn");
const sourceLang = document.getElementById("sourceLang");
const targetLang = document.getElementById("targetLang");
const swapLangs = document.getElementById("swapLangs");
const themeToggle = document.getElementById("themeToggle");
const rateSlider = document.getElementById("rateSlider");
const pitchSlider = document.getElementById("pitchSlider");
const rateLabel = document.getElementById("rateLabel");
const pitchLabel = document.getElementById("pitchLabel");
const charCount = document.getElementById("charCount");
const wordCount = document.getElementById("wordCount");
const pronunciation = document.getElementById("pronunciation");
const detectedLang = document.getElementById("detectedLang");
const searchLink = document.getElementById("searchLink");
const historyList = document.getElementById("historyList");
const favoritesList = document.getElementById("favoritesList");
const emptyHistory = document.getElementById("emptyHistory");
const emptyFavorites = document.getElementById("emptyFavorites");
const exportBtn = document.getElementById("exportBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const mainInputCard = document.getElementById("mainInputCard");
const conversationCard = document.getElementById("conversationCard");
const convMessages = document.getElementById("convMessages");

document.querySelectorAll(".mode-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".mode-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentMode = tab.dataset.mode;
    updateUI();
  });
});

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentTab = btn.dataset.tab;
    document.getElementById("historyPanel").classList.toggle("hidden", currentTab !== "history");
    document.getElementById("favoritesPanel").classList.toggle("hidden", currentTab !== "favorites");
    document.getElementById("panelTitle").textContent = currentTab === "history" ? "Recent Translations" : "Saved Favorites";
  });
});

function updateUI() {
  const isConversation = currentMode === "conversation";
  mainInputCard.style.display = isConversation ? "none" : "block";
  conversationCard.classList.toggle("active", isConversation);
  
  let placeholder = "Type or speak your text here...";
  if (currentMode === "grammar") placeholder = "Enter text to fix grammar...";
  else if (currentMode === "summarize") placeholder = "Enter text to summarize...";
  else if (currentMode === "dictionary") placeholder = "Enter a word to look up...";
  else if (currentMode === "assistant") placeholder = "Ask a question...";
  inputText.placeholder = placeholder;
  
  const labels = { translator: "Translate", assistant: "Ask", grammar: "Fix Grammar", summarize: "Summarize", dictionary: "Look Up", conversation: "Process" };
  processBtn.querySelector("span").textContent = labels[currentMode] || "Process";
  
  updateConvLabels();
}

function updateConvLabels() {
  const source = LANGUAGES[sourceLang.value]?.name || "Source";
  const target = LANGUAGES[targetLang.value]?.name || "Target";
  document.getElementById("convLeftLabel").textContent = `Record (${source})`;
  document.getElementById("convRightLabel").textContent = `Record (${target})`;
}

sourceLang.addEventListener("change", updateConvLabels);
targetLang.addEventListener("change", updateConvLabels);

swapLangs.addEventListener("click", () => {
  if (sourceLang.value === "auto") return;
  const temp = sourceLang.value;
  sourceLang.value = targetLang.value;
  targetLang.value = temp;
  updateConvLabels();
});

inputText.addEventListener("input", () => {
  const text = inputText.value;
  charCount.textContent = `${text.length} characters`;
  wordCount.textContent = `${text.trim() ? text.trim().split(/\s+/).length : 0} words`;
});

rateSlider.addEventListener("input", () => {
  voiceRate = parseFloat(rateSlider.value);
  rateLabel.textContent = voiceRate.toFixed(1) + "x";
});

pitchSlider.addEventListener("input", () => {
  voicePitch = parseFloat(pitchSlider.value);
  pitchLabel.textContent = voicePitch.toFixed(1);
});

let isDark = localStorage.getItem("theme") !== "light";
function applyTheme() {
  document.body.classList.toggle("light-theme", !isDark);
  themeToggle.textContent = isDark ? "dark" : "light";
}
applyTheme();

themeToggle.addEventListener("click", () => {
  isDark = !isDark;
  localStorage.setItem("theme", isDark ? "dark" : "light");
  applyTheme();
});

function setStatus(msg, type = "") {
  statusBar.textContent = msg;
  statusBar.className = "status-bar";
  if (type) statusBar.classList.add(type);
}

function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function speak(text, langCode) {
  if (!text || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = langCode || "en-US";
  u.rate = voiceRate;
  u.pitch = voicePitch;
  window.speechSynthesis.speak(u);
}

stopVoiceBtn.addEventListener("click", () => {
  window.speechSynthesis.cancel();
  setStatus("Voice stopped");
});

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      setStatus("Processing audio...");
      const blob = new Blob(chunks, { type: "audio/webm" });
      const fd = new FormData();
      fd.append("file", blob, "voice.webm");
      
      try {
        const res = await fetch(`${BACKEND_BASE}/speech-to-text`, { method: "POST", body: fd });
        const data = await res.json();
        if (data.error) {
          setStatus(data.error, "error");
          return;
        }
        inputText.value = data.text || "";
        inputText.dispatchEvent(new Event("input"));
        originalText.textContent = data.text || "";
        setStatus("Speech recognized. Click Process to continue.", "success");
      } catch (e) {
        setStatus("Error processing audio: " + e.message, "error");
      }
    };
    
    mediaRecorder.start();
    recording = true;
    recordBtn.classList.add("recording");
    recordBtn.querySelector("span").textContent = "Stop Recording";
    setStatus("Listening... speak now");
  } catch (e) {
    setStatus("Microphone access denied", "error");
  }
}

function stopRecording() {
  if (mediaRecorder && recording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    recording = false;
    recordBtn.classList.remove("recording");
    recordBtn.querySelector("span").textContent = "Start Recording";
  }
}

recordBtn.addEventListener("click", () => {
  if (recording) stopRecording();
  else startRecording();
});

clearBtn.addEventListener("click", () => {
  inputText.value = "";
  originalText.textContent = "";
  translatedText.textContent = "";
  pronunciation.style.display = "none";
  detectedLang.style.display = "none";
  searchLink.style.display = "none";
  inputText.dispatchEvent(new Event("input"));
  setStatus("Cleared");
});

async function processText() {
  const text = inputText.value.trim();
  if (!text) {
    setStatus("Please enter some text", "error");
    return;
  }
  
  originalText.textContent = text;
  translatedText.textContent = "";
  pronunciation.style.display = "none";
  searchLink.style.display = "none";
  
  const target = LANGUAGES[targetLang.value];
  const source = sourceLang.value !== "auto" ? LANGUAGES[sourceLang.value] : null;
  
  try {
    if (currentMode === "translator") {
      setStatus("Translating...");
      const res = await fetch(`${BACKEND_BASE}/translate-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          target_language: target.name,
          source_language: source?.name,
          include_pronunciation: true
        })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      translatedText.textContent = data.translated_text || "";
      if (data.pronunciation) {
        pronunciation.textContent = data.pronunciation;
        pronunciation.style.display = "block";
      }
      if (data.detected_language) {
        detectedLang.textContent = data.detected_language;
        detectedLang.style.display = "inline";
      }
      
      addToHistory(text, data.translated_text, currentMode, target.name);
      setStatus("Translation complete", "success");
      speak(data.translated_text, target.tts);
      
    } else if (currentMode === "assistant") {
      setStatus("Asking assistant...");
      const res = await fetch(`${BACKEND_BASE}/ask-assistant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, target_language: target.name })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      translatedText.textContent = data.answer_translated || data.answer_original || "";
      if (data.google_search_url) {
        searchLink.innerHTML = `<a href="${data.google_search_url}" target="_blank">View on Google</a>`;
        searchLink.style.display = "block";
      }
      
      addToHistory(text, data.answer_translated || data.answer_original, currentMode, target.name);
      setStatus("Answer received", "success");
      speak(data.answer_translated || data.answer_original, target.tts);
      
    } else if (currentMode === "grammar") {
      setStatus("Fixing grammar...");
      const res = await fetch(`${BACKEND_BASE}/fix-grammar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      translatedText.textContent = data.corrected_text || "";
      addToHistory(text, data.corrected_text, currentMode, "Grammar");
      setStatus("Grammar fixed", "success");
      
    } else if (currentMode === "summarize") {
      setStatus("Summarizing...");
      const res = await fetch(`${BACKEND_BASE}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, target_language: target.name })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      translatedText.textContent = data.summary || "";
      addToHistory(text, data.summary, currentMode, target.name);
      setStatus("Summarization complete", "success");
      
    } else if (currentMode === "dictionary") {
      setStatus("Looking up definition...");
      const res = await fetch(`${BACKEND_BASE}/dictionary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word: text, target_language: target.name })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      translatedText.textContent = data.definition || "";
      if (data.pronunciation) {
        pronunciation.textContent = data.pronunciation;
        pronunciation.style.display = "block";
      }
      addToHistory(text, data.definition, currentMode, target.name);
      setStatus("Definition found", "success");
    }
  } catch (e) {
    setStatus("Error: " + e.message, "error");
  }
}

processBtn.addEventListener("click", processText);

copyBtn.addEventListener("click", () => {
  const text = translatedText.textContent;
  if (text) {
    navigator.clipboard.writeText(text);
    showToast("Copied to clipboard!");
  }
});

speakBtn.addEventListener("click", () => {
  const text = translatedText.textContent;
  const target = LANGUAGES[targetLang.value];
  if (text) speak(text, target.tts);
});

favoriteBtn.addEventListener("click", () => {
  const orig = originalText.textContent;
  const trans = translatedText.textContent;
  if (!orig || !trans) return;
  
  const fav = { id: Date.now(), original: orig, translated: trans, mode: currentMode, language: targetLang.value, timestamp: new Date().toISOString() };
  favorites.unshift(fav);
  localStorage.setItem("translationFavorites", JSON.stringify(favorites));
  renderFavorites();
  showToast("Added to favorites!");
});

shareBtn.addEventListener("click", async () => {
  const text = `Original: ${originalText.textContent}\nTranslated: ${translatedText.textContent}`;
  if (navigator.share) {
    try {
      await navigator.share({ title: "Translation", text });
    } catch (e) {}
  } else {
    navigator.clipboard.writeText(text);
    showToast("Copied to clipboard for sharing!");
  }
});

function addToHistory(original, translated, mode, language) {
  const item = { id: Date.now(), original, translated, mode, language, timestamp: new Date().toISOString() };
  history.unshift(item);
  if (history.length > 50) history.pop();
  localStorage.setItem("translationHistory", JSON.stringify(history));
  renderHistory();
}

function renderHistory() {
  emptyHistory.style.display = history.length ? "none" : "block";
  historyList.innerHTML = history.map(item => `
    <div class="history-item" data-id="${item.id}">
      <div class="history-original">${escapeHtml(item.original)}</div>
      <div class="history-translated">${escapeHtml(item.translated)}</div>
      <div class="history-meta">
        <span>${item.mode} - ${item.language}</span>
        <div class="history-actions">
          <button onclick="loadHistoryItem(${item.id})" title="Load">load</button>
          <button onclick="deleteHistoryItem(${item.id})" title="Delete">del</button>
        </div>
      </div>
    </div>
  `).join("");
}

function renderFavorites() {
  emptyFavorites.style.display = favorites.length ? "none" : "block";
  favoritesList.innerHTML = favorites.map(item => `
    <div class="history-item favorite" data-id="${item.id}">
      <div class="history-original">${escapeHtml(item.original)}</div>
      <div class="history-translated">${escapeHtml(item.translated)}</div>
      <div class="history-meta">
        <span>${item.mode} - ${item.language}</span>
        <div class="history-actions">
          <button onclick="loadFavoriteItem(${item.id})" title="Load">load</button>
          <button onclick="deleteFavoriteItem(${item.id})" title="Delete">del</button>
        </div>
      </div>
    </div>
  `).join("");
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

window.loadHistoryItem = (id) => {
  const item = history.find(h => h.id === id);
  if (item) {
    inputText.value = item.original;
    originalText.textContent = item.original;
    translatedText.textContent = item.translated;
    inputText.dispatchEvent(new Event("input"));
  }
};

window.deleteHistoryItem = (id) => {
  history = history.filter(h => h.id !== id);
  localStorage.setItem("translationHistory", JSON.stringify(history));
  renderHistory();
};

window.loadFavoriteItem = (id) => {
  const item = favorites.find(f => f.id === id);
  if (item) {
    inputText.value = item.original;
    originalText.textContent = item.original;
    translatedText.textContent = item.translated;
    inputText.dispatchEvent(new Event("input"));
  }
};

window.deleteFavoriteItem = (id) => {
  favorites = favorites.filter(f => f.id !== id);
  localStorage.setItem("translationFavorites", JSON.stringify(favorites));
  renderFavorites();
};

clearHistoryBtn.addEventListener("click", () => {
  if (currentTab === "history") {
    history = [];
    localStorage.setItem("translationHistory", "[]");
    renderHistory();
  } else {
    favorites = [];
    localStorage.setItem("translationFavorites", "[]");
    renderFavorites();
  }
  showToast("Cleared!");
});

exportBtn.addEventListener("click", () => {
  const data = currentTab === "history" ? history : favorites;
  const text = data.map(item => `[${item.mode}] ${item.original} => ${item.translated}`).join("\n\n");
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `translations-${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
  showToast("Exported!");
});

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey) {
    if (e.key === "r" || e.key === "R") {
      e.preventDefault();
      recordBtn.click();
    } else if (e.key === "Enter") {
      e.preventDefault();
      processBtn.click();
    } else if (e.key === "l" || e.key === "L") {
      e.preventDefault();
      clearBtn.click();
    } else if (e.key === "t" || e.key === "T") {
      e.preventDefault();
      themeToggle.click();
    }
  }
});

let convRecording = null;
document.getElementById("convRecordLeft").addEventListener("click", () => startConvRecording("left"));
document.getElementById("convRecordRight").addEventListener("click", () => startConvRecording("right"));
document.getElementById("convClear").addEventListener("click", () => {
  conversationMessages = [];
  convMessages.innerHTML = "";
});

async function startConvRecording(side) {
  if (convRecording) {
    convRecording.stop();
    convRecording = null;
    return;
  }
  
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    convRecording = new MediaRecorder(stream);
    const convChunks = [];
    
    convRecording.ondataavailable = e => convChunks.push(e.data);
    convRecording.onstop = async () => {
      setStatus("Processing...");
      const blob = new Blob(convChunks, { type: "audio/webm" });
      const fd = new FormData();
      fd.append("file", blob, "voice.webm");
      
      try {
        const sttRes = await fetch(`${BACKEND_BASE}/speech-to-text`, { method: "POST", body: fd });
        const sttData = await sttRes.json();
        const spokenText = sttData.text || "";
        
        const fromLang = side === "left" ? sourceLang.value : targetLang.value;
        const toLang = side === "left" ? targetLang.value : sourceLang.value;
        const fromConfig = fromLang === "auto" ? { name: "Auto" } : LANGUAGES[fromLang];
        const toConfig = LANGUAGES[toLang];
        
        const transRes = await fetch(`${BACKEND_BASE}/translate-text`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: spokenText, target_language: toConfig.name })
        });
        const transData = await transRes.json();
        
        const msg = {
          side: side === "left" ? "left" : "right",
          original: spokenText,
          translated: transData.translated_text || "",
          fromLang: fromConfig.name,
          toLang: toConfig.name
        };
        conversationMessages.push(msg);
        renderConversation();
        speak(transData.translated_text, toConfig.tts);
        setStatus("Ready", "success");
      } catch (e) {
        setStatus("Error: " + e.message, "error");
      }
      
      convRecording.stream.getTracks().forEach(t => t.stop());
      convRecording = null;
    };
    
    convRecording.start();
    setStatus("Listening...");
  } catch (e) {
    setStatus("Microphone error", "error");
  }
}

function renderConversation() {
  convMessages.innerHTML = conversationMessages.map(msg => `
    <div class="conv-message ${msg.side}">
      <div class="conv-lang">${msg.fromLang} to ${msg.toLang}</div>
      <div>${escapeHtml(msg.translated)}</div>
      <div style="font-size: 11px; opacity: 0.7; margin-top: 4px;">(${escapeHtml(msg.original)})</div>
    </div>
  `).join("");
  convMessages.scrollTop = convMessages.scrollHeight;
}

renderHistory();
renderFavorites();
updateUI();
</script>
</body>
</html>
    """


@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        audio_path = "audio_input.wav"
        with open(audio_path, "wb") as f:
            f.write(await file.read())

        transcript = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=open(audio_path, "rb"),
        )

        return {"text": transcript.text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/translate-text")
async def translate_text(data: dict):
    text = data.get("text")
    target_language = data.get("target_language")
    source_language = data.get("source_language")
    include_pronunciation = data.get("include_pronunciation", False)

    if not text or not target_language:
        return {"error": "text and target_language are required"}

    prompt = f"Translate this text into {target_language}. Return ONLY the translated sentence with no explanation.\nText: {text}"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a translation engine. Output only the translated text."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        translated = content.strip() if content else ""

        result = {"translated_text": translated}

        if include_pronunciation and target_language.lower() in ["chinese", "japanese", "korean", "arabic", "russian", "greek", "hebrew", "thai", "hindi"]:
            pron_prompt = f"Provide the romanized pronunciation (transliteration to Latin alphabet) for this text. Return ONLY the romanization:\n{translated}"
            pron_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You provide romanized pronunciations. Output only the transliteration."},
                    {"role": "user", "content": pron_prompt},
                ],
            )
            pron_content = pron_response.choices[0].message.content
            result["pronunciation"] = pron_content.strip() if pron_content else ""

        if source_language and source_language.lower() == "auto":
            detect_prompt = f"What language is this text written in? Reply with only the language name:\n{text}"
            detect_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You detect languages. Reply with only the language name."},
                    {"role": "user", "content": detect_prompt},
                ],
            )
            detect_content = detect_response.choices[0].message.content
            result["detected_language"] = detect_content.strip() if detect_content else ""

        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/ask-assistant")
async def ask_assistant(data: dict):
    question = data.get("question")
    target_language = data.get("target_language", "English")

    if not question:
        return {"error": "question is required"}

    try:
        base_answer = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful, concise assistant. Answer clearly in English in 2-4 sentences."},
                {"role": "user", "content": question},
            ],
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    content_en = base_answer.choices[0].message.content
    answer_en = content_en.strip() if content_en else ""

    if target_language and target_language.lower() != "english":
        prompt = f"Translate this answer into {target_language}. Return ONLY the translated sentences.\nText: {answer_en}"
        try:
            translated_resp = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a translation engine. Output only the translated text."},
                    {"role": "user", "content": prompt},
                ],
            )
            translated_content = translated_resp.choices[0].message.content
            answer_translated = translated_content.strip() if translated_content else answer_en
        except Exception:
            answer_translated = answer_en
    else:
        answer_translated = answer_en

    google_url = "https://www.google.com/search?q=" + urllib.parse.quote(question)

    return {
        "answer_original": answer_en,
        "answer_translated": answer_translated,
        "google_search_url": google_url,
        "target_language": target_language,
    }


@app.post("/fix-grammar")
async def fix_grammar(data: dict):
    text = data.get("text")

    if not text:
        return {"error": "text is required"}

    prompt = f"Fix any grammar, spelling, and punctuation errors in this text. Return ONLY the corrected text with no explanation:\n{text}"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a grammar correction engine. Output only the corrected text."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        corrected = content.strip() if content else ""
        return {"corrected_text": corrected}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/summarize")
async def summarize(data: dict):
    text = data.get("text")
    target_language = data.get("target_language", "English")

    if not text:
        return {"error": "text is required"}

    prompt = f"Summarize the following text in 2-3 concise sentences. Return ONLY the summary:\n{text}"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a summarization engine. Output only the summary."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        summary_en = content.strip() if content else ""

        if target_language.lower() != "english":
            trans_prompt = f"Translate this summary into {target_language}. Return ONLY the translation:\n{summary_en}"
            trans_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a translation engine."},
                    {"role": "user", "content": trans_prompt},
                ],
            )
            trans_content = trans_response.choices[0].message.content
            summary = trans_content.strip() if trans_content else summary_en
        else:
            summary = summary_en

        return {"summary": summary}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/dictionary")
async def dictionary(data: dict):
    word = data.get("word")
    target_language = data.get("target_language", "English")

    if not word:
        return {"error": "word is required"}

    prompt = f"""Define the word "{word}" with:
1. Part of speech
2. Definition
3. Example sentence
4. Synonyms (if any)
Keep it concise."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a dictionary. Provide clear, concise definitions."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        definition_en = content.strip() if content else ""

        if target_language.lower() != "english":
            trans_prompt = f"Translate this dictionary entry into {target_language}. Keep the formatting:\n{definition_en}"
            trans_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a translation engine."},
                    {"role": "user", "content": trans_prompt},
                ],
            )
            trans_content = trans_response.choices[0].message.content
            definition = trans_content.strip() if trans_content else definition_en
        else:
            definition = definition_en

        pron_prompt = f"Provide the phonetic pronunciation for the word '{word}' using IPA notation. Return only the pronunciation:"
        pron_response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You provide phonetic pronunciations."},
                {"role": "user", "content": pron_prompt},
            ],
        )
        pron_content = pron_response.choices[0].message.content
        pronunciation = pron_content.strip() if pron_content else ""

        return {"definition": definition, "pronunciation": pronunciation}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/detect-language")
async def detect_language(data: dict):
    text = data.get("text")

    if not text:
        return {"error": "text is required"}

    prompt = f"What language is this text written in? Reply with only the language name:\n{text}"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You detect languages. Reply with only the language name."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        detected = content.strip() if content else ""
        return {"detected_language": detected}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
