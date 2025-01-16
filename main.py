import os
import sys
import time
import requests
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from subprocess import getstatusoutput
import helper  # Ensure this is implemented correctly
from p_bar import progress_bar  # Ensure this is implemented

# Load credentials from environment variables
api_id = os.getenv("API_ID", "27536109")  # Replace with your default API ID
api_hash = os.getenv("API_HASH", "b84d7d4dfa33904d36b85e1ead16bd63")  # Replace with your default API Hash
bot_token = os.getenv("BOT_TOKEN", "8161679463:AAHPJiQFPkBf-dZEJJOPO3EdiEyEUUYJ3t0")  # Replace with your default token

# Validate environment variables
if not all([api_id, api_hash, bot_token]):
    print("Missing environment variables. Ensure API_ID, API_HASH, and BOT_TOKEN are set.")
    sys.exit(1)

# Initialize the bot client
bot = Client(
    "bot",
    bot_token=bot_token,
    api_id=api_id,
    api_hash=api_hash,
)

cancel = False  # Global cancel flag


@bot.on_message(filters.command("start") & ~filters.edited)
async def start_command(bot: Client, message: Message):
    await message.reply_text(
        "Hello! I am a TXT file downloader bot. Use /pyro to download links listed in a TXT file in the format `Name:link`.\n\nBot created by BATMAN."
    )


@bot.on_message(filters.command("cancel"))
async def cancel_command(bot: Client, message: Message):
    global cancel
    cancel = True
    await message.reply_text("Cancelling all processes... Please wait.")
    cancel = False  # Reset for future commands
    await message.reply_text("Cancelled.")


@bot.on_message(filters.command("restart"))
async def restart_command(bot: Client, message: Message):
    await message.reply_text("Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command("pyro") & ~filters.edited)
async def pyro_command(bot: Client, message: Message):
    await message.reply_text("Please send the TXT file.")
    txt_message: Message = await bot.listen(message.chat.id)
    txt_file_path = await txt_message.download()

    try:
        with open(txt_file_path, "r") as file:
            links = [line.strip().split(":", 1) for line in file.readlines() if ":" in line]
        if not links:
            raise ValueError("No valid links found in the file.")
    except Exception as e:
        await message.reply_text(f"Error reading file: {e}")
        os.remove(txt_file_path)
        return

    os.remove(txt_file_path)  # Clean up the file
    await message.reply_text(f"Found {len(links)} links. Enter the starting index (default is 0).")
    index_message: Message = await bot.listen(message.chat.id)
    start_index = int(index_message.text) if index_message.text.isdigit() else 0

    await message.reply_text("Enter the title for the videos.")
    title_message: Message = await bot.listen(message.chat.id)
    title = title_message.text

    await message.reply_text("Enter the resolution (e.g., 360, 480, 720).")
    resolution_message: Message = await bot.listen(message.chat.id)
    resolution = resolution_message.text

    await message.reply_text("Send the thumbnail URL or type 'no'.")
    thumb_message: Message = await bot.listen(message.chat.id)
    thumb_url = thumb_message.text

    if thumb_url.lower() != "no":
        getstatusoutput(f"wget '{thumb_url}' -O 'thumb.jpg'")
        thumb_path = "thumb.jpg"
    else:
        thumb_path = None

    for idx, (name, url) in enumerate(links[start_index:], start=start_index):
        if cancel:
            break
        try:
            sanitized_name = name.replace(":", "").replace("/", "").replace("+", "").strip()
            output_name = f"{idx + 1:03d}_{sanitized_name}.mp4"

            # Generate yt-dlp command
            if "youtu" in url or "vimeo" in url:
                cmd = f'yt-dlp -o "{output_name}" -f "bestvideo[height<={resolution}]+bestaudio" "{url}"'
            else:
                cmd = f'yt-dlp -o "{output_name}" "{url}"'

            # Execute download
            subprocess.run(cmd, shell=True, check=True)

            # Upload the downloaded file
            await message.reply_text(f"Downloaded: {output_name}")
            if thumb_path:
                subprocess.run(f'ffmpeg -i "{output_name}" -ss 00:00:01 -vframes 1 "{output_name}.jpg"', shell=True)
                await bot.send_video(
                    message.chat.id,
                    output_name,
                    supports_streaming=True,
                    height=720,
                    width=1280,
                    thumb=f"{output_name}.jpg",
                    caption=f"**Title:** {title}\n**File:** {output_name}",
                )
                os.remove(f"{output_name}.jpg")
            else:
                await bot.send_document(message.chat.id, output_name)

            os.remove(output_name)
        except Exception as e:
            await message.reply_text(f"Error downloading {name}: {e}")
            continue

    if thumb_path:
        os.remove(thumb_path)

    await message.reply_text("All downloads completed.")


if __name__ == "__main__":
    bot.run()
