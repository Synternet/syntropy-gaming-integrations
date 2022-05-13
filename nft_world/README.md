# NFT World integration

## Introduction

The Syntropy Stack is a collection of tools and applications that will help you to automatically set up secure, stable, high performance connections between endpoints. These tools can also help you dynamically create connections between your gameservers (such as NFT World) and your players. This is a simple usecase that can be expanded to usecases such as a self-service platform for customers to order a server that can be securely connected to the players.

## How-to

### 1. Getting essential variables

1. Retrieve an Agent API token from the Syntropy Platform
2. Retrieve a Discord bot token from [Discord Developer Portal](https://discord.com/developers)
3. Invite the Discord bot to your channel

### 2. Deploy infrastructure

1. Inside `infra` folder, provide the name of your AWS SSH key. An example is here
```
ssh_key_name = "<CHANGE ME>" 
```
**NOTE! - ** provide only the key name (without *.pem* extension)
2. Change the content of `credentials.sec` file and add your **access** and **secret** key
```
[default]
aws_access_key_id=<CHANGE ME>
aws_secret_access_key=<CHANGE ME>
```
2. Run `terraform apply` command

### 3. Deploy your NFT World bot

1. Inside `bot` folder, create an `.env` file and update with the following values
```
SYNTROPY_ACCESS_TOKEN = "<CHANGE ME>"
DISCORD_TOKEN= "<CHANGE ME>"
NFT_SEED= "<CHANGE ME>"
```
2. Inside `ansible/vars/main.yml` file, define your **Syntropy Agent token**. An example is here
```
SYNTROPY_API_KEY: "<CHANGE ME>"
```
3. Run `ansible-playbook -i inventory.yml main.yml` command
4. Your bot is up and running! You can go over to your *Discord* channel to interact

### 4. Interacting with Discord Bot

1. You can type `.help` command in the chat to see all available commands
2. Using `.start` command will automatically create an NFT World minecraft server
3. The bot will then provide you `access key` and `server IP` to connect to. **Note:** you will have 5 minutes to connect before the agent terminates the connection.
4. Setup the **Syntropy Agent** on your machine using the configuration that the Discord bot sent you
5. Open Minecraft launcher and add a new world with the *IP address* provided by the agent
6. Good luck!