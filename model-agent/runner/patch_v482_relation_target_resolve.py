"""v4.8.2 alias=verifier-relation-target-resolvable.

Live proof (coffee_roastery run 186683145042109, catalog vibe_e2e_v481):
VREQ-003 "green coffee lots must be traceable from the origin purchase through the
roast batch into the finished package ... with real foreign keys" scored FAILED on the
physical ground-truth pass and dragged fidelity precision to 0.3333, while the FKs it
asks for physically exist:

    sourcing.gc_lot.purchase_contract_id  -> sourcing.purchase_contract.purchase_contract_id
    roasting.roast_batch.gc_lot_id        -> sourcing.gc_lot.gc_lot_id
    roasting.finished_package.roast_batch_id -> roasting.roast_batch.roast_batch_id

(all 13/13 sourcing FKs verified live against information_schema.)

Root cause, reproduced offline against the run's own model.json: the relation branch of
_verify_deterministic iterates req.scope_targets and RETURNS on the first target. The
first target is the vibe's own wording ("origin purchase"), which is not a product name
anywhere in the model, so the substring FK match finds nothing and the branch returns a
hard "failed" -- "I could not resolve this name" is reported as "the FK does not exist".
The later targets (roasting.roast_batch, roasting.finished_package) DO resolve and DO
have the FKs, but the early return never reaches them.

Mid-loop this was invisible because a non-fulfilled deterministic verdict routes to the
LLM verifier, which read the model and correctly said fulfilled. The physical pass has
no LLM route, so _v412_combine_verdict took the deterministic "failed" as authoritative
and overwrote the grounded verdict. That is mission failure-class #1 (verifier
false-negative / lying scoreboard) with the exact "too literal name matching" shape.

Fix: in the relation branch, skip a scope_target that names nothing in the model
universe (no domain, no product, no attribute -- compared on a punctuation-insensitive
normal form) and let the loop try the next target. If no target resolves, the function
falls through to the existing "no specific pattern matched" partial, which
_gt_is_blind_partial downgrades to unknown so _v412_combine_verdict defers to the
grounded mid-loop verdict instead of inventing a failure.

The guard sits ahead of BOTH verbs, so it also closes the opposite-polarity hole: a
remove-FK VREQ naming an unresolvable target previously hit "not _rel_linked -> removed"
and false-FULFILLED. Unresolvable now means unknown in both directions.
"""

import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

OLD = """                _rtl = _v407_resolve_dp(tl, product_keys)
"""

NEW = """                _rel_norm = lambda _s: re.sub(r"[^a-z0-9]", "", str(_s or "").lower())
                _rel_tn = _rel_norm(tl)
                _rel_known = (
                    tl in domain_names
                    or tl in product_keys
                    or any(_rel_tn == _rel_norm(_d) for _d in domain_names)
                    or any(_rel_tn in (_rel_norm(_pk), _rel_norm(_pk.split(".")[-1])) for _pk in product_keys)
                    or any(_rel_tn == _rel_norm(_ak.split(".")[-1]) for _ak in attr_keys)
                )
                if not _rel_known:
                    try:
                        self.logger.info(f"  [verifier-relation-target-resolvable FIRED v4.8.2] {req.id}: scope_target '{target}' names no domain/product/attribute in the model \\u2014 skipping it instead of scoring the VREQ failed on a name miss alias=verifier-relation-target-resolvable")
                    except Exception:
                        pass
                    continue
                _rtl = _v407_resolve_dp(tl, product_keys)
"""

VER_OLD = '__AGENT_VERSION__ = "4.8.1"'
VER_NEW = '__AGENT_VERSION__ = "4.8.2"'


def main():
    nb = json.load(open(NB))

    cell = nb["cells"][100]
    src = cell.get("source", [])
    text = "".join(src) if isinstance(src, list) else src
    if "verifier-relation-target-resolvable" in text:
        print("already applied")
        return 0
    assert text.count(OLD) == 1, f"relation anchor count = {text.count(OLD)}, want 1"
    cell["source"] = text.replace(OLD, NEW, 1)
    print("applied: relation target resolvability guard")

    c1 = nb["cells"][1] if VER_OLD in "".join(nb["cells"][1].get("source", [])) else nb["cells"][0]
    t1 = "".join(c1.get("source", []))
    assert t1.count(VER_OLD) == 1, f"version anchor count = {t1.count(VER_OLD)}, want 1"
    c1["source"] = t1.replace(VER_OLD, VER_NEW, 1)
    print("applied: version bump 4.8.1 -> 4.8.2")

    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
