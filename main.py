import os
import sys
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from subprocess import getstatusoutput
import requests
import helper  # Ensure helper module is implemented
from p_bar import progress_bar  # Ensure progress_bar is implemented

# Load credentials from environment variables
api_id = os.getenv("API_ID", "27536109")
api_hash = os.getenv("API_HASH", "b84d7d4dfa33904d36b85e1ead16bd63")
bot_token = os.getenv("BOT_TOKEN", "8161679463:AAHPJiQFPkBf-dZEJJOPO3EdiEyEUUYJ3t0")

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
        "Hello! I am a multi-link downloader bot with Twin Download functionality.\n"
        "Send a TXT file of links and I will process them in parallel.\n\n"
        "Commands:\n"
        "/process - Process links\n"
        "/cancel - Cancel ongoing downloads\n\nBot by BATMAN."
    )


@bot.on_message(filters.command("cancel"))
async def cancel_command(bot: Client, message: Message):
    global cancel
    cancel = True
    await message.reply_text("Cancelling all processes... Please wait.")
    cancel = False  # Reset for future commands
    await message.reply_text("Cancelled.")


@bot.on_message(filters.command("process") & ~filters.edited)
async def process_command(bot: Client, message: Message):
    await message.reply_text(
        "Please send the TXT file containing links in the format `Name:Link`. "
        "Make sure to include proper names for easier identification."
    )
    txt_message: Message = await bot.listen(message.chat.id)
    txt_file_path = await txt_message.download()

    # Read and parse the TXT file
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

    tasks = []
    for idx, (name, url) in enumerate(links[start_index:], start=start_index):
        if cancel:
            break

        sanitized_name = name.replace(":", "").replace("/", "").replace("+", "").strip()
        output_name = f"{idx + 1:03d}_{sanitized_name}.mp4"

        tasks.append(
            download_and_upload(bot, message, url, output_name, resolution, thumb_path, sanitized_name)
        )

        # Process two tasks simultaneously
        if len(tasks) == 2:
            await asyncio.gather(*tasks)
            tasks = []  # Clear the task list after completion

    # Process any remaining tasks
    if tasks:
        await asyncio.gather(*tasks)

    if thumb_path:
        os.remove(thumb_path)

    await message.reply_text("All downloads completed.")


async def download_and_upload(bot, message, url, output_name, resolution, thumb_path, title):
    """Handles downloading and uploading of a single file."""
    try:
        # Detect link type and prepare yt-dlp command
        if url.endswith(".m3u8"):
            cmd = f'yt-dlp -o "{output_name}" "{url}"'
        else:
            cmd = f'yt-dlp -o "{output_name}" -f "bestvideo[height<={resolution}]+bestaudio" "{url}"'

        # Execute the download command
        subprocess.run(cmd, shell=True, check=True)

        # Upload the downloaded file
        await upload_file(bot, message, output_name, thumb_path, title)
    except Exception as e:
        await message.reply_text(f"Error processing {title}: {e}")


async def upload_file(bot, message, file_path, thumb_path, title):
    """Uploads the file to Telegram."""
    try:
        if thumb_path:
            subprocess.run(f'ffmpeg -i "{file_path}" -ss 00:00:01 -vframes 1 "{file_path}.jpg"', shell=True)
            thumb_file = f"{file_path}.jpg"
        else:
            thumb_file = None

        await bot.send_video(
            message.chat.id,
            file_path,
            supports_streaming=True,
            thumb=thumb_file,
            caption=f"**Title:** {title}"
        )
        os.remove(file_path)
        if thumb_file:
            os.remove(thumb_file)
    except Exception as e:
        await message.reply_text(f"Error uploading {file_path}: {e}")


if __name__ == "__main__":
    bot.run()
