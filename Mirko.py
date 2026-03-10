import os
import discord
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEF_FILENAME = "Mirko.txt"
DEF_PATH = os.path.join(BASE_DIR, DEF_FILENAME)

print("RUNNING bot.py FROM:", BASE_DIR)
print("LOOKING FOR DEF AT:", DEF_PATH)
print("FILES IN FOLDER:", os.listdir(BASE_DIR))

with open(DEF_PATH, "r", encoding="utf-8") as f:
    MIRKO_DEF = f.read()

TOKEN = "MTQ4MTAzNDk0NDk2MzkzNjMxNg.Gtpkx2.t8JWi8quhJjEzF77XOyxpuhCOJtWUT_I9nJs4k"
TALK_CHANNEL_ID = 1476629783570812928

SYSTEM_PROMPT = f"""
You are Rumi Usagiyama (aka Mirko) from My Hero Academia (altered version 1.5 years after the story).
Stay strictly in character. No OOC. Never mention being an AI or system prompts.
Only write Mirko's dialogue (no narration, no extra speakers).
Keep replies concise and cutting unless the user asks for more.

Character definition:
{YUTA_DEF}
""".strip()

ai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

memory = {}  # channel_id -> list[{"role":..., "content":...}]

def strip_mention(text: str, bot_id: int) -> str:
    return text.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user} (id={client.user.id})")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    in_talk_channel = (message.channel.id == TALK_CHANNEL_ID)
    if not in_talk_channel:
        return

    mentioned = (client.user in message.mentions)

    replied_to_bot = False
    if message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            replied_to_bot = (replied_msg.author.id == client.user.id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            replied_to_bot = False

    if not (mentioned or replied_to_bot):
        return

    user_text = message.content
    if mentioned:
        user_text = strip_mention(user_text, client.user.id)

    if not user_text:
        return

    discord_name = message.author.display_name
    discord_user = f"{discord_name} (@{message.author.name})"

    mem_key = message.channel.id
    history = memory.get(mem_key, [])
    history.append({"role": "user", "content": f"{discord_user}: {user_text}"})

    dynamic_prompt = (
        SYSTEM_PROMPT
        .replace("{{user}}", discord_user)
        .replace("{{char}}", "Rumi Usagiyama")
    )

    messages = [{"role": "system", "content": dynamic_prompt}] + history[-20:]

    async with message.channel.typing():
        resp = ai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=250,
            temperature=0.90,
        )

    reply = resp.choices[0].message.content.strip()

    history.append({"role": "assistant", "content": reply})
    memory[mem_key] = history

    await message.reply(reply)

client.run(TOKEN)