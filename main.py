from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
import urllib.parse

app = FastAPI()

# Allow browser frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for now allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client (uses your GROQ_API_KEY from Secrets)
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
  <title>AI Voice Translator & Assistant</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      background: #0d1117;
      font-family: 'Segoe UI', Arial, sans-serif;
      color: white;
      display: flex;
      justify-content: center;
      padding-top: 25px;
    }

    .container {
      width: 95%;
      max-width: 900px;
      background: #161b22;
      padding: 25px;
      border-radius: 15px;
      box-shadow: 0 0 25px rgba(0, 150, 255, 0.2);
      border: 1px solid #1f6feb;
    }

    h2 {
      text-align: center;
      margin-bottom: 15px;
      font-size: 26px;
      color: #58a6ff;
      text-shadow: 0 0 10px #1f6feb;
    }

    label {
      font-weight: bold;
    }

    select, textarea {
      width: 100%;
      background: #0d1117;
      border: 1px solid #30363d;
      color: white;
      padding: 8px;
      border-radius: 6px;
      margin-top: 5px;
    }

    textarea {
      height: 70px;
    }

    button {
      padding: 10px 18px;
      font-size: 14px;
      border: none;
      border-radius: 8px;
      margin-top: 8px;
      cursor: pointer;
      transition: 0.25s;
    }

    .micButton {
      background: #1f6feb;
      color: white;
      box-shadow: 0 0 12px rgba(31, 111, 235, 0.6);
    }

    .micButton:hover {
      box-shadow: 0 0 18px rgba(65, 140, 255, 0.9);
    }

    #retranslateBtn, #replayBtn, #pauseVoiceBtn, #resumeVoiceBtn, #manualTranslateBtn {
      background: #238636;
      color: white;
    }

    #retranslateBtn:hover,
    #replayBtn:hover,
    #pauseVoiceBtn:hover,
    #resumeVoiceBtn:hover,
    #manualTranslateBtn:hover {
      background: #2ea043;
    }

    #stopVoiceBtn {
      background: #da3633;
      color: white;
    }

    #stopVoiceBtn:hover {
      background: #f85149;
    }

    .modeGroup,
    .voice-controls {
      padding: 12px;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 10px;
      margin-bottom: 15px;
    }

    .pill {
      display: inline-block;
      background: #21262d;
      padding: 4px 10px;
      border-radius: 8px;
      margin-right: 6px;
      font-size: 12px;
      border: 1px solid #30363d;
    }

    #status {
      margin-top: 10px;
      font-style: italic;
      color: #58a6ff;
    }

    #originalText {
      color: #79c0ff;
      white-space: pre-wrap;
      font-size: 16px;
    }

    #translatedText {
      color: #3fb950;
      white-space: pre-wrap;
      font-size: 16px;
    }

    a {
      color: #58a6ff;
    }
  </style>
</head>

<body>
<div class="container">

  <h2>🌐 AI Voice Translator & Assistant</h2>

  <!-- MODE SELECTOR -->
  <div class="modeGroup">
    <label><input type="radio" name="mode" value="translator" checked> Translator mode</label>
    &nbsp;&nbsp;
    <label><input type="radio" name="mode" value="assistant"> Assistant mode (ask questions)</label>
  </div>

  <!-- LANGUAGE SELECT DROPDOWN -->
  <label for="langSelect"><b>Target language:</b></label>
  <select id="langSelect">
    <option value="auto">Auto (say "in Hindi", "in Japanese", etc.)</option>
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
  </select>

  <p style="font-size: 12px; color: #aaa;">
    In <b>Translator mode</b> the app translates your speech into the selected language.<br>
    In <b>Assistant mode</b> you can ask questions like:
    <span class="pill">"What is the capital of France?"</span>
    <span class="pill">"Explain quantum physics"</span>
    <span class="pill">"How to study product management?"</span>
  </p>

  <!-- MAIN BUTTONS -->
  <button id="recordBtn" class="micButton">🎙️ Start Recording (Translate)</button>
  <button id="retranslateBtn" disabled>🔁 Translate / Answer Again</button>
  <button id="replayBtn" disabled>▶️ Replay Last Voice</button>

  <!-- VOICE CONTROL BUTTONS -->
  <button id="stopVoiceBtn">⏹ Stop Voice</button>
  <button id="pauseVoiceBtn">⏸ Pause Voice</button>
  <button id="resumeVoiceBtn">▶️ Resume Voice</button>

  <div class="voice-controls">
    <b>Voice controls</b><br /><br/>
    <label>
      Speed:
      <input id="rateSlider" type="range" min="0.5" max="1.5" step="0.1" value="1">
      <span id="rateLabel">1.0x</span>
    </label>
    &nbsp;&nbsp;
    <label>
      Pitch:
      <input id="pitchSlider" type="range" min="0.5" max="2" step="0.1" value="1">
      <span id="pitchLabel">1.0</span>
    </label>
  </div>

  <p id="status"></p>

  <h3>Original Speech / Question:</h3>
  <p id="originalText"></p>

  <h3>Translated / Assistant Answer:</h3>
  <p id="translatedText"></p>

  <h3>Search results:</h3>
  <div id="searchLink"></div>

  <h3>Type text manually (optional):</h3>
  <textarea id="manualText" rows="3" placeholder="Type any sentence or question here..."></textarea><br>
  <button id="manualTranslateBtn">Translate / Ask (uses selected mode)</button>

<script>
const BACKEND_BASE = window.location.origin;

// Supported languages
const LANGUAGES = {
  chinese:  { name: "Chinese",  tts: "zh-CN" },
  hindi:    { name: "Hindi",    tts: "hi-IN" },
  japanese: { name: "Japanese", tts: "ja-JP" },
  french:   { name: "French",   tts: "fr-FR" },
  russian:  { name: "Russian",  tts: "ru-RU" },
  italian:  { name: "Italian",  tts: "it-IT" },
  spanish:  { name: "Spanish",  tts: "es-ES" },
  german:   { name: "German",   tts: "de-DE" },
  korean:   { name: "Korean",   tts: "ko-KR" },
  arabic:   { name: "Arabic",   tts: "ar-SA" }
};

let mode = "translator";  // default

// UI references
const recordBtn          = document.getElementById("recordBtn");
const retranslateBtn     = document.getElementById("retranslateBtn");
const replayBtn          = document.getElementById("replayBtn");
const stopVoiceBtn       = document.getElementById("stopVoiceBtn");
const pauseVoiceBtn      = document.getElementById("pauseVoiceBtn");
const resumeVoiceBtn     = document.getElementById("resumeVoiceBtn");
const langSelect         = document.getElementById("langSelect");
const statusEl           = document.getElementById("status");
const originalEl         = document.getElementById("originalText");
const translatedEl       = document.getElementById("translatedText");
const searchLink         = document.getElementById("searchLink");
const manualTranslateBtn = document.getElementById("manualTranslateBtn");
const manualTextEl       = document.getElementById("manualText");
const rateSlider         = document.getElementById("rateSlider");
const rateLabel          = document.getElementById("rateLabel");
const pitchSlider        = document.getElementById("pitchSlider");
const pitchLabel         = document.getElementById("pitchLabel");

// Mode change
document.querySelectorAll("input[name='mode']").forEach(r => {
  r.addEventListener("change", () => {
    mode = r.value;
    updateRecordButtonLabel();
    statusEl.innerText = "";
  });
});

let recording = false;
let mediaRecorder;
let chunks = [];

let lastOriginalText   = "";
let lastTranslatedText = "";
let lastTtsLangCode    = "";

// voice settings
let voiceRate  = 1.0;
let voicePitch = 1.0;

// Update slider labels
rateSlider.oninput = () => {
  voiceRate = parseFloat(rateSlider.value);
  rateLabel.textContent = voiceRate.toFixed(1) + "x";
};
pitchSlider.oninput = () => {
  voicePitch = parseFloat(pitchSlider.value);
  pitchLabel.textContent = voicePitch.toFixed(1);
};

// Update mic button label
function updateRecordButtonLabel() {
  if (recording) {
    recordBtn.innerText = "⏹ Stop Recording";
  } else {
    if (mode === "assistant") {
      recordBtn.innerText = "🎙️ Start Recording (Ask Assistant)";
    } else {
      recordBtn.innerText = "🎙️ Start Recording (Translate)";
    }
  }
}

// Speech synthesis helpers
function stopSpeaking() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
function pauseSpeaking() {
  if ("speechSynthesis" in window && window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
    window.speechSynthesis.pause();
  }
}
function resumeSpeaking() {
  if ("speechSynthesis" in window && window.speechSynthesis.paused) {
    window.speechSynthesis.resume();
  }
}
function speak(text, langCode) {
  if (!text || !langCode) return;
  if ("speechSynthesis" in window) {
    // stop any previous voice
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = langCode;
    u.rate = voiceRate;
    u.pitch = voicePitch;
    window.speechSynthesis.speak(u);
  }
}

// Detect language from "in Hindi" etc.
function detectLanguageFromSpeech(text) {
  const lower = text.toLowerCase();
  for (const key in LANGUAGES) {
    if (lower.includes(" in " + key) || lower.includes(" to " + key)) {
      return key;
    }
  }
  return null;
}

// Translator flow
async function translateAndSpeak(originalText) {
  if (!originalText || !originalText.trim()) {
    statusEl.innerText = "No text to translate.";
    return;
  }

  lastOriginalText = originalText;
  translatedEl.innerText = "";
  searchLink.innerHTML = "";

  let key = langSelect.value;
  if (key === "auto") {
    const detected = detectLanguageFromSpeech(originalText);
    key = detected || "chinese";
  }

  const langConfig = LANGUAGES[key];
  const targetLanguageName = langConfig.name;
  const ttsLangCode        = langConfig.tts;

  statusEl.innerText = "Translating to " + targetLanguageName + "…";

  const res = await fetch(`${BACKEND_BASE}/translate-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: originalText, target_language: targetLanguageName })
  });

  const data = await res.json();
  const translatedText = data.translated_text || "(no translation)";

  translatedEl.innerText = translatedText;
  statusEl.innerText = "Translation done. Speaking…";

  lastTranslatedText = translatedText;
  lastTtsLangCode    = ttsLangCode;

  retranslateBtn.disabled = false;
  replayBtn.disabled      = false;

  speak(translatedText, ttsLangCode);
}

// Assistant flow
async function askAssistantAndSpeak(questionText) {
  if (!questionText || !questionText.trim()) {
    statusEl.innerText = "No question to ask.";
    return;
  }

  lastOriginalText = questionText;
  translatedEl.innerText = "";
  searchLink.innerHTML = "";

  let key = langSelect.value;
  let langConfig;
  if (key === "auto") {
    const detected = detectLanguageFromSpeech(questionText);
    if (detected && LANGUAGES[detected]) {
      langConfig = LANGUAGES[detected];
    } else {
      langConfig = { name: "English", tts: "en-US" };
    }
  } else {
    langConfig = LANGUAGES[key];
  }

  const targetLanguageName = langConfig.name;
  const ttsLangCode        = langConfig.tts || "en-US";

  statusEl.innerText = "Asking assistant…";

  const res = await fetch(`${BACKEND_BASE}/ask-assistant`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: questionText,
      target_language: targetLanguageName
    })
  });

  const data = await res.json();

  const answerText = data.answer_translated || data.answer_original || "(no answer)";
  translatedEl.innerText = answerText;

  if (data.google_search_url) {
    searchLink.innerHTML =
      '<a href="' + data.google_search_url + '" target="_blank">🔎 View related websites on Google</a>';
  }

  statusEl.innerText = "Assistant answered. Speaking…";

  lastTranslatedText = answerText;
  lastTtsLangCode    = ttsLangCode;

  retranslateBtn.disabled = false;
  replayBtn.disabled      = false;

  speak(answerText, ttsLangCode);
}

// Mic button
recordBtn.onclick = async () => {
  // Always stop current voice when starting a new recording
  stopSpeaking();

  if (!recording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      chunks = [];

      mediaRecorder.ondataavailable = e => chunks.push(e.data);

      mediaRecorder.onstop = async () => {
        statusEl.innerText = "Processing audio…";

        const blob = new Blob(chunks, { type: "audio/webm" });
        const fd = new FormData();
        fd.append("file", blob, "voice.webm");

        const res = await fetch(`${BACKEND_BASE}/speech-to-text`, {
          method: "POST",
          body: fd
        });

        const data = await res.json();
        const text = data.text || "";
        originalEl.innerText = text;

        if (mode === "translator") {
          await translateAndSpeak(text);
        } else {
          await askAssistantAndSpeak(text);
        }
      };

      mediaRecorder.start();
      recording = true;
      updateRecordButtonLabel();
      statusEl.innerText = "Listening… speak now.";

    } catch (e) {
      console.error(e);
      statusEl.innerText = "Microphone blocked or unavailable.";
    }
  } else {
    mediaRecorder.stop();
    recording = false;
    updateRecordButtonLabel();
  }
};

// Replay last output
replayBtn.onclick = () => {
  speak(lastTranslatedText, lastTtsLangCode);
};

// Re-translate / re-answer last original text
retranslateBtn.onclick = () => {
  if (!lastOriginalText) {
    statusEl.innerText = "No previous text.";
    return;
  }
  if (mode === "translator") {
    translateAndSpeak(lastOriginalText);
  } else {
    askAssistantAndSpeak(lastOriginalText);
  }
};

// Manual text button (uses current mode)
manualTranslateBtn.onclick = () => {
  const text = manualTextEl.value || "";
  originalEl.innerText = text;
  if (mode === "translator") {
    translateAndSpeak(text);
  } else {
    askAssistantAndSpeak(text);
  }
};

// Voice control buttons
stopVoiceBtn.onclick = () => {
  stopSpeaking();
  statusEl.innerText = "Voice stopped.";
};
pauseVoiceBtn.onclick = () => {
  pauseSpeaking();
  statusEl.innerText = "Voice paused.";
};
resumeVoiceBtn.onclick = () => {
  resumeSpeaking();
  statusEl.innerText = "Voice resumed.";
};

// init label
updateRecordButtonLabel();
rateLabel.textContent = voiceRate.toFixed(1) + "x";
pitchLabel.textContent = voicePitch.toFixed(1);
</script>

</div>
</body>
</html>
    """


# 1️⃣ Speech → Text using Groq Whisper
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


# 2️⃣ Text → Translated text using Groq LLaMA (STRICT: only translated sentence)
@app.post("/translate-text")
async def translate_text(data: dict):
  text = data.get("text")
  target_language = data.get("target_language")

  if not text or not target_language:
    return {"error": "text and target_language are required"}

  prompt = (
      f"Translate this text into {target_language}. "
      f"Return ONLY the translated sentence with no explanation, notes, examples, or breakdowns.\n"
      f"Text: {text}")

  try:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":
                "system",
                "content":
                "You are a translation engine. You output only the translated text.",
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
    )

    translated = response.choices[0].message.content.strip()
    return {"translated_text": translated}
  except Exception as e:
    return JSONResponse(status_code=500, content={"error": str(e)})


# 3️⃣ Assistant: answer questions + optional translation + Google link
@app.post("/ask-assistant")
async def ask_assistant(data: dict):
  question = data.get("question")
  target_language = data.get("target_language", "English")

  if not question:
    return {"error": "question is required"}

  # 1) Get answer in English
  try:
    base_answer = groq_client.chat_completions.create(
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
                "content": question
            },
        ],
    )
  except AttributeError:
    # Correct method for Groq python client is chat.completions.create
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
                "content": question
            },
        ],
    )

  answer_en = base_answer.choices[0].message.content.strip()

  # 2) Translate answer if needed
  if target_language and target_language.lower() != "english":
    prompt = (f"Translate this answer into {target_language}. "
              f"Return ONLY the translated sentences with no explanation.\n"
              f"Text: {answer_en}")
    try:
      translated_resp = groq_client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[
              {
                  "role":
                  "system",
                  "content":
                  "You are a translation engine. You output only the translated text.",
              },
              {
                  "role": "user",
                  "content": prompt
              },
          ],
      )
      answer_translated = translated_resp.choices[0].message.content.strip()
    except Exception:
      answer_translated = answer_en  # fallback
  else:
    answer_translated = answer_en

  # 3) Build a Google search URL
  google_url = "https://www.google.com/search?q=" + urllib.parse.quote(
      question)

  return {
      "answer_original": answer_en,
      "answer_translated": answer_translated,
      "google_search_url": google_url,
      "target_language": target_language,
  }
