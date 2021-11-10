import requests
import os
import json


def get_tag(url, update_type, git_auth):
    headers = {
        'Authorization': git_auth
    }
    print(url)
    release_response = requests.request("GET", url, headers=headers, data={})
    print(release_response.json())
    response_json = release_response.json()[0]
    last_tag = response_json["tag_name"]
    print(f'last_tag: {last_tag}')
    last_tag_processed = last_tag.replace("v", "").split(".")
    print(f'last_tag_processed: {last_tag_processed}')
    if update_type == "bug":
        last_tag_processed[2] = int(last_tag_processed[2]) + 1
    elif update_type == "enhancement":
        last_tag_processed[1] = int(last_tag_processed[1]) + 1
        last_tag_processed[2] = 0
    elif update_type == "major update":
        last_tag_processed[0] = int(last_tag_processed[0]) + 1
        last_tag_processed[1] = 0
        last_tag_processed[2] = 0
    new_tag = "v" + str(last_tag_processed[0]) + "." + str(last_tag_processed[1]) + "." + str(last_tag_processed[2])
    return new_tag


def create_release_draft(url, repo, tag, info, git_auth, org):
    payload = json.dumps({
        "tag_name": f"{tag}",
        "name": f"{tag}",
        "draft": True,
        "prerelease": True,
        "body": f"## What's Changed\r\n### {info['title']} \r\n{info['body']}\r\n\r\n***Full Changelog**: https://github.com/{org}/{repo}/commits/{tag}"

        })
    headers = {
        'Authorization': git_auth,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    return(response.text)



def get_pull_information(repo, git_auth, base_branch, org):
    url = f"https://api.github.com/repos/sporveien/{repo}/pulls?state=closed&base={base_branch}"
    headers = {
        'Authorization': git_auth
    }
    pull_response = requests.request("GET", url, headers=headers, data={})
    data_json = pull_response.json()[0]
    title = data_json['title']
    body = data_json['body']
    update_type = ""
    for label in data_json['labels']:
        if label['name'] == "bug":
            update_type = "bug"
        elif label['name'] == "enhancement":
            update_type = "enhancement"
        elif label['name'] == "major update":
            update_type = "major update"
    info = {
        "title": title,
        "body": body,
        "update_type": update_type
    }
    return(info)



def create_release(repository, release_url, git_auth, base_branch):
    info = get_pull_information(repository, git_auth, base_branch, org)
    tag = get_tag(release_url, info['update_type'], git_auth)
    print(tag)
    print(info)
    create_release_draft(release_url, repository, tag, info, git_auth, org)


try:
    print(os.environ)
    git_auth = os.environ['GITHUB_AUTH']
    base_branch = os.environ['BASE_BRANCH']
    repository = os.environ['CIRCLE_PROJECT_REPONAME']
    org = os.environ['CIRCLE_PROJECT_USERNAME']
    release_url = f"https://api.github.com/repos/{org}/{repository}/releases" 

    create_release(repository, release_url, git_auth, base_branch, org)

except BaseException as err:
    print(f"Unexpected {err=}, {type(err)=}")
    raise
