# How to securely connect a FIVEM server to its players using Syntropy Stack

## Introduction

The Syntropy Stack is a collection of tools and applications that will help you to automatically set up secure, stable, high performance connections between endpoints. These tools can also help you dynamically create connections between your gameservers (FiveM) and your players. This is a simple usecase that can be expanded to usecases such as a self-service platform for customers to order a server that can be securely connected to the players.

## How-to

1. Retrieve an Agent API token from the Syntropy Platform
2. Retrieve a Discord bot token from [Discord Developer Portal](https://discord.com/developers)
3. Retrieve a FiveM server license key from [Cfx.re Keymaster](https://keymaster.fivem.net)
3. Invite the Discord bot to your channel
4. Create a virtual machine that has the Syntropy Agent deployed on it
5. Run the command `usermod -aG docker <your_vm_user>`
6. Create a .env file and fill it with your credentials. An example of this is here:
```
DISCORD_BOT_TOKEN='<BOT_TOKEN>`
SYNTROPY_USERNAME='<SYNTROPY_USERNAME>'
SYNTROPY_PASSWORD='<SYNTROPY_PASSWORD>'
LICENSE_KEY='<LICENSE_KEY>'
```
7. Create a virtual environment and install dependencies
```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```
8. Run the FiveM Discord bot by typing in the command: `python3 bot.py`
9. Run the command `.synFM start @<player1_name> @<player2_name> @<...>` in your Discord channel (the one where the bot is invited to)
10. Setup the Syntropy Agent on your machine (where you'll run the FiveM client) using the configuration that the Discord bot DMs you
11. Connect to the FiveM server with the ip that the bot gives you through the FiveM application direct connect (press F8 to access console and type `connect <IP that bot gave you>`)
12. Good luck, have fun!

## Commands
Command | Description
-------------------- | --------------------
`.synFM start` | starts the server
`.synFM stop`  | stops the server
