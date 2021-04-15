import os
import time
import discord
import docker
import asyncio
import functools
import socket
import choice
from api import ApiManager
from aioify import aioify
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NETWORK_NAME = os.getenv("DOCKER_NETWORK", "syntropynet-network")
PREFIX = ".synterraria "
CONTAINER_NAME = "syn-terraria"
WORLD_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)), "worlds")

terraria_info = {"running": False, "owner": ""}
terraria_lock = asyncio.Lock()
bot = commands.Bot(command_prefix=PREFIX)
api_mgr = ApiManager(os.getenv("SYNTROPY_USERNAME"), os.getenv("SYNTROPY_PASSWORD"))
docker_client = docker.from_env()
docker_api_client = docker.APIClient()



def check_if_world_exists():
    if not os.path.exists(WORLD_PATH):
        os.mkdir(WORLD_PATH)
        return False
    if not os.path.exists(os.path.join(WORLD_PATH, "syntropy.wld")):
        return False
    return True
    
def generate_server_config(difficulty=None, size=None, max_players=8):
    configuration_file = open(os.path.join(WORLD_PATH, "serverconfig.txt"), "w")
    if difficulty != None:
        configuration_file.write("difficulty={0}\n".format(difficulty - 1))
    configuration_file.write("worldname=syntropy\n")
    if size != None:
        configuration_file.write("autocreate={0}\n".format(size))
    configuration_file.write("maxplayers={0}\n".format(max_players + 2))
    configuration_file.close()

def create_or_get_container(difficulty=None, size=None, max_players=8):
    try:
        return docker_client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        pass
    generate_server_config(difficulty, size, max_players)
    container = docker_client.containers.run("ryshe/terraria:vanilla-latest", auto_remove=True, stdin_open=True, detach=True, volumes={WORLD_PATH: {'bind': '/root/.local/share/Terraria/Worlds', 'mode': 'rw'}}, name="syn-terraria", network=NETWORK_NAME, environment=["SYNTROPY_SERVICE_NAME=terraria"], command="-world /root/.local/share/Terraria/Worlds/syntropy.wld -config /root/.local/share/Terraria/Worlds/serverconfig.txt")
    return container

def stop_container():
    container = docker_api_client.containers(filters={"name": CONTAINER_NAME})
    if len(container) == 0:
        print("container not found")
        return
    container = container[0]
    socket = docker_api_client.attach_socket(container, params={'stdin': 1, 'stream': 1})
    socket._sock.send("exit\n".encode('utf-8'))
    socket._sock.send("exit\n".encode('utf-8'))
    socket.close()


def get_container_ip(container):
    while True:
        try:
            container.reload()
            ip_addr = container.attrs['NetworkSettings']['Networks'][NETWORK_NAME]['IPAddress']
            return ip_addr 
        except KeyError:
            continue


def get_connection_id(connections, agent_id):
    return [c["agent_connection_id"] for c in connections if c["agent_1"]["agent_id"] == agent_id or c["agent_2"]["agent_id"] == agent_id][0]


def get_subnet_id(services, service_name):
    service = [s for s in services if s["agent_service_name"] == service_name]
    if len(service) == 0: return None
    service = service[0]
    return service["agent_service_subnets"][0]["agent_service_subnet_id"]


@aioify
def start_terraria(ctx, players, difficulty, world_size):
    players_ids = {player: f"{player.name}-{player.id}" for player in players}

    for player in players:
        api_key = api_mgr.get_or_create_api_key(players_ids[player])[
            "api_key_secret"
        ]
        asyncio.run_coroutine_threadsafe(
            player.send(
                f"**Welcome to your Terraria server.**\n\nSyntropy Agent API key: `{api_key}` \nSyntropy Agent Name: `{player.name}-{player.id}`\nInput these into your Syntropy Agent configuration to continue"
            ),
            bot.loop,
        )

    players_endpoints = {}

    for player in players:
        start_time = time.time()
        while True:
            endpoints = api_mgr.get_endpoints(players_ids[player])
            if len(endpoints) != 0:
                endpoint = endpoints[0]
                if endpoint["agent_is_online"]:
                    players_endpoints[player] = endpoint
                    break
            if time.time() - start_time > 180:
                asyncio.run_coroutine_threadsafe(ctx.message.channel.send("Players have failed to connect in time. The server has been stopped."), bot.loop)
                terraria_info["running"] = False
                return
            time.sleep(10)
            
               
    container = create_or_get_container(difficulty, world_size, len(players))
    ip_addr = get_container_ip(container)

    syn_network = api_mgr.recreate_network("terraria-server")

    agent_ids = []

    terraria_endpoint = api_mgr.get_endpoints(socket.gethostname())[0]

    for player in players:
        agent_ids.append([players_endpoints[player]["agent_id"], terraria_endpoint["agent_id"]])
    time.sleep(5)
    connections = api_mgr.add_connections(syn_network["network_id"], agent_ids)
    print(connections)
    for player in players:
        connection_id = get_connection_id(connections, players_endpoints[player]["agent_id"])
        services = api_mgr.get_services([players_endpoints[player]["agent_id"], terraria_endpoint["agent_id"]]) 
        subnet_id = get_subnet_id(services, "terraria") 
        api_mgr.enable_service(connection_id, subnet_id)

    for player in players:
        asyncio.run_coroutine_threadsafe(
            player.send(
                "Your Terraria server is ready. Connect to this server to continue: `{0}`".format(
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
    async with terraria_lock:
        if terraria_info["running"]:
            await ctx.message.channel.send("Server is already running")
            return
        else:
            terraria_info["running"] = True
            terraria_info["owner"] = ctx.author.id
    world_exists = check_if_world_exists()
    difficulty = None
    world_size = None
    if not world_exists:
        choice_manager = choice.DiscordMultipleChoice(ctx, bot)
        world_size = await choice_manager.createMessage("World size", "1 = small, 2 = medium, 3 = large, 4 = cancel", 4)
        if (world_size == 4):
            await ctx.message.channel.send("Cancelled")
            return
        difficulty = await choice_manager.createMessage("Difficulty", "1 = classic, 2 = expert, 3 = master, 4 = journey, 5 = cancel")
        if (difficulty == 5):
            await ctx.message.channel.send("Cancelled")
            return
    await ctx.message.channel.send(
        f"{ctx.author.name} has created a terraria server!"
    )
    await start_terraria(ctx, [ctx.author] + list(players), difficulty, world_size)

@bot.command("stop")
async def stop_server(ctx):
    async with terraria_lock:
        if not terraria_info["running"]:
            await ctx.message.channel.send("Server is not running")
            return
        if terraria_info["owner"] != ctx.author.id:
            await ctx.message.channel.send("You didn't start this server")
            return
        
    await ctx.message.channel.send("Stopping the server")
    stop_container()
    terraria_info["running"] = False

@bot.command("delete")
async def delete_world(ctx):
    async with terraria_lock:
        if terraria_info["running"]:
            await ctx.message.channel.send("Stop the server first")
            return
        elif not check_if_world_exists():
            await ctx.message.channel.send("World doesn't exist")
            return
        
    choice_manager = choice.DiscordMultipleChoice(ctx, bot, False)
    response = await choice_manager.createMessage("Do you want to delete the world?", "👍 = yes, 👎 = no")
    if (response == 2):
        await ctx.message.channel.send("World wasn't deleted")
        return
    os.remove(os.path.join(WORLD_PATH, "syntropy.wld"))
    await ctx.message.channel.send("World deleted successfully")

bot.run(TOKEN)
