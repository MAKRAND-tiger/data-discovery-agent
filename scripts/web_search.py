"""Web search through the Tiger AI Gateway (Step 2b of the data-discovery skill).

Standard library only. Usage:
    python scripts/web_search.py "<query>"

Reads ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN from the environment, or from a .env
file in the project root if the variables are not already set. WEB_SEARCH_MODEL selects
the model (default: gemini-3.8-flash). Prints the answer, then the citation URLs the
gateway returned. The token and the full request are never printed.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "gemini-3.8-flash"
TIMEOUT_S = 90


def load_dotenv(path: Path) -> None:
    """Fill in variables that are not already set from a simple KEY=VALUE .env file."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def endpoint(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):  # the gateway base URL must not carry /v1; add it exactly once here
        base = base[: -len("/v1")]
    return f"{base}/v1/chat/completions"


def citation_urls(data: dict) -> list[str]:
    """Collect citation URLs the gateway returned in structured form (never scraped from prose)."""
    urls: list[str] = []

    def add(value):
        if isinstance(value, str) and value.startswith("https://") and value not in urls:
            urls.append(value)

    for item in data.get("citations") or []:
        add(item if isinstance(item, str) else (item or {}).get("url"))
    for result in data.get("search_results") or []:
        add((result or {}).get("url"))
    for choice in data.get("choices") or []:
        message = (choice or {}).get("message") or {}
        for ann in message.get("annotations") or []:
            add(((ann or {}).get("url_citation") or {}).get("url"))
    return urls


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].strip():
        print('usage: python scripts/web_search.py "<query>"', file=sys.stderr)
        return 2
    query = argv[1].strip()

    load_dotenv(ROOT / ".env")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    if not base_url:
        fail("Missing ANTHROPIC_BASE_URL (set it in the environment or in .env).")
    if not token:
        fail("Missing ANTHROPIC_AUTH_TOKEN (set it in the environment or in .env).")
    model = os.environ.get("WEB_SEARCH_MODEL", "").strip() or DEFAULT_MODEL

    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }).encode("utf-8")
    request = urllib.request.Request(
        endpoint(base_url),
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )

    def redact(text: str) -> str:
        return text.replace(token, "[REDACTED]")

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        fail(f"Gateway returned HTTP {exc.code} {exc.reason} for model {model!r}.")
    except urllib.error.URLError as exc:
        fail(redact(f"Could not reach the gateway: {exc.reason}"))
    except (TimeoutError, json.JSONDecodeError) as exc:
        fail(redact(f"Gateway call failed: {type(exc).__name__}"))

    try:
        answer = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        fail("Gateway response had no answer text.")

    print(redact(answer.strip()))
    urls = citation_urls(data)
    print("\nCitations:" if urls else "\nCitations: none returned by the gateway.")
    for url in urls:
        print(f"- {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
