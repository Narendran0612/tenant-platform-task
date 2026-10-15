import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("Jenkins URL:", os.getenv("JENKINS_URL"))
print("Username configured:", bool(os.getenv("JENKINS_USER")))

url = os.getenv("JENKINS_URL")
username = os.getenv("JENKINS_USER")
token = os.getenv("JENKINS_API_TOKEN")

response = requests.get(
    f"{url}/api/json",
    auth=(username, token),
    timeout=10
)

print("Status code:", response.status_code)

if response.status_code == 200:
    print("Jenkins API connection successful!")
else:
    print("Connection failed. Check your URL and credentials.")