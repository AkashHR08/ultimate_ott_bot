# ============================================
# ADVANCED OTT DOWNLOADER TELEGRAM BOT
# AUTO THUMBNAIL + AUTO PLATFORM DETECT
# ============================================

import telebot
import yt_dlp
import threading
import os
import requests
import time

# ============================================
# BOT TOKEN
# ============================================

BOT_TOKEN = "8751935211:AAEKf3kld4eqqTMuo8RKAh6OMIzFLY7oVqY"

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# DOWNLOAD STATUS
# ============================================

download_status = {}

# ============================================
# PLATFORM DETECTION
# ============================================

PLATFORMS = {
    "hotstar": "Hotstar",
    "zee5": "Zee5",
    "sonyliv": "SonyLiv",
    "mxplayer": "MXPlayer",
    "aha": "Aha",
    "discoveryplus": "DiscoveryPlus",
    "jiotv": "JioTV",
    "hoichoi": "Hoichoi",
    "chaupal": "ChaupalTV",
    "erosnow": "ErosNow",
    "airtelxstream": "AirtelXstream",
    "sunnxt": "SunNXT",
    "etvwin": "ETVWin",
    "tubitv": "TubiTV",
    "primevideo": "PrimeVideo",
    "netflix": "Netflix",
}

# ============================================
# START MESSAGE
# ============================================

@bot.message_handler(commands=['start'])
def start(message):

    text = """
🔥 *ADVANCED OTT DOWNLOADER*

✅ Auto Platform Detect
✅ Auto Thumbnail
✅ HD Quality
✅ Telegram Upload
✅ Progress Bar
✅ Auto Rename

━━━━━━━━━━━━━━━

📥 Send:

`/dl URL`

Example:

`/dl https://www.hotstar.com/...`

━━━━━━━━━━━━━━━
"""

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown"
    )

# ============================================
# DOWNLOAD COMMAND
# ============================================

@bot.message_handler(commands=['dl'])
def download_cmd(message):

    try:

        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:
            bot.reply_to(
                message,
                "❌ Send URL with command",
                parse_mode="Markdown"
            )
            return

        url = parts[1]

        chat_id = message.chat.id

        msg = bot.send_message(
            chat_id,
            "🔍 Detecting Platform..."
        )

        download_status[chat_id] = {
            "msg_id": msg.id,
            "progress": 0,
            "speed": "0 KB/s",
            "eta": "Starting",
            "filename": "Preparing..."
        }

        thread = threading.Thread(
            target=start_download,
            args=(chat_id, url)
        )

        thread.start()

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{e}")

# ============================================
# DOWNLOAD FUNCTION
# ============================================

def start_download(chat_id, url):

    thumb_file = None

    try:

        platform = "Unknown"

        for key in PLATFORMS:
            if key in url.lower():
                platform = PLATFORMS[key]
                break

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [progress_hook(chat_id)],
            'quiet': True,
            'noplaylist': True
        }

        # cookies support
        if os.path.exists("cookies.txt"):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            title = info.get("title", "Video")
            filesize = round(os.path.getsize(filename) / (1024 * 1024), 2)

            # =====================================
            # AUTO THUMBNAIL DOWNLOAD
            # =====================================

            thumbnail = info.get("thumbnail")

            if thumbnail:

                thumb_file = "thumb.jpg"

                r = requests.get(thumbnail)

                with open(thumb_file, "wb") as f:
                    f.write(r.content)

            update_status(
                chat_id,
                100,
                f"✅ Download Complete!\n\n📦 {filesize} MB"
            )

            caption = f"""
🎬 *{title}*

🔥 Platform: {platform}
📦 Size: {filesize} MB
🎞 Quality: Original

✅ Uploaded Successfully
"""

            with open(filename, "rb") as vid:

                bot.send_video(
                    chat_id,
                    vid,
                    caption=caption,
                    parse_mode="Markdown",
                    supports_streaming=True,
                    thumb=open(thumb_file, "rb") if thumb_file else None
                )

            # delete files
            os.remove(filename)

            if thumb_file and os.path.exists(thumb_file):
                os.remove(thumb_file)

    except Exception as e:

        update_status(
            chat_id,
            0,
            f"❌ Download Failed\n\n{e}"
        )

# ============================================
# PROGRESS FUNCTION
# ============================================

def progress_hook(chat_id):

    def hook(d):

        if d['status'] == 'downloading':

            try:

                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1)

                percent = round(downloaded * 100 / total, 1)

                speed = d.get('_speed_str', '0 KB/s')
                eta = d.get('_eta_str', '0s')

                filename = os.path.basename(
                    d.get('filename', 'video')
                )

                download_status[chat_id]['progress'] = percent
                download_status[chat_id]['speed'] = speed
                download_status[chat_id]['eta'] = eta
                download_status[chat_id]['filename'] = filename

                update_status(chat_id)

            except:
                pass

    return hook

# ============================================
# STATUS UPDATE
# ============================================

def update_status(chat_id, progress=None, custom_text=None):

    try:

        data = download_status.get(chat_id)

        if not data:
            return

        if progress is not None:
            data['progress'] = progress

        filled = int(data['progress'] / 5)

        bar = "█" * filled + "░" * (20 - filled)

        text = f"""
🔥 *OTT Downloader*

`{bar}`

📊 Progress: {data['progress']}%
⚡ Speed: {data['speed']}
⏳ ETA: {data['eta']}

📄 {data['filename']}
"""

        if custom_text:
            text = custom_text

        bot.edit_message_text(
            text,
            chat_id,
            data['msg_id'],
            parse_mode="Markdown"
        )

    except:
        pass

# ============================================
# START BOT
# ============================================

print("🚀 Advanced OTT Downloader Running...")

bot.infinity_polling()
