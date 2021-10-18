import docker
from loguru import logger

CONTAINER_NAME = "syn-csgo"
IMAGE_NAME = "timche/csgo:pug-practice"

docker_client = docker.from_env()

def create_or_get_container(network_name):
    try:
        return docker_client.containers.get(CONTAINER_NAME)
    except docker.errors.NotFound:
        logger.info("Did not found a running CSGO container, creating one")
        pass

    container = docker_client.containers.run(IMAGE_NAME, detach=True, volumes={'csgo': {'bind': '/home/csgo/server', 'mode': 'rw'}}, name=CONTAINER_NAME, network=network_name, environment=["SYNTROPY_SERVICE_NAME=syn-csgo"])

    logger.info(f"Created container with id {container.id}")

    return container

def stop_container():
    logger.info(f"Stopping container with name {CONTAINER_NAME}")
    try:
        container = docker_client.containers.get(CONTAINER_NAME)
        container.stop()
    except docker.errors.NotFound:
        logger.error("Trying to stop a stopped/non-existant container?")


def get_container_ip(container, network_name):
    while True:
        try:
            container.reload()
            ip_addr = container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']
            return ip_addr 
        except KeyError:
            continue
