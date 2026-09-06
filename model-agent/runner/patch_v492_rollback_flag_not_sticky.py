"""v4.9.2 - stop latching the fidelity rollback recommendation.

The write site only ever set the flag True. The gate is re-evaluated after each
remediation round, so a run that failed early and recovered kept advertising
rollback_recommended=True with passed=True on the same line.

Live: coffee_roastery run 934019101231955 (v4.9.1) - 14:11:44 precision 0.6667 FAILED,
14:14:37 gate passed, flag still True, 14:17:03 physical ground truth precision=1.0.
"""

import json
import os

NB = os.path.join(os.path.dirname(__file__), "..", "agent", "dbx_vibe_modelling_agent.ipynb")

# Anchored on the CLOSE of the failing branch, not its opening line. Inserting the else:
# right after the `= True` assignment silently re-parents the demote/warning body that
# follows it onto the passing path, because that body sits at the same indent as the new
# else: block. The behavioral test caught the inversion.
OLD = '''                else:
                    self.logger.info("  Fidelity gates FAILED (no user-provided VibeContract \u2014 informational only)")
            self.logger.info('''

NEW = '''                else:
                    self.logger.info("  Fidelity gates FAILED (no user-provided VibeContract \u2014 informational only)")
            else:
                # The gate runs again after every remediation round. Latching on the first
                # failure made a recovered run still advertise rollback_recommended=True
                # next to passed=True (coffee_roastery run 934019101231955: 0.6667 FAILED
                # at 14:11:44, gate passed at 14:14:37, ground truth precision=1.0).
                if self.widgets_values.get("vibe_rollout_rollback_recommended"):
                    self.logger.info(
                        "  [fidelity-rollback-flag-clear FIRED v4.9.2] fidelity gate now "
                        "passes - clearing the rollback recommendation left by an earlier "
                        "failed round alias=fidelity-rollback-flag-clear"
                    )
                self.widgets_values["vibe_rollout_rollback_recommended"] = False
            self.logger.info('''


def sub_once(src, old, new, label):
    n = src.count(old)
    assert n == 1, "%s: expected 1 occurrence, got %d" % (label, n)
    return src.replace(old, new, 1)


def main():
    nb = json.load(open(NB))
    touched = []

    for idx, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        src = cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])

        if OLD in src:
            cell["source"] = sub_once(src, OLD, NEW, "rollback clear branch")
            touched.append(idx)
            continue

        if '__AGENT_VERSION__ = "4.9.1"' in src:
            cell["source"] = sub_once(src, '__AGENT_VERSION__ = "4.9.1"',
                                      '__AGENT_VERSION__ = "4.9.2"', "version bump")
            touched.append(idx)

    assert len(touched) == 2, "expected 2 cells touched, got %s" % (touched,)
    json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
    print("patched cells:", touched)


if __name__ == "__main__":
    main()
