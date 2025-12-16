import requests


# CONFIG_STORE_BASE_URL = settings.CONFIG_STORE_BASE_URL
# CONFIG_STORE_API_KEY = settings.CONFIG_STORE_API_KEY

CONFIG_STORE_BASE_URL = "https://config-store.zagent.dev.yavar.ai"
CONFIG_STORE_API_KEY = "891f41ee454479c49e458c4a7c50dd1e"

URL=f"{CONFIG_STORE_BASE_URL}/api/v1/configs"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": CONFIG_STORE_API_KEY
}

def get_users():
    response = requests.get(f"{URL}/users", headers=HEADERS)
    response.raise_for_status()
    users = response.json().get("data", [])
    return users

def get_chatbots():
    response = requests.get(f"{URL}/chatbots", headers=HEADERS)
    response.raise_for_status()
    chatbots = response.json().get("data", [])
    return chatbots


def get_settings():
    response = requests.get(f"{URL}/settings", headers=HEADERS)
    response.raise_for_status()
    settings = response.json().get("data", [])
    return settings

def get_record_by_id(table_name: str, record_id: str):
    try:
        response = requests.get(
            f"{URL}/{table_name}/{record_id}",
            headers=HEADERS
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}) or {}
    except Exception as e:
        print(f"Error fetching record {record_id} from {table_name}: {e}")
        return {}


def query_records(table_name: str, field_name: str, field_value: str) -> list[dict]:
    response = requests.get(f"{URL}/{table_name}/query/{field_name}/{field_value}", headers=HEADERS)
    response.raise_for_status()
    data = response.json().get("data", [])
    return data