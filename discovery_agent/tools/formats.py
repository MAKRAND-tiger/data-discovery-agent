"""Summarisers for self-describing metadata formats the supplementary URLs use.

The tool wrappers (fetch + call) are provided. The pure functions that do the
summarising are LEARNER TODOs (G3). The data-package summary is not graded in this version. They are pure so you can test them offline
against tests/fixtures/ without network or LLM.
"""
from __future__ import annotations

import re

from .base import NotImplementedTool, ToolContext, tool

LARGE_RESOURCE_BYTES = 100_000_000

# ISO 3166-1 alpha-2 country codes (249). Eurostat uses non-ISO codes such as UK (GB), EL (GR), XK, and
# aggregates such as EU27_2020 or EA; those are reported as NON_ISO_GEO_CODES, never silently renamed.
ISO_3166_ALPHA2 = frozenset("""
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ
CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO
FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE
JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO
MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW
PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM
TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW
""".split())


# ---------------------------------------------------------------------------
# Not graded in this version (former G2). Left as a stub: no graded link uses a data package.
# ---------------------------------------------------------------------------
# Spec: https://specs.frictionlessdata.io/data-package/
# Return a dict with EXACTLY these keys (tests/test_learner_gaps.py checks them):
#   title, version, profile          : str | None, copied from the package
#   declared_licences                : the package's "licenses" list, or None if absent/empty
#   temporal                         : {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} from package["temporal"], or None
#   resources                        : [{"name", "path", "format", "bytes", "field_count"}] one per resource
#   total_bytes                      : sum of resource bytes (missing bytes count as 0)
#   largest_resource_bytes           : max resource bytes
#   matching_fields                  : fields whose name starts with any prefix in field_filter (all resources,
#                                      de-duplicated by name, max 60): [{"resource", "name", "unit", "source"}]
#                                      where "source" is field["source"]["name"] if present. [] if field_filter is None.
#   upstream_sources                 : sorted distinct field["source"]["name"] values across ALL fields
#   warnings                         : list containing (when they apply)
#                                        "NO_PACKAGE_LICENCE"         no package-level licence declared
#                                        "LARGE_RESOURCE"             any resource > LARGE_RESOURCE_BYTES
#                                        "MULTIPLE_UPSTREAM_SOURCES"  more than one upstream source
def datapackage_summary(package: dict, field_filter: list[str] | None = None) -> dict:
    raise NotImplementedTool("datapackage_summary is not implemented in this version (former G2).")


# ---------------------------------------------------------------------------
# LEARNER TODO (G3): JSON-stat 2.0 dataset -> summary
# ---------------------------------------------------------------------------
# Spec: https://json-stat.org/full/   (Eurostat's dissemination API returns this format)
# Return a dict with EXACTLY these keys:
#   label, updated, source           : copied from the dataset
#   dimensions                       : [{"id", "size", "labels"}] in the order of dataset["id"];
#                                      labels = first 10 "code: label" strings for that dimension
#   time                             : {"first", "last", "values"} for the "time" dimension (codes, sorted), or None
#   geo_codes                        : list of codes in the "geo" dimension, in index order ([] if no geo dimension)
#   expected_cells                   : product of dataset["size"]
#   value_count                      : number of non-null values (dataset["value"] can be a dict OR a list)
#   missing_cells                    : expected_cells - value_count
#   status_counts                    : {status_code: count} from dataset.get("status") (dict or list), {} if absent
#   warnings                         : list containing (when they apply)
#                                        "MISSING_CELLS"       missing_cells > 0
#                                        "NON_ISO_GEO_CODES"   any geo code that is not ISO 3166-1 alpha-2,
#                                                              including Eurostat's "UK" (ISO: GB) and "EL" (ISO: GR)
#                                                              and aggregates such as "EU27_2020"
# Hint: dimension categories look like
#   dataset["dimension"]["geo"]["category"] = {"index": {"UK": 0, "FR": 1}, "label": {"UK": "United Kingdom", ...}}
#   "index" can also be a list of codes.
def _category_codes(dim: dict) -> tuple[list[str], dict]:
    """Codes of one dimension in index order, plus its labels. Index may be a dict (code -> position) or a list."""
    cat = (dim or {}).get("category") or {}
    labels = cat.get("label") or {}
    index = cat.get("index")
    if isinstance(index, dict):
        codes = sorted(index, key=lambda c: index[c])
    elif isinstance(index, list):
        codes = list(index)
    else:
        codes = list(labels)  # no index: fall back to the label keys, in their order
    return [str(c) for c in codes], labels


def _time_key(code: str):
    """Chronological sort key: '2010M9' < '2010M10', '2010-Q1' < '2011'. Falls back to the text itself."""
    nums = [int(n) for n in re.findall(r"\d+", code)]
    return (nums, code) if nums else ([float("inf")], code)


def _value_count(values, expected: int) -> int:
    """Non-null cells inside [0, expected). Dict and list forms. A missing key or None is NOT a value."""
    if isinstance(values, dict):
        positions = []
        for key, v in values.items():
            try:
                pos = int(key)
            except (TypeError, ValueError):
                continue
            if v is not None and 0 <= pos < expected:
                positions.append(pos)
        return len(positions)
    if isinstance(values, list):
        return sum(1 for i, v in enumerate(values) if v is not None and i < expected)
    return 0


def _status_counts(status) -> dict:
    if isinstance(status, dict):
        items = status.values()
    elif isinstance(status, list):
        items = [s for s in status if s is not None]
    else:
        items = []
    counts: dict[str, int] = {}
    for code in items:
        counts[str(code)] = counts.get(str(code), 0) + 1
    return counts


def _is_iso_alpha2(code: str) -> bool:
    return code in ISO_3166_ALPHA2


def jsonstat_summary(dataset: dict) -> dict:
    """Summarise a JSON-stat 2.0 dataset. Pure: no network, no LLM. See the contract above."""
    ids = list(dataset.get("id") or [])
    sizes = list(dataset.get("size") or [])
    dims_meta = dataset.get("dimension") or {}
    expected = 1
    for s in sizes:
        expected *= int(s)

    dimensions = []
    parsed: dict[str, tuple[list[str], dict]] = {}
    for i, dim_id in enumerate(ids):
        codes, labels = _category_codes(dims_meta.get(dim_id, {}))
        parsed[dim_id] = (codes, labels)
        dimensions.append({
            "id": dim_id,
            "size": int(sizes[i]) if i < len(sizes) else len(codes),
            "labels": [f"{c}: {labels[c]}" if labels.get(c) else c for c in codes[:10]],
        })

    time = None
    if "time" in parsed:
        time_codes, _ = parsed["time"]
        ordered = sorted(time_codes, key=_time_key)
        time = {"first": ordered[0] if ordered else None, "last": ordered[-1] if ordered else None, "values": ordered}

    geo_codes = parsed["geo"][0] if "geo" in parsed else []

    value_count = _value_count(dataset.get("value"), expected)
    missing_cells = expected - value_count
    status_counts = _status_counts(dataset.get("status"))

    warnings = []
    if missing_cells > 0:
        warnings.append("MISSING_CELLS")
    if any(not _is_iso_alpha2(c) for c in geo_codes):
        warnings.append("NON_ISO_GEO_CODES")

    return {
        "label": dataset.get("label"),
        "updated": dataset.get("updated"),
        "source": dataset.get("source"),
        "dimensions": dimensions,
        "time": time,
        "geo_codes": geo_codes,
        "expected_cells": expected,
        "value_count": value_count,
        "missing_cells": missing_cells,
        "status_counts": status_counts,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Tool wrappers (provided)
# ---------------------------------------------------------------------------
@tool("summarize_datapackage",
      "Summarise a Frictionless Data Package descriptor (datapackage.json): licence declarations, temporal coverage, "
      "resource sizes, matching fields and their upstream sources. Reads only the descriptor, never the data files.",
      {"url": {"type": "string"},
       "field_filter": {"type": "array", "items": {"type": "string"},
                        "description": "Field-name prefixes to list, e.g. ['AB_', 'CD_load']"}},
      ["url"])
def summarize_datapackage(ctx: ToolContext, args: dict) -> dict:
    package, res = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], "last_modified_header": res.headers.get("last-modified"),
            **datapackage_summary(package, args.get("field_filter"))}


@tool("summarize_jsonstat",
      "Summarise a JSON-stat 2.0 dataset (for example from the Eurostat dissemination API): dimensions, time coverage, "
      "geo codes, missing cells and status flags.",
      {"url": {"type": "string"}}, ["url"])
def summarize_jsonstat(ctx: ToolContext, args: dict) -> dict:
    dataset, _ = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], **jsonstat_summary(dataset)}
