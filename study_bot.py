from zoneinfo import ZoneInfo
import requests
import json
import inspect
import sys
import logging
import discord
import datetime
from typing import Optional, NamedTuple, Union

from colorama import Fore, Style

# Make sure that the user is running Python 3.7 or higher
if sys.version_info < (3, 7):
    exit("Python 3.7 or higher is required to run this bot.")

# Now make sure that the discord.py library is installed or/and is up to date
try:
    from discord import app_commands, Intents, Client, Interaction, Message, ui, Embed, ButtonStyle, TextChannel
    # from discord.ext.commands import BadArgument, Context, CommandError
    from discord.app_commands import CommandInvokeError, AppCommandError
    from discord.ext.commands import BadArgument
    from discord.ext import tasks
except ImportError:
    exit(
        "Either discord.py is not installed or you are running an older version of it. "
        "Please make sure by re-installing the requirements."
    )

# ASCII logo, uses Colorama for coloring the logo. ASCII art ripped from https://www.asciiart.eu/books/books
logo = inspect.cleandoc(f"""
{Fore.BLUE}
          ______ ______
        _/      Y      \_
       // ~~ ~~ | ~~ ~  \\\\
      // ~ ~ ~~ | ~~~ ~~ \\\\      Original Unknown
     //________.|.________\\\\     Diddled by David Issel
    `----------`-'----------'
{Fore.RESET}
\n
""")

# inspect.cleandoc() is used to remove the indentation from the message
# when using triple quotes (makes the code much cleaner)
# Typicly developers woudln't use cleandoc rather they move the text
# all the way to the left
print(logo + inspect.cleandoc(f"""
    Hey, welcome to Study Manager Bot
    Please enter your bot's token below to continue.

    {Style.DIM}Don't close this application after entering the token
    You may close it after the bot has been invited and the command has been ran{Style.RESET_ALL}
"""))

# Try except block is useful for when you'd like to capture errors
try:
    with open("config.json") as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    # You can in theory also do "except:" or "except Exception:", but it is not recommended
    # unless you want to suppress all errors
    config = {}


while True:
    # If no token is stored in "config" the value defaults to None
    token = config.get("token", None)
    if token:
        print(f"\n--- Detected token in {Fore.GREEN}./config.json{Fore.RESET} (saved from a previous run). Using stored token. ---\n")
    else:
        # Take input from the user if no token is detected
        token = input("> ")

    # Validates if the token you provided was correct or not
    # There is also another one called aiohttp.ClientSession() which is asynchronous
    # However for such simplicity, it is not worth playing around with async
    # and await keywords outside of the event loop
    try:
        data = requests.get("https://discord.com/api/v10/users/@me", headers={
            "Authorization": f"Bot {token}"
        }).json()
    except requests.exceptions.RequestException as e:
        if e.__class__ == requests.exceptions.ConnectionError:
            exit(f"{Fore.RED}ConnectionError{Fore.RESET}: Discord is commonly blocked on public networks, please make sure discord.com is reachable!")

        elif e.__class__ == requests.exceptions.Timeout:
            exit(f"{Fore.RED}Timeout{Fore.RESET}: Connection to Discord's API has timed out (possibly being rate limited?)")

        # Tells python to quit, along with printing some info on the error that occured
        exit(f"Unknown error has occurred! Additional info:\n{e}")

    # If the token is correct, it will continue the code
    if data.get("id", None):
        break  # Breaks out of the while loop

    # If the token is incorrect, an error will be printed
    # You will then be asked to enter a token again (while Loop)
    print(f"\nSeems like you entered an {Fore.RED}invalid token{Fore.RESET}. Please enter a valid token (see Github repo for help).")

    # Resets the config so that it doesn't use the previous token again
    config.clear()


# This is used to save the token for the next time you run the bot
with open("config.json", "w") as f:
    # Check if 'token' key exists in the config.json file
    config["token"] = token

    # This dumps our working setting to the config.json file
    # Indent is used to make the file look nice and clean
    # If you don't want to indent, you can remove the indent=2 from code
    json.dump(config, f, indent=2)

# Globals used to track scheduled pings and server info
scheduledPings = {}
guilds = {}

@tasks.loop(seconds=60)
async def check_scheduled_pings():
    ids_to_pop = []
    stable_ping_agenda = scheduledPings.copy()
    for scheduledPingID, ping_dict in stable_ping_agenda.items():
        if datetime.datetime.now().astimezone(ZoneInfo("America/Los_Angeles")) >= ping_dict["study_time"]:
            ping_str = "Its time to study:\n"
            guild = ping_dict["guild_obj"]
            for member_id in ping_dict["user_ids"]:
                ping_str += guild.get_member(member_id).mention
                ping_str += "\n"
            ping_str = ping_str[:-1]
            await guild.get_channel(guilds[guild.id]["Preferred Channel"]).send(ping_str)
            ids_to_pop.append(scheduledPingID)
    for ping_id in ids_to_pop:
        scheduledPings.pop(ping_id)

@check_scheduled_pings.before_loop
async def before_start():
    await client.wait_until_ready()

class SchedulePingError(CommandInvokeError):
    def __init__(self, command, e, msg):
        super().__init__(command, e)
        self.error_msg = msg

class StudyMananger(Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """ This is called when the bot boots, to setup the global commands """
        check_scheduled_pings.start()
        await self.tree.sync()



# Variable to store the bot class and interact with it
# Since this is a simple bot to run 1 command over slash commands
# We then do not need any intents to listen to events
botIntents = Intents.default()
handler = logging.FileHandler(filename='discord.log', encoding="utf-8", mode="w")
logging.getLogger().addHandler(handler)
botIntents.members = True
client = StudyMananger(intents=botIntents)

@client.event
async def on_ready():
    """ This is called when the bot is ready and has a connection with Discord
        It also prints out the bot's invite URL that automatically uses your
        Client ID to make sure you invite the correct bot with correct scopes.
    """
    print(inspect.cleandoc(f"""
        Logged in as {client.user} (ID: {client.user.id})

        Use this URL to invite {client.user} to your server:
        {Fore.LIGHTBLUE_EX}https://discord.com/api/oauth2/authorize?client_id={client.user.id}&scope=applications.commands%20bot{Fore.RESET}
    """), end="\n\n")
    try:
        with open("channel_prefs.json", "r") as f:
            guilds = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("JSON Load error")
        guilds = {}



@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """ Remove user from list to be pinged at scheduled time """
    if payload.message_id not in scheduledPings:
        return
    
    if payload.user_id in scheduledPings[payload.message_id]["user_ids"]:
        scheduledPings[payload.message_id]["user_ids"].remove(payload.user_id)
    


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """ Add user to list of users to be pinged at appointed time """
    if payload.message_id not in scheduledPings:
        return
    
    if payload.user_id not in scheduledPings[payload.message_id]["user_ids"]:
        scheduledPings[payload.message_id]["user_ids"].append(payload.user_id)


async def parseDateTime(time: str, date: str) -> datetime.datetime:
    """ Helper to parse out datetime from a time and date strings. Returns datetime
        object representation of time and date string parameters.
    """
    logging.debug(f"parseDateTime call: {time} {date}")
    if date:
        try:
            fields = date.split("/")
            if len(fields) < 3:
                raise SchedulePingError(parseDateTime, BadArgument("Bad Date"), "Incorrect Date Format: mm/dd/yyyy")
            year = int(fields[2])
            pDate = datetime.date(year, int(fields[0]), int(fields[1]))
        except ValueError:
            raise SchedulePingError(parseDateTime, BadArgument("Bad Date"), "Incorrect Date Format: mm/dd/yyyy")
    else:
        pDate = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()
        # print(pDate)
    
    # Time validation
    try:
        fields = time.split(":")
        if len(fields) != 2:
            raise SchedulePingError(parseDateTime, BadArgument("Bad time"), "Incorrect time format: hh:mm using 24 hour time")
        pTime = datetime.time(int(fields[0]), int(fields[1]), tzinfo=ZoneInfo("America/Los_Angeles"))
    except ValueError:
        raise SchedulePingError(parseDateTime, BadArgument("Bad time"), "Incorrect time format: hh:mm using 24 hour time")
    
    pingDatetime = (datetime.datetime.combine(pDate, pTime))
    if (datetime.datetime.now()).astimezone(ZoneInfo("America/Los_Angeles")) > pingDatetime:
        # print(datetime.datetime.now())
        raise SchedulePingError(parseDateTime, BadArgument("Datetime has already passed"), "This time has already passed")

    return pingDatetime

async def generateScheduledMeetingPrompt(interaction: Interaction, dt: datetime.datetime) -> Embed:
    """ Create an embed object to respond to a schedule ping request """
    # Create event embed
    embed = Embed(title="Study Call")
    embed.description = inspect.cleandoc(f"""
        Study call scheduled for **{dt.strftime("%H:%M")}** on **{dt.strftime("%m/%d/%y")}**. Please react to this message if you would like to be pinged then.
    """)
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    embed.add_field(name="Time", value=dt.strftime("%H:%M"), inline=True)
    embed.add_field(name="Date", value=dt.strftime("%m/%d/%y"), inline=True)
    embed.set_footer(text="Created").timestamp = interaction.created_at
    return embed


@client.tree.command()
@app_commands.describe(
    time = "24 Time you want to schedule: HH:MM",
    date = "[Opt] Date for Ping: mm/dd/yyyy",
)
async def schedule_ping(interaction: Interaction, time: str, date: Optional[str] = None):
    """ Post a message where anyone that reacts will be pinged at the scheduled time. """
    # Responds in the console that the command has been ran
    print(f"> {Style.BRIGHT}{interaction.user}{Style.RESET_ALL} used the schedule_ping command.")

    # Date Validation; Errors will catch in the global error handler
    pingDatetime = await parseDateTime(time, date);

    # Respond to user
    await interaction.response.send_message(inspect.cleandoc(f"""
        Hi **{interaction.user}**, ping scheduled for {pingDatetime.ctime()}
    """), ephemeral=True)

    # Generate embed
    embed = await generateScheduledMeetingPrompt(interaction, pingDatetime)

    response_channel = interaction.guild.get_channel(guilds[interaction.guild.id]["Preferred Channel"])
    message = await response_channel.send(embed=embed)

    global scheduledPings
    scheduledPings[message.id] = {}
    scheduledPings[message.id]["guild_obj"] = interaction.guild
    scheduledPings[message.id]["user_ids"] = []
    scheduledPings[message.id]["user_ids"].append(interaction.user.id)
    scheduledPings[message.id]["study_time"] = pingDatetime
    # print(scheduledPings)

@client.tree.command()
async def study_manager_info(interaction: Interaction):
    """ Synopsis of available commands """
    help_message = inspect.cleandoc(f"""
        > Hi I am a study manager bot. Currently I am pretty bare bones.
        > 
        > Currently I offer the following commands:
        > `/set_default_channel <Channel>` A command that tells me where to put posts to schedule calls.
        > \t - `Channel` The text channel this bot will respond in when scheduling pings and pinging.
        > \t Only needs to be run once per server once bot is online
        > `/schedule_ping <time> <Optional[Date]>` Schedule a ping for the given time
        > \t - `time` Time to schedule ping: hh:mm format. Currently all times are PST Sorry east coasters
        > \t - `Optional[Date]` An optional date in mm:dd:yyyy format.
        > \t Will ping everyone who reacts to the generated post at the given time.
        > \t **Limitations**: Only supports PST times right now
        > `study_manager_info` Commmand to show you this information
        > 
        > Known Issues:
        > * Only supports PST
        > * Bot breaks if `/schedule_ping` is used before `/set_default_channel` is used once.
    """)
    await interaction.response.send_message(help_message, ephemeral=True)

@client.tree.command()
@app_commands.describe(channel = "Channel for bot to respond in.")
async def set_default_channel(interaction: Interaction, channel: TextChannel):
    """ Select which channel this bot puts scheduled messages """
    global guilds
    if interaction.guild.id not in guilds:
        guilds[interaction.guild.id] = {}
    guilds[interaction.guild.id]["Preferred Channel"] = channel.id
    await interaction.response.send_message(inspect.cleandoc(f"""
        The channel this bot will respond in is ***{channel.name}***.
    """), ephemeral=True)
    with open("channel_prefs.json", "w") as f:
        # Dump guild info
        json.dump(guilds, f, indent=2)


@client.tree.error
async def schedule_ping_error(interaction: Interaction, error: AppCommandError):
   """ Error handler for errors raised in the /schedule_ping command """
   # Potentially unecessary now
   if isinstance(error, SchedulePingError):
        await interaction.response.send_message(f"**[Error]** Bad Command:{error.error_msg}", ephemeral=True)

# Runs the bot with the token you provided
client.run(token, log_handler=handler, log_level=logging.DEBUG)
