# ============================================
# ADVANCED OTT DOWNLOADER BOT
# WITH ADMIN SYSTEM & RENDER FIX
# ============================================

import telebot
import yt_dlp
import threading
import os
import requests
from flask import Flask  # Naya Add Kiya
from threading import Thread # Naya Add Kiya

# ============================================
# RENDER PORT FIX (KEEP ALIVE SYSTEM)
# ============================================

app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Successfully!"

def run_flask():
    # Render hamesha environment se PORT uthata hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ============================================
# BOT TOKEN & ADMINS
# ============================================

BOT_TOKEN = "8751935211:AAEKf3kld4eqqTMuo8RKAh6OMIzFLY7oVqY" # Apna asli token yaha dalein
ADMINS = [5254068665] # Apna numeric ID yaha dalein
FORCE_SUB_CHANNEL = "@YourChannelUsername"

bot = telebot.TeleBot(BOT_TOKEN)
download_status = {}
USERS_FILE = "users.txt"

# ============================================
# HELPERS
# ============================================

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def send_force_sub(chat_id):
    text = f"❌ *Join Channel First*\n\n👉 {FORCE_SUB_CHANNEL}\n\nThen send /start again."
    bot.send_message(chat_id, text, parse_mode="Markdown")

def is_admin(user_id):
    return user_id in ADMINS

def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

# ============================================
# COMMANDS
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    save_user(user_id)
    if not check_subscription(user_id):
        send_force_sub(message.chat.id)
        return
    text = "🔥 *ADVANCED OTT DOWNLOADER*\n\n✅ Auto Thumbnail\n✅ HD Quality\n✅ Admin System\n✅ Progress Bar\n\n📥 Usage:\n`/dl URL`"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id): return
    text = "👑 *ADMIN PANEL*\n\n/users - Total users\n/broadcast - Message all"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def total_users(message):
    if not is_admin(message.from_user.id): return
    total = len(open(USERS_FILE).readlines()) if os.path.exists(USERS_FILE) else 0
    bot.send_message(message.chat.id, f"👥 Total Users: {total}")

@bot.message_handler(commands=['dl'])
def download_cmd(message):
    if not check_subscription(message.from_user.id):
        send_force_sub(message.chat.id); return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: `/dl URL`", parse_mode="Markdown"); return

    url = parts[1]
    msg = bot.send_message(message.chat.id, "🔍 Processing...")
    threading.Thread(target=start_download, args=(message.chat.id, url)).start()

# ============================================
# DOWNLOAD LOGIC
# ============================================

def start_download(chat_id, url):
    thumb_file = None
    try:
        ydl_opts = {'format': 'best', 'merge_output_format': 'mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith(".mp4"): filename = filename.rsplit(".", 1)[0] + ".mp4"
            
            thumbnail = info.get("thumbnail")
            if thumbnail:
                thumb_file = "thumb.jpg"
                with open(thumb_file, "wb") as f: f.write(requests.get(thumbnail).content)

            with open(filename, "rb") as vid:
                bot.send_video(chat_id, vid, caption=f"🎬 *{info.get('title')}*", 
                               parse_mode="Markdown", thumb=open(thumb_file, "rb") if thumb_file else None)
            
            os.remove(filename)
            if thumb_file: os.remove(thumb_file)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Failed: {e}")

# ============================================
# BOT START (UPDATED)
# ============================================

if __name__ == "__main__":
    print("🌐 Starting Flask Server...")
    keep_alive() # Yeh Render ke port error ko thik karega
    print("🚀 Bot is Polling...")
    bot.infinity_polling()
