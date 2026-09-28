"""
github_source.py
Wrapper around the GitHub REST API for researching repositories and extracting content.
Supports GITHUB_TOKEN for high rate limits (5000/hr) with automatic rate-limit backoff.
"""
import os
import time
import base64
import requests

API = "https://api.github.com"


def _headers():
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Hermes-Research-Loop/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url, params=None, retries=3):
    for attempt in range(retries):
        resp = requests.get(url, headers=_headers(), params=params, timeout=20)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 30))
            wait = max(reset - time.time(), 1)
            print(f"[github_source] Rate limited. Sleeping {wait:.0f}s...")
            time.sleep(min(wait, 60))
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"GitHub API failed after {retries} retries: {url}")


def search_repos(query, language=None, sort="stars", max_results=8):
    """Search repositories by topic/keyword with optional language filtering."""
    q = query
    if language:
        q += f" language:{language}"
    data = _get(f"{API}/search/repositories", {
        "q": q,
        "sort": sort,
        "order": "desc",
        "per_page": max_results,
    })
    return data.get("items", [])


def search_code(query, language=None, max_results=8):
    """Search code snippets across GitHub."""
    q = query
    if language:
        q += f" language:{language}"
    data = _get(f"{API}/search/code", {
        "q": q,
        "per_page": max_results,
    })
    return data.get("items", [])


def fetch_file(owner, repo, path, ref=None):
    """Fetch a single file's decoded text content from a repo."""
    url = f"{API}/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": ref} if ref else None
    data = _get(url, params)
    if isinstance(data, list):
        raise ValueError(f"{path} is a directory, not a file")
    content = data.get("content", "")
    encoding = data.get("encoding", "base64")
    if encoding == "base64":
        return base64.b64decode(content).decode("utf-8", errors="replace")
    return content


def list_repo_readme(owner, repo):
    """Fetch README text automatically resolving README.md / README.rst."""
    url = f"{API}/repos/{owner}/{repo}/readme"
    data = _get(url)
    content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    return content
