# query format - "v#.#.#
# data format (int, int, int)
# Example data
# {
#   "url": "https://api.github.com/repos/jaylinwylie/sbv2txt/releases/233763552",
#   "assets_url": "https://api.github.com/repos/jaylinwylie/sbv2txt/releases/233763552/assets",
#   "upload_url": "https://uploads.github.com/repos/jaylinwylie/sbv2txt/releases/233763552/assets{?name,label}",
#   "html_url": "https://github.com/jaylinwylie/sbv2txt/releases/tag/v1.0.1",
#   "id": 233763552,
#   "author": {
#     "login": "jaylinwylie",
#     "id": 79897627,
#     "node_id": "MDQ6VXNlcjc5ODk3NjI3",
#     "avatar_url": "https://avatars.githubusercontent.com/u/79897627?v=4",
#     "gravatar_id": "",
#     "url": "https://api.github.com/users/jaylinwylie",
#     "html_url": "https://github.com/jaylinwylie",
#     "followers_url": "https://api.github.com/users/jaylinwylie/followers",
#     "following_url": "https://api.github.com/users/jaylinwylie/following{/other_user}",
#     "gists_url": "https://api.github.com/users/jaylinwylie/gists{/gist_id}",
#     "starred_url": "https://api.github.com/users/jaylinwylie/starred{/owner}{/repo}",
#     "subscriptions_url": "https://api.github.com/users/jaylinwylie/subscriptions",
#     "organizations_url": "https://api.github.com/users/jaylinwylie/orgs",
#     "repos_url": "https://api.github.com/users/jaylinwylie/repos",
#     "events_url": "https://api.github.com/users/jaylinwylie/events{/privacy}",
#     "received_events_url": "https://api.github.com/users/jaylinwylie/received_events",
#     "type": "User",
#     "user_view_type": "public",
#     "site_admin": false
#   },
#   "node_id": "RE_kwDOPPkFys4N7vLg",
#   "tag_name": "v1.0.1",
#   "target_commitish": "master",
#   "name": "sbv2txt-windows-1.0.1",
#   "draft": false,
#   "immutable": false,
#   "prerelease": false,
#   "created_at": "2025-07-20T17:00:51Z",
#   "published_at": "2025-07-20T17:15:25Z",
#   "assets": [
#     {
#       "url": "https://api.github.com/repos/jaylinwylie/sbv2txt/releases/assets/274660631",
#       "id": 274660631,
#       "node_id": "RA_kwDOPPkFys4QXv0X",
#       "name": "sbv2txt-windows-1.0.1.zip",
#       "label": null,
#       "uploader": {
#         "login": "jaylinwylie",
#         "id": 79897627,
#         "node_id": "MDQ6VXNlcjc5ODk3NjI3",
#         "avatar_url": "https://avatars.githubusercontent.com/u/79897627?v=4",
#         "gravatar_id": "",
#         "url": "https://api.github.com/users/jaylinwylie",
#         "html_url": "https://github.com/jaylinwylie",
#         "followers_url": "https://api.github.com/users/jaylinwylie/followers",
#         "following_url": "https://api.github.com/users/jaylinwylie/following{/other_user}",
#         "gists_url": "https://api.github.com/users/jaylinwylie/gists{/gist_id}",
#         "starred_url": "https://api.github.com/users/jaylinwylie/starred{/owner}{/repo}",
#         "subscriptions_url": "https://api.github.com/users/jaylinwylie/subscriptions",
#         "organizations_url": "https://api.github.com/users/jaylinwylie/orgs",
#         "repos_url": "https://api.github.com/users/jaylinwylie/repos",
#         "events_url": "https://api.github.com/users/jaylinwylie/events{/privacy}",
#         "received_events_url": "https://api.github.com/users/jaylinwylie/received_events",
#         "type": "User",
#         "user_view_type": "public",
#         "site_admin": false
#       },
#       "content_type": "application/x-zip-compressed",
#       "state": "uploaded",
#       "size": 7062221,
#       "digest": "sha256:361991b740057fcba94088e3e8a941d85dd5185029378629e2d3d3473765bbc3",
#       "download_count": 0,
#       "created_at": "2025-07-20T17:15:17Z",
#       "updated_at": "2025-07-20T17:15:19Z",
#       "browser_download_url": "https://github.com/jaylinwylie/sbv2txt/releases/download/v1.0.1/sbv2txt-windows-1.0.1.zip"
#     }
#   ],
#   "tarball_url": "https://api.github.com/repos/jaylinwylie/sbv2txt/tarball/v1.0.1",
#   "zipball_url": "https://api.github.com/repos/jaylinwylie/sbv2txt/zipball/v1.0.1",
#   "body": "**Full Changelog**: https://github.com/jaylinwylie/sbv2txt/compare/v1.0.0...v1.0.1"
# }

import requests

USER = "jaylinwylie"
REPO = "sbv2txt"

VERSION = "v1.0.0"
DOWNLOAD_LINK = "https://github.com/jaylinwylie/sbv2txt/releases"


def to_version(tag: str) -> tuple[int, ...]:
    return tuple(map(int, tag[1:].split(".")))


def is_newer_version(current: tuple, latest: tuple):
    for i in range(3):
        if current[i] < latest[i]:
            return True
        elif current[i] > latest[i]:
            return False
    return False


def query_latest(user, repo):
    try:
        url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
        response = requests.get(url, timeout=10)  # Add timeout to prevent hanging

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to query latest version: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error when checking for updates: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error when checking for updates: {e}")
        return None

