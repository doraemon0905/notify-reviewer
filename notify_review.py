from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os
import requests
import re
import logging
# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
USER_ID = os.getenv("USER_ID")

client = WebClient(token=BOT_TOKEN)
logger = logging.getLogger(__name__)

# Mapping external ID to reviewer
EXTERNAL_ID_MAP = {
    "@squad-konohagakure": "SQ0AW4MST",
    "@squad-eternals": "S06DU7PTYLW",
    "@squad-alchemist": "S07EBNZ4PRB",
    "@squad-titans": "S07H0R5EUH0",
    "@squad-helios": "S01T1977RBK",
    "@squad-jokers": "SPQHMGGRF",
    "@squad-asgardians": "SPY1HGKN0",
    "@squad-double-espresso": "S02CKDU0XGF",
    "@squad-platform": "SESGW2A5A",
    "@squad-apollo": "S06R3DUBRT4",
    "@squad-azem": "S074RPT07AA",
    "@squad-hatha": "S032MQJ3MJ5",
    "@squad-architects": "S03C13KS6GY",
    "@ai-hero-bot": "S06N42PMKEF",
    "@squad-ada": "S06EPL3UE8Y",
    "@squad-alpaca": "S04932DNQNA",
    "@squad-andromeda": "S01EL311C1W",
    "@squad-august": "S02EB5MU2PL",
    "@squad-autobot": "SPM19LF8B",
    "@squad-banh-mi": "S02DQS49Z40",
    "@squad-decepticon": "S05ST2MAC84",
    "@squad-dragonx": "S06E1954ZFY",
    "@squad-dynamos": "S075D609A57",
    "@squad-entropy": "S05LZGTM75E",
    "@squad-eagles": "S07FKGJL8NM",
    "@squad-elysium": "S04564E081G",
    "@squad-enigma": "S061H1FTY2Y",
    "@squad-expendables": "S0619S440TA",
    "@squad-saitama": "S077GBH64FL",
    "@engineering-managers": "S05FPFUQKK6",
}

def convert_reviewers_to_subteam_format(reviewers):
    subteams = []
    for reviewer in reviewers.split(", "):
        external_id = EXTERNAL_ID_MAP.get(reviewer.strip())
        if external_id:
            subteams.append(f"<!subteam^{external_id}>")
        else:
            subteams.append(reviewer)
    return " ".join(subteams)

def send_to_slack(title, reviewers, pr_url, email):
    formatted_reviewers = convert_reviewers_to_subteam_format(reviewers)

    message = f"Hi team, please help <@{USER_ID}> review this PR {pr_url} \nSummary: {title} \ncc {formatted_reviewers}"

    if not CHANNEL_ID:
        raise ValueError("Invalid CHANNEL_ID.")
    
    if not BOT_TOKEN:
        raise ValueError("Invalid BOT_TOKEN.")
    
    if not USER_ID:
        raise ValueError("Invalid USER_ID.")
    try:
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel=CHANNEL_ID, 
            text=message,
        )
        logger.info(result)

    except SlackApiError as e:
        logger.error(f"Error posting message: {e}")

def get_user_email(user_login):
    user_url = f"https://api.github.com/users/{user_login}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    user_response = requests.get(user_url, headers=headers).json()
    email = user_response.get('email', 'No public email')

    return email

def contains_reviewer(reviewers, reviewer_to_check):
    return reviewer_to_check in reviewers

def get_pr_details(pr_url):
    if not GITHUB_TOKEN:
        raise ValueError("Invalid GITHUB_TOKEN.")
    
    match = re.match(r'https://github.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError("Invalid GitHub Pull Request URL format.")
    organization = match.group(1)
    repo = match.group(2)
    pr_number = match.group(3)
    pr_api_url = f"https://api.github.com/repos/{organization}/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    response = requests.get(pr_api_url, headers=headers).json()
    state = response.get('state')
    if state != 'open':
        raise ValueError("Pull Request is not open.")

    title = response.get('title', 'No title')

    reviewers = [f"@{team['name']}" for team in response.get('requested_teams', [])]
    reviewers = ", ".join(reviewers)

    if not contains_reviewer(reviewers, "@squad-eternals"):
        reviewers += ", @squad-eternals"
    if not contains_reviewer(reviewers, "@squad-alchemist"):
        reviewers += ", @squad-alchemist"

    external_reviewers = input(f"We already requested review to {reviewers}. Do you want to add any external reviewers (comma-separated)? ")
    if external_reviewers:
        external_reviewers = ", ".join([f"@{reviewer.strip()}" for reviewer in external_reviewers.split(",")])
        reviewers += f", {external_reviewers}"

    user_login = response['user']['login']

    email = get_user_email(user_login)

    send_to_slack(title, reviewers, pr_url, email)

def main():
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
