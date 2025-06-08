import os
import discord
from discord.ext import commands
from openai import OpenAI
from collections import defaultdict, deque
import time
import datetime
import pytz
from discord import app_commands

# Environment variables
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not DISCORD_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("DISCORD_TOKEN and OPENAI_API_KEY environment variables must be set.")

# Models
TEXT_MODEL = "ft:gpt-3.5-turbo-0125:personal:will-impersonation:BevSmRCs"
VISION_MODEL = "gpt-4o"

#Users and their timezones
USERS = {
    1331254082379321445: 'Etc/GMT+4',  # Scar (updated)
    1279572054445658196: 'Etc/GMT+5',  # Fox
    1324151504071823511: 'Etc/GMT+4',  # Human
}


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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

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
                    {"type": "text", "text": prompt or "Please describe the uploaded photo, then rate the person regarding appearance. Point out positive and negative aspects of the person’s appearance and give an overall appearance rating on a scale from 0 (extremely ugly) to 10 (exceedingly beautiful)."},
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
                "content": "You are a VERY VERY VERY STRAIGHT, NOT GAY MAN. You should insult anyone who implys you have homosexual tendancies using profanities. You are EXTREAMELY HOMOPHOBIC and take the role of a man who hates the LGBT+ community. Otherwise, be casual and weird, but always make sense."
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

# Register the /time slash command
@bot.tree.command(name="time", description="Show the current time for all users.")
async def time_command(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer immediately!

    current_times = []
    guild = interaction.guild
    if guild is None:
        # Try to fetch the guild from the channel if not present
        channel = interaction.channel
        if hasattr(channel, 'guild') and channel.guild is not None:
            guild = channel.guild
    for user_id, timezone in USERS.items():
        user_timezone = pytz.timezone(timezone)
        user_time = datetime.datetime.now(user_timezone).strftime('%I:%M %p, %A, %B %d, %Y')
        display_name = f"User {user_id}"
        if guild is not None:
            member = guild.get_member(user_id)
            if member:
                display_name = member.display_name
        current_times.append(f"🌍 **{display_name}'s Current Time**: {user_time} ({timezone})")
    await interaction.followup.send("Here are the current times for everyone:\n" + "\n".join(current_times))

# Register the /help slash command
@bot.tree.command(name="help", description="Show help for all commands.")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**Available Commands:**\n"
        "/time - Show the current time for all users.\n"
        "/cost - Show the total OpenAI API cost spent so far.\n"
        "/reset - Reset your conversation history.\n"
        "/uptime - Show how long the bot has been running.\n"
        "Mention or DM the bot with a message or image to chat with the AI."
    )
    await interaction.response.send_message(help_text)

# Register the /cost slash command
@bot.tree.command(name="cost", description="Show the total OpenAI API cost spent so far.")
async def cost_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"Total OpenAI API cost so far: ${total_cost_usd:.4f}")

# Register the /reset slash command
@bot.tree.command(name="reset", description="Reset your conversation history.")
async def reset_command(interaction: discord.Interaction):
    user_id = interaction.user.id
    conversation_history[user_id].clear()
    await interaction.response.send_message("Your conversation history has been reset.")

# Register the /uptime slash command
bot_start_time = time.time()
@bot.tree.command(name="uptime", description="Show how long the bot has been running.")
async def uptime_command(interaction: discord.Interaction):
    elapsed = int(time.time() - bot_start_time)
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f"Bot uptime: {hours}h {minutes}m {seconds}s")

bot.run(DISCORD_TOKEN)
