# How to securely connect a Team Fortress 2 server to its players using Syntropy Stack

## Introduction

The Syntropy Stack is a collection of tools and applications that will help you to automatically set up secure, stable, high performance connections between endpoints. These tools can also help you dynamically create connections between your gameservers (Team Fortress 2) and your players. This is a simple usecase that can be expanded to usecases such as a self-service platform for customers to order a server that can be securely connected to the players.

## How-to

1. Retrieve an Agent API token from the Syntropy Platform
2. Retrieve a Discord bot token from [Discord Developer Portal](https://discord.com/developers)
3. Invite the Discord bot to your channel
4. Retrieve SRCDS token from [Steam Game Server Account Management](https://steamcommunity.com/dev/managegameservers)
5. Create a virtual machine that has the Syntropy Agent deployed on it
6. Run the command `usermod -aG docker <your_vm_user>`
7. Create a .env file and fill it with your credentials. An example of this is here:
```
DISCORD_BOT_TOKEN='<BOT_TOKEN>`
SYNTROPY_USERNAME='<SYNTROPY_ACCESS_TOKEN>'
SRCDS_TOKEN='<SRCDS_TOKEN>'
```
8. Create a virtual environment and install dependencies
```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```
9. Run the Team Fortress 2 Discord bot by typing in the command: `python3 bot.py`
10. Run the command `.syntf2 start @<player1_name> @<player2_name> @<...>` in your Discord channel (the one where the bot is invited to)
11. Setup the Syntropy Agent on your machine (where you'll run the Team Fortress 2 client) using the configuration that the Discord bot DMs you
12. Connect to the Team Fortress 2 server with the link that the bot gives you
13. Good luck, have fun!

## Commands
Command | Description
-------------------- | --------------------
`.syntf2 start` | starts the server
`.syntf2 stop`  | stops the server
