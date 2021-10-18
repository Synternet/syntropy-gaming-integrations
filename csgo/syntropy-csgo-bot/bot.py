import os
import time
import discord
import containers
import asyncio
import functools
import socket
import api
import messages
from loguru import logger
from aioify import aioify
from discord.ext import commands
from dotenv import load_dotenv
from syntropy_sdk import AgentsPairObject


load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NETWORK_NAME = os.getenv("DOCKER_NETWORK", "syntropynet-network")
PREFIX = ".synmatch "

bot = commands.Bot(command_prefix=PREFIX)
api_mgr = api.ApiManager(os.getenv("SYNTROPY_ACCESS_TOKEN"))

match_lock = asyncio.Lock()
match_info = {"running": False, "owner": ""}

def get_subnet_id(services, service_name, terraria_agent_id):
    services = services[0].agent_1.agent_services if services[0].agent_1.agent_id == terraria_agent_id else services[0].agent_2.agent_services
    service = [s for s in services if s.agent_service_name == service_name]
    if len(service) == 0: return None
    service = service[0]
    return service.agent_service_subnets[0].agent_service_subnet_id

@aioify
def start_match(ctx, players):
    player_ids = {player: f"{player.name}-{player.id}" for player in players}

    logger.debug("Sending API keys to players")

    for player in players:
        api_key = api_mgr.get_or_create_api_key(player_ids[player])
        if (api_key == -1):
            api_key = "use the api key bot provided before"
        else:
            api_key = api_key.api_key_secret
        asyncio.run_coroutine_threadsafe(
            player.send(
               messages.WELCOME_MATCH.format(api_key=api_key, name=player.name, id=player.id) 
            ),
            bot.loop,
        )
    
    logger.debug("Waiting on player endpoints to come alive")

    players_endpoints = {}

    for player in players:
        start_time = time.time()
        logger.debug(f"Waiting on player {player.name}")
        while True:
            endpoints = api_mgr.get_endpoints(player_ids[player])
            if len(endpoints) != 0:
                endpoint = endpoints[0]
                if endpoint.agent_is_online:
                    players_endpoints[player] = endpoint
                    break
            if time.time() - start_time > 180:
                asyncio.run_coroutine_threadsafe(ctx.message.channel.send(messages.FAILED_TO_CONNECT), bot.loop)
                return
            time.sleep(10)
            
               
    logger.debug("Creating a CSGO container")
    container = containers.create_or_get_container(NETWORK_NAME)
    logger.debug("Retrieving CSGO container IP address")
    ip_addr = containers.get_container_ip(container, NETWORK_NAME) 

    agent_ids = []

    csgo_endpoint = api_mgr.get_endpoints(socket.gethostname())[0] 

    for player in players:
        agent_ids.append(AgentsPairObject(players_endpoints[player].agent_id, csgo_endpoint.agent_id))
    print(agent_ids)
    time.sleep(5)

    api_mgr.remove_all_connections(csgo_endpoint.agent_id)
    connections_ids = api_mgr.add_connections(agent_ids, csgo_endpoint.agent_id)

    for player in players:
        logger.debug(f"Enabling connection for player {player.name}")
        connection_id = connections_ids[players_endpoints[player].agent_id]
        services = api_mgr.get_services([connection_id]) 
        subnet_id = get_subnet_id(services, "syn-csgo", csgo_endpoint.agent_id)
        print("SUBNET_ID: ", subnet_id)
        api_mgr.enable_service(connection_id, subnet_id)

    time.sleep(5)

    logger.debug("Creating connections between players and CSGO endpoint")

    for player in players:
        logger.debug(f"Notifying player {player.name}")
        asyncio.run_coroutine_threadsafe(
            player.send(messages.READY_MATCH.format(ip=ip_addr)),
            bot.loop
        )


@bot.event
async def on_ready():
    print("The bot is ready")


@bot.command("create")
async def create_duel(ctx, *players: discord.Member):
    async with match_lock:
        if match_info["running"]:
            await ctx.message.channel.send(messages.MATCH_ALREADY_RUNNING)
            return
        else:
            match_info["owner"] = ctx.author.id
            match_info["running"] = True
    
    created_match_message = messages.CREATED_MATCH

    created_match_message += f"{ctx.author.mention}\n"

    for player in players:
        created_match_message += f"{player.mention}\n"

    await ctx.message.channel.send(created_match_message)
    await start_match(ctx, [ctx.author] + list(players))

@bot.command("stop")
async def stop_match(ctx):
    async with match_lock:
        if not match_info["running"]:
            await ctx.message.channel.send(messages.MATCH_IS_NOT_RUNNING)
            return
        
        if match_info["owner"] != ctx.author.id:
            await ctx.message.channel.send(messages.NOT_YOUR_MATCH)
            return
    
    await ctx.message.channel.send(messages.STOPPING_MATCH.format(name=ctx.author.name))
    containers.stop_container()
    match_info["running"] = False
    
bot.run(TOKEN)
