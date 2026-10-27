"""W89.2 survivor filter over run_w89_2.py output. A cell SURVIVES iff: BH-flagged (q=0.10, family-wise over all testable
cells), split-half sign agrees, net-of-fee game-clustered 95% lower bound > 0, and it is not NFL D0 (date-only ticker, may
include in-play snapshots -> contaminated). Part B survives iff BH-flagged AND net_lo > 0. Everything else is DESCRIPTIVE."""
import csv
import os
import sys


def main(out):
    a = list(csv.DictReader(open(os.path.join(out, "partA_cells.csv"))))
    keep = [r for r in a if r["bh"] == "True" and r["split_same"] == "True" and float(r["net_lo"]) > 0 and r["tier"] != "D0"]
    d0 = [r for r in a if r["bh"] == "True" and r["split_same"] == "True" and float(r["net_lo"]) > 0 and r["tier"] == "D0"]
    b = list(csv.DictReader(open(os.path.join(out, "partB_cells.csv"))))
    bk = [r for r in b if r["bh"] == "True" and float(r["net_lo"]) > 0]
    with open(os.path.join(out, "survivors_partA.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=a[0].keys())
        w.writeheader()
        w.writerows(sorted(keep, key=lambda r: (r["family"], r["tier"], r["bucket"], r["book"])))
    print("partA survivors", len(keep), "| NFL D0 excluded", len(d0), "| partB survivors", len(bk), "of", len(b))
    print("bh flagged A", sum(r["bh"] == "True" for r in a), "net_lo<=0 among them",
          sum(r["bh"] == "True" and float(r["net_lo"]) <= 0 for r in a))
    for r in sorted(keep, key=lambda r: (r["family"], r["tier"], r["bucket"], r["book"])):
        print(r["family"], r["tier"], r["bucket"], r["book"], "n", r["n"], "g", r["games"], "pbar", r["pbar"], "f", r["f"],
              "gap", r["gap"], r["side"], "net", r["net_mean"], "lo", r["net_lo"], "p", r["p"])


if __name__ == "__main__":
    main(sys.argv[1])
