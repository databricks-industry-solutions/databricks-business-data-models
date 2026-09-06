#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vov_v2_marathon as M

PROFILE = "my-adp"
M.WAREHOUSE[PROFILE] = "2ad1b26db73a7c6f"
preferred = "abfss://unity-catalog-storage@dbstoragem6ow6jhr3huvi.dfs.core.windows.net/7405617889454112"
bases = M._external_location_bases(PROFILE) + M._managed_bases(PROFILE)
cand = [preferred] + [b for b in bases if b != preferred]


def ensure_cat(name: str) -> None:
    cats = M.dbj(["catalogs", "list"], PROFILE)
    items = cats if isinstance(cats, list) else cats.get("catalogs", [])
    exists = any(c.get("name") == name for c in items)
    if not exists:
        last = "none"
        created = False
        for base in cand:
            for loc in (f"{base}/{name}", base):
                try:
                    M.sql_exec(PROFILE, f"CREATE CATALOG `{name}` MANAGED LOCATION '{loc}'")
                    print("created", name, "at", loc)
                    created = True
                    break
                except Exception as e:
                    last = str(e)[:240]
                    if "already exists" in last.lower():
                        created = True
                        break
            if created:
                break
        if not created:
            raise SystemExit(f"fail create {name}: {last}")
    else:
        print("exists", name)
    M.sql_exec(PROFILE, f"CREATE SCHEMA IF NOT EXISTS `{name}`.`_metamodel`")
    try:
        M.sql_exec(PROFILE, f"CREATE VOLUME IF NOT EXISTS `{name}`.`_metamodel`.`vol_root`")
    except Exception as e:
        print("vol warn", name, str(e)[:200])
    print("metamodel ok", name)


def main():
    for n in [
        "vibe_vibetest_small_v1",
        "vibetest_small_ecm",
        "vibetest_small_ecm_v1",
        "vibetest_small_mvm",
        "vibetest_small_mvm_v1",
    ]:
        ensure_cat(n)
    print("DONE")


if __name__ == "__main__":
    main()
