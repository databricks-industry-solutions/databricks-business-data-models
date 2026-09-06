#!/usr/bin/env python3
"""
sync_to_repo: post-sector hook for orchestrate_sectors.py.

Mirrors completed-industry artifacts from the Databricks workspace folder
`/Users/<user>@example.com/vibe_runner_models/<industry>/` into a local
git working copy of `amralieg/vibe-business-data-models`, then commits and
pushes one commit per industry.

Industries already present in the local repo are skipped (idempotent).

The hook is intentionally tolerant: any failure surfaces as a log line and
returns a structured result dict. It NEVER raises, so the orchestrator's
sector loop is never blocked by a repo-sync error.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional


DEFAULT_WORKSPACE_ROOT = "/Users/user@example.com/vibe_runner_models"
DEFAULT_REPO_PATH = os.path.expanduser("~/Documents/projects/vibe-business-data-models")
DEFAULT_REPO_REMOTE = "https://github.com/amralieg/vibe-business-data-models.git"
DEFAULT_REPO_BRANCH = "main"
GIT_OP_TIMEOUT_S = 600
EXPORT_TIMEOUT_S = 600
WS_LIST_TIMEOUT_S = 60

XLSX_BUILDER_PATH = os.path.expanduser("~/claude/vibe-agent/json_to_excel.py")
XLSX_REBUILD_TIMEOUT_S = 30


_TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|\s*$")
_ANCHOR_RE = re.compile(r'^\s*<a\s+id="(domain-[^"]+)"></a>\s*$')
_COMPARISON_HEADING = "## Domain & Product Comparison"


def normalize_domain_product_comparison(md_text: str) -> str:
    """
    Repair the 'Domain & Product Comparison' section in industry-root readme.md.

    Bug (agent v0.7.1): the agent appends '\\n<a id=\"domain-X\"></a>\\n' between
    the markdown table header+separator and the first data row, which inserts a
    blank line that breaks the table — every data row then renders as paragraph
    text with literal '|' characters.

    Fix: rewrite the section as one mini-table per domain, with the anchor and
    an H3 heading BEFORE each table. The first 'Domain' column is dropped
    because each table now lives under its own '### domain' heading.

    Idempotent: returns the input unchanged if the section is already in the
    fixed shape (no broken anchor-in-table pattern found).
    """
    if _COMPARISON_HEADING not in md_text:
        return md_text

    lines = md_text.split("\n")

    section_start = None
    for i, line in enumerate(lines):
        if line.strip() == _COMPARISON_HEADING:
            section_start = i
            break
    if section_start is None:
        return md_text

    section_end = len(lines)
    for i in range(section_start + 1, len(lines)):
        if lines[i].startswith("## "):
            section_end = i
            break

    section = lines[section_start:section_end]

    sep_idx = None
    for i, line in enumerate(section):
        if _TABLE_SEP_RE.match(line):
            sep_idx = i
            break
    if sep_idx is None:
        return md_text

    has_anchor_after_sep = False
    j = sep_idx + 1
    while j < len(section):
        s = section[j].strip()
        if s == "":
            j += 1
            continue
        if _ANCHOR_RE.match(section[j]):
            has_anchor_after_sep = True
        break

    if not has_anchor_after_sep:
        return md_text

    blocks: List[tuple] = []
    current_anchor: Optional[str] = None
    current_rows: List[str] = []
    for i in range(sep_idx + 1, len(section)):
        line = section[i]
        m = _ANCHOR_RE.match(line)
        if m:
            if current_anchor is not None:
                blocks.append((current_anchor, current_rows))
            current_anchor = m.group(1)
            current_rows = []
            continue
        if line.lstrip().startswith("|") and not _TABLE_SEP_RE.match(line):
            current_rows.append(line)
    if current_anchor is not None:
        blocks.append((current_anchor, current_rows))

    if not blocks:
        return md_text

    new_section: List[str] = [_COMPARISON_HEADING, ""]
    for anchor_id, rows in blocks:
        domain_label = anchor_id[len("domain-"):].replace("-", " ")
        new_section.append(f'<a id="{anchor_id}"></a>')
        new_section.append(f"### {domain_label}")
        new_section.append("")
        new_section.append("| Subdomain | Product | ECM | MVM | Notes |")
        new_section.append("|---|---|:---:|:---:|---|")
        for row in rows:
            cells = [c.strip() for c in row.split("|")]
            if len(cells) < 7:
                continue
            subdomain = cells[2]
            product = cells[3]
            ecm = cells[4]
            mvm = cells[5]
            notes = cells[6]
            new_section.append(f"| {subdomain} | {product} | {ecm} | {mvm} | {notes} |")
        new_section.append("")

    new_lines = lines[:section_start] + new_section + lines[section_end:]
    return "\n".join(new_lines)


def normalize_industry_readmes(industry_dir: str, log: Optional[Callable[[str], None]] = None) -> Dict[str, object]:
    """
    Apply readme normalizations to <industry_dir>/readme.md (and recursively safe
    on any other readme that exposes the same broken pattern).
    Returns {"normalized": [paths]}.
    """
    if log is None:
        log = print
    normalized: List[str] = []
    for root, _dirs, files in os.walk(industry_dir):
        for fn in files:
            if fn.lower() != "readme.md":
                continue
            path = os.path.join(root, fn)
            try:
                original = open(path, encoding="utf-8", errors="ignore").read()
            except Exception as e:
                log(f"  [readme-normalizer] could not read {path}: {str(e)[:200]}")
                continue
            fixed = normalize_domain_product_comparison(original)
            if fixed != original:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(fixed)
                normalized.append(path)
                log(f"  [readme-normalizer FIRED] rewrote {path} (Domain & Product Comparison section)")
    return {"normalized": normalized}


def _run(cmd: List[str], timeout: int = GIT_OP_TIMEOUT_S, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)


def _ensure_repo_clone(repo_path: str, repo_remote: str, branch: str, log: Callable[[str], None]) -> bool:
    if os.path.isdir(os.path.join(repo_path, ".git")):
        return True
    Path(os.path.dirname(repo_path)).mkdir(parents=True, exist_ok=True)
    log(f"  [repo-sync] cloning {repo_remote} -> {repo_path}")
    p = _run(["git", "clone", "--branch", branch, repo_remote, repo_path], timeout=GIT_OP_TIMEOUT_S)
    if p.returncode != 0:
        log(f"  [repo-sync] clone failed: {p.stderr[:300]}")
        return False
    return True


def _list_workspace_industries(workspace_root: str, profile: str, log: Callable[[str], None]) -> List[str]:
    p = _run(
        ["databricks", "workspace", "list", workspace_root, "--profile", profile, "-o", "json"],
        timeout=WS_LIST_TIMEOUT_S,
    )
    if p.returncode != 0:
        log(f"  [repo-sync] workspace list failed: {p.stderr[:300]}")
        return []
    try:
        items = json.loads(p.stdout) if p.stdout.strip() else []
        if isinstance(items, dict):
            items = items.get("objects") or items.get("items") or []
    except Exception as e:
        log(f"  [repo-sync] could not parse workspace list JSON: {str(e)[:200]}")
        return []
    industries: List[str] = []
    for it in items:
        if it.get("object_type") != "DIRECTORY":
            continue
        path = it.get("path") or ""
        ind = path.rstrip("/").split("/")[-1]
        if ind:
            industries.append(ind)
    return industries


def _extract_counts(model_json_path: str) -> str:
    try:
        with open(model_json_path) as f:
            m = json.load(f)
        model = m.get("model") or m
        domains = model.get("domains", []) or []
        n_d = len(domains)
        n_p = sum(len(d.get("products") or d.get("data_products") or []) for d in domains)
        n_a = sum(
            len(p.get("attributes", []) or [])
            for d in domains
            for p in (d.get("products") or d.get("data_products") or [])
        )
        n_mv = len(model.get("metric_views", []) or [])
        return f"{n_d}d/{n_p}p/{n_a}a/{n_mv}mv"
    except Exception:
        return "?"


def _quality_score(vibes_path: str) -> Optional[str]:
    try:
        txt = open(vibes_path, errors="ignore").read()
    except Exception:
        return None
    import re
    m = re.search(r"Model Quality Score:\s*\**\s*([\d.]+)\s*/\s*100", txt)
    return m.group(1) if m else None


def _export_industry(workspace_root: str, industry: str, dest_path: str,
                     profile: str, log: Callable[[str], None]) -> bool:
    src = f"{workspace_root}/{industry}"
    log(f"  [repo-sync FIRED] exporting {industry} from workspace -> {dest_path}")
    p = _run(
        ["databricks", "workspace", "export-dir", src, dest_path, "--profile", profile],
        timeout=EXPORT_TIMEOUT_S,
    )
    if p.returncode != 0:
        log(f"  [repo-sync] export-dir failed for {industry}: {p.stderr[:300]}")
        return False
    return True


def _commit_and_push(repo_path: str, industry: str, branch: str,
                     log: Callable[[str], None]) -> bool:
    pretty = industry.replace("_", " ").title()
    ecm_counts = _extract_counts(os.path.join(repo_path, industry, "ecm_v1", "model.json"))
    mvm_counts = _extract_counts(os.path.join(repo_path, industry, "mvm_v1", "model.json"))
    ecm_score = _quality_score(os.path.join(repo_path, industry, "ecm_v1", "vibes", "next_vibes.txt"))
    mvm_score = _quality_score(os.path.join(repo_path, industry, "mvm_v1", "vibes", "next_vibes.txt"))
    score_line = ""
    if ecm_score or mvm_score:
        parts = []
        if ecm_score:
            parts.append(f"ECM: {ecm_score}/100")
        if mvm_score:
            parts.append(f"MVM: {mvm_score}/100")
        score_line = "\n\nModel quality score (next_vibes):\n  - " + "\n  - ".join(parts)

    msg = (
        f"Add {pretty} (ECM {ecm_counts}, MVM {mvm_counts})\n\n"
        f"Generated by vibe-modelling-agent (auto-pushed by orchestrator hook)."
        f"{score_line}\n\n"
        f"Co-authored-by: Isaac <user@example.com>"
    )

    add = _run(["git", "-C", repo_path, "add", industry])
    if add.returncode != 0:
        log(f"  [repo-sync] git add failed for {industry}: {add.stderr[:200]}")
        return False
    has_changes = _run(["git", "-C", repo_path, "diff", "--cached", "--quiet"])
    if has_changes.returncode == 0:
        log(f"  [repo-sync] no staged changes for {industry} — already up to date")
        return True
    commit = _run(["git", "-C", repo_path, "commit", "-m", msg])
    if commit.returncode != 0:
        log(f"  [repo-sync] git commit failed for {industry}: {commit.stderr[:300]}")
        return False
    push = _run(["git", "-C", repo_path, "push", "origin", branch], timeout=GIT_OP_TIMEOUT_S)
    if push.returncode != 0:
        log(f"  [repo-sync] git push failed for {industry}: {push.stderr[:300]}")
        return False
    log(f"  [repo-sync FIRED] pushed {industry} to origin/{branch}")
    return True


def _rebuild_state_xlsx(log: Callable[[str], None]) -> None:
    """Fast rebuild of ~/claude/vibe-agent/state/vibe_state_raw.xlsx after a push.

    Reads existing cost_results.json + runtime_results.json + the now-updated
    repo to refresh the dashboard. ~1.5s. Best-effort: any failure is logged
    but never raised — repo-sync MUST NEVER block on dashboard refresh.

    Cost+runtime data is refreshed separately by sync_watchdog.py after each
    cycle that pushed (calls refresh_dashboard.py). This hook just refreshes
    the model-metric / status columns instantly.
    """
    if not os.path.exists(XLSX_BUILDER_PATH):
        log(f"  [xlsx-rebuild SKIP] {XLSX_BUILDER_PATH} not found")
        return
    try:
        import sys as _sys
        proc = subprocess.run(
            [_sys.executable, XLSX_BUILDER_PATH],
            capture_output=True, text=True, timeout=XLSX_REBUILD_TIMEOUT_S,
        )
        if proc.returncode == 0:
            tail = (proc.stdout or "").strip().splitlines()[-1:] or [""]
            log(f"  [xlsx-rebuild FIRED] vibe_state_raw.xlsx refreshed: {tail[0]}")
        else:
            log(f"  [xlsx-rebuild FAILED] rc={proc.returncode} err={(proc.stderr or '')[:200]}")
    except subprocess.TimeoutExpired:
        log(f"  [xlsx-rebuild TIMEOUT] >{XLSX_REBUILD_TIMEOUT_S}s — best-effort, continuing")
    except Exception as _e:
        log(f"  [xlsx-rebuild THREW] {str(_e)[:200]} — best-effort, continuing")


def sync_completed_industries(
    repo_path: str = DEFAULT_REPO_PATH,
    workspace_root: str = DEFAULT_WORKSPACE_ROOT,
    profile: str = "<profile>",
    repo_remote: str = DEFAULT_REPO_REMOTE,
    branch: str = DEFAULT_REPO_BRANCH,
    log: Optional[Callable[[str], None]] = None,
    industry_allowlist: Optional[List[str]] = None,
) -> Dict[str, object]:
    """
    Sync any workspace industry not yet present in the local repo, commit+push each.
    """
    if log is None:
        log = print
    result = {"synced": [], "skipped_existing": [], "failed": [], "error": None}

    if not _ensure_repo_clone(repo_path, repo_remote, branch, log):
        result["error"] = "clone_failed"
        return result

    industries = _list_workspace_industries(workspace_root, profile, log)
    if industry_allowlist:
        # v0.7.2 (alias=sync-allowlist-snake-case) — orchestrator passes display
        # names like "Health Insurance" / "Payments Fintech" into industry_allowlist
        # (these are the names from state.json["industries"] which preserves
        # widget capitalization), but workspace folder names are sanitized
        # snake_case ("health_insurance", "payments_fintech"). Pre-fix the set
        # intersection was empty for every orchestrator-fired sync — silent
        # zero-push on every sector END despite multiple GREEN industries
        # being ready in the workspace. Normalize BOTH sides to snake_case
        # before intersecting so the orchestrator's allowlist actually matches.
        def _to_snake(n):
            import re as _re
            s = str(n).lower()
            s = _re.sub(r"[^a-z0-9_]+", "_", s)
            s = _re.sub(r"_+", "_", s).strip("_")
            return s
        allow = {_to_snake(i) for i in industry_allowlist}
        industries = [i for i in industries if _to_snake(i) in allow]
        log(f"  [sync-allowlist-snake-case FIRED] allowlist normalized to {sorted(allow)} — matched {len(industries)} workspace dirs")
    if not industries:
        log(f"  [repo-sync] no industries found under {workspace_root}")
        return result

    for ind in industries:
        local = os.path.join(repo_path, ind)
        if os.path.isdir(local) and os.listdir(local):
            result["skipped_existing"].append(ind)
            continue
        ok = _export_industry(workspace_root, ind, local, profile, log)
        if not ok:
            result["failed"].append(ind)
            continue
        try:
            normalize_industry_readmes(local, log)
        except Exception as _norm_err:
            log(f"  [readme-normalizer] threw on {ind}: {str(_norm_err)[:200]}")
        ok = _commit_and_push(repo_path, ind, branch, log)
        if ok:
            result["synced"].append(ind)
        else:
            result["failed"].append(ind)

    if result["synced"]:
        log(f"  [repo-sync] {len(result['synced'])} industries pushed — rebuilding xlsx dashboard")
        _rebuild_state_xlsx(log)
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO_PATH)
    ap.add_argument("--workspace-root", default=DEFAULT_WORKSPACE_ROOT)
    ap.add_argument("--profile", default="<profile>")
    ap.add_argument("--branch", default=DEFAULT_REPO_BRANCH)
    ap.add_argument("--industry", action="append", default=None,
                    help="Optional allowlist (repeat flag); default = sync all new")
    args = ap.parse_args()
    out = sync_completed_industries(
        repo_path=args.repo,
        workspace_root=args.workspace_root,
        profile=args.profile,
        branch=args.branch,
        industry_allowlist=args.industry,
    )
    print(json.dumps(out, indent=2))
