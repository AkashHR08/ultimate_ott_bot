import telebot
import os
import yt_dlp
import threading
from telebot import types
from flask import Flask # Added for Render
import time

# --- FLASK SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
# -------------------------------

BOT_TOKEN = "8751935211:AAEKf3kld4eqqTMuo8RKAh6OMIzFLY7oVqY"
bot = telebot.TeleBot(BOT_TOKEN)

download_status = {}

@bot.message_handler(commands=['start', 'help'])
def start(message):
    help_text = """
🚀 *OTT Pro Downloader Bot*

*Commands:*
`/dl -jstar [hotstar_url]` - Hotstar support
`/dl [direct_link]` - Direct m3u8/mp4

*Example:*
`/dl -jstar https://hotstar.com/show/123`

*Features:*
✅ Original Quality
✅ Live Progress Bar
✅ Hotstar Auto-extract
✅ 1080p Full HD
"""
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📱 Test Hotstar", callback_data="test")
    markup.add(btn1)
    
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['dl'])
def handle_dl_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Format: `/dl -jstar [hotstar_url]`", parse_mode='Markdown')
            return
        
        platform = parts[1]
        url = ' '.join(parts[2:])
        chat_id = message.chat.id
        
        status_msg = bot.send_message(chat_id, "🔍 Extracting streams...")
        download_status[chat_id] = {
            'status_msg_id': status_msg.id,
            'progress': 0,
            'speed': '0 KB/s',
            'eta': 'Extracting...',
            'filename': 'Hotstar Stream'
        }
        
        thread = threading.Thread(target=process_download, args=(url, platform, chat_id))
        thread.start()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_download(url, platform, chat_id):
    try:
        if platform == '-jstar':
            ydl_opts = {
                'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                'outtmpl': 'hotstar_%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook(chat_id)],
                'cookies': 'cookies.txt' if os.path.exists("cookies.txt") else None,
            }
        else:
            ydl_opts = {
                'format': 'best[ext=mp4]+bestaudio[ext=m4a]/best',
                'outtmpl': '%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook(chat_id)],
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                filename = filename.rsplit(".", 1)[0] + ".mp4"
            
            filesize = os.path.getsize(filename) / (1024*1024)
            height = info.get('height', 'Unknown')
            
            update_status(chat_id, 100, f"✅ Downloaded!\n📺 {height}p | {filesize:.1f}MB")
            
            with open(filename, 'rb') as video:
                caption = f"🎬 *{info.get('title', 'Video')}*\n\n📺 Quality: {height}p\n📦 Size: {filesize:.1f}MB"
                bot.send_video(chat_id, video, caption=caption, parse_mode='Markdown', supports_streaming=True)
            
            os.remove(filename)
            
    except Exception as e:
        update_status(chat_id, 0, f"❌ Failed: {str(e)}")
    
    finally:
        if chat_id in download_status:
            del download_status[chat_id]

def progress_hook(chat_id):
    def hook(d):
        if d['status'] == 'downloading':
            status = download_status.get(chat_id)
            if status:
                p = d.get('_percent_str', '0%').replace('%','')
                status['progress'] = float(p)
                status['speed'] = d.get('_speed_str', '0 KB/s')
                status['eta'] = d.get('_eta_str', '00:00')
                update_status(chat_id)
    return hook

def update_status(chat_id, progress=None, custom_text=None):
    status = download_status.get(chat_id)
    if not status: return
    
    if progress is not None: status['progress'] = progress
    
    bar = "█" * int(status['progress']/4) + "░" * (25 - int(status['progress']/4))
    text = f"🔥 *Downloader*\n\n`{bar} {status['progress']}%` \n⚡ {status['speed']} | ⏰ {status['eta']}"
    
    if custom_text: text = custom_text
    
    try:
        bot.edit_message_text(text, chat_id, status['status_msg_id'], parse_mode='Markdown')
    except: pass

# --- START BOT ---
if __name__ == "__main__":
    print("🌐 Starting Flask Keep-Alive Server...")
    keep_alive() 
    print("🚀 Hotstar OTT Bot Started!")
    bot.infinity_polling()
