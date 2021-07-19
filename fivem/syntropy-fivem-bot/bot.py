import os
import time
import discord
import asyncio
import functools
import socket
from container_manager import ContainerManager
from api import ApiManager
from aioify import aioify
from discord.ext import commands
from dotenv import load_dotenv
import choice

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NETWORK_NAME = os.getenv("DOCKER_NETWORK", "syntropynet-network")
PREFIX = ".synFM "
CONTAINER_NAME = "syn-fivem"
LICENSE_KEY = os.getenv("LICENSE_KEY")
fivem_lock = asyncio.Lock()
bot = commands.Bot(command_prefix=PREFIX)
api_mgr = ApiManager(os.getenv("SYNTROPY_USERNAME"), os.getenv("SYNTROPY_PASSWORD"))
container_manager = ContainerManager(CONTAINER_NAME, NETWORK_NAME, LICENSE_KEY)
def get_connection_id(connections, agent_id):
    return [c["agent_connection_id"] for c in connections if c["agent_1"]["agent_id"] == agent_id or c["agent_2"]["agent_id"] == agent_id][0]
def get_subnet_id(services, service_name):
    service = [s for s in services if s["agent_service_name"] == service_name]
    if len(service) == 0: return None
    service = service[0]
    return service["agent_service_subnets"][0]["agent_service_subnet_id"]

@aioify
def start_fivem(ctx, players):
    players_ids = {player: f"{player.name}-{player.id}" for player in players}
    print("sending api keys to players")
    for player in players:
        api_key = api_mgr.get_or_create_api_key(players_ids[player])
        if api_key == -1:
            api_key = "use the api key bot provided before"
        else:
            api_key = api_key["api_key_secret"]
        asyncio.run_coroutine_threadsafe(
            player.send(
                f"**Welcome to your GTA V: server.**\n\nSyntropy Agent API key: `{api_key}` \nSyntropy Agent Name: `{player.name}-{player.id}`\nInput these into your Syntropy Agent configuration to continue"
            ),
            bot.loop,
        )
    players_endpoints = {}
    for player in players:
        start_time = time.time()
        print("waiting for player " + player.name)
        while True:
            endpoints = api_mgr.get_endpoints(players_ids[player])
            if len(endpoints) != 0:
                endpoint = endpoints[0]
                if endpoint["agent_is_online"]:
                    players_endpoints[player] = endpoint
                    break
            if time.time() - start_time > 180:
                asyncio.run_coroutine_threadsafe(ctx.message.channel.send("Players have failed to connect in time. The server has been stopped."), bot.loop)
                return
            time.sleep(10)
            
    container_manager.number_of_players = len(players)
    print("starting container")
    container = container_manager.start_container()
    ip_addr = container_manager.get_container_ip(container)
    print("creating syntropynetwork")
    syn_network = api_mgr.recreate_network("fivem-server")
    agent_ids = []
    fivem_endpoint = api_mgr.get_endpoints(socket.gethostname())[0]
    print("creating services")
    for player in players:
        agent_ids.append([players_endpoints[player]["agent_id"], fivem_endpoint["agent_id"]])
    time.sleep(5)
    connections = api_mgr.add_connections(syn_network["network_id"], agent_ids)
    print(connections)
    for player in players:
        connection_id = get_connection_id(connections, players_endpoints[player]["agent_id"])
        services = api_mgr.get_services([players_endpoints[player]["agent_id"], fivem_endpoint["agent_id"]]) 
        subnet_id = get_subnet_id(services, "fivem")
        api_mgr.enable_service(connection_id, subnet_id)
    for player in players:
        asyncio.run_coroutine_threadsafe(
            player.send(
                "Your GTA: Server is ready. Connect to this server to continue: {0}".format(
                    ip_addr
                )
            ),
            bot.loop
        )
@bot.event
async def on_ready():
    print("The bot is ready")
    
@bot.command("start")
async def start_server(ctx, *players: discord.Member):
    async with fivem_lock:
        if container_manager.is_running():
            await ctx.message.channel.send("Server is already running")
            return
    await ctx.message.channel.send(
        f"{ctx.author.name} has created GTA V: Server!"
    )
    await start_fivem(ctx, [ctx.author] + list(players))
@bot.command("stop")
async def stop_server(ctx):
    async with fivem_lock:
        if not container_manager.is_running():
            await ctx.message.channel.send("Server is not running")
            return
        
    await ctx.message.channel.send("Stopping the server")
    container_manager.stop_container()
bot.run(TOKEN)