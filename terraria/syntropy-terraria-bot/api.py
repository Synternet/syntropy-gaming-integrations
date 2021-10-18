import syntropy_sdk
import datetime
from pprint import pprint
from syntropy_sdk.rest import ApiException

"""
Patches syntropy-sdk 0.3.0
"""
def patched_agent_provider_icon_url(self, agent_provider_icon_url):
    self._agent_provider_icon_url = agent_provider_icon_url

def patched_agent_provider_id(self, agent_provider_id):
    self._agent_provider_id = agent_provider_id

def patched_agent_connection_subnet_error(self, agent_connection_subnet_error):
    self._agent_connection_subnet_error = agent_connection_subnet_error

def patched_agent_provider(self, agent_provider):
    self._agent_provider = agent_provider

def patched_agent_type(self, agent_type):
    self._agent_type = agent_type

syntropy_sdk.AgentProviderObject.agent_provider_icon_url = patched_agent_provider_icon_url
syntropy_sdk.AgentConnGroupAgentObject.agent_provider_id = patched_agent_provider_id
syntropy_sdk.TsoaPickAgentConnectionSubnetOrAgentConnectionSubnetIdOrAgentServiceSubnetIdOrAgentConnectionSubnetIsEnabledOrAgentConnectionSubnetErrorOrAgentConnectionSubnetStatus_.agent_connection_subnet_error = patched_agent_connection_subnet_error
syntropy_sdk.AgentFoundAndCountObject.agent_provider = patched_agent_provider
syntropy_sdk.AgentConnectionWithServicesAgent.agent_type = patched_agent_type

def get_configuration(api_key=""):
    config = syntropy_sdk.Configuration()
    config.host = "https://controller-prod-server.syntropystack.com"
    if api_key != "":
        config.api_key["Authorization"] = api_key
    return config


def get_date_after_years(years):
    delta = datetime.timedelta(days=5 * 365)
    return (datetime.datetime.utcnow() + delta).isoformat() + "Z"

class ApiManager:
    def __init__(self, access_token):
        api = syntropy_sdk.ApiClient(get_configuration())
        self.platform_api_auth = syntropy_sdk.AuthApi(api)
        self.login(access_token)

    def login(self, access_token):
        # Login
        login_body = syntropy_sdk.AccessTokenData(access_token)
        api_response = self.platform_api_auth.auth_access_token_login(login_body)
        config = get_configuration(api_response.access_token)
        # Api objects
        api = syntropy_sdk.ApiClient(config)
        self.platform_api_keys = syntropy_sdk.APIKeysApi(api)
        self.platform_api_auth = syntropy_sdk.AuthApi(api)
        self.platform_api_agents = syntropy_sdk.AgentsApi(api)
        self.platform_api_connections = syntropy_sdk.ConnectionsApi(api)
        self.platform_api_services = syntropy_sdk.ServicesApi(api)

    def get_or_create_api_key(self, name):
        get_api_key_response = self.platform_api_keys.get_api_key(
            filter="api_key_name:{0}".format(name)
        )

        data = get_api_key_response.data
        
        if len(data) > 0:
           return -1

        body = {
            "api_key_name": name,
            "api_key_valid_until": get_date_after_years(5),
        }
        create_api_key_response = self.platform_api_keys.create_api_key(body)
        return create_api_key_response.data
        
    def get_endpoints(self, name):
        endpoints = self.platform_api_agents.platform_agent_index(filter="name:{0}".format(name))
        return endpoints.data

    def filter_connections_by_agent_pairs(self, connections, agent_pairs, game_server_agent_id):
        connection_ids = {}
        for agent_pair in agent_pairs:
            for connection in connections:
                if ((connection.agent_1.agent_id == agent_pair.agent_1_id and connection.agent_2.agent_id == agent_pair.agent_2_id) or
                    (connection.agent_1.agent_id == agent_pair.agent_2_id and connection.agent_2.agent_id == agent_pair.agent_1_id)):
                    connection_ids[agent_pair.agent_2_id if agent_pair.agent_1_id == game_server_agent_id else agent_pair.agent_1_id] = connection.agent_connection_group_id
        return connection_ids

    def remove_all_connections(self, agent_id):
        connection_groups = self.platform_api_connections.platform_connection_groups_index().data
        connections_to_delete = []
        for connection in connection_groups:
            if (connection.agent_1.agent_id == agent_id or connection.agent_2.agent_id == agent_id):
                connections_to_delete.append(syntropy_sdk.AgentConnectionGroupIdObject(connection.agent_connection_group_id))
        self.platform_api_connections.platform_connection_groups_destroy(connections_to_delete)

    def add_connections(self, connections, game_server_agent_id):
        body = syntropy_sdk.ConnectionCreationBodyP2p(connections, False)
        self.platform_api_connections.platform_connection_create_p2p(body)
        connection_groups = self.platform_api_connections.platform_connection_groups_index().data
        return self.filter_connections_by_agent_pairs(connection_groups, connections, game_server_agent_id)

    def get_services(self, connection_group_ids):
        return self.platform_api_services.platform_connection_service_show(connection_group_ids).data

    def enable_service(self, connection_id, service_id):
        body = {
            "connectionGroupId": connection_id,
            "changes": [
                {
                    "isEnabled": True,
                    "agentServiceSubnetId": service_id
                } 
            ]
        } 

        self.platform_api_services.platform_connection_service_update(body)