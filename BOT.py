import os
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL = "ft:gpt-3.5-turbo-0125:personal:will-impersonation:BevSmRCs"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
openai = OpenAI(api_key=OPENAI_API_KEY)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if is_dm or is_mentioned:
        prompt = message.content
        if is_mentioned:
            prompt = prompt.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            return

        try:
            completion = openai.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            reply = completion.choices[0].message.content.strip()
            await message.reply(reply)
        except Exception as e:
            await message.reply("Sorry, there was an error processing your request.")

bot.run(DISCORD_TOKEN)