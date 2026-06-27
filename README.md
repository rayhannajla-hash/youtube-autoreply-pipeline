# 🤖 YouTube Auto Reply Pipeline

> Automated YouTube comment reply system using N8N, Claude Code CLI, and Google Sheets — built for content creators who want to stay engaged with their audience without manual effort.

---

## 📌 Overview

Pipeline otomasi yang berjalan setiap 1 jam untuk membalas komentar YouTube secara otomatis menggunakan AI (Claude). Setiap reply di-generate dalam Bahasa Indonesia, natural, dan engaging — lalu dicatat ke Google Sheets sebagai tracker.

**Dibangun untuk:** Content creator YouTube yang aktif di niche edukasi dan ingin menjaga engagement tanpa harus membalas komentar satu per satu secara manual.

---

## 🏗️ Architecture

```
[N8N Schedule: Every 1 Hour]
         ↓
[YouTube Data API v3]
  → GET commentThreads (max 50, order: time)
         ↓
[Google Sheets]
  → Read replied_comments (filter duplikat)
         ↓
[Code Node: Filter & Sanitize]
  → Exclude already-replied comments
  → Sanitize text (strip quotes, newlines, backslash)
  → Build prompt string
         ↓
[HTTP Request → Claude Bridge Server]
  → POST http://127.0.0.1:8765/reply
  → Python bridge calls: claude.exe -p "prompt"
         ↓
[Code Node: Clean Output]
  → Strip wrapping quotes from Claude output
  → Fallback jika output kosong
         ↓
[YouTube Data API v3]
  → POST /comments (reply ke comment thread)
         ↓
[Google Sheets]
  → Append: commentId, timestamp, videoId, commentText, replyText
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Workflow Automation | [N8N](https://n8n.io) v2.23.4 (self-hosted) |
| AI Reply Generation | [Claude Code CLI](https://claude.ai/code) via local bridge |
| Bridge Server | Python 3 (standard library only, no pip install) |
| Comment Source | YouTube Data API v3 |
| Deduplication Tracker | Google Sheets |
| Auth | OAuth 2.0 (Google Cloud Console) |
| OS | Windows 10/11 |

---

## ✨ Features

- ✅ **Auto-reply** semua komentar baru setiap 1 jam
- ✅ **AI-generated replies** via Claude — natural, Bahasa Indonesia, max 3 kalimat
- ✅ **Deduplication** via Google Sheets — tidak ada komentar yang dibalas dua kali
- ✅ **Sanitization** — komentar dengan karakter spesial (quotes, newlines) aman diproses
- ✅ **Fallback reply** jika Claude output kosong
- ✅ **Auto-start** bridge server via Windows Task Scheduler
- ✅ **Audit trail** lengkap di Google Sheets (commentId, timestamp, reply text)

---

## 📁 File Structure

```
youtube-autoreply/
├── claude_bridge.py           # Python bridge server (N8N → Claude CLI)
├── claude_bridge_startup.xml  # Windows Task Scheduler config (auto-start)
├── youtube_autoreply_v2.json  # N8N workflow (importable)
└── README.md
```

---

## ⚙️ Prerequisites

| Requirement | Notes |
|---|---|
| N8N self-hosted | Tested on v2.23.4 |
| Claude Code CLI | `claude.exe` terinstall di path lokal |
| Python 3.x | Standard library only, no pip install needed |
| Google Cloud Project | YouTube Data API v3 + Google Sheets API enabled |
| OAuth 2.0 Credentials | Client ID + Client Secret + Refresh Token |
| Google Sheets | Tab `replied_comments` dengan 5 kolom header |

---

## 🚀 Setup Guide

### 1. Google Cloud Setup

```
Google Cloud Console
├── Enable: YouTube Data API v3
├── Enable: Google Sheets API
├── OAuth Consent Screen → External → Add Test Users
└── Credentials → OAuth 2.0 → Web Application
    └── Authorized redirect URIs:
        ├── https://developers.google.com/oauthplayground
        └── http://localhost:5678/rest/oauth2-credential/callback
```

Generate Refresh Token via [OAuth Playground](https://developers.google.com/oauthplayground):
- Scope: `https://www.googleapis.com/auth/youtube.force-ssl`

### 2. Google Sheets Setup

Buat spreadsheet baru dengan tab bernama `replied_comments` dan header di baris 1:

```
| commentId | timestamp | videoId | commentText | replyText |
```

### 3. Claude Bridge Server

```bash
# Simpan claude_bridge.py ke local
# Jalankan manual:
python claude_bridge.py

# Atau install sebagai Windows startup task:
Register-ScheduledTask -Xml (Get-Content "claude_bridge_startup.xml" -Raw) -TaskName "ClaudeBridgeServer" -Force
```

Bridge berjalan di `http://127.0.0.1:8765/reply`

Test bridge:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8765/reply" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"prompt":"Balas: Videonya bagus!"}' `
  -UseBasicParsing
```

### 4. N8N Setup

1. Import `youtube_autoreply_v2.json` ke N8N
2. Setup credentials:
   - **YouTube OAuth2** → OAuth2 API (generic) → isi Client ID, Secret, Refresh Token
   - **Google Sheets** → Google Sheets OAuth2 API → Sign in with Google
3. Edit node `Get YouTube Comments`:
   - Ganti `GANTI_CHANNEL_ID_KAMU` → Channel ID format `UCxxxxxxx`
4. Edit node `Baca Sheet Sudah Dibalas` dan `Catat ke Google Sheets`:
   - Ganti Spreadsheet ID
   - Sheet name: `replied_comments`
5. Aktifkan workflow → toggle **Active**

---

## 🔧 Configuration

### Ubah Prompt Claude

Di node **Filter dan Sanitize**, cari bagian:

```javascript
const prompt = `Kamu adalah admin channel YouTube yang ramah dan informatif. 
Balas komentar dari ${sanitizedAuthor} dalam Bahasa Indonesia, 
maksimal 3 kalimat, natural dan engaging...`
```

Sesuaikan dengan tone dan persona channel kamu.

### Ubah Interval Polling

Di node **Setiap 1 Jam** → ubah `hoursInterval` sesuai kebutuhan.

### Ubah Port Bridge Server

Di `claude_bridge.py`:
```python
PORT = 8765  # Ganti sesuai kebutuhan
```

Sesuaikan juga di node **Generate Reply Claude** → URL `http://127.0.0.1:8765/reply`.

---

## ⚠️ Known Limitations

- Pipeline hanya berjalan saat **laptop hidup** dan terhubung internet
- YouTube OAuth Refresh Token bisa expired jika tidak digunakan > 6 bulan
- Memproses maksimal **50 komentar per run** (YouTube API limit per request)
- Tidak support multi-channel dalam satu workflow (perlu duplikat workflow)
- Claude Code CLI tetap memanggil Anthropic API — bukan offline/local model

---

## 🔮 Roadmap

- [ ] TikTok comment auto-reply (pending API access)
- [ ] Multi-channel support dalam satu workflow
- [ ] Sentiment filter (skip komentar negatif/spam)
- [ ] Deploy ke VPS untuk 24/7 operation
- [ ] Reply tone customization per video topic

---

## 📊 How It Works (Detail)

### Bridge Server Pattern

N8N tidak memiliki Execute Command node yang aktif di versi ini, sehingga digunakan pendekatan **local HTTP bridge**:

```
N8N HTTP Request
      ↓ POST /reply {"prompt": "..."}
Python HTTPServer (127.0.0.1:8765)
      ↓ subprocess.run()
claude.exe -p "prompt"
      ↓ stdout
{"reply": "...", "exitCode": 0}
      ↑ JSON response
N8N HTTP Request
```

### Deduplication Logic

```javascript
// Di Code Node "Filter dan Sanitize"
const repliedIds = sheetsItems.map(i => i.json.commentId).filter(Boolean);
const unreplied = ytItems.filter(item => !repliedIds.includes(item.id));
```

---

## 📝 License

MIT License — bebas digunakan dan dimodifikasi.

---

## 🙋 Author

Built by **Budhi** — R&D Manager & Content Creator  
YouTube channel niche: Psikologi & Edukasi Keuangan

---

*Pipeline ini dibangun iteratif dalam satu sesi — dari OAuth setup, debugging Execute Command node, Python bridge workaround, hingga full production deployment.*
