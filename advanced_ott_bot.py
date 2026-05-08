# ============================================
# ADVANCED OTT DOWNLOADER BOT
# WITH ADMIN SYSTEM
# ============================================

import telebot
import yt_dlp
import threading
import os
import requests

# ============================================
# BOT TOKEN
# ============================================

BOT_TOKEN = "8751935211:AAEKf3kld4eqqTMuo8RKAh6OMIzFLY7oVqY"

# ============================================
# ADMIN USER IDS
# ============================================

ADMINS = [5254068665]

# Your Telegram numeric ID here
# Example:
# ADMINS = [123456789, 987654321]

# ============================================

bot = telebot.TeleBot(BOT_TOKEN)

download_status = {}

# ============================================
# FORCE SUB CHANNEL
# ============================================

FORCE_SUB_CHANNEL = "@YourChannelUsername"

# ============================================
# START
# ============================================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    if not check_subscription(user_id):
        send_force_sub(message.chat.id)
        return

    text = """
🔥 *ADVANCED OTT DOWNLOADER*

✅ Auto Thumbnail
✅ HD Quality
✅ Admin System
✅ Auto Upload
✅ Progress Bar

━━━━━━━━━━━━━━━

📥 Usage:

`/dl URL`

━━━━━━━━━━━━━━━
"""

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown"
    )

# ============================================
# FORCE SUB CHECK
# ============================================

def check_subscription(user_id):

    try:

        member = bot.get_chat_member(
            FORCE_SUB_CHANNEL,
            user_id
        )

        if member.status in ["member", "administrator", "creator"]:
            return True

    except:
        return False

    return False

# ============================================
# FORCE SUB MESSAGE
# ============================================

def send_force_sub(chat_id):

    text = f"""
❌ *Join Channel First*

👉 {FORCE_SUB_CHANNEL}

Then send /start again.
"""

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown"
    )

# ============================================
# ADMIN CHECK
# ============================================

def is_admin(user_id):
    return user_id in ADMINS

# ============================================
# ADMIN PANEL
# ============================================

@bot.message_handler(commands=['admin'])
def admin_panel(message):

    if not is_admin(message.from_user.id):
        return

    text = """
👑 *ADMIN PANEL*

/users - Total users
/broadcast - Broadcast message
/stats - Bot stats
"""

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown"
    )

# ============================================
# USERS COMMAND
# ============================================

USERS_FILE = "users.txt"

def save_user(user_id):

    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

@bot.message_handler(func=lambda m: True)
def all_messages(message):
    save_user(message.from_user.id)

# ============================================
# TOTAL USERS
# ============================================

@bot.message_handler(commands=['users'])
def total_users(message):

    if not is_admin(message.from_user.id):
        return

    if not os.path.exists(USERS_FILE):
        total = 0
    else:
        with open(USERS_FILE, "r") as f:
            total = len(f.readlines())

    bot.send_message(
        message.chat.id,
        f"👥 Total Users: {total}"
    )

# ============================================
# BROADCAST
# ============================================

@bot.message_handler(commands=['broadcast'])
def broadcast(message):

    if not is_admin(message.from_user.id):
        return

    msg = message.text.replace("/broadcast", "").strip()

    if not msg:
        bot.reply_to(message, "Send message also.")
        return

    if not os.path.exists(USERS_FILE):
        return

    sent = 0

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    for user in users:

        try:

            bot.send_message(user, msg)

            sent += 1

        except:
            pass

    bot.send_message(
        message.chat.id,
        f"✅ Broadcast Sent To {sent} Users"
    )

# ============================================
# DOWNLOAD COMMAND
# ============================================

@bot.message_handler(commands=['dl'])
def download_cmd(message):

    user_id = message.from_user.id

    if not check_subscription(user_id):
        send_force_sub(message.chat.id)
        return

    try:

        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:

            bot.reply_to(
                message,
                "❌ Usage:\n`/dl URL`",
                parse_mode="Markdown"
            )

            return

        url = parts[1]

        chat_id = message.chat.id

        msg = bot.send_message(
            chat_id,
            "🔍 Processing..."
        )

        download_status[chat_id] = {
            "msg_id": msg.id,
            "progress": 0
        }

        thread = threading.Thread(
            target=start_download,
            args=(chat_id, url)
        )

        thread.start()

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Error:\n{e}"
        )

# ============================================
# DOWNLOAD FUNCTION
# ============================================

def start_download(chat_id, url):

    thumb_file = None

    try:

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }

        if os.path.exists("cookies.txt"):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            if not filename.endswith(".mp4"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"

            title = info.get("title", "Video")

            filesize = round(
                os.path.getsize(filename) / (1024 * 1024),
                2
            )

            thumbnail = info.get("thumbnail")

            if thumbnail:

                thumb_file = "thumb.jpg"

                r = requests.get(thumbnail)

                with open(thumb_file, "wb") as f:
                    f.write(r.content)

            caption = f"""
🎬 *{title}*

📦 Size: {filesize} MB
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

            os.remove(filename)

            if thumb_file and os.path.exists(thumb_file):
                os.remove(thumb_file)

    except Exception as e:

        bot.send_message(
            chat_id,
            f"❌ Download Failed\n\n{e}"
        )

# ============================================
# BOT START
# ============================================

print("🚀 Advanced OTT Bot Running...")

bot.infinity_polling()