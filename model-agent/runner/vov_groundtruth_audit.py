#!/usr/bin/env python3
"""GROUND-TRUTH VReq audit: parse VReqs from the SOURCE vibe ourselves, verify each
against the agent's v2 model.json, score adherence = fulfilled / ALL parsed VReqs.

This is deliberately INDEPENDENT of the agent's own vibe_orchestrator_scored payload
(the "lying scoreboard" whose denominator = what the agent extracted). Here the
denominator is what WE parse from next_vibes.txt, so a vibe with 100 VReqs where the
agent extracted 50 and applied 45 scores 45%, not 90%.

VReq sources parsed from vibes/<ind>/next_vibes.txt:
  - SEC1 preserve   : every v1 domain + product (from vibes/<ind>/model.json) must exist in v2 ecm
  - SEC3C P1..P20   : connect_table / rename_attribute / move_product / remove_fk / rename_product
  - SEC3A stubs     : listed products must gain real data attributes (> PK/FK)
  - SEC3B thin      : listed products should be expanded vs v1
  - SEC2 entities   : snake_case multi-token entities the reviewer flags as missing/add/required

Verification is deterministic against v2 ecm model.json (+ v1 model.json for baselines).
Industry-agnostic: nothing hardcoded per industry.
"""
import json
import os
import re
import sys

VIBES = "/Users/user/Documents/projects/vibe-business-data-models-v2/vibes"
V2REPO = "/Users/user/Documents/projects/vibe-business-data-models-v2"
OUT = os.path.expanduser("~/claude/vibe-agent/v2_groundtruth")


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")


_TIER_TOKENS = {"mvm", "ecm", "mvm_tier", "ecm_tier", "metric_view_model",
                "metric_view_model_tier"}


def _is_tier_target(nd):
    # 'promote X to MVM tier' is a tier/scope op, not a real domain move; the LLM
    # extractor maps it to move_product{new_domain=mvm...}. Not verifiable from an
    # ECM model.json (same rationale as add_metric living in MVM scope).
    if not nd:
        return False
    if nd in _TIER_TOKENS:
        return True
    return bool(set(nd.split("_")) & {"mvm", "ecm"})


def load_model(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def index_model(mj):
    """Return (prod2domain, prod2attrs) where attrs = {attr_name: fk_to_or_None}."""
    prod2domain, prod2attrs = {}, {}
    model = (mj or {}).get("model", {})
    for d in model.get("domains", []):
        dn = norm(d.get("name"))
        for p in (d.get("products") or d.get("data_products") or []):
            pn = norm(p.get("name"))
            prod2domain[pn] = dn
            prod2attrs[pn] = {norm(a.get("name")): a.get("foreign_key_to") for a in p.get("attributes", [])}
    return prod2domain, prod2attrs


_NUMERIC = ("INT", "BIGINT", "SMALLINT", "TINYINT", "DECIMAL", "NUMERIC",
            "DOUBLE", "FLOAT", "REAL", "LONG")


def attr_meta(mj):
    """Return {product: {attr: {'type': UPPER, 'tags': lower-joined}}} for type/tag verification."""
    model = (mj or {}).get("model", {})
    out = {}
    for d in model.get("domains", []):
        for p in (d.get("products") or d.get("data_products") or []):
            pn = norm(p.get("name"))
            m = {}
            for a in p.get("attributes", []):
                an = norm(a.get("name"))
                bits = []
                for key in ("tags", "tag_set", "classification"):
                    val = a.get(key)
                    if isinstance(val, str):
                        bits.append(val)
                    elif isinstance(val, list):
                        bits.extend(str(x) for x in val)
                m[an] = {"type": (a.get("type") or a.get("data_type") or "").upper(),
                         "tags": " ".join(bits).lower()}
            out[pn] = m
    return out


def metric_names(mj):
    model = (mj or {}).get("model", {})
    out = []
    for x in model.get("metric_views", []):
        nm = x.get("view_name") or x.get("name") or x.get("metric_name")
        if nm:
            out.append(norm(nm))
    return out


def metric_blob(mj):
    """All metric-view names + SQL + descriptions, lowercased — KPIs like RevPAR live in SQL."""
    model = (mj or {}).get("model", {})
    parts = []
    for x in model.get("metric_views", []):
        for k in ("view_name", "name", "sql", "description"):
            if x.get(k):
                parts.append(str(x[k]))
    return " ".join(parts).lower()


def v1_structure(mj):
    domains, products = set(), set()
    for d in (mj or {}).get("model", {}).get("domains", []):
        domains.add(norm(d.get("name")))
        for p in (d.get("products") or d.get("data_products") or []):
            products.add(norm(p.get("name")))
    return domains, products


# ---------------- verification -----------------
def fk_matches(fk_val, fk_to):
    if not fk_val:
        return False
    fv = norm(fk_val); want = norm(fk_to)
    # match on the product token of the target (2nd-to-last) or full contains
    parts = [p for p in re.split(r"_+", want) if p]
    return want in fv or fv in want or (len(parts) >= 2 and "_".join(parts[-3:]) in fv)


def find_product(prod, prod2domain):
    if prod in prod2domain:
        return prod
    # tolerate domain-prefixed rename (e.g. nameplate -> aftersales_nameplate)
    for p in prod2domain:
        if p.endswith("_" + prod) or p == prod:
            return p
    return None


def verify(v, v2pd, v2pa, v1_products):
    a = v["action"]
    prod = v.get("product")
    if a == "preserve":
        present = v["target"] in v2pd
        return ("fulfilled" if present else "missed",
                "" if present else f"product '{v['target']}' from v1 absent in v2 ECM (dropped)")
    if a == "add_entity":
        e = v["entity"]
        if e in v2pd:
            return "fulfilled", f"entity present as product '{e}'"
        for pn, attrs in v2pa.items():
            if any(e in an or an in e for an in attrs):
                return "fulfilled", f"entity present as attribute on '{pn}'"
        # token-overlap soft check
        toks = set(t for t in e.split("_") if len(t) > 3)
        for pn in v2pd:
            if toks and toks.issubset(set(pn.split("_"))):
                return "partial", f"near-match product '{pn}'"
        return "missed", f"reviewer-requested entity '{e}' not found as product or attribute"
    # P-actions need the product to exist somewhere
    rp = find_product(prod, v2pd)
    if a == "connect_table":
        if not rp:
            return "missed", f"target product '{prod}' absent in v2 (cannot connect)"
        col = v.get("column"); attrs = v2pa.get(rp, {})
        if not col:
            # column-less connect_table = table-level "link this table" intent; the
            # extractor did not name a specific column, so verify at table granularity.
            if any(attrs[an] for an in attrs):
                return "fulfilled", "table linked via outbound FK(s) (no specific column required)"
            return "missed", "table has no outbound FK (still isolated)"
        if col and col in attrs and fk_matches(attrs[col], v.get("fk_to", "")):
            return "fulfilled", f"column '{col}' present with FK -> {attrs[col]}"
        if col and col in attrs:
            return "partial", f"column '{col}' present but FK missing/wrong (got {attrs[col]})"
        if any(attrs[an] for an in attrs):
            return "partial", f"exact column '{col}' absent but product has other outbound FKs (connected differently)"
        return "missed", f"column '{col}' absent and product has no outbound FK (still isolated)"
    if a == "rename_attribute":
        if not rp:
            return "missed", f"target product '{prod}' absent"
        attrs = v2pa.get(rp, {})
        new, old = v.get("new_col"), v.get("old_col")
        if new and new in attrs and (not old or old not in attrs):
            return "fulfilled", f"renamed to '{new}'"
        if old and old in attrs:
            return "missed", f"old column '{old}' still present (rename not applied)"
        return "partial", f"neither '{old}' nor '{new}' found (column may have been dropped/restructured)"
    if a == "move_product":
        if not rp:
            return "missed", f"product '{prod}' absent"
        cur = v2pd.get(rp); nd = v.get("new_domain")
        if _is_tier_target(nd):
            return ("unverifiable",
                    f"tier/scope promotion to '{nd}' (MVM/ECM) not verifiable from ECM model")
        if nd and cur == nd:
            return "fulfilled", f"now in domain '{nd}'"
        return "missed", f"still in domain '{cur}', not moved to '{nd}'"
    if a == "remove_fk":
        if not rp:
            return "missed", f"product '{prod}' absent"
        attrs = v2pa.get(rp, {}); col = v.get("column")
        if col not in attrs:
            return "fulfilled", f"column '{col}' removed entirely"
        if not attrs.get(col):
            return "fulfilled", f"FK removed from '{col}'"
        return "missed", f"FK still present on '{col}' (-> {attrs[col]})"
    if a == "rename_product":
        new = v.get("new_name")
        if not new:
            return "unverifiable", "rename target name not captured in extraction"
        if new in v2pd:
            return "fulfilled", f"product renamed to '{new}'"
        if prod in v2pd:
            return "missed", f"old name '{prod}' still present (rename not applied)"
        return "partial", f"neither old '{prod}' nor new '{new}' present"
    return "unverifiable", "no rule for action"


# ---------------- LLM-structured VReq extraction -----------------
LLM_ENDPOINT = "databricks-claude-sonnet-4-6"
LLM_PROFILE = "<profile>"

_ACTIONS = ("connect_table", "rename_attribute", "move_product", "remove_fk",
            "rename_product", "add_entity", "expand_stub", "expand_thin",
            "change_type", "add_tag", "add_metric")


def _salvage_vreqs(s):
    """Recover complete VReq objects from a truncated 'vreqs' array via balanced-brace scan."""
    k = s.find('"vreqs"')
    if k < 0:
        return None
    lb = s.find("[", k)
    if lb < 0:
        return None
    objs = []
    depth = 0
    start = None
    in_str = False
    esc = False
    for idx in range(lb + 1, len(s)):
        ch = s[idx]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                frag = s[start:idx + 1]
                try:
                    objs.append(json.loads(frag))
                except Exception:
                    pass
                start = None
        elif ch == "]" and depth == 0:
            break
    return {"vreqs": objs} if objs else None


def _extract_json(raw):
    if not raw:
        return None
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n", "", s)
        s = re.sub(r"\n```\s*$", "", s)
    i = s.find("{")
    j = s.rfind("}")
    if i >= 0 and j > i:
        try:
            return json.loads(s[i:j + 1])
        except Exception:
            pass
    return _salvage_vreqs(s)


_HOST_CACHE = {}
_TOKEN_CACHE = {}


def _profile_host(profile):
    if profile in _HOST_CACHE:
        return _HOST_CACHE[profile]
    import configparser
    c = configparser.ConfigParser()
    c.read(os.path.expanduser("~/.databrickscfg"))
    host = c[profile].get("host") if profile in c else None
    if host:
        host = host.rstrip("/")
    _HOST_CACHE[profile] = host
    return host


def _profile_token(profile):
    if profile in _TOKEN_CACHE:
        return _TOKEN_CACHE[profile]
    import subprocess
    try:
        p = subprocess.run(["databricks", "auth", "token", "--profile", profile, "-o", "json"],
                           capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            return None
        tok = json.loads(p.stdout).get("access_token")
        _TOKEN_CACHE[profile] = tok
        return tok
    except Exception:
        return None


def _llm_invoke(profile, endpoint, system, user, max_tokens=32000, timeout=600):
    import urllib.request
    import urllib.error
    host = _profile_host(profile)
    token = _profile_token(profile)
    if not host or not token:
        return None
    payload = {"messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}],
               "max_tokens": max_tokens, "temperature": 0}
    req = urllib.request.Request(
        f"{host}/serving-endpoints/{endpoint}/invocations",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        return d.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception:
        _TOKEN_CACHE.pop(profile, None)
        return None


_LLM_SYS = (
    "You are a meticulous data-modeling requirements extractor. You are given a "
    "'next_vibes' review document: instructions to evolve a v1 data model into v2. "
    "Your job is to extract EVERY atomic, independently-verifiable improvement "
    "requirement (VReq) the document states, regardless of wording: numbered "
    "priorities, prose sentences, gap statements, tables, stub/thin callouts. "
    "Capture all of them; never invent requirements not in the document; never merge "
    "two distinct requirements into one. Output STRICT JSON only, no prose.")


def _llm_user_prompt(text, v1_domains, v1_products):
    schema = (
        "Allowed action values and their required fields (snake_case names; for "
        "`product` use the v1 product token, i.e. the table name without its domain "
        "prefix):\n"
        "- connect_table {product, column?, fk_to?}  (table must gain an FK / be linked)\n"
        "- rename_attribute {product, old_col, new_col}\n"
        "- move_product {product, new_domain}\n"
        "- remove_fk {product, column}\n"
        "- rename_product {product, new_name}\n"
        "- add_entity {entity}  (a NEW table/entity the reviewer says is missing/required)\n"
        "- expand_stub {product, domain?}  (a near-empty table that must gain real attributes)\n"
        "- expand_thin {product, domain?}  (an under-developed table that must be expanded)\n"
        "- change_type {product, column, new_type}  (a column whose data type must change, "
        "e.g. STRING -> a numeric/decimal/timestamp type; use 'numeric' if the doc just says "
        "'make numeric')\n"
        "- add_tag {product, column?, tag}  (a column/table that must gain a tag or "
        "classification, e.g. PII; use tag='pii' for any PII/sensitive-data tagging ask)\n"
        "- add_metric {metric}  (a metric view / KPI / formula that must exist or be fixed, "
        "e.g. RevPAR, occupancy_rate; metric = the metric/KPI name)\n")
    return (
        f"v1 DOMAINS: {sorted(v1_domains)}\n\n"
        f"v1 PRODUCTS (tables): {sorted(v1_products)}\n\n"
        f"{schema}\n"
        "Return JSON: {\"vreqs\": [ {\"action\": <one of the above>, ...required fields..., "
        "\"verbatim\": <the exact source phrase, <=200 chars>, \"interpretation\": "
        "<one-line plain English of what must change>} ] }\n"
        "Rules: resolve every `product` to an existing v1 product token when the document "
        "refers to one; if a requirement names a brand-new table not in v1, use add_entity. "
        "Do NOT emit a requirement that merely says 'preserve/keep existing tables' (those "
        "are handled separately).\n"
        "CRITICAL — observations are NOT requirements: the document includes DIAGNOSTIC "
        "listings that merely REPORT what an analyzer detected (e.g. a 'Cross-domain SSOT "
        "duplicates' section listing pairs like \"'a.x' vs 'b.x'\", counts like 'siloed "
        "tables: 5', or inventory tables of findings). These are context, NOT directives. "
        "Do NOT emit any VReq (no move_product, no remove_fk, nothing) from a bare "
        "'X vs Y' duplicate-observation line or any detection-count line. Only emit a VReq "
        "when the document gives an IMPERATIVE instruction to change the model — typically a "
        "numbered PRIORITY (P1, P2, ...) or an explicit 'add/rename/connect/move/remove/"
        "expand/make/tag' sentence. If a duplicate pair is genuinely actioned, it will have "
        "its own PRIORITY line; extract THAT, not the observation.\n"
        "Extract EVERYTHING that is an actual instruction, exhaustively.\n\n"
        "=== NEXT_VIBES DOCUMENT START ===\n"
        f"{text[:120000]}\n"
        "=== NEXT_VIBES DOCUMENT END ===")


def _normalize_vreqs(raw_vreqs, idprefix="LLM"):
    out = []
    for i, v in enumerate(raw_vreqs):
        a = (v.get("action") or "").strip()
        if a not in _ACTIONS:
            continue
        vr = {"id": f"{idprefix}-{i+1}", "source": "LLM", "action": a,
              "verbatim": (v.get("verbatim") or "")[:200],
              "interpretation": (v.get("interpretation") or "")[:200]}
        if a == "add_entity":
            vr["entity"] = norm(v.get("entity"))
            if not vr["entity"]:
                continue
        elif a == "add_metric":
            vr["metric"] = norm(v.get("metric") or v.get("entity") or v.get("product"))
            if not vr["metric"]:
                continue
        else:
            vr["product"] = norm(v.get("product"))
            if not vr["product"] and a not in ("add_entity",):
                continue
        if a == "connect_table":
            if v.get("column"):
                vr["column"] = norm(v.get("column"))
            if v.get("fk_to"):
                vr["fk_to"] = str(v.get("fk_to")).strip(". ")
        elif a == "rename_attribute":
            vr["old_col"] = norm(v.get("old_col"))
            vr["new_col"] = norm(v.get("new_col"))
        elif a == "move_product":
            vr["new_domain"] = norm(v.get("new_domain"))
            # Defensive: a move_product with no target domain is a malformed extraction —
            # almost always a misread 'X vs Y' SSOT-duplicate OBSERVATION line (not a real
            # move directive). Dropping it prevents the denominator from being inflated with
            # non-requirements (which would understate true adherence).
            if not vr["new_domain"]:
                continue
        elif a == "remove_fk":
            vr["column"] = norm(v.get("column"))
        elif a == "rename_product":
            vr["new_name"] = norm(v.get("new_name"))
        elif a in ("expand_stub", "expand_thin"):
            vr["domain"] = norm(v.get("domain")) if v.get("domain") else ""
        elif a == "change_type":
            vr["column"] = norm(v.get("column"))
            vr["new_type"] = (v.get("new_type") or "").strip().upper()
            if not vr["column"] or not vr["new_type"]:
                continue
        elif a == "add_tag":
            vr["column"] = norm(v.get("column")) if v.get("column") else ""
            vr["tag"] = (v.get("tag") or "").strip().lower()
            if not vr["tag"]:
                continue
        out.append(vr)
    return out


def _vreq_key(v):
    a = v["action"]
    if a == "add_entity":
        return ("add_entity", v.get("entity"))
    if a == "rename_attribute":
        return (a, v.get("product"), v.get("old_col"), v.get("new_col"))
    if a == "connect_table":
        return (a, v.get("product"), v.get("column"))
    if a == "move_product":
        return (a, v.get("product"), v.get("new_domain"))
    if a == "rename_product":
        return (a, v.get("product"), v.get("new_name"))
    if a == "remove_fk":
        return (a, v.get("product"), v.get("column"))
    if a == "change_type":
        return (a, v.get("product"), v.get("column"))
    if a == "add_tag":
        return (a, v.get("product"), v.get("column"), v.get("tag"))
    if a == "add_metric":
        return (a, v.get("metric"))
    return (a, v.get("product"))


_GAP_SYS = (
    "You are a completeness auditor for data-model requirement extraction. You are "
    "given a next_vibes document and a list of requirements already extracted from it. "
    "Find EVERY additional atomic requirement in the document that is MISSING from the "
    "list. Output STRICT JSON only.")


def _gap_user_prompt(text, v1_domains, v1_products, have):
    have_lines = "\n".join(f"- {v['action']}: {v.get('product') or v.get('entity')}"
                           for v in have)
    return (
        f"v1 DOMAINS: {sorted(v1_domains)}\nv1 PRODUCTS: {sorted(v1_products)}\n\n"
        "ALREADY-EXTRACTED requirements:\n" + have_lines + "\n\n"
        "Same action vocabulary and JSON schema as before "
        "(connect_table/rename_attribute/move_product/remove_fk/rename_product/"
        "add_entity/expand_stub/expand_thin; each with required fields + verbatim + "
        "interpretation). Return JSON {\"vreqs\":[...]} containing ONLY requirements "
        "present in the document but ABSENT from the already-extracted list. If none are "
        "missing, return {\"vreqs\":[]}.\n"
        "Do NOT emit VReqs from diagnostic OBSERVATION lines (e.g. a 'Cross-domain SSOT "
        "duplicates' list of \"'a.x' vs 'b.x'\" pairs, or detection counts) — those are "
        "context, not directives. Only actual imperative instructions / numbered "
        "PRIORITIES count.\n\n"
        "=== NEXT_VIBES DOCUMENT START ===\n" + text[:120000] +
        "\n=== NEXT_VIBES DOCUMENT END ===")


def llm_extract_vreqs(text, v1_domains, v1_products, profile, endpoint,
                      retries=3, gap_passes=2, base_passes=2):
    # Multiple independent base extractions unioned: the LLM is non-deterministic about
    # WHICH atomic VReqs it surfaces in one pass, so a single pass under-counts. Unioning
    # 2+ passes (then gap passes) converges on the true VReq set, making the ground-truth
    # denominator stable + comparable across model versions (so 'improving vs previous' is
    # a fair same-denominator comparison, not extraction noise).
    base = None
    for _ in range(retries):
        raw = _llm_invoke(profile, endpoint, _LLM_SYS,
                          _llm_user_prompt(text, v1_domains, v1_products))
        d = _extract_json(raw)
        if d and "vreqs" in d:
            base = _normalize_vreqs(d["vreqs"])
            break
    if base is None:
        return None
    seen = {_vreq_key(v) for v in base}
    nid = len(base)
    # additional union base passes
    for _ in range(max(0, base_passes - 1)):
        raw = _llm_invoke(profile, endpoint, _LLM_SYS,
                          _llm_user_prompt(text, v1_domains, v1_products))
        d = _extract_json(raw)
        if not d or not d.get("vreqs"):
            continue
        for v in _normalize_vreqs(d["vreqs"], idprefix="U"):
            k = _vreq_key(v)
            if k in seen:
                continue
            seen.add(k)
            nid += 1
            v["id"] = f"LLM-{nid}"
            base.append(v)
    for _ in range(gap_passes):
        raw = _llm_invoke(profile, endpoint, _GAP_SYS,
                          _gap_user_prompt(text, v1_domains, v1_products, base))
        d = _extract_json(raw)
        if not d or not d.get("vreqs"):
            break
        added = 0
        for v in _normalize_vreqs(d["vreqs"], idprefix="GAP"):
            k = _vreq_key(v)
            if k in seen:
                continue
            seen.add(k)
            nid += 1
            v["id"] = f"LLM-{nid}"
            base.append(v)
            added += 1
        if added == 0:
            break
    return base


def _norm_type_family(t):
    t = (t or "").upper()
    if any(n in t for n in _NUMERIC) or t in ("NUMERIC", "NUMBER"):
        return "NUMERIC"
    if "TIMESTAMP" in t or "DATE" in t:
        return "TEMPORAL"
    if "BOOL" in t:
        return "BOOL"
    if "STRING" in t or "VARCHAR" in t or "CHAR" in t or "TEXT" in t:
        return "STRING"
    return t


def _score_one(v, v2pd, v2pa, v1_products, meta=None, metrics=None, mblob=""):
    a = v["action"]
    meta = meta or {}
    metrics = metrics or []
    if a in ("expand_stub", "expand_thin"):
        rp = find_product(v["product"], v2pd)
        if not rp:
            return "missed", f"product '{v['product']}' absent in v2"
        attrs = v2pa.get(rp, {})
        nonkey = [an for an in attrs if not (an.endswith("_id") or an == "id")]
        thr = 8 if a == "expand_stub" else 12
        if len(nonkey) >= thr:
            return "fulfilled", f"{len(nonkey)} non-key attributes"
        return "partial", f"only {len(nonkey)} non-key attributes (< {thr})"
    if a == "change_type":
        rp = find_product(v["product"], v2pd)
        if not rp:
            return "missed", f"product '{v['product']}' absent in v2"
        col = v.get("column")
        cm = meta.get(rp, {}).get(col)
        if not cm:
            return "missed", f"column '{col}' absent in v2 (cannot verify type change)"
        want = _norm_type_family(v.get("new_type"))
        got = _norm_type_family(cm["type"])
        if want == got and got != "STRING":
            return "fulfilled", f"'{col}' is {cm['type']} (family {got})"
        if got == "STRING":
            return "missed", f"'{col}' still STRING ({cm['type']}), expected {v.get('new_type')}"
        return "partial", f"'{col}' is {cm['type']} (family {got}), asked {v.get('new_type')}"
    if a == "add_tag":
        rp = find_product(v["product"], v2pd)
        if not rp:
            return "missed", f"product '{v['product']}' absent in v2"
        tag = (v.get("tag") or "").lower()
        pm = meta.get(rp, {})
        col = v.get("column")
        if col:
            cm = pm.get(col)
            if not cm:
                return "missed", f"column '{col}' absent (cannot verify tag)"
            if tag in cm["tags"] or (tag == "pii" and "pii" in cm["tags"]):
                return "fulfilled", f"'{col}' tagged ({cm['tags'][:40]})"
            return "missed", f"'{col}' lacks tag '{tag}' (has: {cm['tags'][:40] or 'none'})"
        # product-level: any attribute carrying the tag
        hits = [an for an, cm in pm.items() if tag in cm["tags"] or (tag == "pii" and "pii" in cm["tags"])]
        if hits:
            return "fulfilled", f"{len(hits)} column(s) carry tag '{tag}'"
        return "missed", f"no column on '{rp}' carries tag '{tag}'"
    if a == "add_metric":
        m = v.get("metric") or ""
        if not metrics and not mblob:
            return "unverifiable", "no metric views in this model scope (metrics live in MVM)"
        mt = set(t for t in m.split("_") if len(t) > 2)
        for mn in metrics:
            if m and (m in mn or mn in m):
                return "fulfilled", f"metric view '{mn}' present"
            mtoks = set(mn.split("_"))
            if mt and mt.issubset(mtoks):
                return "fulfilled", f"metric view '{mn}' covers '{m}'"
        # KPI may live inside metric SQL/description (e.g. RevPAR formula)
        if m and m.replace("_", " ") in mblob or (m and m in mblob):
            return "fulfilled", f"'{m}' referenced in metric-view SQL/description"
        return "missed", f"metric/KPI '{m}' not found among {len(metrics)} metric views"
    return verify(v, v2pd, v2pa, v1_products)


def score_against_model(vreqs, model_json, v1_products):
    v2pd, v2pa = index_model(model_json)
    meta = attr_meta(model_json)
    metrics = metric_names(model_json)
    mblob = metric_blob(model_json)
    results = []
    for v in vreqs:
        status, reason = _score_one(v, v2pd, v2pa, v1_products, meta, metrics, mblob)
        results.append({**v, "status": status, "reason": reason})
    by = {}
    for r in results:
        by[r["status"]] = by.get(r["status"], 0) + 1
    # adherence denominator excludes out-of-scope 'unverifiable' (neither applied nor a fair miss)
    scorable = [r for r in results if r["status"] != "unverifiable"]
    total = len(scorable)
    ful = by.get("fulfilled", 0)
    imp = [r for r in scorable if r["source"] != "SEC1"]
    imp_ful = sum(1 for r in imp if r["status"] == "fulfilled")
    summary = {
        "total_vreqs": len(results), "scorable_vreqs": total, "by_status": by, "fulfilled": ful,
        "adherence_all": round(100.0 * ful / total, 1) if total else 0.0,
        "improvement_total": len(imp), "improvement_fulfilled": imp_ful,
        "improvement_adherence": round(100.0 * imp_ful / len(imp), 1) if imp else 0.0,
        "unverifiable": by.get("unverifiable", 0), "v2_products": len(v2pd)}
    return results, summary


_AGENT_VREQ = re.compile(r"\[VREQ-(\d+)\]\s*(?:\(([^)]*)\))?\s*(.*)")
_COMPLETENESS = re.compile(
    r"vov-extract-completeness-audit[^\]]*\][^\n]*?missing=(\d+)[^\n]*?detected=(\d+)"
    r"[^\n]*?recovered_total=(\d+)", re.I)
_MUT_SUMMARY = re.compile(r"MUTATION-SUMMARY[^\n]*?applied[=:\s]+(\d+)[^\n]*?skipped[=:\s]+(\d+)", re.I)


def parse_agent_selfscore(log_text):
    """Agent's own extracted/applied counts from the vov log — the agent self-scoreboard
    we audit against (lying-scoreboard check). [VREQ-NNN] are the agent's extracted VReqs;
    VREQ-001 is the bundled preserve-all directive, the rest are generative/improvement."""
    if not log_text:
        return {}
    out = {}
    ids = {}
    preserve = 0
    for m in _AGENT_VREQ.finditer(log_text):
        vid = m.group(1)
        body = (m.group(3) or "")
        ids[vid] = body
        bl = body.lower()
        # preserve-equivalent: the bundled preserve directive AND the per-domain
        # "create the <existing-domain> domain with the following products" recreations
        if ("preserve the existing model" in bl or "preserve the required model" in bl
                or re.match(r"create the \w+ domain with the following products", bl)):
            preserve += 1
    if ids:
        out["agent_extracted_total"] = len(ids)
        out["agent_preserve_vreqs"] = preserve
        out["agent_improvement_extracted"] = len(ids) - preserve
    cm = _COMPLETENESS.search(log_text)
    if cm:
        out["agent_completeness"] = {"missing": int(cm.group(1)),
                                     "detected": int(cm.group(2)),
                                     "recovered": int(cm.group(3))}
    ms = _MUT_SUMMARY.findall(log_text)
    if ms:
        out["agent_applied"] = sum(int(a) for a, _ in ms)
        out["agent_skipped"] = sum(int(s) for _, s in ms)
    return out


def extract_vreqs_for(ind, profile=None, endpoint=None, refresh=False):
    """Pure-LLM VReq set for an industry: deterministic SEC1 preserve (from v1 model)
    + exhaustive LLM improvement extraction (multi-pass union + gap passes, NO regex,
    NO cache — extracted fresh every audit). The denominator is EVERY requirement the
    user's vibe states; the score = fulfilled / ALL, i.e. did v2 adhere to 100% of the
    user's vibes."""
    v1 = load_model(os.path.join(VIBES, ind, "model.json"))
    v1_domains, v1_products = v1_structure(v1)
    vibe = open(os.path.join(VIBES, ind, "next_vibes.txt"), errors="ignore").read()
    vreqs = [{"id": f"PRES-{p}", "source": "SEC1", "action": "preserve", "target": p}
             for p in sorted(v1_products)]
    imp = llm_extract_vreqs(vibe, v1_domains, v1_products,
                            profile or LLM_PROFILE, endpoint or LLM_ENDPOINT)
    if imp is None:
        raise RuntimeError(f"LLM VReq extraction failed for {ind} after retries (NO regex fallback)")
    vreqs += imp
    return vreqs, v1_products


_STATUS_RANK = {"fulfilled": 3, "partial": 2, "missed": 1, "unverifiable": 0}


def _merge_xscope(ecm_results, mvm_results):
    """Best status per VReq across ECM+MVM scopes. A metric/MVM-tier VReq that is
    unverifiable in ECM but fulfilled in MVM becomes fulfilled overall."""
    by_key = {}
    for r in mvm_results:
        by_key[r.get("id") or _vreq_key(r)] = r
    merged = []
    for r in ecm_results:
        m = by_key.get(r.get("id") or _vreq_key(r))
        if m and _STATUS_RANK.get(m["status"], 0) > _STATUS_RANK.get(r["status"], 0):
            merged.append({**r, "status": m["status"],
                           "reason": f"[mvm] {m['reason']}", "_scope": "mvm"})
        else:
            merged.append({**r, "_scope": "ecm"})
    by = {}
    for r in merged:
        by[r["status"]] = by.get(r["status"], 0) + 1
    scorable = [r for r in merged if r["status"] != "unverifiable"]
    total = len(scorable)
    ful = by.get("fulfilled", 0)
    imp = [r for r in scorable if r["source"] != "SEC1"]
    imp_ful = sum(1 for r in imp if r["status"] == "fulfilled")
    return merged, {
        "xscope_scorable": total, "xscope_fulfilled": ful, "xscope_by_status": by,
        "xscope_adherence_all": round(100.0 * ful / total, 1) if total else 0.0,
        "xscope_improvement_total": len(imp), "xscope_improvement_fulfilled": imp_ful,
        "xscope_improvement_adherence": round(100.0 * imp_ful / len(imp), 1) if imp else 0.0}


def audit_industry(ind, use_llm=True, profile=None, endpoint=None,
                   v2_path=None, prior_model=None, log_text=None, mvm_model=None,
                   refresh=False):
    v2_path = v2_path or os.path.join(V2REPO, ind, "v2", "ecm", "model.json")
    v2ecm = load_model(v2_path)
    if not v2ecm:
        return None
    vreqs, v1_products = extract_vreqs_for(ind, profile, endpoint, refresh=refresh)
    results, summary = score_against_model(vreqs, v2ecm, v1_products)

    out = {"industry": ind, "extraction_mode": "llm", "v2_path": v2_path,
           "v1_products": len(v1_products), "results": results, **summary}

    if mvm_model is not None:
        mvm_results, _ = score_against_model(vreqs, mvm_model, v1_products)
        merged, xsum = _merge_xscope(results, mvm_results)
        out["xscope_results"] = merged
        out.update(xsum)

    coverage = parse_agent_selfscore(log_text) if log_text else {}
    if coverage:
        out["agent_selfscore"] = coverage
        ae = coverage.get("agent_improvement_extracted")
        if ae is not None and summary["improvement_total"]:
            # coverage = of MY ground-truth improvement VReqs, how many the agent captured
            out["agent_coverage_improvement_pct"] = round(
                100.0 * min(ae, summary["improvement_total"]) / summary["improvement_total"], 1)
        # lying-scoreboard delta: agent claims full capture (missing=0) but my verified
        # adherence is the truth
        comp = coverage.get("agent_completeness") or {}
        if comp.get("missing") == 0:
            out["agent_claimed_complete"] = True
            out["truth_vs_claim_gap_pct"] = round(100.0 - summary["improvement_adherence"], 1)

    if prior_model is not None:
        _, prior_summary = score_against_model(vreqs, prior_model, v1_products)
        out["prior"] = {k: prior_summary[k] for k in
                        ("adherence_all", "fulfilled", "improvement_adherence",
                         "improvement_fulfilled", "by_status")}
        out["delta_adherence_all"] = round(summary["adherence_all"] - prior_summary["adherence_all"], 1)
        out["delta_improvement_adherence"] = round(
            summary["improvement_adherence"] - prior_summary["improvement_adherence"], 1)
    return out


_STATUS_MAP = {"fulfilled": "applied", "partial": "partial", "missed": "missed",
               "unverifiable": "missed"}


def _affected(v):
    a = v["action"]
    p = v.get("product")
    if a == "preserve":
        return {"type": "product", "fqname": v.get("target"), "blast_radius": "1"}
    if a == "add_entity":
        return {"type": "product", "fqname": v.get("entity"), "blast_radius": "1"}
    if a == "connect_table":
        col = v.get("column")
        return {"type": "fk", "fqname": f"{p}.{col}" if col else p, "blast_radius": "1"}
    if a == "rename_attribute":
        return {"type": "attribute",
                "fqname": f"{p}.{v.get('old_col')}->{v.get('new_col')}", "blast_radius": "1"}
    if a == "move_product":
        return {"type": "product", "fqname": f"{p}->{v.get('new_domain')}", "blast_radius": "1"}
    if a == "remove_fk":
        return {"type": "fk", "fqname": f"{p}.{v.get('column')}", "blast_radius": "1"}
    if a == "rename_product":
        return {"type": "product", "fqname": f"{p}->{v.get('new_name')}", "blast_radius": "1"}
    if a in ("expand_stub", "expand_thin"):
        return {"type": "product", "fqname": p, "blast_radius": "<N>"}
    if a == "change_type":
        return {"type": "attribute", "fqname": f"{p}.{v.get('column')}:{v.get('new_type')}",
                "blast_radius": "1"}
    if a == "add_tag":
        col = v.get("column")
        return {"type": "tag", "fqname": f"{p}.{col}#{v.get('tag')}" if col else f"{p}#{v.get('tag')}",
                "blast_radius": "1"}
    if a == "add_metric":
        return {"type": "metric", "fqname": v.get("metric"), "blast_radius": "1"}
    return {"type": "unknown", "fqname": p or "", "blast_radius": "1"}


def build_lineage(audit):
    out = []
    for r in audit["results"]:
        vibe = r.get("verbatim") or r.get("raw") or f"{r['action']} {_affected(r)['fqname']}"
        interp = r.get("interpretation") or f"{r['action'].replace('_', ' ')} on {_affected(r)['fqname']}"
        out.append({"id": r["id"], "vibe": vibe[:200], "interpretation": interp[:200],
                    "status": _STATUS_MAP.get(r["status"], r["status"]),
                    "affected": _affected(r)})
    return out


def main(industries, use_llm=False, profile=None, endpoint=None, out_dir=None,
         refresh=False):
    out = out_dir or OUT
    os.makedirs(out, exist_ok=True)
    agg = {"per_industry": [], "totals": {}}
    tot = ful = 0
    print(f"{'industry':<20}{'ALL':>8}{'ful':>6}{'adher%':>8}   {'impr':>5}{'impr%':>7}  {'xscope%':>8}")
    for ind in industries:
        try:
            mvm = load_model(os.path.join(V2REPO, ind, "v2", "mvm", "model.json"))
            a = audit_industry(ind, use_llm=True, profile=profile, endpoint=endpoint,
                               mvm_model=mvm, refresh=refresh)
        except Exception as e:
            print(f"{ind:<20}  LLM-EXTRACT FAILED: {str(e)[:80]}")
            continue
        if not a:
            print(f"{ind:<20}  (no v2 ecm)")
            continue
        json.dump(a, open(os.path.join(out, f"{ind}.json"), "w"), indent=2)
        json.dump(build_lineage(a), open(os.path.join(out, f"{ind}.lineage.json"), "w"), indent=2)
        agg["per_industry"].append({k: a[k] for k in
            ("industry", "total_vreqs", "fulfilled", "adherence_all", "by_status",
             "improvement_total", "improvement_fulfilled", "improvement_adherence",
             "extraction_mode")})
        tot += a["total_vreqs"]; ful += a["fulfilled"]
        xs = a.get("xscope_adherence_all")
        print(f"{ind:<20}{a['total_vreqs']:>8}{a['fulfilled']:>6}{a['adherence_all']:>8}"
              f"   {a['improvement_total']:>5}{a['improvement_adherence']:>7}  "
              f"{(xs if xs is not None else a['adherence_all']):>8}  [{a['extraction_mode']}]")
    agg["totals"] = {"total_vreqs": tot, "fulfilled": ful,
                     "adherence_all": round(100.0 * ful / tot, 1) if tot else 0.0,
                     "extraction_mode": "llm"}
    json.dump(agg, open(os.path.join(out, "_aggregate.json"), "w"), indent=2)
    print(f"\nAGGREGATE: {ful}/{tot} = {agg['totals']['adherence_all']}% (all-VReq, ground-truth denominator)")


if __name__ == "__main__":
    args = sys.argv[1:]
    use_llm = "--llm" in args
    refresh = "--refresh" in args
    profile = endpoint = out_dir = None
    inds = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--llm":
            i += 1
        elif a == "--refresh":
            i += 1
        elif a == "--profile":
            profile = args[i + 1]; i += 2
        elif a == "--endpoint":
            endpoint = args[i + 1]; i += 2
        elif a == "--out":
            out_dir = os.path.expanduser(args[i + 1]); i += 2
        else:
            inds.append(a); i += 1
    if not inds:
        inds = ["automotive", "construction", "consumer_goods", "health_insurance",
                "healthcare", "manufacturing", "ngo", "restaurants", "retail",
                "semiconductors", "travel_hospitality", "water_utilities"]
    main(inds, use_llm=use_llm, profile=profile, endpoint=endpoint, out_dir=out_dir,
         refresh=refresh)
