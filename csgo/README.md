# Setting up a self-service CSGO pickup-game Discord bot using the Syntropy Stack

## Introduction

The Syntropy Stack is a collection of tools and applications that will help you to automatically set up secure, stable, high performance connections between endpoints. In this showcase, Syntropy Stack will be used to connect
CSGO players to the pick-up game server that a Discord bot automatically orchestrates. This Discord bot
will automatically set up the Docker container for the CSGO server, orchestrate API keys and connections between
the players and the server. This can be expanded and integrated into self-service paid CSGO hosting platforms and other usecases such as secure tournament setups.

## How-to

1. Retrieve an Agent API token from the Syntropy Platform
2. Retrieve a Discord bot token from [Discord Developer Portal](https://discord.com/developers)
3. Invite the Discord bot to your channel
4. Create a virtual machine that has the Syntropy Agent deployed on it
5. Run the command `usermod -aG docker <your_vm_user>`
6. Create a .env file and fill it with your credentials. An example of this is here:
```
DISCORD_BOT_TOKEN='<BOT_TOKEN>`
SYNTROPY_ACCESS_TOKEN='<SYNTROPY_ACCESS_TOKEN>'
```
8. Create a virtual environment and install dependencies
```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```
9. Run the Syntropy CSGO Discord bot by typing in the command: `python3 bot.py`
10. Run the command `.synmatch create @<player1_name> <@player2_name> <...>` in your Discord channel (the one where the bot is invited to)
11. Setup the Syntropy App on your players' machines (where you'll run the CSGO clients) using the configuration that the Discord bot DMs you
12. Connect to the CSGO server with the IP that the bot gives you
13. When connected, use the PugSetup mod to setup a pick up game. How to use the mod can be found [here](https://github.com/splewis/csgo-pug-setup).
13. Good luck, have fun!
