import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("JENKINS_URL", "").rstrip("/")
username = os.getenv("JENKINS_USER")
token = os.getenv("JENKINS_API_TOKEN")
job = os.getenv("JENKINS_JOB_NAME")

if not all([url, username, token, job]):
    raise SystemExit("ERROR: Check your .env settings.")

try:
    response = requests.post(
        f"{url}/job/{job}/build",
        auth=(username, token),
        timeout=15
    )

    print("HTTP status:", response.status_code)

    if response.status_code in (200, 201, 202):
        print("Jenkins job triggered successfully!")
    elif response.status_code == 403:
        print("Permission denied. Check Jenkins job permissions and CSRF settings.")
    elif response.status_code == 404:
        print("Job not found. Check JENKINS_JOB_NAME.")
    else:
        print("Trigger failed:", response.text[:300])

except requests.RequestException as error:
    print("Connection error:", error)