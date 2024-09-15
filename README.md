# StudyManagerBot

## What is this bot?

This is a simple discord bot to schedule pinging people at a planned time based on reacting to a scheduling message. This bot was made before Discord implemented [events](https://support.discord.com/hc/en-us/articles/4409494125719-Scheduled-Events) which essentially do the same thing, but way more fleshed out and with dedicated support. For the future you should likely just use Discord events unless you need something very custom tailored to your use case.

## How to use

### Install dependencies

This project uses discord.py and colorama for the bot. Additionally, python 3.7 or higher is required for correct async activities.

To install dependencies run:

```Bash
python3 -m pip install -r requirements.txt
```

### Run the bot
Run the bot using the following steps:

1. Run `python3 study_bot.py` to start the bot
2. Follow the directions and get your bot token from [discord](https://discord.com/developers/applications)
3. Put your token in the bot
4. Use the link it gives you to join your server
5. Use `/set_default_channel` and select a channel in your server for the bot to use from discord
6. Use the bot to do scheduled pings

## Limitations

- Currently limited to PST timezone.
- Some minor bugs involving setup order.
