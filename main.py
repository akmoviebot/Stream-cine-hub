import os
import math
import asyncio
import inspect
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# --- CONFIGURATION (Koyeb Environment Variables) ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL", "0"))
PORT = int(os.environ.get("PORT", 8080))

SERVER_URL = os.environ.get("SERVER_URL", "https://cinehubpro.free.nf").rstrip("/")
CHANNEL_LINK = "https://t.me/Movieupdatewithak01"

bot = Client(
    "CineHubProBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def humanbytes(size):
    if not size:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def format_duration(seconds):
    if not seconds:
        return "N/A"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

# --- TELEGRAM BOT HANDLERS ---
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "👋 **Welcome to CineHubPro Streaming Bot!**\n\n"
        "Mujhe koi bhi Video ya Document file bhejo, main instantly uska High-Speed Direct Stream aur Download link bana dunga.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Main Channel", url=CHANNEL_LINK)]
        ])
    )

@bot.on_message(filters.private & (filters.video | filters.document))
async def handle_media(client, message):
    media = message.video or message.document
    if not media:
        return

    wait_msg = await message.reply_text("⚡ *Processing file & creating CineHubPro links...*", quote=True)

    try:
        # File ko BIN_CHANNEL me forward karein taaki permanent streaming id generate ho
        forwarded = await media.forward(BIN_CHANNEL)
        file_id = forwarded.id
    except Exception as e:
        await wait_msg.edit_text(f"❌ **Error:** Bin channel forward failed. Make sure Bot is Admin in `BIN_CHANNEL`.\n`{str(e)}`")
        return

    file_name = media.file_name or "CineHubPro_Media.mp4"
    file_size = humanbytes(media.file_size)
    duration = format_duration(getattr(media, "duration", 0))

    stream_link = f"{SERVER_URL}/watch/{file_id}"
    download_link = f"{SERVER_URL}/download/{file_id}"

    caption = (
        f"**{file_name}**\n\n"
        f"⏱ **Duration:** `{duration}`\n"
        f"📦 **Size:** `{file_size}`\n"
        f"🔊 **Audio:** `Hindi / Multi-Audio`\n"
        f"⚡ **Quality:** `1080p / 720p WEB-DL`\n\n"
        f"📢 *Powered by CineHubPro Streaming*"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("STREAM 🔺", url=stream_link),
            InlineKeyboardButton("DOWNLOAD 🔻", url=download_link)
        ],
        [
            InlineKeyboardButton("📝 View Tracks", callback_data=f"info_{file_id}")
        ],
        [
            InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)
        ]
    ])

    if media.thumbs:
        try:
            thumb = await client.download_media(media.thumbs[0].file_id)
            await message.reply_photo(photo=thumb, caption=caption, reply_markup=buttons)
            if os.path.exists(thumb):
                os.remove(thumb)
            await wait_msg.delete()
            return
        except Exception:
            pass

    await message.reply_text(text=caption, reply_markup=buttons, quote=True)
    await wait_msg.delete()

@bot.on_callback_query(filters.regex(r"^info_"))
async def track_popup(client, callback: CallbackQuery):
    track_text = (
        "🎧 **Audio & Subtitle Tracks (CineHubPro):**\n\n"
        "• Track 1: Hindi Clean Audio (Default)\n"
        "• Track 2: English Original Audio\n"
        "• Subtitles: English & Hindi (Soft-coded)\n\n"
        "ℹ️ *Browser me audio issue aane par external VLC / MX Player chalaayein.*"
    )
    await callback.message.reply_text(
        track_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close", callback_data="close_info")]])
    )
    await callback.answer()

@bot.on_callback_query(filters.regex("^close_info$"))
async def close_info(client, callback: CallbackQuery):
    await callback.message.delete()

# --- WEB STREAMING HTML TEMPLATE ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CineHubPro Streaming</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root { --bg: #090c13; --card: #131926; --border: #1e293b; --red: #ff3344; --orange: #ff7700; --text: #e2e8f0; }
    * { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI', sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 15px; }
    .container { max-width: 850px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 15px; border-bottom: 1px solid var(--border); margin-bottom: 15px; }
    .logo { font-size: 22px; font-weight: 800; background: linear-gradient(90deg, var(--orange), var(--red)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .channel-btn { background: #0088cc; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600; }
    .ad-box { background: #0f1420; border: 1px dashed var(--border); border-radius: 8px; padding: 12px; text-align: center; margin: 12px 0; font-size: 12px; color: #64748b; }
    .player-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 15px; }
    .media-title { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 12px; word-break: break-all; }
    video { width: 100%; max-height: 440px; border-radius: 8px; background: #000; margin-bottom: 15px; }
    .alert-box { background: rgba(255,119,0,0.1); border-left: 4px solid var(--orange); padding: 10px; font-size: 13px; color: #fba953; margin-bottom: 15px; border-radius: 4px; }
    .btn-down { display: block; width: 100%; background: linear-gradient(90deg, var(--red), #dd1122); color: white; text-align: center; padding: 12px; border-radius: 8px; font-weight: 700; text-decoration: none; margin-bottom: 15px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-top: 10px; }
    .p-btn { background: #1a2234; border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 6px; text-align: center; text-decoration: none; font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 6px; }
    footer { text-align: center; margin-top: 30px; font-size: 12px; color: #64748b; border-top: 1px solid var(--border); padding-top: 15px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo"><i class="fa-solid fa-play"></i> CineHubPro</div>
      <a href="__CHANNEL_LINK__" target="_blank" class="channel-btn"><i class="fa-brands fa-telegram"></i> Join Updates</a>
    </header>

    <div class="ad-box">ADVERTISEMENT (AdSense / Monetag Header Slot)</div>

    <div class="player-card">
      <div class="media-title">__FILE_NAME__</div>
      <div class="alert-box">
        <i class="fa-solid fa-circle-exclamation"></i> <strong>Audio Tip:</strong> Multi-channel audio me browser me aawaz na aaye to VLC ya MX Player chalaayein.
      </div>

      <video controls playsinline controlsList="nodownload">
        <source src="__RAW_STREAM_URL__" type="video/mp4">
        Your browser does not support HTML5 video.
      </video>

      <a href="__RAW_DOWNLOAD_URL__" class="btn-down"><i class="fa-solid fa-cloud-arrow-down"></i> High-Speed Direct Download</a>

      <p style="font-size:13px; color:#94a3b8; font-weight:600;"><i class="fa-solid fa-mobile-screen"></i> Play in External Players:</p>
      <div class="grid">
        <a href="vlc://__RAW_STREAM_URL__" class="p-btn"><i class="fa-solid fa-traffic-cone" style="color:#ff8800;"></i> VLC</a>
        <a href="intent:__RAW_STREAM_URL__#Intent;package=com.mxtech.videoplayer.ad;type=video/*;end" class="p-btn"><i class="fa-solid fa-circle-play" style="color:#0099ff;"></i> MX Player</a>
        <a href="intent:__RAW_STREAM_URL__#Intent;package=com.shield.android.splayer;type=video/*;end" class="p-btn"><i class="fa-solid fa-bolt" style="color:#aa00ff;"></i> SPlayer</a>
        <a href="playit://playerv2/video?url=__RAW_STREAM_URL_ENC__" class="p-btn"><i class="fa-solid fa-play" style="color:#ff2244;"></i> PLAYit</a>
      </div>
    </div>

    <div class="ad-box">ADVERTISEMENT (Native Sponsored Banner)</div>

    <footer>
      <p>&copy; 2026 CineHubPro Streaming | Powered by Movieupdatewithak01</p>
    </footer>
  </div>
</body>
</html>
"""

# --- KOYEB HEALTH CHECK & STREAMING ROUTES ---
async def health_check(request):
    # Koyeb HEAD aur GET dono ping bhejta hai
    return web.Response(text="CineHubPro Streaming Core is Online! ⚡", status=200)

async def watch_handler(request):
    try:
        file_id = int(request.match_info["file_id"])
        msg = await bot.get_messages(BIN_CHANNEL, file_id)
        media = msg.video or msg.document
        fname = media.file_name or "CineHubPro_Stream.mp4"
    except Exception:
        fname = "CineHubPro_Stream.mp4"

    raw_stream = f"{SERVER_URL}/stream/{file_id}"
    raw_download = f"{SERVER_URL}/download/{file_id}"

    html = HTML_TEMPLATE.replace("__FILE_NAME__", fname)\
                         .replace("__RAW_STREAM_URL__", raw_stream)\
                         .replace("__RAW_STREAM_URL_ENC__", raw_stream)\
                         .replace("__RAW_DOWNLOAD_URL__", raw_download)\
                         .replace("__CHANNEL_LINK__", CHANNEL_LINK)
    return web.Response(text=html, content_type="text/html")

async def raw_media_stream(request):
    try:
        file_id = int(request.match_info["file_id"])
        msg = await bot.get_messages(BIN_CHANNEL, file_id)
        media = msg.video or msg.document
        file_size = media.file_size
    except Exception as e:
        return web.Response(text=f"File not found: {str(e)}", status=404)

    range_header = request.headers.get("Range", None)
    from_bytes = 0
    until_bytes = file_size - 1

    if range_header:
        ranges = range_header.replace("bytes=", "").split("-")
        from_bytes = int(ranges[0])
        if len(ranges) > 1 and ranges[1]:
            until_bytes = int(ranges[1])

    chunk_size = 1024 * 1024
    status = 206 if range_header else 200
    headers = {
        "Content-Type": media.mime_type or "video/mp4",
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
        "Content-Length": str(until_bytes - from_bytes + 1),
    }

    if request.path.startswith("/download"):
        headers["Content-Disposition"] = f'attachment; filename="{media.file_name or "video.mp4"}"'

    response = web.StreamResponse(status=status, headers=headers)
    await response.prepare(request)

    async for chunk in bot.stream_media(message=msg, limit=until_bytes - from_bytes + 1, offset=from_bytes // chunk_size):
        await response.write(chunk)

    return response

# --- ASYNC RUNNER ---
async def main():
    # 1. Koyeb ke HEAD aur GET requests ke liye web routes
    app_server = web.Application()
    app_server.router.add_get("/", health_check)
    app_server.router.add_head("/", health_check)
    app_server.router.add_get("/health", health_check)
    app_server.router.add_head("/health", health_check)
    app_server.router.add_get("/watch/{file_id}", watch_handler)
    app_server.router.add_get("/download/{file_id}", raw_media_stream)
    app_server.router.add_get("/stream/{file_id}", raw_media_stream)

    runner = web.AppRunner(app_server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server running on port {PORT}")

    # 2. Pyrogram Bot ko start karein (Sync/Async safe)
    start_result = bot.start()
    if inspect.isawaitable(start_result):
        await start_result

    print("CineHubPro Bot started successfully!")
    await idle()

    stop_result = bot.stop()
    if inspect.isawaitable(stop_result):
        await stop_result

if __name__ == "__main__":
    asyncio.run(main())
