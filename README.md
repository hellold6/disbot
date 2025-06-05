# ImposterBot

A simple Discord bot that impersonates me using OpenAI.

## Features

- Listens to messages in Discord
- Uses OpenAI's API to generate responses that sound like me

## Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/yourusername/imposterbot.git
   cd imposterbot
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file or set your environment variables:

   ```
   DISCORD_TOKEN=your_bot_token
   OPENAI_API_KEY=your_openai_key
   ```

4. Run the bot:

   ```bash
   python bot.py
   ```

## Dependencies

- `discord.py`
- `openai`
- `python-dotenv` (optional)

## Notes

- Make sure your bot has the right permissions in your Discord server.
- Responses are generated using OpenAI’s language model.

## License

Do whatever. I don't care.
