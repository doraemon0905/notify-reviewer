import os
import re
import requests
import base64
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Initialize Slack client and logger
client = WebClient(token=BOT_TOKEN)
logger = logging.getLogger(__name__)

SPECIFIC_CASES = {
    "@ai-hero-bot": "S06N42PMKEF"  # Example: Slack ID for @ai-hero-bot is hardcoded to "ABC"
}


def validate_env_vars():
    if not GITHUB_TOKEN:
        raise ValueError("Invalid GITHUB_TOKEN.")
    if not BOT_TOKEN:
        raise ValueError("Invalid BOT_TOKEN.")
    if not CHANNEL_ID:
        raise ValueError("Invalid CHANNEL_ID.")


def make_github_request(url):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error fetching data from GitHub: {response.status_code}")
        return {}


def convert_reviewers_to_subteam_format(reviewers, usergroup_map):
    subteams = []
    for reviewer in reviewers.split(", "):
        external_id = SPECIFIC_CASES.get(reviewer, usergroup_map.get(reviewer.strip()))
        subteams.append(f"<!subteam^{external_id}>" if external_id else reviewer)
    return " ".join(subteams)


def find_user_id_by_email(email):
    try:
        result = client.users_lookupByEmail(email=email)
        return result["user"]["id"]
    except SlackApiError as e:
        logger.error(f"Error looking up user: {e}")


def send_to_slack(title, reviewers, pr_url, email, usergroup_map):
    user_id = find_user_id_by_email(email) if email else ""
    formatted_reviewers = convert_reviewers_to_subteam_format(reviewers, usergroup_map)
    message = f"Hi team, please help {'<@' + user_id + '> ' if user_id else ''}review this PR {pr_url} \nSummary: {title} \ncc {formatted_reviewers}"

    try:
        result = client.chat_postMessage(channel=CHANNEL_ID, text=message)
        logger.info(result)
    except SlackApiError as e:
        logger.error(f"Error posting message: {e}")


def get_user_email(user_login):
    user_url = f"https://api.github.com/users/{user_login}"
    user_response = make_github_request(user_url)
    return user_response.get("email", "No public email")


def get_changed_files(repo_owner, repo_name, pr_number):
    pr_files_url = (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
    )
    return make_github_request(pr_files_url)


def get_codeowners(repo_owner, repo_name):
    codeowners_url = (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/CODEOWNERS"
    )
    response = make_github_request(codeowners_url)
    content = response.get("content", "")
    return base64.b64decode(content).decode("utf-8") if content else ""


def parse_codeowners(content):
    codeowners = {}
    for line in content.splitlines():
        if line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                file_path = parts[0]
                owners = [owner.replace("@Thinkei/", "") for owner in parts[1:]]
                codeowners[file_path] = owners
    return codeowners


def match_files_to_owners(changed_files, codeowners):
    file_owners = {}
    for file_info in changed_files:
        filename = file_info["filename"]
        if filename == "CODEOWNERS" or filename.startswith("db/"):
            file_owners[filename] = ["squad-eternals"]
        else:
            file_owners[filename] = codeowners.get(filename, [])
    return file_owners


def get_reviewers_ats(repo_owner, repo_name, pr_number):
    changed_files = get_changed_files(repo_owner, repo_name, pr_number)
    codeowners_content = get_codeowners(repo_owner, repo_name)
    codeowners = parse_codeowners(codeowners_content)
    file_owners = match_files_to_owners(changed_files, codeowners)

    pr_owners = {f"@{owner}" for owners in file_owners.values() for owner in owners}
    return ", ".join(pr_owners)


def contains_reviewer(reviewers, reviewer_to_check):
    return reviewer_to_check in reviewers


def get_pr_details(pr_url):
    match = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError("Invalid GitHub Pull Request URL format.")
    organization, repo, pr_number = match.groups()
    pr_api_url = f"https://api.github.com/repos/{organization}/{repo}/pulls/{pr_number}"
    response = make_github_request(pr_api_url)

    title = response.get("title", "No title")
    reviewers = (
        get_reviewers_ats(organization, repo, pr_number)
        if repo == "ats" 
        else ", ".join(
            [f"@{team['name']}" for team in response.get("requested_teams", [])]
        )
    )

    if not contains_reviewer(reviewers, "@squad-eternals"):
        reviewers += ", @squad-eternals"

    external_reviewers = input(f"We already requested review to {reviewers}. Do you want to add any external reviewers (comma-separated)? ")
    if external_reviewers:
        reviewers += ", " + ", ".join(
            [f"@{reviewer.strip()}" for reviewer in external_reviewers.split(",")]
        )

    user_login = response["user"]["login"]
    email = get_user_email(user_login)
    usergroup_map = get_slack_usergroups()

    send_to_slack(title, reviewers, pr_url, email, usergroup_map)

def get_slack_usergroups():
    try:
        result = client.usergroups_list()
        return {f"@{ug['handle']}": ug["id"] for ug in result["usergroups"]}
    except SlackApiError as e:
        logger.error(f"Error fetching Slack user groups: {e}")
        return {}

def main():
    validate_env_vars()
    pr_url = input("Enter the Pull Request URL: ")

    if re.match(r"^https://github.com/[^/]+/[^/]+/pull/\d+$", pr_url):
        print("Processing Pull Request...")
        get_pr_details(pr_url)
        print("Notification sent to Slack!")
    else:
        print("Invalid Pull Request URL. Please provide a valid GitHub PR URL.")
        exit(1)
if __name__ == "__main__":
    main()
