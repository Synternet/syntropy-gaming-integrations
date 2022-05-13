from json import load
from syntropy_sdk.exceptions import ApiException
from syntropy_sdk.utils import WithRetry
import datetime
import time
import syntropy_sdk

def get_date_after_years(years):
    delta = datetime.timedelta(days=5 * 365)
    return (datetime.datetime.utcnow() + delta).isoformat() + "Z"

def get_configuration(api_key):
    config = syntropy_sdk.Configuration()
    config.api_key['Authorization'] = 'Bearer ' + api_key
    config.host = "https://api.syntropystack.com"

    return config

class ApiManager:
    def __init__(self, token):
        self.token = token
        self.api_instance = syntropy_sdk.AuthApi()
        body = syntropy_sdk.V1NetworkAuthAccessTokenLoginRequest(access_token=self.token) 
        response = self.api_instance.v1_network_auth_access_token_login(body)
        response_data = response.data.to_dict()
        self.access_token = response_data["access_token"]

        self.init_api_endpoints()

    def init_api_endpoints(self):
        self.keys_api = syntropy_sdk.AuthApi(syntropy_sdk.ApiClient(get_configuration(api_key=self.access_token)))
        self.endpoint_api = syntropy_sdk.AgentsApi(syntropy_sdk.ApiClient(get_configuration(api_key=self.access_token)))
        self.connections_api = syntropy_sdk.ConnectionsApi(syntropy_sdk.ApiClient(get_configuration(api_key=self.access_token)))

    def create_or_get_api_keys(self, name):
        body = syntropy_sdk.V1NetworkAuthApiKeysCreateRequest(
            api_key_name=name, 
            api_key_valid_until=get_date_after_years(5), 
            api_key_description = f"Minecraft client {name} connection"
        ) 
 
        try:
            response = self.keys_api.v1_network_auth_api_keys_create(body)
            secret_key = response.data.to_dict()["api_key_secret"]
            return secret_key
        except ApiException as e:
            print("Exception when calling AuthApi->v1_network_auth_api_keys_create: %s\n" % e)

    def get_endpoint_id(self, name):
        try:
            response = self.endpoint_api.v1_network_agents_get().data
            
            data = [ agents.to_dict()["agent_id"] for agents in response 
                if agents.to_dict()["agent_name"] == name]

            return data[0] if data else -1

        except ApiException as e:
            print("Exception when calling AgentsApi->v1_network_agents_get: %s\n" % e)

    def get_client_endpoint(self, name):
        try:
            notFound = True
            count = 1
            while notFound:
                data = self.get_endpoint_id(name)

                if data != -1:
                    print("Client has connected")
                    notFound = True
                    return data

                print("Waiting for client connection...")

                if count >= 3:
                    print("Client was not found...")
                    return -1

                count += 1
                time.sleep(60)
            
        except ApiException as e:
            print("Exception when calling AgentsApi->v1_network_agents_get: %s\n" % e)

    def create_p2p_connection(self, server_id, client_id):
        body = syntropy_sdk.V1NetworkConnectionsCreateP2PRequest(
            agent_pairs=[
                syntropy_sdk.V1NetworkConnectionsCreateP2PRequestAgentPairs(
                    agent_2_id=server_id, agent_1_id=client_id
                )
            ]
        )

        try:
            self.connections_api.v1_network_connections_create_p2_p(body=body, _preload_content=False)
        except ApiException as e:
            print("Exception when calling ConnectionsApi->v1_network_connections_create_p2_p: %s\n" % e)
        



