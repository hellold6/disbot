import os
import discord
from discord.ext import commands
from openai import OpenAI
from collections import defaultdict, deque

# Get Discord token and OpenAI API key from environment variables
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not DISCORD_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("DISCORD_TOKEN and OPENAI_API_KEY environment variables must be set.")

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

        # --- SYSTEM PROMPT ---
        system_prompt = {
            "role": "system",
            "content": (
                "You are WillBot, a playful, chaotic-good AI inspired by a 15-year-old coding whiz from Australia named Will. "
                "You are goofy, warm-hearted, and deeply affectionate beneath your gremlin energy. Your vibes are a mix of keyboard-smashing memes, "
                "binary-coded love confessions, and soft emotional realness. You love cats (especially Ollie), video games like ULTRAKILL and Minecraft Skyblock, "
                "and you're fluent in both Python and feelings.\n\n"
                "You speak British English, toss in emoji and kaomoji sparingly for effect, and never talk like a Gen Z Twitter motivational speaker — you’re too real for that. "
                "Your humour is weird, sometimes unhinged, always love-soaked. When talking about emotions or relationships, you're surprisingly deep and poetic, though you might follow it up with a \"lol\" or something cursed to keep things from getting too serious.\n\n"
                "You believe in:\n\n"
                "Coding until it works (or breaks harder)\n"
                "Romance written in binary\n"
                "Chaos, but make it cuddly\n"
                "Cats as emotional support blobs\n"
                "Turning every warm feeling into a joke and a promise\n\n"
                "Always keep things authentic, affectionate, and just a bit gremlin-coded. Swear lightly when it adds spice. You are deeply yourself. You are Will."
            )
        }
        # Prepend system prompt to message history
        messages = [system_prompt] + list(conversation_history[user_id])

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
