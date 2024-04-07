from api.github_helper.utils import get_diff_text
from api.github_helper.installation import get_installation_access_token
from cloudcode.actions.reviews import CodeReviewer
import requests
import logging
from api.github_helper.permissions import PULL_REQUEST_PERMISSION
import os

logger = logging.getLogger(__name__)

GITHUB_API_BASE_URL = os.environ["GITHUB_API_BASE_URL"]

ACTIONS_TO_PROCESS_PR = ["review_requested", "ready_for_review"]
ACTIONS_TO_UPDATE_DESC = ["opened", "reopened"]


def process_pull_request(payload):
    comment_url = payload["pull_request"]["comments_url"]
    repo_name = payload["repository"]["full_name"]
    pull_number = payload["pull_request"]["number"]
    diff_url = GITHUB_API_BASE_URL + f"/repos/{repo_name}/pulls/{pull_number}.diff"
    installation_id = payload["installation"]["id"]
    pr_title = payload["pull_request"]["title"]
    pr_description = payload["pull_request"]["body"]

    access_token = get_installation_access_token(
        installation_id, PULL_REQUEST_PERMISSION
    )
    diff_text = get_diff_text(diff_url, access_token)
    reviewer = CodeReviewer()
    review_body = reviewer.review_pull_request(
        diff_text=diff_text,
        pull_request_title=pr_title,
        pull_request_desc=pr_description,
        user=repo_name,
    )
    access_token = get_installation_access_token(
        installation_id, PULL_REQUEST_PERMISSION
    )
    post_pull_request(comment_url, review_body, access_token)


def process_pr_desc(payload):
    pr_url = payload["pull_request"]["url"]
    repo_name = payload["repository"]["full_name"]
    pull_number = payload["pull_request"]["number"]
    diff_url = GITHUB_API_BASE_URL + f"/repos/{repo_name}/pulls/{pull_number}.diff"
    installation_id = payload["installation"]["id"]
    pr_title = payload["pull_request"]["title"]
    pr_description = payload["pull_request"]["body"]

    access_token = get_installation_access_token(
        installation_id, PULL_REQUEST_PERMISSION
    )
    diff_text = get_diff_text(diff_url, access_token)
    reviewer = CodeReviewer()
    desc = reviewer.generate_pull_request_desc(
        diff_text=diff_text,
        pull_request_title=pr_title,
        pull_request_desc=pr_description,
        user=repo_name,
    )

    access_token = get_installation_access_token(
        installation_id, PULL_REQUEST_PERMISSION
    )
    patch_pr_body(pr_url, desc, access_token)


def post_pull_request(url, data, access_token):
    data = {"body": f"{data}\n\n -- Generated by Cloud Code AI"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.post(url, headers=headers, json=data)
    logger.debug(f"Post Pull request response: {response.text}")


def patch_pr_body(url, data, access_token):
    data = {"body": data}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.patch(url, headers=headers, json=data)
    logger.debug(f"Patch Pull request response: {response.text}")
