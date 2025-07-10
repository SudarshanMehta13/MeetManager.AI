import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BITBUCKET_USERNAME = os.getenv('BITBUCKET_USERNAME')
BITBUCKET_APP_PASSWORD = os.getenv('BITBUCKET_APP_PASSWORD')
BITBUCKET_BASE_URL = os.getenv('BITBUCKET_BASE_URL')
BITBUCKET_PROJECT_KEY = os.getenv('BITBUCKET_PROJECT_KEY')
BITBUCKET_REPO_SLUG = os.getenv('BITBUCKET_REPO_SLUG')

BITBUCKET_API_URL = f"{BITBUCKET_BASE_URL}/rest/api/1.0/projects/{BITBUCKET_PROJECT_KEY}/repos/{BITBUCKET_REPO_SLUG}/pull-requests"
BITBUCKET_PR_URL_TEMPLATE = f"{BITBUCKET_BASE_URL}/projects/{BITBUCKET_PROJECT_KEY}/repos/{BITBUCKET_REPO_SLUG}/pull-requests/{{}}/overview"

def fetch_pull_requests(state=None):
    params = {}
    if state:
        params['state'] = state

    try:
        response = requests.get(BITBUCKET_API_URL, params=params, auth=HTTPBasicAuth(BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pull requests: {e}")
        return None

def filter_prs_by_user(pull_requests, user_id):
    return [pr for pr in pull_requests.get('values', []) if pr['author']['user']['name'] == user_id]

def fetch_open_pull_requests_for_user(user_id):
    open_prs = fetch_pull_requests(state='OPEN')
    if open_prs:
        return filter_prs_by_user(open_prs, user_id)
    return None

def fetch_merged_pull_requests_for_user(user_id):
    merged_prs = fetch_pull_requests(state='MERGED')
    if merged_prs:
        return filter_prs_by_user(merged_prs, user_id)
    return None