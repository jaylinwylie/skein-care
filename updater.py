import requests
VERSION = "v1.1.0"

USER = "jaylinwylie"
REPO = "skein-care"
GITHUB_RELEASES_URL = f"https://github.com/{USER}/{REPO}/releases"
KO_FI_URL = "https://ko-fi.com/s/011d38ab3b"


def to_version(tag: str) -> tuple[int, ...]:
    """Convert a tag string to a tuple of integers. Example: "v1.2.3" -> (1, 2, 3)"""
    return tuple(map(int, tag[1:].split(".")))


def is_newer_version(current: tuple, latest: tuple):
    """Check if the current version is newer than the latest version"""
    for i in range(3):
        if current[i] < latest[i]:
            return True
        elif current[i] > latest[i]:
            return False
    return False


def query_latest(user, repo) -> tuple[bool, str | dict]:
    """Query the latest version of the app from GitHub"""
    try:
        url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
        response = requests.get(url, timeout=10)  # Add timeout to prevent hanging

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Failed to query latest version: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error when checking for updates: {e}"
    except Exception as e:
        return False, f"Unexpected error when checking for updates: {e}"
