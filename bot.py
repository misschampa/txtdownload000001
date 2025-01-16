
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = "23900056"
API_HASH = "db7e21e638bc2359907814f4ed8b48a8"
BOT_TOKEN = "7350085099:AAHQ6uYn3uFPpf0o4p_BrDrf9MM4Fz41iSU"

app = Client("AktxtExtractor", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
def start_message(client, message):
    message.reply("Hello! Welcome to AktxtExtractor bot.")

if __name__ == "__main__":
    app.run()