"""Deterministic red-flag rules, run on every catalog record before the Risk Assessor agent.

Why rules and an agent? Rules are cheap, repeatable and testable, and they catch what can be
read from structured fields. The agent adds judgement flags (conflicts, consent gaps,
representativeness, ...) and may dismiss a rule flag only with a written reason, and the
orchestrator enforces that.

Each rule: (record, candidate, use_case, settings) -> list of {"code", "evidence"}.
"""
from __future__ import annotations

import re
from datetime import date

Flag = dict

GRAIN_ORDER = ["minute", "15min", "30min", "hourly", "daily", "weekly", "monthly", "quarterly", "annual"]
INACTIVE_STATUSES = {"deprecated", "archived", "frozen", "retired", "decommissioned", "superseded"}

# A negated clause ("no missing values", "without missing data") is not evidence of missing data.
_NEGATED_MISSING_RE = re.compile(
    r"\b(?:no|without|zero|free of|not contain(?:ed|s)?|does not contain|do not contain)\b(?:\s+\w+){0,3}?"
    r"\s+(?:missing|absent|absence)\b", re.I)
# Wording that says a file has missing values or uses a sentinel for them.
_MISSING_SIGNAL_RE = re.compile(
    r"missing[ -]?(?:values?|data|measurements?|entries|rows?|cells?|observations?)"
    r"|absence of (?:a )?(?:value|data)|(?<![\d.])-200(?!\d)|(?<![\d.])-999(?!\d)|\bNaN\b|\bsentinel", re.I)


def _flag(code: str, evidence: str) -> Flag:
    return {"code": code, "evidence": evidence}


def _d(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Provided rules (read these as worked examples)
# ---------------------------------------------------------------------------
def rule_licence(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal":
        return []
    lic = record.get("licence") or {}
    name = (lic.get("name") or "").strip()
    flags = []
    if not name or name.lower() in {"unknown", "none", "null", "not found", "n/a"}:
        flags.append(_flag("LIC-UNKNOWN", f"No licence established. Evidence field: {lic.get('evidence')!r}"))
    elif re.search(r"\bNC\b|non[- ]?commercial", name, re.I):
        flags.append(_flag("LIC-NONCOMMERCIAL", f"Licence {name!r} restricts commercial use"))
    elif re.search(r"\bBY\b|attribution|OGL|open government", name, re.I):
        flags.append(_flag("LIC-ATTRIBUTION", f"Licence {name!r} requires attribution"))
    if lic.get("mixed_sources"):
        flags.append(_flag("LIC-MIXED", "Record states that parts come from upstream providers with different terms"))
    return flags


def rule_agreement(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = ((record.get("licence") or {}).get("agreement_status") or "").lower()
    if record["kind"] == "vendor_feed" and status not in {"active", "signed"}:
        return [_flag("LIC-AGREEMENT-NOT-ACTIVE", f"Vendor feed with agreement_status={status or 'unknown'!r}")]
    return []


def rule_access(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    acc = record.get("access") or {}
    flags = []
    if acc.get("auth_required") or (acc.get("classification") or "").lower() == "restricted":
        flags.append(_flag("ACC-RESTRICTED", f"auth_required={acc.get('auth_required')}, "
                                             f"classification={acc.get('classification')}, process={acc.get('request_process')!r}"))
    if (acc.get("method") or "").lower() in {"manual_export", "manual", "spreadsheet", "email"}:
        flags.append(_flag("ACC-MANUAL", f"Access method {acc.get('method')!r}"))
    if acc.get("reachable") is False:
        flags.append(_flag("ACC-UNREACHABLE", "Record states the source could not be reached or restored"))
    return flags


def rule_payload(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    size = (record.get("access") or {}).get("approx_size_bytes")
    limit = settings["rules"]["large_payload_bytes"]
    if isinstance(size, int) and size > limit:
        return [_flag("OPS-LARGE-PAYLOAD", f"approx_size_bytes={size:,} > {limit:,}")]
    return []


def rule_pii(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    pii_fields = [f["name"] for f in (record.get("schema") or {}).get("fields", []) if f.get("pii") is True]
    declared = (record.get("declared_metadata") or {}).get("contains_pii")
    if pii_fields or declared is True:
        return [_flag("GOV-PII", f"PII fields: {pii_fields or 'declared contains_pii=true'}")]
    return []


def rule_owner(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal" and not ((record.get("ownership") or {}).get("owner") or "").strip():
        return [_flag("GOV-OWNER-UNKNOWN", "Internal source with no recorded owner")]
    return []


def rule_status(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = (record.get("status") or "").lower()
    if status in INACTIVE_STATUSES:
        return [_flag("GOV-DEPRECATED", f"status={status!r}")]
    return []


# ---------------------------------------------------------------------------
# LEARNER TODO (G4): three rules. tests/test_learner_gaps.py::test_g4_* checks them.
# ---------------------------------------------------------------------------
def rule_temporal_coverage(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    """Coverage of the candidate's target windows, plus staleness.

    - Skip records whose temporal.grain is "static", or whose start is unknown.
    - Treat a null end as "still updating", i.e. covered up to uc["as_of"].
    - For each window id in candidate["target_windows"], compute the fraction of that window
      (uc["windows"], inclusive dates) covered by [start, end].
        all fractions == 0                                      -> COV-OUT-OF-WINDOW
        otherwise any fraction < settings["rules"]["partial_window_threshold"] -> COV-PARTIAL-WINDOW
    - FRS-STALE if end is not null and end is more than settings["rules"]["stale_after_years"]
      years before uc["as_of"].
    Evidence strings must name the window(s) and the dates you compared.
    """
    temporal = record.get("temporal") or {}
    if temporal.get("grain") == "static":
        return []
    start = _d(temporal.get("start"))
    if start is None:
        return []  # no start date: nothing to compare, and no guess
    as_of = _d(uc["as_of"])
    end = _d(temporal.get("end"))
    covered_to = end or as_of  # open-ended ("still updating") covers up to the as-of date

    windows = {w["id"]: w for w in uc["windows"]}
    target = candidate.get("target_windows")
    if not target:  # fall back to the windows the candidate's needs ask for
        needs = {n["id"]: n for n in uc["needs"]}
        target = sorted({w for nid in candidate.get("need_ids", []) for w in needs.get(nid, {}).get("windows", [])})

    fractions = {}
    for wid in target:
        w = windows.get(wid)
        if w is None:
            continue
        w_start, w_end = _d(w["start"]), _d(w["end"])
        overlap = (min(covered_to, w_end) - max(start, w_start)).days + 1
        window_days = (w_end - w_start).days + 1
        fractions[wid] = max(0, overlap) / window_days

    flags = []
    if fractions and all(f == 0 for f in fractions.values()):
        spans = ", ".join(f"{wid} {windows[wid]['start']}..{windows[wid]['end']}" for wid in fractions)
        flags.append(_flag("COV-OUT-OF-WINDOW",
                           f"Record covers {start}..{end or 'open'} and does not overlap window(s) {spans}"))
    elif fractions:
        threshold = settings["rules"]["partial_window_threshold"]
        partial = {wid: f for wid, f in fractions.items() if f < threshold}
        if partial:
            detail = "; ".join(f"{wid} {windows[wid]['start']}..{windows[wid]['end']} covered {f:.0%} "
                               f"(record {start}..{end or 'open'})" for wid, f in partial.items())
            flags.append(_flag("COV-PARTIAL-WINDOW", detail))

    if end is not None:
        years = settings["rules"]["stale_after_years"]
        cutoff = as_of.replace(year=as_of.year - years) if not (as_of.month == 2 and as_of.day == 29) \
            else as_of.replace(year=as_of.year - years, day=28)
        if end <= cutoff:
            flags.append(_flag("FRS-STALE", f"Data ends {end}, more than {years} years before the as-of date {as_of}"))
    return flags


def rule_grain(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    """COV-GRAIN-MISMATCH if the record's grain is coarser than min_grain of any need the
    candidate serves (candidate["need_ids"] -> uc["needs"]). Only grains in GRAIN_ORDER are
    comparable; "event", "static" and "unknown" on either side never raise the flag."""
    grain = (record.get("temporal") or {}).get("grain")
    if grain not in GRAIN_ORDER:
        return []
    needs = {n["id"]: n for n in uc["needs"]}
    flags = []
    for nid in candidate.get("need_ids", []):
        need = needs.get(nid)
        min_grain = (need or {}).get("min_grain")
        if min_grain not in GRAIN_ORDER:
            continue
        if GRAIN_ORDER.index(grain) > GRAIN_ORDER.index(min_grain):
            flags.append(_flag("COV-GRAIN-MISMATCH",
                               f"Record grain {grain!r} is coarser than min_grain {min_grain!r} of {nid} ({need['name']})"))
    return flags


def rule_metadata_contradiction(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    """DQ-METADATA-CONTRADICTION when record["declared_metadata"]["has_missing_values"] is a
    'no' (False, "no", "false") but documentation_excerpts or quality_notes describe missing
    values (e.g. "missing values", "absence of value", "-200", "?" used as missing, "NaN").
    Careful: "Data set has no missing values" is NOT a contradiction. Strip negated phrases
    before matching."""
    declared = (record.get("declared_metadata") or {}).get("has_missing_values")
    # The profiler may record a qualified value such as "no (UCI variable table); the page says Yes".
    # The leading token is the declared value; a page that also says "Yes" is still a contradiction to report.
    says_none = declared is False or bool(re.match(r"\s*(?:no|false)\b", str(declared), re.I))
    if not says_none:
        return []
    sources = [("documentation", t) for t in record.get("documentation_excerpts") or []]
    sources += [("quality_notes", t) for t in record.get("quality_notes") or []]
    for origin, text in sources:
        stripped = _NEGATED_MISSING_RE.sub(" ", text or "")
        hit = _MISSING_SIGNAL_RE.search(stripped)
        if hit:
            return [_flag("DQ-METADATA-CONTRADICTION",
                          f"declared has_missing_values={declared!r}, but {origin} says: \"{text.strip()[:200]}\" "
                          f"(matched {hit.group(0)!r})")]
    return []


RULES = [rule_licence, rule_agreement, rule_access, rule_payload, rule_pii, rule_owner, rule_status,
         rule_temporal_coverage, rule_grain, rule_metadata_contradiction]


def evaluate(record: dict, candidate: dict, uc: dict, settings: dict) -> tuple[list[Flag], list[str]]:
    """Run every rule. Returns (flags, warnings). A rule that is not implemented yet is skipped with a warning."""
    flags: list[Flag] = []
    warnings: list[str] = []
    for rule in RULES:
        try:
            for f in rule(record, candidate, uc, settings):
                flags.append({**f, "raised_by": f"rule:{rule.__name__}"})
        except NotImplementedError as exc:
            warnings.append(f"{rule.__name__} skipped: {exc}")
    seen, unique = set(), []
    for f in flags:
        if f["code"] not in seen:
            seen.add(f["code"])
            unique.append(f)
    return unique, warnings
