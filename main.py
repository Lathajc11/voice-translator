from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
import urllib.parse
import razorpay
import hmac
import hashlib
from datetime import datetime

app = FastAPI()

# Allow browser frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client (uses your GROQ_API_KEY from Secrets)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
  razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID,
                                          RAZORPAY_KEY_SECRET))

# Optional: simple access token protection for core AI endpoints
ACCESS_TOKEN = os.getenv(
    "TRANSLATOR_ACCESS_TOKEN")  # if not set, protection is disabled


def verify_access_token(x_access_token: str = Header(None)):
  """
    If TRANSLATOR_ACCESS_TOKEN is set, require clients to send it as X-Access-Token.
    If not set, this check does nothing (for easy local testing).
    """
  if ACCESS_TOKEN and x_access_token != ACCESS_TOKEN:
    raise HTTPException(status_code=401, detail="Unauthorized")
  return None


# Simple in-memory payment log
payments_log = []


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
  <title>🌐 AI Voice Translator & Assistant</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
  <style>
.paywall-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 20, 0.96);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.paywall-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 16px;
  padding: 24px 28px;
  max-width: 420px;
  text-align: center;
}

    :root {
      --bg-main: #0d1117;
      --bg-card: #161b22;
      --bg-input: #0d1117;
      --border: #30363d;
      --accent-blue: #1f6feb;
      --accent-blue-light: #58a6ff;
      --accent-green: #238636;
      --accent-green-light: #3fb950;
      --accent-red: #da3633;
      --text-main: #ffffff;
      --text-muted: #8b949e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      background: var(--bg-main);
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--text-main);
      display: flex;
      justify-content: center;
      align-items: flex-start;
      min-height: 100vh;
    }
    .container {
      margin: 20px;
      width: 100%;
      max-width: 960px;
      background: var(--bg-card);
      border-radius: 16px;
      border: 1px solid var(--border);
      box-shadow: 0 0 25px rgba(0, 0, 0, 0.5);
      padding: 24px 24px 32px;
    }
    h1 {
      margin: 0 0 6px;
      font-size: 26px;
      color: var(--accent-blue-light);
    }
    .subtitle {
      margin: 0 0 18px;
      color: var(--text-muted);
      font-size: 13px;
    }
    .mode-tabs {
      display: inline-flex;
      border-radius: 999px;
      padding: 3px;
      background: #0d1117;
      border: 1px solid var(--border);
      margin-bottom: 16px;
    }
    .mode-tab {
      border-radius: 999px;
      border: none;
      padding: 6px 14px;
      font-size: 13px;
      cursor: pointer;
      background: transparent;
      color: var(--text-muted);
    }
    .mode-tab.active {
      background: var(--accent-blue);
      color: #fff;
    }
    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 10px;
      align-items: center;
    }
    label {
      font-size: 13px;
      font-weight: 600;
      margin-right: 6px;
    }
    select, textarea {
      background: var(--bg-input);
      border: 1px solid var(--border);
      color: var(--text-main);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 13px;
    }
    select {
      min-width: 160px;
    }
    textarea {
      width: 100%;
      min-height: 80px;
      resize: vertical;
    }
    .hint {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    button {
      border-radius: 8px;
      border: none;
      padding: 9px 16px;
      font-size: 13px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-right: 8px;
      margin-top: 8px;
      transition: 0.2s;
    }
    .btn-primary {
      background: var(--accent-blue);
      color: #fff;
    }
    .btn-primary:hover {
      box-shadow: 0 0 15px rgba(31, 111, 235, 0.6);
    }
    .btn-record {
      background: #f5f5f5;
      color: #111;
    }
    .btn-record.recording {
      background: var(--accent-red);
      color: #fff;
      box-shadow: 0 0 15px rgba(218, 54, 51, 0.7);
    }
    .btn-ghost {
      background: var(--bg-input);
      border: 1px solid var(--border);
      color: var(--text-main);
    }
    .btn-ghost:hover {
      border-color: var(--accent-blue);
    }
    .btn-red {
      background: var(--accent-red);
      color: #fff;
    }
    .section {
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
    }
    .section h3 {
      margin: 0 0 6px;
      font-size: 15px;
    }
    #status {
      margin-top: 10px;
      font-size: 12px;
      color: var(--accent-blue-light);
      font-style: italic;
    }
    .text-box {
      background: var(--bg-input);
      border-radius: 10px;
      border: 1px solid var(--border);
      padding: 10px 12px;
      min-height: 40px;
      white-space: pre-wrap;
      font-size: 14px;
    }
    #originalText {
      color: var(--accent-blue-light);
    }
    #translatedText {
      color: var(--accent-green-light);
    }
    .counts {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .voice-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 4px;
    }
    .voice-row label {
      font-weight: normal;
    }
    .voice-row input[type=range] {
      width: 120px;
    }
    #searchLink a {
      color: var(--accent-blue-light);
      text-decoration: none;
      font-size: 13px;
    }
    #searchLink a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>

<!-- PAYWALL OVERLAY -->
<div id="paywallOverlay" class="paywall-overlay">
  <div class="paywall-card">
    <h2>🔒 Unlock AI Voice Translator</h2>
    <p style="color:#8b949e; font-size:14px;">
      Pay ₹59 one-time to unlock full access to the AI Voice Translator & Assistant on this browser.
    </p>
    <button id="payBtn" style="padding:12px 20px;font-size:16px;background:#5b8efb;color:white;border:none;border-radius:8px;cursor:pointer;">
      Pay ₹59
    </button>
  </div>
</div>

<!-- PAYMENT SUCCESS BANNER -->
<div id="payment-success" style="display:none; margin-top:12px; text-align:center; width:100%; max-width:960px;">
  <h3>✅ Payment successful!</h3>
  <p>Your translator is now unlocked on this browser.</p>
</div>

<!-- MAIN APP WRAPPER (HIDDEN UNTIL PAID) -->
<div id="appWrapper" class="container" style="display:none;">
  <h1>🌐 AI Voice Translator & Assistant</h1>
  <p class="subtitle">
    Speak or type once, listen in any language. Switch between Translator and Assistant modes.
  </p>

  <!-- MODE TABS -->
  <div class="mode-tabs">
    <button class="mode-tab active" data-mode="translator">Translator</button>
    <button class="mode-tab" data-mode="assistant">Assistant</button>
  </div>

  <!-- LANGUAGE ROW -->
  <div class="row">
    <label>Source:</label>
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
      <option value="bengali">Bengali</option>
      <option value="tamil">Tamil</option>
      <option value="telugu">Telugu</option>
      <option value="kannada">Kannada</option>
      <option value="malayalam">Malayalam</option>
      <option value="marathi">Marathi</option>
      <option value="gujarati">Gujarati</option>
      <option value="punjabi">Punjabi</option>
      <option value="urdu">Urdu</option>
      <option value="filipino">Filipino</option>
      <option value="romanian">Romanian</option>
      <option value="hungarian">Hungarian</option>
      <option value="norwegian">Norwegian</option>
      <option value="danish">Danish</option>
      <option value="finnish">Finnish</option>
      <option value="swahili">Swahili</option>
      <option value="afrikaans">Afrikaans</option>
      <option value="malay">Malay</option>
      <option value="persian">Persian</option>
      <option value="bulgarian">Bulgarian</option>
      <option value="croatian">Croatian</option>
      <option value="serbian">Serbian</option>
    </select>

    <label>Target:</label>
    <select id="targetLang">
      <option value="japanese">Japanese</option>
      <option value="english">English</option>
      <option value="chinese">Chinese</option>
      <option value="hindi">Hindi</option>
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
      <option value="bengali">Bengali</option>
      <option value="tamil">Tamil</option>
      <option value="telugu">Telugu</option>
      <option value="kannada">Kannada</option>
      <option value="malayalam">Malayalam</option>
      <option value="marathi">Marathi</option>
      <option value="gujarati">Gujarati</option>
      <option value="punjabi">Punjabi</option>
      <option value="urdu">Urdu</option>
      <option value="filipino">Filipino</option>
      <option value="romanian">Romanian</option>
      <option value="hungarian">Hungarian</option>
      <option value="norwegian">Norwegian</option>
      <option value="danish">Danish</option>
      <option value="finnish">Finnish</option>
      <option value="swahili">Swahili</option>
      <option value="afrikaans">Afrikaans</option>
      <option value="malay">Malay</option>
      <option value="persian">Persian</option>
      <option value="bulgarian">Bulgarian</option>
      <option value="croatian">Croatian</option>
      <option value="serbian">Serbian</option>
    </select>
  </div>

  <p class="hint">
    In <b>Translator</b> mode, the text is translated to the target language and spoken aloud.<br>
    In <b>Assistant</b> mode, you can ask questions like “What is AI?” or “Explain gravity”.
  </p>

  <!-- INPUT -->
  <div class="section">
    <h3>Input</h3>
    <textarea id="inputText" placeholder="Type or speak your text here..."></textarea>
    <div class="counts">
      <span id="charCount">0 characters</span> ·
      <span id="wordCount">0 words</span>
    </div>

    <div>
      <button id="recordBtn" class="btn-record">🎙 Start Recording</button>
      <button id="processBtn" class="btn-primary">▶ Process</button>
      <button id="clearBtn" class="btn-ghost">🧹 Clear</button>
    </div>
  </div>

  <!-- OUTPUT -->
  <div class="section">
    <h3>Mode: <span id="modeLabel">Translator</span></h3>

    <h4>Original</h4>
    <div id="originalText" class="text-box"></div>

    <h4>Result</h4>
    <div id="translatedText" class="text-box"></div>
    <div id="searchLink" class="hint" style="margin-top:6px;"></div>

    <div style="margin-top:8px;">
      <button id="replayBtn" class="btn-ghost" disabled>🔊 Speak / Replay</button>
      <button id="copyBtn" class="btn-ghost">📋 Copy</button>
      <button id="saveBtn" class="btn-ghost">⭐ Save</button>
      <button id="shareBtn" class="btn-ghost">📤 Share</button>
      <button id="stopVoiceBtn" class="btn-red">⏹ Stop Voice</button>
    </div>

    <div class="section">
      <h3>History & Favorites</h3>
      <div style="margin-bottom:6px;">
        <button id="clearHistoryBtn" class="btn-ghost">🧹 Clear history</button>
        <button id="clearFavBtn" class="btn-ghost">🧹 Clear favorites</button>
      </div>
      <div class="hint"><b>Recent:</b> <span id="historyList">(empty)</span></div>
      <div class="hint" style="margin-top:4px;"><b>Favorites:</b> <span id="favList">(empty)</span></div>
    </div>
  </div>

  <!-- VOICE CONTROLS -->
  <div class="section">
    <h3>Voice Controls</h3>
    <div class="voice-row">
      <label>Speed</label>
      <input type="range" id="rateSlider" min="0.5" max="1.5" step="0.1" value="1">
      <span id="rateLabel">1.0x</span>

      <label>Pitch</label>
      <input type="range" id="pitchSlider" min="0.5" max="2" step="0.1" value="1">
      <span id="pitchLabel">1.0</span>
    </div>
  </div>

  <p id="status">Ready.</p>
</div>

<!-- Unlock logic on page load -->
<script>
document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("paywallOverlay");
  const successBox = document.getElementById("payment-success");
  const app = document.getElementById("appWrapper");

  function showPaidUI() {
    if (overlay) overlay.style.display = "none";
    if (successBox) successBox.style.display = "block";
    if (app) app.style.display = "block";
  }

  function showPaywall() {
    if (overlay) overlay.style.display = "flex";
    if (successBox) successBox.style.display = "none";
    if (app) app.style.display = "none";
  }

  // Expose for use after payment
  window._translatorShowPaidUI = showPaidUI;

  if (localStorage.getItem("translator_paid") === "yes") {
    showPaidUI();
  } else {
    showPaywall();
  }
});
</script>

<script>
const BACKEND_BASE = window.location.origin;
// Optional: if you set TRANSLATOR_ACCESS_TOKEN in backend,
// put the same value here so the UI can call protected endpoints.
const API_ACCESS_TOKEN = "CHANGE_ME_ACCESS_TOKEN";

// Many languages with names + TTS codes
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
  czech:      { name: "Czech",      tts: "cs-CZ" },
  bengali:    { name: "Bengali",    tts: "bn-IN" },
  tamil:      { name: "Tamil",      tts: "ta-IN" },
  telugu:     { name: "Telugu",     tts: "te-IN" },
  kannada:    { name: "Kannada",    tts: "kn-IN" },
  malayalam:  { name: "Malayalam",  tts: "ml-IN" },
  marathi:    { name: "Marathi",    tts: "mr-IN" },
  gujarati:   { name: "Gujarati",   tts: "gu-IN" },
  punjabi:    { name: "Punjabi",    tts: "pa-IN" },
  urdu:       { name: "Urdu",       tts: "ur-PK" },
  filipino:   { name: "Filipino",   tts: "fil-PH" },
  romanian:   { name: "Romanian",   tts: "ro-RO" },
  hungarian:  { name: "Hungarian",  tts: "hu-HU" },
  norwegian:  { name: "Norwegian",  tts: "nb-NO" },
  danish:     { name: "Danish",     tts: "da-DK" },
  finnish:    { name: "Finnish",    tts: "fi-FI" },
  swahili:    { name: "Swahili",    tts: "sw-KE" },
  afrikaans:  { name: "Afrikaans",  tts: "af-ZA" },
  malay:      { name: "Malay",      tts: "ms-MY" },
  persian:    { name: "Persian",    tts: "fa-IR" },
  bulgarian:  { name: "Bulgarian",  tts: "bg-BG" },
  croatian:   { name: "Croatian",   tts: "hr-HR" },
  serbian:    { name: "Serbian",    tts: "sr-RS" },
};

let currentMode = "translator";
let recording = false;
let mediaRecorder = null;
let chunks = [];

let voiceRate = 1.0;
let voicePitch = 1.0;
let lastTTS = "en-US";
let lastOutput = "";

// DOM elements
const modeTabs = document.querySelectorAll(".mode-tab");
const modeLabel = document.getElementById("modeLabel");
const sourceLang = document.getElementById("sourceLang");
const targetLang = document.getElementById("targetLang");
const inputText = document.getElementById("inputText");
const charCount = document.getElementById("charCount");
const wordCount = document.getElementById("wordCount");
const recordBtn = document.getElementById("recordBtn");
const processBtn = document.getElementById("processBtn");
const clearBtn = document.getElementById("clearBtn");
const originalEl = document.getElementById("originalText");
const translatedEl = document.getElementById("translatedText");
const searchLink = document.getElementById("searchLink");
const rateSlider = document.getElementById("rateSlider");
const pitchSlider = document.getElementById("pitchSlider");
const rateLabel = document.getElementById("rateLabel");
const pitchLabel = document.getElementById("pitchLabel");
const stopVoiceBtn = document.getElementById("stopVoiceBtn");
const replayBtn = document.getElementById("replayBtn");
const statusEl = document.getElementById("status");
const copyBtn        = document.getElementById("copyBtn");
const saveBtn        = document.getElementById("saveBtn");
const shareBtn       = document.getElementById("shareBtn");
const clearHistoryBtn= document.getElementById("clearHistoryBtn");
const clearFavBtn    = document.getElementById("clearFavBtn");
const historyListEl  = document.getElementById("historyList");
const favListEl      = document.getElementById("favList");

// simple in-memory + localStorage storage
let history  = JSON.parse(localStorage.getItem("vt_history") || "[]");
let favorites= JSON.parse(localStorage.getItem("vt_favorites") || "[]");

function renderHistory() {
  if (!history.length) {
    historyListEl.textContent = "(empty)";
  } else {
    historyListEl.textContent = history
      .slice(0, 5)
      .map(h => h.output)
      .join("  •  ");
  }
}

function renderFavorites() {
  if (!favorites.length) {
    favListEl.textContent = "(empty)";
  } else {
    favListEl.textContent = favorites
      .slice(0, 5)
      .map(f => f.output)
      .join("  •  ");
  }
}

function addToHistory(original, output, mode, targetKey) {
  if (!original || !output) return;
  history.unshift({ original, output, mode, targetKey });
  if (history.length > 20) history.pop();
  localStorage.setItem("vt_history", JSON.stringify(history));
  renderHistory();
}

function addToFavorites(original, output, mode, targetKey) {
  if (!original || !output) return;
  favorites.unshift({ original, output, mode, targetKey });
  if (favorites.length > 50) favorites.pop();
  localStorage.setItem("vt_favorites", JSON.stringify(favorites));
  renderFavorites();
}

// initial render
renderHistory();
renderFavorites();

// Mode switching
modeTabs.forEach(tab => {
  tab.addEventListener("click", () => {
    modeTabs.forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentMode = tab.dataset.mode;
    modeLabel.textContent = currentMode === "assistant" ? "Assistant" : "Translator";
    statusEl.textContent = "Ready.";
  });
});

// Counters
inputText.addEventListener("input", () => {
  const text = inputText.value;
  charCount.textContent = text.length + " characters";
  const wc = text.trim() ? text.trim().split(/\\s+/).length : 0;
  wordCount.textContent = wc + " words";
});

// Voice helpers
function stopSpeaking() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
function speak(text, langCode) {
  if (!text || !("speechSynthesis" in window)) return;
  stopSpeaking();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = langCode || "en-US";
  u.rate = voiceRate;
  u.pitch = voicePitch;
  window.speechSynthesis.speak(u);
}
rateSlider.addEventListener("input", () => {
  voiceRate = parseFloat(rateSlider.value);
  rateLabel.textContent = voiceRate.toFixed(1) + "x";
});
pitchSlider.addEventListener("input", () => {
  voicePitch = parseFloat(pitchSlider.value);
  pitchLabel.textContent = voicePitch.toFixed(1);
});
stopVoiceBtn.addEventListener("click", () => {
  stopSpeaking();
  statusEl.textContent = "Voice stopped.";
});
replayBtn.addEventListener("click", () => {
  if (lastOutput) speak(lastOutput, lastTTS);
});
copyBtn.addEventListener("click", () => {
  const text = translatedEl.textContent;
  if (!text) { statusEl.textContent = "Nothing to copy."; return; }
  navigator.clipboard.writeText(text);
  statusEl.textContent = "Copied result to clipboard.";
});

saveBtn.addEventListener("click", () => {
  const orig = originalEl.textContent;
  const out  = translatedEl.textContent;
  if (!out) { statusEl.textContent = "Nothing to save."; return; }
  addToFavorites(orig, out, currentMode, targetLang.value);
  statusEl.textContent = "Saved to favorites.";
});

shareBtn.addEventListener("click", async () => {
  const orig = originalEl.textContent;
  const out  = translatedEl.textContent;
  if (!out) { statusEl.textContent = "Nothing to share."; return; }
  const text = `Original: ${orig}\\nResult: ${out}`;
  if (navigator.share) {
    try {
      await navigator.share({ title: "AI Voice Translator", text });
      statusEl.textContent = "Shared.";
    } catch (e) {
      statusEl.textContent = "Share cancelled.";
    }
  } else {
    navigator.clipboard.writeText(text);
    statusEl.textContent = "Copied to clipboard (no Web Share support).";
  }
});

clearHistoryBtn.addEventListener("click", () => {
  history = [];
  localStorage.setItem("vt_history", "[]");
  renderHistory();
  statusEl.textContent = "History cleared.";
});

clearFavBtn.addEventListener("click", () => {
  favorites = [];
  localStorage.setItem("vt_favorites", "[]");
  renderFavorites();
  statusEl.textContent = "Favorites cleared.";
});

// Recording
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      statusEl.textContent = "Processing audio…";
      const blob = new Blob(chunks, { type: "audio/webm" });
      const fd = new FormData();
      fd.append("file", blob, "voice.webm");
      try {
        const res = await fetch(`${BACKEND_BASE}/speech-to-text`, {
          method: "POST",
          headers: { "X-Access-Token": API_ACCESS_TOKEN },
          body: fd
        });
        const data = await res.json();
        if (data.error) {
          statusEl.textContent = data.error;
          return;
        }
        const txt = data.text || "";
        inputText.value = txt;
        inputText.dispatchEvent(new Event("input"));
        await processText(txt);
      } catch (e) {
        statusEl.textContent = "Error: " + e.message;
      }
    };
    mediaRecorder.start();
    recording = true;
    recordBtn.classList.add("recording");
    recordBtn.textContent = "⏹ Stop Recording";
    statusEl.textContent = "Listening… speak now.";
  } catch (e) {
    statusEl.textContent = "Microphone blocked or unavailable.";
  }
}
function stopRecording() {
  if (mediaRecorder && recording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    recording = false;
    recordBtn.classList.remove("recording");
    recordBtn.textContent = "🎙 Start Recording";
  }
}
recordBtn.addEventListener("click", () => {
  stopSpeaking();
  if (recording) stopRecording();
  else startRecording();
});

// Clear
clearBtn.addEventListener("click", () => {
  inputText.value = "";
  originalEl.textContent = "";
  translatedEl.textContent = "";
  searchLink.innerHTML = "";
  statusEl.textContent = "Cleared.";
  inputText.dispatchEvent(new Event("input"));
});

// Process button
processBtn.addEventListener("click", async () => {
  await processText(inputText.value);
});

async function processText(text) {
  text = (text || "").trim();
  if (!text) {
    statusEl.textContent = "Please enter some text.";
    return;
  }
  originalEl.textContent = text;
  translatedEl.textContent = "";
  searchLink.innerHTML = "";
  lastOutput = "";
  replayBtn.disabled = true;

  const targetKey = targetLang.value;
  const targetInfo = LANGUAGES[targetKey] || { name: "English", tts: "en-US" };
  lastTTS = targetInfo.tts;

  try {
    if (currentMode === "translator") {
      statusEl.textContent = "Translating…";
      const res = await fetch(`${BACKEND_BASE}/translate-text`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Access-Token": API_ACCESS_TOKEN
        },
        body: JSON.stringify({
          text,
          target_language: targetInfo.name,
          source_language: sourceLang.value === "auto"
            ? "auto"
            : LANGUAGES[sourceLang.value]?.name,
          include_pronunciation: false
        })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      const out = data.translated_text || "";
      translatedEl.textContent = out;
      addToHistory(text, out, "translator", targetKey);
      lastOutput = out;
      replayBtn.disabled = !out;
      statusEl.textContent = "Done.";
      speak(out, targetInfo.tts);
    } else {
      // Assistant mode
      statusEl.textContent = "Asking assistant…";
      const res = await fetch(`${BACKEND_BASE}/ask-assistant`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Access-Token": API_ACCESS_TOKEN
        },
        body: JSON.stringify({
          question: text,
          target_language: targetInfo.name
        })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      const out = data.answer_translated || data.answer_original || "";
      translatedEl.textContent = out;
      addToHistory(text, out, "assistant", targetKey);
      lastOutput = out;
      replayBtn.disabled = !out;
      if (data.google_search_url) {
        searchLink.innerHTML =
          '<a href="' + data.google_search_url + '" target="_blank">🔍 View related results on Google</a>';
      }
      statusEl.textContent = "Assistant answered.";
      speak(out, targetInfo.tts);
    }
  } catch (e) {
    statusEl.textContent = "Error: " + e.message;
  }
}
</script>

<!-- Razorpay payment flow -->
<script>
const payBtn = document.getElementById("payBtn");

if (payBtn) {
  payBtn.addEventListener("click", async () => {
    try {
      // 1) Create order
      const res = await fetch(`${BACKEND_BASE}/create-order`, {
        method: "POST"
      });
      const order = await res.json();

      if (order.error || order.detail) {
        alert("Error creating order: " + (order.error || order.detail));
        return;
      }

      // 2) Configure Razorpay Checkout
      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency || "INR",
        name: "AI Voice Translator",
        description: "Unlock Full Access",
        order_id: order.order_id,
        handler: async function (response) {
          try {
            // 3) Verify with backend
            const verifyRes = await fetch(`${BACKEND_BASE}/verify-payment`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(response)
            });
            const verify = await verifyRes.json();

            if (verify.success) {
              localStorage.setItem("translator_paid", "yes");
              if (window._translatorShowPaidUI) {
                window._translatorShowPaidUI();
              }
              alert("Payment Successful! 🎉 Full access unlocked.");
              // If you want redirect instead:
              // window.location.href = "/success";
            } else {
              alert("Payment verification failed. Please try again.");
            }
          } catch (e) {
            alert("Error verifying payment: " + e.message);
          }
        },
        theme: { color: "#5b8efb" }
      };

      const rzp = new Razorpay(options);
      rzp.on("payment.failed", function () {
        alert("Payment failed. Please try again.");
      });
      rzp.open();
    } catch (e) {
      alert("Something went wrong: " + e.message);
    }
  });
}
</script>

</body>
</html>
    """


# 1️⃣ Speech → Text using Groq Whisper
@app.post("/speech-to-text")
async def speech_to_text(
    file: UploadFile = File(...),
    _: None = Depends(verify_access_token),
):
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


# 2️⃣ Text → Translated text
@app.post("/translate-text")
async def translate_text(
    data: dict,
    _: None = Depends(verify_access_token),
):
  text = data.get("text")
  target_language = data.get("target_language")
  source_language = data.get("source_language")
  include_pronunciation = data.get("include_pronunciation", False)

  if not text or not target_language:
    return {"error": "text and target_language are required"}

  prompt = (f"Translate this text into {target_language}. "
            f"Return ONLY the translated sentence with no explanation.\n"
            f"Text: {text}")

  try:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":
                "system",
                "content":
                "You are a translation engine. Output only the translated text.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content
    translated = content.strip() if content else ""

    result = {"translated_text": translated}

    # Optional pronunciation
    if include_pronunciation and target_language.lower() in [
        "chinese",
        "japanese",
        "korean",
        "arabic",
        "russian",
        "greek",
        "hebrew",
        "thai",
        "hindi",
    ]:
      pron_prompt = (
          "Provide the romanized pronunciation (Latin letters) for this text. "
          "Return ONLY the romanization:\n" + translated)
      pron_response = groq_client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[
              {
                  "role": "system",
                  "content": "You provide romanized pronunciations.",
              },
              {
                  "role": "user",
                  "content": pron_prompt,
              },
          ],
      )
      pron_content = pron_response.choices[0].message.content
      result["pronunciation"] = pron_content.strip() if pron_content else ""

    # Optional language detection
    if source_language and source_language.lower() == "auto":
      detect_prompt = (
          "What language is this text written in? Reply with only the language name:\n"
          + text)
      detect_response = groq_client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[
              {
                  "role":
                  "system",
                  "content":
                  "You detect languages. Reply with only the language name.",
              },
              {
                  "role": "user",
                  "content": detect_prompt,
              },
          ],
      )
      detect_content = detect_response.choices[0].message.content
      result["detected_language"] = detect_content.strip(
      ) if detect_content else ""

    return result
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": str(e)})


# 3️⃣ Assistant: answer questions + optional translation + Google link
@app.post("/ask-assistant")
async def ask_assistant(
    data: dict,
    _: None = Depends(verify_access_token),
):
  question = data.get("question")
  target_language = data.get("target_language", "English")

  if not question:
    return {"error": "question is required"}

  try:
    base_answer = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":
                "system",
                "content":
                "You are a helpful, concise assistant. Answer clearly in English in 2-4 sentences.",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": str(e)})

  content_en = base_answer.choices[0].message.content
  answer_en = content_en.strip() if content_en else ""

  if target_language and target_language.lower() != "english":
    prompt = (f"Translate this answer into {target_language}. "
              f"Return ONLY the translated sentences.\nText: {answer_en}")
    try:
      translated_resp = groq_client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[
              {
                  "role":
                  "system",
                  "content":
                  "You are a translation engine. Output only the translated text.",
              },
              {
                  "role": "user",
                  "content": prompt,
              },
          ],
      )
      translated_content = translated_resp.choices[0].message.content
      answer_translated = (translated_content.strip()
                           if translated_content else answer_en)
    except Exception:
      answer_translated = answer_en
  else:
    answer_translated = answer_en

  google_url = "https://www.google.com/search?q=" + urllib.parse.quote(
      question)

  return {
      "answer_original": answer_en,
      "answer_translated": answer_translated,
      "google_search_url": google_url,
      "target_language": target_language,
  }


# Extra endpoints (grammar / summarize / dictionary / detect-language)
@app.post("/fix-grammar")
async def fix_grammar(data: dict):
  text = data.get("text")
  if not text:
    return {"error": "text is required"}

  prompt = ("Fix any grammar, spelling, and punctuation errors in this text. "
            "Return ONLY the corrected text with no explanation:\n" + text)

  try:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a grammar correction engine.",
            },
            {
                "role": "user",
                "content": prompt,
            },
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

  prompt = "Summarize the following text in 2-3 concise sentences. Return ONLY the summary:\n" + text

  try:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a summarization engine.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    content = response.choices[0].message.content
    summary_en = content.strip() if content else ""

    if target_language.lower() != "english":
      trans_prompt = (
          f"Translate this summary into {target_language}. Return ONLY the translation:\n{summary_en}"
      )
      trans_response = groq_client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[
              {
                  "role": "system",
                  "content": "You are a translation engine.",
              },
              {
                  "role": "user",
                  "content": trans_prompt,
              },
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
            {
                "role": "system",
                "content": "You are a dictionary.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    content = response.choices[0].message.content
    definition_en = content.strip() if content else ""

    if target_language.lower() != "english":
      trans_prompt = (
          f"Translate this dictionary entry into {target_language}. Keep the formatting:\n{definition_en}"
      )
      trans_response = groq_client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[
              {
                  "role": "system",
                  "content": "You are a translation engine.",
              },
              {
                  "role": "user",
                  "content": trans_prompt,
              },
          ],
      )
      trans_content = trans_response.choices[0].message.content
      definition = trans_content.strip() if trans_content else definition_en
    else:
      definition = definition_en

    pron_prompt = (
        f"Provide the phonetic pronunciation for the word '{word}' using IPA notation. "
        f"Return only the pronunciation:")
    pron_response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You provide phonetic pronunciations.",
            },
            {
                "role": "user",
                "content": pron_prompt,
            },
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

  prompt = (
      "What language is this text written in? Reply with only the language name:\n"
      + text)

  try:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You detect languages.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    content = response.choices[0].message.content
    detected = content.strip() if content else ""
    return {"detected_language": detected}
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": str(e)})


# ✅ Create Razorpay order for Premium purchase (₹59)
@app.post("/create-order")
def create_order():
  if razorpay_client is None:
    raise HTTPException(status_code=500, detail="Razorpay not configured")

  amount_rupees = 59  # change this price whenever you want
  amount_paise = amount_rupees * 100  # Razorpay uses paise

  try:
    order = razorpay_client.order.create(
        dict(
            amount=amount_paise,
            currency="INR",
            payment_capture=1,  # auto capture
            notes={"product": "AI Voice Translator Premium"},
        ))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

  return {
      "order_id": order["id"],
      "amount": order["amount"],
      "currency": order["currency"],
      "key_id": RAZORPAY_KEY_ID,
  }


# ✅ Verify Razorpay payment signature + log
@app.post("/verify-payment")
async def verify_payment(data: dict):
  if razorpay_client is None:
    raise HTTPException(status_code=500, detail="Razorpay not configured")

  order_id = data.get("razorpay_order_id")
  payment_id = data.get("razorpay_payment_id")
  signature = data.get("razorpay_signature")

  if not (order_id and payment_id and signature):
    raise HTTPException(status_code=400, detail="Missing payment details")

  try:
    # Use Razorpay utility to verify HMAC signature
    razorpay_client.utility.verify_payment_signature({
        "razorpay_order_id":
        order_id,
        "razorpay_payment_id":
        payment_id,
        "razorpay_signature":
        signature,
    })
  except razorpay.errors.SignatureVerificationError:
    return {"success": False}

  # ✅ Signature is valid → payment succeeded → log it
  payments_log.append({
      "order_id": order_id,
      "payment_id": payment_id,
      "amount": 59 * 100,
      "currency": "INR",
      "timestamp": datetime.utcnow().isoformat() + "Z",
  })

  return {"success": True}


# Simple success page (optional redirect target)
@app.get("/success", response_class=HTMLResponse)
def payment_success_page():
  return """
    <html>
      <head><title>Payment Successful</title></head>
      <body style="font-family: sans-serif; background:#0d1117; color:white; display:flex; justify-content:center; align-items:center; min-height:100vh;">
        <div style="background:#161b22; padding:24px 28px; border-radius:16px; border:1px solid #30363d; max-width:420px; text-align:center;">
          <h2>✅ Payment successful</h2>
          <p>Your AI Voice Translator is now unlocked on this browser.</p>
          <a href="/ui" style="display:inline-block; margin-top:16px; padding:10px 18px; background:#1f6feb; color:white; border-radius:8px; text-decoration:none;">Go to App</a>
        </div>
      </body>
    </html>
    """


# Admin endpoint to view payment logs
@app.get("/admin/payments")
def get_payments(admin_key: str = Query(...)):
  if admin_key != os.getenv("ADMIN_KEY"):
    raise HTTPException(status_code=401, detail="Not allowed")
  return payments_log
