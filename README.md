<div align="center">

# 🎀 Slutty Miss

### An AI-powered Discord bot with server management, music, and an e-girl voice assistant

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.7+-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![Powered by Grok](https://img.shields.io/badge/AI-Grok%20xAI-FF6B35?style=for-the-badge&logo=x&logoColor=white)](https://x.ai)
[![Fish Audio](https://img.shields.io/badge/TTS-Fish%20Audio-FF69B4?style=for-the-badge)](https://fish.audio)

</div>

---

## ✨ Features

### 🧠 `!do` — Natural Language Server Management
Tell the bot what you want in plain English. It thinks, plans, confirms, then executes.
```
!do make this server look like a friends group
!do create a gaming section with 3 channels
!do rename the server to Akhilesh Gang
```

### 🎵 `!music` — AI Playlist Builder
Grok generates an 8-song playlist based on your vibe, searches SoundCloud, queues it all up, and plays with zero audio glitches (download-first, not streaming).
```
!music Stay
!music sad hindi songs
!music chill lofi beats
```

### 🎙️ `!listen` — E-Girl Voice AI (Miss)
Type a question, Miss answers you out loud in the voice channel with a soft breathy e-girl voice powered by Fish Audio. Includes live emotion tags — she actually laughs, sighs, and whispers.
```
!listen roast me
!listen tell me something interesting
!listen say something cute
```

### 🤖 `!ai` — Direct Grok Chat *(owner only)*
Raw access to Grok for anything.
```
!ai explain quantum entanglement simply
```

### 🛡️ Moderation
Full mod toolkit — kick, ban, unban, mute, unmute, warn, auto-mute on 3 warnings, clear messages, slowmode, lock/unlock channels, announcements, role management.

---

## 📋 All Commands

| Command | Description |
|---|---|
| `!do [instruction]` | AI executes any server change |
| `!ai [question]` | Chat with Grok (owner only) |
| `!music [song/mood]` | Build & play an AI playlist |
| `!skip` | Skip current song |
| `!stop` | Stop music & leave voice |
| `!pause` / `!resume` | Pause or resume playback |
| `!queue` / `!q` | Show the queue |
| `!np` | Now playing |
| `!listen [question]` | Miss answers you in voice |
| `!kick @user` | Kick a member |
| `!ban @user` | Ban a member |
| `!mute @user [minutes]` | Timeout a member |
| `!warn @user` | Warn a member (auto-mute at 3) |
| `!warnings @user` | Check warnings |
| `!clear [amount]` | Delete messages |
| `!slowmode [seconds]` | Set channel slowmode |
| `!lock` / `!unlock` | Lock or unlock a channel |
| `!announce [message]` | Post an announcement embed |
| `!role @user [role]` | Give a role |
| `!serverinfo` | Server stats |
| `!userinfo @user` | User info |
| `!help` | Full command list |

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/human045/slutty-miss.git
cd slutty-miss
```

### 2. Install dependencies
```bash
pip install "discord.py[voice]" httpx yt-dlp pynacl
apt install ffmpeg libopus0   # or brew install ffmpeg on macOS
```

### 3. Set environment variables
```bash
cp .env.example .env
# Fill in your values in .env
export $(cat .env | xargs)
```

### 4. Run
```bash
python3 discordbot.py
```

### Run as a systemd service (Linux VPS)
```ini
[Unit]
Description=Slutty Miss Discord Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/discordbot/discordbot.py
Restart=always
EnvironmentFile=/opt/discordbot/.env

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable --now discordbot
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Your Discord bot token |
| `XAI_KEY` | ✅ | xAI / Grok API key from [x.ai](https://x.ai) |
| `OWNER_ID` | ✅ | Your Discord user ID (for owner-only commands) |
| `FISH_KEY` | ✅ | Fish Audio API key from [fish.audio](https://fish.audio) |
| `FISH_VOICE_ID` | ❌ | Fish Audio voice model ID (defaults to Egirl voice) |
| `XAI_MODEL` | ❌ | Grok model name (default: `grok-3-latest`) |
| `PREFIX` | ❌ | Command prefix (default: `!`) |

---

## 🛠️ Tech Stack

| Component | Tech |
|---|---|
| Bot framework | [discord.py 2.7](https://discordpy.readthedocs.io) |
| AI brain | [Grok (xAI)](https://x.ai) — server management + playlists + chat |
| Music source | [SoundCloud via yt-dlp](https://github.com/yt-dlp/yt-dlp) — no bot detection |
| Audio playback | FFmpeg (download-first for glitch-free audio) |
| Voice TTS | [Fish Audio](https://fish.audio) — e-girl voice with emotion tags |
| HTTP client | [httpx](https://www.python-httpx.org/) |

---

## 💡 How the Music Works

Songs are **downloaded to a temp file first** before playing — this eliminates all audio glitches caused by SoundCloud's HLS segment streaming. The next song is pre-downloaded in the background while the current one plays, so transitions are instant.

## 💡 How the Voice AI Works

`!listen [question]` → Grok generates a short e-girl response with emotion tags like `[laugh]`, `[sigh]`, `[whisper]`, `[emphasis]` → Fish Audio renders it with the Egirl voice model → bot plays it in your voice channel. If music is playing, it pauses, Miss speaks, music resumes.

---

<div align="center">

Made with 💕 by [human045](https://github.com/human045)

</div>
