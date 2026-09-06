#!/usr/bin/env python3
"""Export the FULL v2 artifact tree from each industry's volume into the fork repo, EXACT v1 layout.

Each industry's volume business/<ind>/v2/ holds the agent-generated tree:
    v2/readme.md
    v2/ecm/{model.json, readme.md, diagram/, docs/, metrics/, ontology/, schemas/, vibes/}
    v2/mvm/{...same...}
which mirrors the committed v1 layout exactly EXCEPT the agent also writes samples/ and
vibes/vibe_lineage.json, neither of which exist in v1. We recursively pull the tree, then prune those
two so the v2 folder is byte-for-byte structurally identical to v1. Industry->profile comes from the
marathon ASSIGN map (each industry's catalog lives on its assigned workspace).
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

REPO = "/Users/user/Documents/projects/lakehouse-business-data-models"
IND_PROFILE = {ind: prof for prof, inds in M.ASSIGN.items() for ind in inds}
# v3.8.0 output-parity-samples-csv: samples/*.csv are now first-class artifacts (install reads them,
# reference repo ships them) so they are NO LONGER pruned on export.
PRUNE_DIRS = set()
PRUNE_FILES = {"vibe_lineage.json"}


def export(ind):
    prof = IND_PROFILE.get(ind)
    if not prof:
        print(f"[{ind}] no profile mapping — skip")
        return False
    cat = M.cat_name(ind)
    src = f"dbfs:/Volumes/{cat}/_metamodel/vol_root/business/{ind}/v2"
    dest = f"{REPO}/data-models/{ind}/v2"
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["databricks", "fs", "cp", "-r", src, dest, "--profile", prof],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[{ind}] EXPORT FAILED: {(r.stderr or r.stdout)[:300]}")
        return False
    # prune to EXACT v1 format
    for root, dirs, files in os.walk(dest, topdown=False):
        for d in list(dirs):
            if d in PRUNE_DIRS:
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
        for f in files:
            if f in PRUNE_FILES:
                try:
                    os.remove(os.path.join(root, f))
                except OSError:
                    pass
    # sanity: must have both ecm/model.json and mvm/model.json
    ecm_mj = os.path.isfile(f"{dest}/ecm/model.json")
    mvm_mj = os.path.isfile(f"{dest}/mvm/model.json")
    nf = sum(len(fs) for _, _, fs in os.walk(dest))
    print(f"[{ind}] exported -> data-models/{ind}/v2 files={nf} ecm_model={ecm_mj} mvm_model={mvm_mj}")
    return ecm_mj and mvm_mj


if __name__ == "__main__":
    inds = sys.argv[1:] or list(IND_PROFILE)
    ok = []
    for ind in inds:
        if export(ind):
            ok.append(ind)
    print(f"=== EXPORT-FULL DONE {len(ok)}/{len(inds)} :: {sorted(ok)} ===")
