import requests

API_URL = "https://kit-tracker.peacemosquitto.workers.dev"
API_TOKEN = "63T-nAch05-p3W5-lIn60t"

headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

def fetch_device_data():
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("GPS:", data.get("gps"))
        print("Battery:", data.get("battery"))
        print("Image URL:", data.get("image"))
        return data
    else:
        print("Error:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    fetch_device_data()
