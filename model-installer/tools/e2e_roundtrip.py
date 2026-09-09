#!/usr/bin/env python3
"""Install a model with samples, audit it, uninstall it, and prove the metastore came
back to exactly where it started.

    python3 e2e_roundtrip.py <profile> <notebook_path> <catalog> <industry> \
        [local_install=<path>] [sample_rows=10]

The three snapshots are kept so a failure can be inspected afterwards:
    /tmp/<catalog>_before.json   /tmp/<catalog>_installed.json   /tmp/<catalog>_after.json
"""
import re
import subprocess
import sys

import metastore_snapshot as snap
import run_installer_job as runner


def step(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def rescue_install_log(profile, result, catalog):
    """Copy the install log off the volume before uninstall deletes the catalog holding it.

    Without this the one artifact that explains a sample failure dies with the thing it
    was diagnosing, and recovering it costs a full re-install.
    """
    match = re.search(r"log:\s*(/Volumes/\S+\.log)", result or "")
    if not match:
        print("  (no install log path in the result string - nothing to rescue)")
        return None
    local = "/tmp/%s_install.log" % catalog
    copy = subprocess.run(
        ["databricks", "fs", "cp", "dbfs:" + match.group(1), local,
         "--overwrite", "--profile", profile],
        capture_output=True, text=True)
    if copy.returncode != 0:
        print("  (could not rescue %s: %s)" % (match.group(1), copy.stderr.strip()[:160]))
        return None
    print("  install log rescued -> %s" % local)
    return local


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    profile, notebook, catalog, industry = argv[1:5]
    extra = dict(a.split("=", 1) for a in argv[5:])
    rows = extra.pop("sample_rows", "10")

    step("1. snapshot BEFORE")
    before = snap.capture(profile, only={catalog})
    snap.json.dump(before, open("/tmp/%s_before.json" % catalog, "w"), indent=1)
    print(snap.summarize(before))

    step("2. install with samples (%s rows/table)" % rows)
    params = {"operation": "Install", "model": industry, "model_size": "mvm",
              "catalog_name": catalog, "generate_samples": "Yes", "sample_rows": rows}
    params.update(extra)
    state, result = runner.submit_and_wait(profile, notebook, params)
    print(result)
    if state != "SUCCESS":
        return 1

    step("3. snapshot INSTALLED")
    installed = snap.capture(profile, only={catalog})
    snap.json.dump(installed, open("/tmp/%s_installed.json" % catalog, "w"), indent=1)
    print(snap.summarize(installed))

    step("4. audit the installed samples")
    audit = subprocess.run([sys.executable, "-u", "audit_installed_samples.py",
                            catalog, "--profile", profile], text=True)
    audit_ok = audit.returncode == 0

    step("5. rescue the install log, then uninstall (widgets only, no local_install)")
    rescue_install_log(profile, result, catalog)
    # Uninstall is driven from the widgets alone: the install manifest in the target
    # catalog records exactly what to drop, so local_install must NOT be required here.
    uninstall_extra = {k: v for k, v in extra.items() if k != "local_install"}
    params = {"operation": "Uninstall", "model": industry, "model_size": "mvm",
              "catalog_name": catalog}
    params.update(uninstall_extra)
    state, result = runner.submit_and_wait(profile, notebook, params)
    print(result)
    if state != "SUCCESS":
        return 1

    step("6. snapshot AFTER, and diff against BEFORE")
    after = snap.capture(profile, only={catalog})
    snap.json.dump(after, open("/tmp/%s_after.json" % catalog, "w"), indent=1)
    print("before: %s" % snap.summarize(before))
    print("after : %s" % snap.summarize(after))
    rowsd = snap.diff(before, after)
    for row in rowsd:
        print("  " + row)
    print("\nROUND TRIP: %s | sample audit: %s"
          % ("CLEAN - the metastore is back to its pre-install state" if not rowsd
             else "DIRTY - %d difference(s)" % len(rowsd),
             "passed" if audit_ok else "FAILED"))
    return 0 if (not rowsd and audit_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
