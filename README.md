# Social-Bot 𐔌՞. .՞𐦯
*(Work in Progress — V1 Local Functional)*

**Social-Bot** is an automated pipeline designed to help content creators manage and prepare their social media posts (TikTok, Shorts, Reels) with zero manual text preparation.

---

## 🌟 Overview

Managing daily video content requires consistent metadata generation and file management. **Social-Bot** automates the heavy lifting:
1. **Scans** incoming raw video files (`.mp4`).
2. **Extracts keyframes** directly from the video without manual editing.
3. **Generates tailored captions** (titles, descriptions, and hashtags in a fast-paced reaction style) using OpenAI's GPT-4o-mini vision model.
4. **Tracks publication state** using a local SQLite database to prevent duplicate processing.
5. **Archives processed content** and delivers ready-to-use metadata files for each video.

---

## 🛠️ Tech Stack & Architecture

- **Language:** Python 3.11+
- **Computer Vision:** `opencv-python` (Frame extraction & base64 encoding)
- **AI Integration:** `openai` API (GPT-4o-mini Vision for text and hashtag generation)
- **Database:** `sqlite3` (Local database for scheduling & post history)
- **Environment Management:** `python-dotenv`
- **File System Automation:** `os`, `shutil`

---

## 📂 Project Structure

```text
SOCIAL_BOT/
├── CLIENTS/
│   └── [client_name]/
│       ├── conf.db          # Client's SQLite DB (history & schedule)
│       ├── videos_input/    # Drop your raw .mp4 videos here
│       └── videos_done/     # Processed videos & generated metadata (.txt)
├── main.py                  # Core engine & execution loop
├── .env                     # API keys (ignored by git)
└── README.md
```

---
> **Note:** I used AI to help structure and complete this documentation to make it as thorough and clear as possible. Contributions and feedback are warmly welcomed!
```
 /\_/\  
( o.o ) 
 > ^ <  
           ____  __    __   ____
          (_  _)/  \  / _\ (    \
            )( (  O )/    \ ) D (
           (__) \__/ \_/\_/(____/
```
