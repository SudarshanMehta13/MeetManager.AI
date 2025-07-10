import requests
from requests.auth import HTTPBasicAuth
import os

def trigger_jenkins_build():
    """Trigger a Jenkins build."""
    # Define the URL and endpoint
    url = "dummyURL"

    # Credentials
    username = os.getenv("jenkins_username")
    token = os.getenv("jenkins_token")

    # Data payload for the POST request
    data = {
        "DEFAULT": "release/catc313",
        "APIC_BUILD_TOOLS_BRANCH": "release/catc313"
    }

    # Make the POST request with basic authentication
    response = requests.post(url, auth=HTTPBasicAuth(username, token), data=data)

    # Check the response
    if response.status_code == 201:
        return "Build triggered successfully."
    else:
        return f"Failed to trigger build. Status code: {response.status_code}, Response: {response.text}"
