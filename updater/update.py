import os
import requests

import updater

USER_REPO = "jaylinwylie/skeincare"


def to_version(tag: str) -> tuple[int, ...]:
    return tuple(map(int, tag.replace('v', '').split(".")))


def is_newer_version(current: tuple, latest: tuple):
    for i in range(3):
        if current[i] < latest[i]:
            return True
        elif current[i] > latest[i]:
            return False
    return False


def query_latest() -> dict:
    url = f"https://api.github.com/repos/{USER_REPO}/releases/latest"
    response = requests.get(url, timeout=10)  # Add timeout to prevent hanging
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to query latest version: {response.status_code}")


def check_for_updates(skip_version: str = None) -> dict | None:
    latest = query_latest()
    latest_tag = latest['tag_name']
    
    # Skip this version if it matches the skip_version
    if skip_version and skip_version == latest_tag:
        return None
        
    if is_newer_version(to_version(updater.VERSION), to_version(latest_tag)):
        return latest
    else:
        return None
