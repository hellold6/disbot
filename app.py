import os
import base64
import discord
from discord.ext import commands
from openai import OpenAI
from collections import defaultdict, deque

# Decode Discord token from base64
DISCORD_TOKEN = base64.b64decode(
    "TVRNNE1EQXpOak0wTnpZd01qa3lOelkzTmcuR2tKYnpOLjAxbGliYVpaLW1YWHBxNktNdldKTXo2VjI2YWU1OVBDb1Fvem5n"
).decode()

OPENAI_API_KEY = ("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")

MODEL = "ft:gpt-3.5-turbo-0125:personal:will-impersonation:BevSmRCs"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
openai = OpenAI(api_key=OPENAI_API_KEY)

# Store conversation history per user (user_id: deque of messages)
conversation_history = defaultdict(lambda: deque(maxlen=10))

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

        user_id = message.author.id
        # Add the user's message to their history
        conversation_history[user_id].append({"role": "user", "content": prompt})

        # Prepare the message history for OpenAI (include previous bot replies)
        messages = list(conversation_history[user_id])

        try:
            completion = openai.chat.completions.create(
                model=MODEL,
                messages=messages
            )
            reply = completion.choices[0].message.content.strip()
            # Add the bot's reply to the conversation history
            conversation_history[user_id].append({"role": "assistant", "content": reply})
            await message.reply(reply)
        except Exception as e:
            print(f"OpenAI API error: {e}")  # Print the error for debugging
            await message.reply("Sorry, there was an error processing your request.")

bot.run(DISCORD_TOKEN)