import os
import discord
from discord.ext import commands
from openai import OpenAI
from collections import defaultdict, deque
import time

# Environment variables
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not DISCORD_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("DISCORD_TOKEN and OPENAI_API_KEY environment variables must be set.")

# Models
TEXT_MODEL = "ft:gpt-3.5-turbo-0125:personal:will-impersonation:BevSmRCs"
VISION_MODEL = "gpt-4o"

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
openai = OpenAI(api_key=OPENAI_API_KEY)

# Track conversation history per user
conversation_history = defaultdict(lambda: deque(maxlen=10))

# Track total cost
total_cost_usd = 0.0

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    global total_cost_usd

    if message.author.bot:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if not (is_dm or is_mentioned):
        return

    prompt = message.content
    if is_mentioned:
        prompt = prompt.replace(f"<@{bot.user.id}>", "").strip()

    if not prompt and not message.attachments:
        return

    user_id = message.author.id

    image_url = None
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            image_url = attachment.url
            break

    # Use GPT-4o for image messages
    if image_url:
        model = VISION_MODEL
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or "What's in this image? If it is a meme, please describe it. If it is a photo, please describe and rate the person OBJECTIVELY based on looks."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
            }
        ]
    else:
        model = TEXT_MODEL
        conversation_history[user_id].append({"role": "user", "content": prompt})
        messages = [
            {
                "role": "system",
                "content": "You are a VERY VERY VERY STRAIGHT, NOT GAY MAN. Be casual and weird, but always make sense."
            }
        ] + list(conversation_history[user_id])

    try:
        start = time.time()
        completion = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        end = time.time()

        reply = completion.choices[0].message.content.strip()
        usage = getattr(completion, "usage", None)

        # Log and store cost info
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        if model == VISION_MODEL:
            # Estimate image cost ~ $0.01 + token costs
            token_cost = (input_tokens * 0.005 + output_tokens * 0.015) / 1000
            cost = 0.01 + token_cost
        else:
            cost = (input_tokens * 0.0015 + output_tokens * 0.002) / 1000  # gpt-3.5 fine-tuned

        total_cost_usd += cost

        if model == TEXT_MODEL:
            conversation_history[user_id].append({"role": "assistant", "content": reply})

        await message.reply(reply)

        print(f"[{model}] {input_tokens}+{output_tokens} tokens | ${cost:.4f} | Total: ${total_cost_usd:.4f} | Time: {end - start:.2f}s")

    except Exception as e:
        print(f"OpenAI API error: {e}")
        await message.reply("Sorry, there was an error processing your request.")

bot.run(DISCORD_TOKEN)
