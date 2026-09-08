#!/usr/bin/env python3
"""Run PUMA, with the input-processing mode selectable.

netZooPy exposes no `netzoopy puma` command -- its CLI carries `panda` and
`lioness` only -- so the sole route to PUMA is the legacy
`netZooPy/puma/run_puma.py`. That script constructs `Puma(...)` without a
`modeProcess` argument at all, taking the class default `"union"`, and offers no
flag to change it. Upstream's own reference network
(`tests/puma/matlablike_test_puma.txt`) is built under `"legacy"`, so no numeric
comparison against it was reachable through the production path: the two run
different processing modes, which is a difference in what is computed rather
than in precision.

This replaces that script with the same four lines of substance plus
`--mode_process`. Everything else is deliberately identical, and a test asserts
value-for-value equality with the upstream script when the flag is not given,
so adding the option changes no existing result.

`scripts/run_puma_precomputed.py` already owns the equivalent path for a
supplied co-expression matrix; this is the ordinary case beside it.
"""

from __future__ import annotations

import argparse
import sys

from netZooPy.puma.puma import Puma

#: `Puma.__init__`'s own vocabulary. Rejecting anything else matters more than
#: it looks: a mode that silently fell back to the default would let a test
#: pinning "legacy reproduces upstream's reference" pass while the flag did
#: nothing, and the test would then be pinning the default under another name.
MODES = ("union", "legacy", "intersection")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run PUMA on expression, motif, PPI and miRNA inputs.",
    )
    parser.add_argument("-e", "--expression", required=True)
    parser.add_argument("-m", "--motif", required=True)
    parser.add_argument("-p", "--ppi", required=True)
    parser.add_argument("-i", "--mir", required=True)
    parser.add_argument("-o", "--out", default="output_puma.txt")
    parser.add_argument("-q", "--lioness", default="")
    parser.add_argument(
        "--mode_process", choices=MODES, default="union",
        help="How genes and TFs from the priors are combined (default: union, "
             "which is what the legacy script always used).",
    )
    # Accepted and ignored, exactly as before. Upstream declares `r` to getopt
    # as taking no argument and then assigns that argument to `rm_missing`, so
    # the value is always the empty string and `remove_missing` is always
    # falsy -- the flag has never done anything. Reproducing that is the point:
    # this change is about `modeProcess` and must move nothing else. Making the
    # flag work is a separate decision, and a real one, since it would change
    # every network built with it.
    parser.add_argument("-r", "--rm_missing", action="store_true")
    args = parser.parse_args(argv)

    print("Input data:")
    print("Expression:", args.expression)
    print("Motif data:", args.motif)
    print("PPI data:", args.ppi)
    print("miR file:", args.mir)
    print("Mode process:", args.mode_process)

    print("Start Puma run ...")
    puma_obj = Puma(
        args.expression, args.motif, args.ppi, args.mir,
        modeProcess=args.mode_process,
        save_tmp=True,
        remove_missing=False,
        keep_expression_matrix=bool(args.lioness),
    )
    puma_obj.save_puma_results(args.out)

    if args.lioness:
        from netZooPy.lioness.lioness_for_puma import LionessPuma

        LionessPuma(puma_obj).save_lioness_results(args.lioness)
    print("All done!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
