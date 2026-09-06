#!/usr/bin/env python3
"""Repair published metric views that reference a column their own DDL does not declare.

Companion to scan_published_mv_column_drift.py. The drift is systematic rather than
random: the metric-view generator emitted the LOGICAL column name, complete with its
role prefix, while the schema DDL applied naming normalization that stripped that prefix.

    metric view                          DDL
    origin_plant_id                      plant_id
    dealer_account_id                    account_id
    primary_aftersales_customer_party_id party_id
    meter_installation_id                installation_id

So most drifted references have exactly one honest destination, and renaming is strictly
better than the agent's prune (which deletes the dimension and silently costs analytic
content). Where the destination is not unique the reference is NOT guessed - the whole
dimension/measure block is removed, which is what the agent already does and leaves the
view installable.

    python3 repair_published_mv_drift.py [repo_root] [--apply]

Default is a dry run. Nothing is written without --apply.
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_published_mv_column_drift import (  # noqa: E402
    EXPR, LITERAL, IDENT, NOT_A_COLUMN, SOURCE, VIEW, parse_ddl, view_blocks,
)

ITEM = re.compile(r"^(?P<indent>[ \t]*)- name:", re.M)


def items(block):
    """(start, end) of every `- name:` YAML list item in a view block.

    An item owns its own line plus every following line indented deeper than its `-`
    marker, which is what ends it at the next sibling item and at the next section key
    (`measures:`, `$$`). Matching that by regex lookahead is what broke the first cut:
    `expr:` is itself `\\w+:` and truncated every item to its name line.
    """
    spans = []
    for m in ITEM.finditer(block):
        depth = len(m.group("indent"))
        at = block.index("\n", m.end()) + 1 if "\n" in block[m.end():] else len(block)
        while at < len(block):
            eol = block.find("\n", at)
            eol = len(block) if eol < 0 else eol + 1
            line = block[at:eol]
            if line.strip() and len(line) - len(line.lstrip()) <= depth:
                break
            at = eol
        spans.append((m.start(), at))
    return spans


def resolve(missing, columns):
    """The one physical column a drifted reference means, or None when it is ambiguous.

    Matching is on whole underscore-delimited segments so `status` can never silently
    become `complaint_status` unless that is the only candidate in the table.
    """
    hits = sorted({c for c in columns
                   if missing.endswith("_" + c) or c.endswith("_" + missing)})
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # Prefer the longest shared tail: primary_x_customer_party_id -> party_id
        # beats -> id, but only when that choice is strictly unique.
        longest = max(len(h) for h in hits)
        best = [h for h in hits if len(h) == longest]
        if len(best) == 1:
            return best[0]
    return None


def missing_in(block, columns):
    out = set()
    for expr in EXPR.findall(block):
        for token in IDENT.findall(LITERAL.sub(" ", expr.lower())):
            if token not in NOT_A_COLUMN and token not in columns:
                out.add(token)
    return out


def repair_block(block, columns):
    """(new_block or None to delete it, {old: new} renames, [unresolvable])."""
    missing = missing_in(block, columns)
    if not missing:
        return block, {}, []
    renames, dead = {}, []
    for name in sorted(missing):
        target = resolve(name, columns)
        if target:
            renames[name] = target
        else:
            dead.append(name)
    if dead:
        return None, {}, dead
    out = block
    for old, new in renames.items():
        out = re.sub(r"\b%s\b" % re.escape(old), new, out)
    return out, renames, []


ITEM_NAME = re.compile(r"- name:\s*\"?([^\"\n]+?)\"?\s*$", re.M)


def repair_view(block, columns):
    """Rewrite one CREATE VIEW block. Returns (text, renames, dropped_count)."""
    renamed = Counter()
    dropped = 0
    repairs = [(start, end) + repair_block(block[start:end], columns)
               for start, end in items(block)]

    def label_of(text):
        m = ITEM_NAME.search(text or "")
        return m.group(1).strip().lower() if m else None

    # Two role-prefixed logical names can collapse onto one physical column
    # (guest_profile_id and preference_guest_profile_id both -> profile_id), and a
    # renamed item can also collide with a healthy item that already carries the
    # physical name. The item this tool rewrote is the one that yields.
    untouched = {label_of(block[s:e]) for s, e, new, ren, dead in repairs
                 if new is not None and not ren}
    taken = {lbl for lbl in untouched if lbl}

    pieces, at = [], 0
    for start, end, new, renames, dead in repairs:
        pieces.append(block[at:start])
        at = end
        if new is None:
            dropped += 1
            continue
        label = label_of(new)
        if renames and label and label in taken:
            dropped += 1
            continue
        if label:
            taken.add(label)
        pieces.append(new)
        for old, target in renames.items():
            renamed["%s -> %s" % (old, target)] += 1
    pieces.append(block[at:])
    return "".join(pieces), renamed, dropped


def repair_file(path, tables, apply_changes):
    text = path.read_text(encoding="utf-8", errors="ignore")
    starts = [(m.start(), m.group(1)) for m in VIEW.finditer(text)]
    if not starts:
        return Counter(), 0, 0
    out, renamed, dropped, views_touched = [], Counter(), 0, 0
    out.append(text[:starts[0][0]])
    for i, (at, _name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        block = text[at:end]
        src = SOURCE.search(block)
        key = ""
        if src:
            parts = [p for p in src.group(1).replace("`", "").split(".") if p]
            key = ".".join(parts[-2:]).lower() if len(parts) >= 2 else ""
        if key not in tables:
            out.append(block)
            continue
        new_block, r, d = repair_view(block, tables[key])
        if r or d:
            views_touched += 1
        renamed.update(r)
        dropped += d
        out.append(new_block)
    if (renamed or dropped) and apply_changes:
        path.write_text("".join(out), encoding="utf-8")
    return renamed, dropped, views_touched


def main(argv):
    apply_changes = "--apply" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    root = Path(args[0]) if args else Path.home() / "Documents/projects/lakehouse-business-data-models"
    models = root / "data-models"
    if not models.is_dir():
        print("no data-models directory under %s" % root)
        return 2

    all_renames, all_dropped, all_views, touched_models = Counter(), 0, 0, 0
    for industry in sorted(p for p in models.iterdir() if p.is_dir()):
        for version in sorted(p for p in industry.iterdir()
                              if p.is_dir() and re.match(r"^v\d+$", p.name)):
            for size in sorted(p for p in version.iterdir() if p.is_dir()):
                metrics = size / "metrics"
                if not metrics.is_dir() or not (size / "schemas").is_dir():
                    continue
                tables = parse_ddl(size / "schemas")
                m_ren, m_drop, m_views = Counter(), 0, 0
                for sql in sorted(metrics.glob("*.sql")):
                    r, d, v = repair_file(sql, tables, apply_changes)
                    m_ren.update(r)
                    m_drop += d
                    m_views += v
                if not m_ren and not m_drop:
                    continue
                touched_models += 1
                all_renames.update(m_ren)
                all_dropped += m_drop
                all_views += m_views
                print("%-34s %2d view(s)  %3d rename(s)  %2d block(s) removed"
                      % ("%s/%s/%s" % (industry.name, version.name, size.name),
                         m_views, sum(m_ren.values()), m_drop))

    print("\n" + "=" * 72)
    print("%s" % ("APPLIED" if apply_changes else "DRY RUN - re-run with --apply"))
    print("models repaired    : %d" % touched_models)
    print("views touched      : %d" % all_views)
    print("references renamed : %d" % sum(all_renames.values()))
    print("blocks removed     : %d" % all_dropped)
    if all_renames:
        top = all_renames.most_common(12)
        print("most common renames: %s" % ", ".join("%s(%d)" % (k, n) for k, n in top))
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
