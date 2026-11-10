"""Licence and structured-metadata extraction from dataset landing pages."""
from __future__ import annotations

import json
import re


def jsonld_datasets(html: str) -> list[dict]:
    """Return every schema.org Dataset object embedded as JSON-LD in a page.

    Many portals (Kaggle, Zenodo, data.gov, Hugging Face, Dataverse, CKAN sites) embed one.
    It is the most reliable machine-readable description of a dataset when it exists.
    """
    found = []
    for m in re.finditer(r"""(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>""", html):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and "Dataset" in str(item.get("@type", "")):
                found.append(item)
    return found


def summarise_jsonld_dataset(d: dict) -> dict:
    """Keep the fields that matter for discovery, clipped for the model."""
    def name_of(v):
        if isinstance(v, list):
            return [name_of(x) for x in v][:5]
        if isinstance(v, dict):
            return v.get("name") or v.get("url") or v.get("@id")
        return v

    def clip(v, n=600):
        v = re.sub(r"<[^>]+>", " ", str(v)) if v is not None else None
        return None if v is None else (" ".join(v.split())[:n])

    dist = d.get("distribution") or []
    dist = dist if isinstance(dist, list) else [dist]
    return {
        "name": d.get("name"), "description": clip(d.get("description")),
        "license": d.get("license"), "creator": name_of(d.get("creator")), "publisher": name_of(d.get("publisher")),
        "datePublished": d.get("datePublished"), "dateModified": d.get("dateModified"),
        "temporalCoverage": d.get("temporalCoverage"), "spatialCoverage": name_of(d.get("spatialCoverage")),
        "isAccessibleForFree": d.get("isAccessibleForFree"), "keywords": clip(d.get("keywords"), 300),
        "variableMeasured": name_of(d.get("variableMeasured")),
        "distribution": [{k: x.get(k) for k in ("contentUrl", "encodingFormat", "fileFormat", "contentSize", "requiresSubscription", "name")
                          if isinstance(x, dict) and x.get(k) is not None} for x in dist[:10]],
    }


# ---------------------------------------------------------------------------
# LEARNER TODO (G1): find the licence of ANY dataset from its landing page
# ---------------------------------------------------------------------------
# Without this, every dataset link ends up LIC-UNKNOWN (a blocker) and verdicts are wrong.
#
# Contract (tests/test_learner_gaps.py::test_g1_* checks it):
#   extract_licence(html: str, jsonld: list[dict] | None = None) -> dict with EXACTLY these keys
#     licence_name : normalised name, one of e.g. "CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC 4.0", "CC BY-NC-SA 4.0",
#                    "CC BY-ND 4.0", "CC0 1.0", "ODbL 1.0", "OGL v3.0", "MIT", "Apache-2.0"; None if not found
#                    or if the page says the licence is unknown/unspecified
#     licence_url  : the licence URL you found, or None
#     snippet      : the text or JSON-LD value you read it from (<= 400 chars), or None
#     found_in     : "json-ld" | "link" | "text" | None
#
# Order of evidence: JSON-LD "license" (string URL, or {"name", "url"}) first; then links to
# creativecommons.org / opendatacommons.org / nationalarchives.gov.uk (OGL) / choosealicense.com;
# then sentences such as "licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license".
# jsonld defaults to jsonld_datasets(html) when None. Never guess: return None values when unsure.
_EMPTY = {"licence_name": None, "licence_url": None, "snippet": None, "found_in": None}
_SNIPPET_MAX = 400
_UNKNOWN_WORDS = {"", "unknown", "unspecified", "none", "null", "not specified", "n/a", "other"}
_LICENCE_HOSTS = ("creativecommons.org", "opendatacommons.org", "nationalarchives.gov.uk", "choosealicense.com")


def _from_url(url: str) -> str | None:
    """Canonical licence name from a licence URL (most reliable text source), or None."""
    u = (url or "").lower()
    m = re.search(r"creativecommons\.org/licenses/((?:by)(?:-nc)?(?:-sa)?(?:-nd)?)/(\d\.\d)", u)
    if m:
        return _cc_name(m.group(1), m.group(2))
    if re.search(r"creativecommons\.org/publicdomain/zero/1\.0", u):
        return "CC0 1.0"
    if "opendatacommons.org/licenses/odbl" in u:
        return "ODbL 1.0"
    m = re.search(r"nationalarchives\.gov\.uk/doc/open-government-licen[cs]e/version/(\d)", u)
    if m:
        return f"OGL v{m.group(1)}.0"
    m = re.search(r"choosealicense\.com/licenses/([a-z0-9.\-]+)", u)
    if m:
        slug = m.group(1).strip("/")
        return {"cc0-1.0": "CC0 1.0", "mit": "MIT", "apache-2.0": "Apache-2.0"}.get(slug)
    return None


def _cc_name(parts: str, version: str) -> str:
    """'by-nc-sa' + '4.0' -> 'CC BY-NC-SA 4.0'."""
    return "CC " + parts.upper() + " " + version


def _from_text(text: str) -> str | None:
    """Canonical licence name from licence wording, or None. Only the names the pipeline knows."""
    t = " ".join((text or "").split())
    # Abbreviated Creative Commons: "CC BY-NC-SA 4.0", "CC BY 4.0"
    m = re.search(r"\bCC[ -]?(BY(?:[- ](?:NC|SA|ND))*)\s*(\d\.\d)", t, re.I)
    if m:
        parts = re.sub(r"[ ]", "-", m.group(1).lower())
        return _cc_name(parts, m.group(2))
    # Long form: "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International"
    m = re.search(r"creative commons\s+(attribution|zero)([^.()]{0,60}?)(\d\.\d)", t, re.I)
    if m:
        if m.group(1).lower() == "zero":
            return "CC0 1.0"
        extra = m.group(2).lower()
        suffix = ("-nc" if "noncommercial" in extra else "") + ("-sa" if "sharealike" in extra else "") \
            + ("-nd" if "noderiv" in extra else "")
        return _cc_name("by" + suffix, m.group(3))
    if re.search(r"\bCC0\b", t):
        return "CC0 1.0"
    if re.search(r"\bODbL\b|open database licen[cs]e", t, re.I):
        v = re.search(r"ODbL\s*(\d(?:\.\d)?)", t, re.I)
        return "ODbL " + (v.group(1) if v and "." in v.group(1) else "1.0")
    m = re.search(r"open government licen[cs]e\s*v?(\d)(?:\.(\d))?", t, re.I)
    if m:
        return f"OGL v{m.group(1)}.{m.group(2) or '0'}"
    if re.search(r"\bMIT licen[cs]e\b", t, re.I):
        return "MIT"
    if re.search(r"apache license,?\s*version 2\.0", t, re.I):
        return "Apache-2.0"
    return None


def _jsonld_licences(dataset: dict) -> list[tuple[str | None, str | None]]:
    """(name, url) pairs from a Dataset's license (or licence) property, string or object form."""
    out = []
    for key in ("license", "licence"):
        value = dataset.get(key)
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, str):
                out.append((None, item.strip() or None))
            elif isinstance(item, dict):
                url = item.get("url") or item.get("@id")
                out.append((item.get("name"), url.strip() if isinstance(url, str) else None))
    return out


def _visible_text(html: str) -> str:
    no_scripts = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", no_scripts).split())


def _context(html: str, start: int, end: int, radius: int = 160) -> str:
    return _visible_text(html[max(0, start - radius):end + radius])


def _result(name, url, snippet, found_in) -> dict:
    return {"licence_name": name, "licence_url": url,
            "snippet": snippet[:_SNIPPET_MAX] if snippet else None, "found_in": found_in}


def extract_licence(html: str, jsonld: list[dict] | None = None) -> dict:
    """Licence of a dataset landing page: JSON-LD first, then licence links, then licence sentences.

    jsonld=None means "read the JSON-LD from html"; an empty list means "the page has none".
    Returns all four keys, all None when no licence wording is found. Never guesses.
    """
    html = html or ""
    datasets = jsonld_datasets(html) if jsonld is None else jsonld

    # 1. schema.org JSON-LD. An explicit "Unknown" is a finding: no licence, not a licence name.
    for dataset in datasets:
        for raw_name, url in _jsonld_licences(dataset):
            name_text = (raw_name or "").strip()
            url = (url or "").strip() or None
            if not name_text and not url:
                continue
            snippet = f"license: {name_text or url}"
            name = _from_url(url or "") or _from_text(name_text)
            if name is None and name_text.lower() in _UNKNOWN_WORDS:
                # Kaggle-style "Unknown": the page states there is no licence. Not a licence name.
                return _result(None, url, snippet, "json-ld")
            if name is None and name_text:
                # Unrecognised but stated: keep the publisher's own words, never a guessed canonical name.
                return _result(name_text[:80], url, snippet, "json-ld")
            # Recognised by URL or by name. A bare unrecognised URL gives no name (None).
            return _result(name, url, snippet, "json-ld")

    # 2. licence links: rel="license", or a link to a known licence publisher.
    for m in re.finditer(r"(?is)<a\b([^>]*)>(.*?)</a>", html):
        attrs, inner = m.group(1), m.group(2)
        href = re.search(r"""href\s*=\s*["']([^"']+)""", attrs, re.I)
        rel = re.search(r"""rel\s*=\s*["']([^"']+)""", attrs, re.I)
        href_url = href.group(1).strip() if href else ""
        is_licence_link = bool(rel and re.search(r"licen[cs]e", rel.group(1), re.I)) or \
            any(host in href_url.lower() for host in _LICENCE_HOSTS)
        if not is_licence_link:
            continue
        name = _from_url(href_url) or _from_text(_visible_text(inner))
        if name:
            return _result(name, href_url, _context(html, m.start(), m.end()), "link")

    # 3. licence sentences in the visible text: the wording must sit near the word "licence/license/terms".
    text = _visible_text(html)
    for m in re.finditer(r"(?i)\b(?:CC\s?BY|CC0|ODbL|Open Government Licen[cs]e|Creative Commons|MIT licen[cs]e|"
                         r"Apache License)", text):
        window = text[max(0, m.start() - 120):m.end() + 120]
        if not re.search(r"(?i)licen[cs]|terms", window):
            continue
        name = _from_text(window)
        if name:
            return _result(name, None, window, "text")

    return dict(_EMPTY)
