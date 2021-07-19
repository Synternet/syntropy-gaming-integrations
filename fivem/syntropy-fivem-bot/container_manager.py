import docker
import os
class ContainerManager:
    def __init__(self, CONTAINER_NAME, NETWORK_NAME, LICENSE_KEY):
        self.CONTAINER_NAME = CONTAINER_NAME
        self.NETWORK_NAME = NETWORK_NAME
        self.LICENSE_KEY = LICENSE_KEY
        self.docker_client = docker.from_env()
        self.FIVEM_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fivem-data")
        self.number_of_players = 0
    
    def __get_container(self):
        try:
            return self.docker_client.containers.get(self.CONTAINER_NAME)
        except docker.errors.NotFound:
            return False
    def __create_data_dir(self):
        if not os.path.exists(self.FIVEM_DATA_PATH):
            os.umask(0)
            os.mkdir(self.FIVEM_DATA_PATH, 0o777)
    def __create_container(self):
        container = self.__get_container()
        if (container):
            return container
        self.__create_data_dir()
        return self.docker_client.containers.run("spritsail/fivem", 
            name=self.CONTAINER_NAME,
            network=self.NETWORK_NAME,
            detach=True,
            stdin_open=True,
            tty=True,
            volumes={self.FIVEM_DATA_PATH: {"bind":"/config", "mode":"rw"}},
            environment=["SYNTROPY_SERVICE_NAME=fivem", "LICENSE_KEY="+ self.LICENSE_KEY])
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
        container.exec_run("fivemmanager saveworld")
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
