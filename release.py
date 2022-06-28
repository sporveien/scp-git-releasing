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
    if release_response.json() == []:
        print("No previous releases")
        new_tag = "v0.1.0"
    else:
        response_json = release_response.json()
        for i in response_json:
            tag_name = i["tag_name"]
            p = i["prerelease"]
            d = i["draft"]
            if not p or not d:
                last_tag = tag_name
                break
        if not last_tag:
            new_tag = "v0.1.0"
        elif last_tag[0] == "v":
            last_tag_processed = last_tag.replace("v", "").split(".")
            print(f'last_tag_processed: {last_tag_processed}')
            if update_type == "bug" or update_type == "documentation":
                last_tag_processed[2] = int(last_tag_processed[2]) + 1
            elif update_type == "enhancement":
                last_tag_processed[1] = int(last_tag_processed[1]) + 1
                last_tag_processed[2] = 0
            elif update_type == "major update":
                last_tag_processed[0] = int(last_tag_processed[0]) + 1
                last_tag_processed[1] = 0
                last_tag_processed[2] = 0
            new_tag = "v" + str(last_tag_processed[0]) + "." + str(last_tag_processed[1]) + "." + str(last_tag_processed[2])
        else:
            new_tag = "v0.1.0"
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
    url = f"https://api.github.com/repos/{org}/{repo}/pulls?state=closed&base={base_branch}"
    print(url)
    headers = {
        'Authorization': git_auth
    }
    pull_response = requests.request("GET", url, headers=headers, data={})
    print(pull_response.status_code)
    data_json = pull_response.json()[0]
    title = data_json['title']
    body = data_json['body']
    update_type = ""
    for label in data_json['labels']:
        if label['name'] == "bug":
            update_type = "bug"
        elif label['name'] == "documentation":
            update_type = "documentation"
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


def create_release(repository, release_url, git_auth, base_branch, org):
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
