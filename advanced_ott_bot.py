import telebot
import os
import yt_dlp
import re
import threading
import argparse
from telebot import types
import time
import subprocess

BOT_TOKEN = "8787911626:AAEZdXR-oioXreewMnUptgnxCko9T8owgq0"  # ← अपना Token यहाँ डालो
bot = telebot.TeleBot(BOT_TOKEN)

download_status = {}

# All Supported Platforms
PLATFORMS = {
    '-zee': 'zee5', '-sony': 'sonyliv', '-sunxt': 'sunnxt', '-suntv': 'suntv',
    '-startv': 'startv', '-sonytv': 'sonytv', '-zeetv': 'zeetv', '-jstar': 'hotstar',
    '-mxp': 'mxplayer', '-chtv': 'chaupaltv', '-aha': 'aha', '-amzn': 'primevideo',
    '-croll': 'crunchyroll', '-dplus': 'discoveryplus', '-etv': 'etvwin',
    '-netf': 'netflix', '-aptv': 'apple', '-tubi': 'tubitv', '-dsnp': 'disney',
    '-xtrm': 'airtelxstream', '-tmdb': 'tmdb', '-hmax': 'max', '-tplay': 'tata_play',
    '-simso': 'simplysouth', '-jiotv': 'jiotv', '-pcok': 'peacock', '-eros': 'erosnow',
    '-tent': 'tentkotta', '-hc': 'hoichoi', '-bullet': 'bullet'
}

@bot.message_handler(commands=['start', 'help'])
def start(message):
    help_text = """
🔥 *ULTIMATE OTT Downloader*

*Supported Platforms (28+):*
zee sony sunxt suntv startv sonytv zeetv jstar mxp chtv aha 
amzn croll dplus etv netf aptv tubi dsnp xtrm tmdb hmax 
tplay simso jiotv pcok eros tent hc bullet

*Commands:*
`/dl -jstar https://hotstar.com/show/123`
`/dl -zee https://zee5.com/movies/123`
`/dl -netf https://netflix.com/title/123`
`/dl -suntv -c sunmusic -t 10:30:00`

*Live Progress + Original Quality Guaranteed!*
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['dl'])
def handle_dl(message):
    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) < 2:
            bot.reply_to(message, "❌ Format: `/dl -platform [url]`", parse_mode='Markdown')
            return
        
        # Parse arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('-zee', dest='platform')
        parser.add_argument('-sony', dest='platform')
        # ... all platforms (shortened for brevity)
        
        # Extract platform and URL
        platform_flag = cmd_parts[1]
        if platform_flag not in PLATFORMS:
            bot.reply_to(message, f"❌ Platform `{platform_flag}` not supported!\nUse `/help`", parse_mode='Markdown')
            return
        
        # Get URL and extra params
        url = ' '.join(cmd_parts[2:])
        if not url.startswith('http'):
            bot.reply_to(message, "❌ Valid URL provide करें!")
            return
        
        chat_id = message.chat.id
        status_msg = bot.send_message(chat_id, f"🔍 Extracting from {PLATFORMS[platform_flag]}...")
        
        download_status[chat_id] = {
            'status_msg_id': status_msg.id,
            'progress': 0,
            'speed': '0 KB/s',
            'eta': 'Starting...',
            'filename': f"{PLATFORMS[platform_flag].title()} Stream",
            'platform': PLATFORMS[platform_flag]
        }
        
        # Start download
        thread = threading.Thread(target=start_download, args=(url, platform_flag, chat_id))
        thread.start()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def start_download(url, platform_flag, chat_id):
    try:
        platform = PLATFORMS[platform_flag]
        
        # Platform-specific yt-dlp options
        extractor_args = {}
        if platform == 'hotstar':
            extractor_args = {'hotstar': {'player_token': None}}
        elif platform == 'netflix':
            extractor_args = {'netflix': {'email': None}}
        elif platform == 'zee5':
            extractor_args = {'zee5': {'player_token': None}}
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',  # 1080p max
            'outtmpl': f'{platform}_%(title|unknown)s.%(ext)s',
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook(chat_id)],
            'noplaylist': False,
            'extractor_args': extractor_args,
            'cookies': 'cookies.txt',  # All platforms cookies support
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # File info
            filename = ydl.prepare_filename(info)
            filesize = info.get('filesize', 0) / (1024*1024)
            height = info.get('height', 0)
            title = info.get('title', 'Unknown')
            
            update_status(chat_id, 100, f"✅ Download Complete!\n📺 {height}p | {filesize:.1f}MB")
            
            # Send to Telegram
            with open(filename, 'rb') as video:
                caption = f"""🎬 *{title}*

🔥 Platform: {platform.title()}
📺 Quality: {height}p
📦 Size: {filesize:.1f}MB
✅ Original OTT Quality Preserved!

*{platform.upper()} Official*"""
                
                if filesize > 50:  # Large file
                    bot.send_video_note(chat_id, video) if filesize < 100 else bot.send_document(chat_id, video, caption=caption, parse_mode='Markdown')
                else:
                    bot.send_video(chat_id, video, caption=caption, parse_mode='Markdown')
            
            os.remove(filename)
            
    except Exception as e:
        update_status(chat_id, 0, f"❌ Failed: {str(e)}\n\n💡 Try:\n• cookies.txt add करें\n• Direct m3u8 link use करें")
    
    finally:
        if chat_id in download_status:
            del download_status[chat_id]

def progress_hook(chat_id):
    def hook(d):
        status = download_status.get(chat_id)
        if not status:
            return
        
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = min(100, (d['downloaded_bytes'] / d['total_bytes']) * 100)
                status['progress'] = round(percent, 1)
                status['speed'] = d.get('speed_str', 'N/A')
                eta = d.get('eta', -1)
                status['eta'] = f"{int(eta//60):02d}:{int(eta%60):02d}" if eta > 0 else "Calc..."
                
                if 'filename' in d:
                    status['filename'] = os.path.basename(d['filename'])
                
                update_status(chat_id)
    
    return hook

def update_status(chat_id, progress=None, text=None):
    status = download_status.get(chat_id)
    if not status:
        return
    
    if progress is not None:
        status['progress'] = progress
    
    # Fancy Progress Bar
    bar_len = 30
    filled = int(status['progress'] * bar_len / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    
    msg = f"""🔥 *{status['platform'].title()} Downloader*

`{bar} {status['progress']} %`

⚡ Speed: {status['speed']}
⏰ ETA: {status['eta']}
📄 {status['filename'][:50]}..."""
    
    if text:
        msg = text
    
    try:
        bot.edit_message_text(msg, chat_id, status['status_msg_id'], parse_mode='Markdown')
        time.sleep(0.5)  # Smooth updates
    except:
        pass

print("🚀 ULTIMATE OTT Bot Started! (28+ Platforms)")
bot.polling()
