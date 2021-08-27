import docker
import os

class ContainerManager:
    def __init__(self, CONTAINER_NAME, NETWORK_NAME, SRCDS_TOKEN):
        self.CONTAINER_NAME = CONTAINER_NAME
        self.NETWORK_NAME = NETWORK_NAME
        self.SRCDS_TOKEN = SRCDS_TOKEN
        self.docker_client = docker.from_env()
        self.TF2_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tf2-data")
        self.number_of_players = 0
    
    def __get_container(self):
        try:
            return self.docker_client.containers.get(self.CONTAINER_NAME)
        except docker.errors.NotFound:
            return False

    def __create_data_dir(self):
        if not os.path.exists(self.TF2_DATA_PATH):
            os.umask(0)
            os.mkdir(self.TF2_DATA_PATH, 0o777)

    def __create_container(self):
        container = self.__get_container()
        if (container):
            return container
        self.__create_data_dir()
        return self.docker_client.containers.run("cm2network/tf2", 
            volumes={self.TF2_DATA_PATH: {"bind": "/home/steam/tf-dedicated/", "mode": "rw"}}, 
            name=self.CONTAINER_NAME, 
            network=self.NETWORK_NAME, 
            detach=True, 
            environment=["SYNTROPY_SERVICE_NAME=tf2", "SRCDS_TOKEN={}".format(self.SRCDS_TOKEN), 
                "SRCDS_MAXPLAYERS={}".format(self.number_of_players), "SRCDS_PW={}".format(""), "SRCDS_RCONPW={}".format("")])

    def start_container(self):
        container = self.__create_container()
        if (container.status == "running"):
            return container
        else:
            container.start()
            return container

    def stop_container(self):
        is_running = self.is_running()
        if (not is_running):
            return 0
        container = self.__get_container()
        container.stop()
        container.remove()
        return 1

    
    def is_running(self):
        container = self.__get_container()
        if (not container):
            return False
        if (container.status != "running"):
            return False
        return True

    def get_container_ip(self, container=False):
        container = container if container else self.__get_container()
        while True:
            try:
                container.reload()
                ip_addr = container.attrs['NetworkSettings']['Networks'][self.NETWORK_NAME]['IPAddress']
                return ip_addr 
            except KeyError:
                continue