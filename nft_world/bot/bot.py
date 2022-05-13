from discord.ext import commands
from requests import api
from agent import ApiManager
from dotenv import load_dotenv 
import docker
import discord
import os

load_dotenv()

docker_client = docker.from_env()
bot = commands.Bot(command_prefix = '.')

CONTAINER_NAME = "mc"
NETWORK_NAME = "syntropy-mc"
SUBNET = "10.0.1.0/24"
SERVER_CONTAINER_NAME = "server"
SEED = os.getenv('NFT_SEED')

api_manager = ApiManager(os.getenv('SYNTROPY_ACCESS_TOKEN'))

@bot.event
async def on_ready():
    print("Bot is ready")

@bot.command("start")
async def start(ctx):
    author = ctx.author.name
    await ctx.send(f"**Creating NFT World server...**")

    create_recreate_network()
    container_ip = create_get_container()
    await ctx.send(f"**Server IP address:**\n> {container_ip}")

    key = api_manager.create_or_get_api_keys(author)
    await ctx.send(f"**Syntropy API key to connect:**\n> {key}")

    await create_connection(author, ctx)

async def create_connection(name, ctx):
    server_id = api_manager.get_endpoint_id(SERVER_CONTAINER_NAME)
    client_id = api_manager.get_client_endpoint(name)

    if (client_id == -1):
        await ctx.send(f"**{name}** failed to connect...")
        return -1
    
    api_manager.create_p2p_connection(server_id, client_id)

def create_get_container():
    try:
        container = docker_client.containers.get(CONTAINER_NAME)
        return container.attrs['NetworkSettings']['Networks'][NETWORK_NAME]['IPAddress']
    except docker.errors.NotFound:
        print("Container was not found...")
        pass
    except docker.errors.APIError:
        print("Internal server error...")
        pass
    
    print("Creating new docker container...")

    container = docker_client.containers.run("itzg/minecraft-server", detach=True, ports={'25565/tcp': 25565}, name=CONTAINER_NAME, volumes={'/data': {'bind': '/data', 'mode': 'rw'}}, network=NETWORK_NAME, environment=
        [
            "EULA=TRUE", 
            "SYNTROPY_SERVICES_STATUS=true", 
            f"SYNTROPY_SERVICE_NAME={SERVER_CONTAINER_NAME}", 
            f"SEED={SEED}",
            "VERSION=1.17.1"
        ]
    )
    
    container.reload()
    return container.attrs['NetworkSettings']['Networks'][NETWORK_NAME]['IPAddress']


def create_recreate_network():
    networks = docker_client.networks.list(names=[NETWORK_NAME])

    if networks:
        return networks[0]
    else:
        ipam_pool = docker.types.IPAMPool(
            subnet=SUBNET
        )

        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )

        network = docker_client.networks.create(NETWORK_NAME, driver="bridge", ipam=ipam_config)

        return network

bot.run(os.getenv('DISCORD_TOKEN'))