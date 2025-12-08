from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
import urllib.parse
import razorpay
from datetime import datetime, timezone
from razorpay.errors import SignatureVerificationError

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


# Simple JSON health-check (optional, for you)
@app.get("/status")
def status():
  return {
      "status": "ok",
      "message": "Voice translator backend is running (Groq-powered)",
  }


# Public landing page
@app.get("/", response_class=HTMLResponse)
def landing_page():
  return """
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>AI Voice Translator & Assistant – Pay ₹59, Use Forever</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        --bg-main: #020617;
        --bg-card: #020617;
        --bg-soft: #020617;
        --accent-blue: #2563eb;
        --accent-blue-soft: #1d4ed8;
        --accent-green: #22c55e;
        --accent-yellow: #facc15;
        --text-main: #e5e7eb;
        --text-muted: #9ca3af;
        --border-subtle: #1f2937;
      }
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: radial-gradient(circle at top, #0f172a 0, #020617 50%, #000 100%);
        color: var(--text-main);
        min-height: 100vh;
      }
      a { color: inherit; text-decoration: none; }

      .page {
        max-width: 1040px;
        margin: 0 auto;
        padding: 24px 16px 40px;
      }

      .nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 28px;
      }
      .nav-left {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
        letter-spacing: 0.03em;
      }
      .nav-logo {
        width: 32px;
        height: 32px;
        border-radius: 999px;
        background: radial-gradient(circle at 30% 20%, #4ade80 0, #22c55e 25%, #2563eb 60%, #0f172a 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
      }
      .badge-live {
        font-size: 11px;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid rgba(34,197,94,0.4);
        color: #bbf7d0;
        background: rgba(21,128,61,0.2);
      }

      .nav-right {
        display: flex;
        gap: 10px;
        align-items: center;
        font-size: 13px;
      }
      .nav-link {
        color: var(--text-muted);
        cursor: pointer;
      }
      .nav-link:hover {
        color: var(--text-main);
      }
      .nav-cta {
        padding: 7px 14px;
        border-radius: 999px;
        background: var(--accent-blue);
        border: none;
        color: white;
        font-size: 13px;
        cursor: pointer;
      }
      .nav-cta:hover {
        background: var(--accent-blue-soft);
      }

      .hero {
        display: grid;
        grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
        gap: 26px;
        align-items: center;
        margin-bottom: 40px;
      }
      @media (max-width: 800px) {
        .hero {
          grid-template-columns: minmax(0, 1fr);
        }
      }

      .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(15,23,42,0.9);
        border: 1px solid var(--border-subtle);
        margin-bottom: 10px;
      }
      .hero-kicker span {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 999px;
        background: rgba(37,99,235,0.2);
        color: #bfdbfe;
      }

      .hero-title {
        font-size: 28px;
        line-height: 1.15;
        margin-bottom: 12px;
      }
      .hero-title span {
        color: #60a5fa;
      }
      .hero-sub {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.6;
        margin-bottom: 16px;
      }

      .hero-benefits {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        font-size: 11px;
        margin-bottom: 18px;
      }
      .chip {
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.5);
        color: #e5e7eb;
        background: rgba(15,23,42,0.8);
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .chip-dot {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: #22c55e;
      }

      .hero-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
      }
      .btn-primary {
        padding: 9px 18px;
        border-radius: 999px;
        border: none;
        background: linear-gradient(135deg,#2563eb,#4f46e5);
        color: white;
        font-size: 13px;
        cursor: pointer;
      }
      .btn-primary:hover {
        filter: brightness(1.08);
      }
      .btn-ghost {
        padding: 8px 14px;
        border-radius: 999px;
        border: 1px solid var(--border-subtle);
        background: rgba(15,23,42,0.85);
        color: var(--text-main);
        font-size: 13px;
        cursor: pointer;
      }
      .btn-ghost:hover {
        border-color: var(--accent-blue);
      }

      .hero-note {
        font-size: 11px;
        color: var(--text-muted);
      }

      .hero-right {
        border-radius: 18px;
        background: radial-gradient(circle at top left,#1d4ed8 0,#020617 55%,#000 100%);
        border: 1px solid rgba(31,41,55,0.9);
        padding: 16px 16px 18px;
        box-shadow: 0 18px 45px rgba(15,23,42,0.85);
      }
      .hero-right-title {
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 6px;
      }
      .hero-right-sub {
        font-size: 11px;
        color: #cbd5f5;
        margin-bottom: 10px;
      }
      .mini-card {
        background: rgba(15,23,42,0.95);
        border-radius: 12px;
        border: 1px solid rgba(30,64,175,0.6);
        padding: 10px 12px;
        font-size: 11px;
        margin-bottom: 10px;
      }
      .mini-label {
        font-size: 10px;
        color: #9ca3af;
        margin-bottom: 2px;
      }
      .mini-value {
        font-size: 12px;
      }
      .mini-row {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-top: 6px;
      }

      .secure-row {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 10px;
        color: #9ca3af;
        margin-top: 8px;
      }
      .secure-dot {
        width: 7px;
        height: 7px;
        border-radius: 999px;
        background: #22c55e;
      }

      .section {
        margin-top: 30px;
        border-top: 1px solid rgba(31,41,55,0.9);
        padding-top: 22px;
      }
      .section-title {
        font-size: 15px;
        margin-bottom: 10px;
      }
      .section-sub {
        font-size: 12px;
        color: var(--text-muted);
        margin-bottom: 16px;
      }

      .features-grid {
        display: grid;
        grid-template-columns: repeat(3,minmax(0,1fr));
        gap: 16px;
      }
      @media (max-width: 900px) {
        .features-grid {
          grid-template-columns: minmax(0,1fr);
        }
      }
      .feature-card {
        background: rgba(15,23,42,0.9);
        border-radius: 14px;
        border: 1px solid var(--border-subtle);
        padding: 12px 12px 14px;
        font-size: 12px;
      }
      .feature-title {
        font-size: 13px;
        margin-bottom: 4px;
      }
      .feature-pill {
        display: inline-block;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid rgba(148,163,184,0.5);
        margin-bottom: 4px;
        color: #e5e7eb;
      }

      .pricing {
        display: grid;
        grid-template-columns: minmax(0,1.2fr) minmax(0,1fr);
        gap: 18px;
        align-items: flex-start;
      }
      @media (max-width: 900px) {
        .pricing { grid-template-columns: minmax(0,1fr); }
      }
      .pricing-card {
        background: rgba(15,23,42,0.98);
        border-radius: 16px;
        border: 1px solid rgba(55,65,81,0.9);
        padding: 14px 14px 16px;
      }
      .price-main {
        font-size: 26px;
        font-weight: 600;
      }
      .price-tag {
        font-size: 11px;
        color: var(--text-muted);
        margin-top: 2px;
        margin-bottom: 8px;
      }
      .price-list {
        list-style: none;
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 6px;
      }
      .price-list li { margin-bottom: 4px; }

      .faq-list {
        font-size: 12px;
        color: var(--text-muted);
      }
      .faq-item {
        margin-bottom: 8px;
      }
      .faq-q {
        color: var(--text-main);
        font-weight: 500;
        margin-bottom: 2px;
      }

      .footer {
        margin-top: 26px;
        font-size: 11px;
        color: var(--text-muted);
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 6px;
        border-top: 1px solid rgba(31,41,55,0.9);
        padding-top: 10px;
      }
    </style>
  </head>
  <body>
    <div class="page">
      <!-- NAV -->
      <header class="nav">
        <div class="nav-left">
          <div class="nav-logo">🌐</div>
          <div>
            <div>AI Voice Translator</div>
            <div style="font-size:11px; color:#9ca3af;">Groq-powered · Razorpay secure</div>
          </div>
        </div>
        <div class="nav-right">
          <div class="badge-live">LIVE · accepting payments</div>
          <button class="nav-cta" onclick="window.location.href='/ui'">Open Translator</button>
        </div>
      </header>

      <!-- HERO -->
      <section class="hero">
        <div>
          <div class="hero-kicker">
            <span>New</span>
            <div>Speak once. Translate & listen in any language.</div>
          </div>
          <h1 class="hero-title">
            Your personal <span>AI voice translator</span><br/>
            for <span>₹59 one-time</span>.
          </h1>
          <p class="hero-sub">
            Record or type anything in your language and instantly hear it in English, Japanese,
            Hindi, Kannada and dozens more. Runs in the browser, no app install, no complicated setup.
          </p>

          <div class="hero-benefits">
            <div class="chip"><div class="chip-dot"></div> One-time payment · lifetime unlock on this browser</div>
            <div class="chip">🎙 Voice input + spoken output</div>
            <div class="chip">🤝 Perfect for students, travellers & online calls</div>
          </div>

          <div class="hero-actions">
            <button class="btn-primary" onclick="window.location.href='/ui'">Start translating now</button>
            <button class="btn-ghost" onclick="document.getElementById('pricing').scrollIntoView({behavior:'smooth'});">
              View pricing & FAQs
            </button>
          </div>
          <div class="hero-note">
            ✅ Payments handled securely by Razorpay. You can test with UPI, card or wallet.<br/>
            ✅ If payment succeeds once, the translator stays unlocked on this browser.
          </div>
        </div>

        <div class="hero-right">
          <div class="hero-right-title">Live preview</div>
          <div class="hero-right-sub">
            Type in English and hear it in Japanese, or speak in Kannada and see English text. All in one screen.
          </div>

          <div class="mini-card">
            <div class="mini-label">Input</div>
            <div class="mini-value">“Hello, hi, how are you?”</div>
            <div class="mini-row">
              <div>
                <div class="mini-label">Source</div>
                <div class="mini-value">English · Auto detect</div>
              </div>
              <div>
                <div class="mini-label">Target</div>
                <div class="mini-value">Japanese 🇯🇵</div>
              </div>
            </div>
          </div>

          <div class="mini-card">
            <div class="mini-label">Output (spoken + text)</div>
            <div class="mini-value">こんにちは、ハロー、どうですか？</div>
            <div class="mini-row">
              <div>
                <div class="mini-label">Mode</div>
                <div class="mini-value">Translator</div>
              </div>
              <div>
                <div class="mini-label">Engine</div>
                <div class="mini-value">Groq LLM + Whisper</div>
              </div>
            </div>
          </div>

          <div class="secure-row">
            <div class="secure-dot"></div>
            <div>Secure checkout with Razorpay · We never see your card / UPI PIN.</div>
          </div>
        </div>
      </section>

      <!-- FEATURES -->
      <section class="section">
        <h2 class="section-title">What you get when you unlock</h2>
        <p class="section-sub">
          All features are included with the one-time payment. No hidden limits, no subscriptions.
        </p>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-pill">🎙 Voice in · Voice out</div>
            <div class="feature-title">Speak naturally, hear the translation</div>
            <p>
              Use your microphone to speak once. The app converts speech to text, translates it,
              and then speaks it aloud in the target language using browser voice.
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-pill">🌐 40+ languages</div>
            <div class="feature-title">From English, Hindi & Kannada to Japanese</div>
            <p>
              Translate between English, Hindi, Japanese, Kannada and many more languages.
              Great for study, travel, anime, K-dramas, or talking to international friends.
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-pill">🤖 Assistant mode</div>
            <div class="feature-title">Ask questions like ChatGPT, but translated</div>
            <p>
              Switch to Assistant mode to ask questions (“Explain gravity”, “What is AI?”) and
              automatically get the answer translated to your chosen language.
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-pill">🧠 Groq + Whisper</div>
            <div class="feature-title">Fast, accurate AI under the hood</div>
            <p>
              Powered by Groq’s Llama-3 models and Whisper for transcription. You get
              fast responses with high-quality translations and summaries.
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-pill">⭐ History & favorites</div>
            <div class="feature-title">Save useful phrases</div>
            <p>
              Mark important translations as favorites and quickly revisit them later
              for conversations, exams, or repeated travel phrases.
            </p>
          </div>
          <div class="feature-card">
            <div class="feature-pill">🛡️ No login required</div>
            <div class="feature-title">Runs in your browser</div>
            <p>
              Everything works inside your browser. No account creation needed.
              Once payment succeeds, the translator stays unlocked on that browser.
            </p>
          </div>
        </div>
      </section>

      <!-- PRICING + FAQ -->
      <section class="section" id="pricing">
        <div class="pricing">
          <div class="pricing-card">
            <h2 class="section-title">Simple pricing</h2>
            <p class="section-sub">
              One small payment, then use the AI voice translator as much as you want
              on this browser.
            </p>
            <div class="price-main">₹59</div>
            <div class="price-tag">One-time payment · Lifetime unlock on this browser</div>

            <button class="btn-primary" style="margin-top:8px;" onclick="window.location.href='/ui'">
              Pay ₹59 & unlock now
            </button>

            <ul class="price-list">
              <li>✔ Unlimited translations & assistant questions</li>
              <li>✔ All supported languages + voice features</li>
              <li>✔ Secure Razorpay checkout (UPI / card / wallet)</li>
              <li>✔ No subscription, no monthly charges</li>
            </ul>
          </div>

          <div>
            <h3 class="section-title" style="margin-bottom:6px;">FAQ</h3>
            <div class="faq-list">
              <div class="faq-item">
                <div class="faq-q">Will I get my money directly to my bank?</div>
                <div>Yes. Payments you receive go to the bank account linked to your Razorpay KYC, as per their settlement cycle.</div>
              </div>
              <div class="faq-item">
                <div class="faq-q">What if I close the tab or restart my laptop?</div>
                <div>Once payment is successful, the app saves the unlock status in your browser. When you reopen the site, the translator stays unlocked on that browser.</div>
              </div>
              <div class="faq-item">
                <div class="faq-q">Can I use it on mobile?</div>
                <div>Yes. The translator works in modern mobile browsers. You’ll need to pay once per device/browser to unlock premium features there.</div>
              </div>
              <div class="faq-item">
                <div class="faq-q">Is my card / UPI data safe?</div>
                <div>All payments are processed by Razorpay. Your card, UPI PIN, and passwords never touch our servers.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer class="footer">
        <div>© 2025 AI Voice Translator. All rights reserved.</div>
        <div>Built in India · Powered by Groq · Payments by Razorpay</div>
      </footer>
    </div>
  </body>
  </html>


      """


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
    # create-order endpoint
    order = razorpay_client.order.create(  # type: ignore[attr-defined]
        dict(
            amount=amount_paise,
            currency="INR",
            payment_capture=1,
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
    razorpay_client.utility.verify_payment_signature(  # type: ignore[attr-defined]
        {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        }
    )
  except SignatureVerificationError:
    return {"success": False}

  # ✅ Signature is valid → payment succeeded → log it
  payments_log.append({
      "order_id": order_id,
      "payment_id": payment_id,
      "amount": 59 * 100,
      "currency": "INR",
      "timestamp": datetime.now(timezone.utc).isoformat(),
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
