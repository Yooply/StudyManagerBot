import requests
import json
import inspect
import sys

from colorama import Fore, Style

# Make sure that the user is running Python 3.7 or higher
if sys.version_info < (3, 7):
    exit("Python 3.7 or higher is required to run this bot.")

# Now make sure that the discord.py library is installed or/and is up to date
try:
    from discord import app_commands, Intents, Client, Interaction
except ImportError:
    exit(
        "Either discord.py is not installed or you are running an older version of it. "
        "Please make sure by re-installing the requirements."
    )

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


class FunnyBadge(Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """ This is called when the bot boots, to setup the global commands """
        await self.tree.sync()


# Variable to store the bot class and interact with it
# Since this is a simple bot to run 1 command over slash commands
# We then do not need any intents to listen to events
client = FunnyBadge(intents=Intents.none())


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


@client.tree.command()
async def initrec(interaction: Interaction):
    """ Initialize a 0-0 record for all stats """
    # Responds in the console that the command has been ran
    print(f"> {Style.BRIGHT}{interaction.user}{Style.RESET_ALL} initialized their record.")
    with open(f"{str(interaction.user)}.json", "w") as record:
        empty_dict = {"wins":0,"losses":0,"rank":"?","agents":{}}
        json.dump(empty_dict,record,indent=2)

    # Then responds in the channel with this message
    await interaction.response.send_message(inspect.cleandoc(f"""
        Hi **{interaction.user}**, initializing your tracker to 0 for all stats.
    """))
    """
    await interaction.response.send_message(inspect.cleandoc(f\"""
        Hi **{interaction.user}**, thank you for saying hello to me.
        > __**Where's my badge?**__
        > Eligibility for the badge is checked by Discord in intervals,
        > at this moment in time, 24 hours is the recommended time to wait before trying.
        > __**It's been 24 hours, now how do I get the badge?**__
        > If it's already been 24 hours, you can head to
        > https://discord.com/developers/active-developer and fill out the 'form' there.
        > __**Active Developer Badge Updates**__
        > Updates regarding the Active Developer badge can be found in the
        > Discord Developers server -> https://discord.gg/discord-developers - in the #active-dev-badge channel.
    \"""))"""

def print__overall_stats(stats: dict) -> str:
    retStr = inspect.cleandoc(f"""
        > You currently have **{stats["wins"]} wins**.
        > You currently have **{stats["losses"]} losses**.
        > Your rank is currently {stats["rank"]}
        > Your w/l rate is **{(stats["wins"]/stats["losses"]) if stats["losses"] > 0 else stats["wins"]}**
        > Use [fill command in later] for agent specific stats
    """)
    return retStr

@client.tree.command()
async def updaterec(interaction: Interaction, arg1: str = commands.parameter()):
    """ Update record using command args """
    print(f"> {Style.BRIGHT}{interaction.user}{Style.RESET_ALL} updated their record.")

    try:
        record = open(f"{str(interaction.user)}.json", "r")
    except FileNotFoundError:
        print("Error opening records file. Contact dev for debugging")
        await interaction.response.send_message(inspect.cleandoc("""
            Your records file does not exist. If you did not run **/initrec**
            > first try running that command to initialize your record. If this does not
            > work the bot is broken please contact the developer.
        """))
        return None
    except OSError:
        print("Error opening records file. Contact dev for debugging")
        await interaction.response.send_message(inspect.cleandoc("""
            There was an error opening your records file. If you did not run **/initrec**
            > first try running that command to initialize your record. If this does not
            > work the bot is broken please contact the developer.
        """))
        return None
    
    stats = json.load(record)
    print(str(interaction.data))
    print(str(interaction.command.parameters))
    print(stats)
    await interaction.response.send_message(print__overall_stats(stats))
    #TODO: Figure out how command args work
    

# Runs the bot with the token you provided
client.run(token)