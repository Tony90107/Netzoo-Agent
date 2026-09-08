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


def _puma(args) -> Puma:
    """Build the network, and explain the one option netZooPy cannot honour.

    `remove_missing` works for PANDA and fails for PUMA in both processing
    modes, because `Puma` does not inherit from `Panda`: it calls
    `Panda.processData(self, ...)` unbound, and that function's
    `self.__remove_missing()` mangles to `self._Panda__remove_missing`, which a
    `Puma` instance does not have. `Puma` defines its own `__remove_missing`,
    mangled to `_Puma__remove_missing`, so it can never be reached from there.

    Nothing here works around that. Reimplementing the filtering would mean this
    wrapper owning a piece of PUMA's semantics with no upstream reference to
    check it against. What it does is replace an obscure `TypeError` about
    integral indices with the reason, since the flag's previous behaviour --
    accepted and silently ignored -- was the actual defect being repaired.
    """
    try:
        return Puma(
            args.expression, args.motif, args.ppi, args.mir,
            modeProcess=args.mode_process,
            save_tmp=True,
            remove_missing=args.rm_missing,
            keep_expression_matrix=bool(args.lioness),
        )
    except (AttributeError, TypeError) as error:
        if not args.rm_missing:
            raise
        raise SystemExit(
            f"netZooPy's PUMA cannot honour --rm_missing ({type(error).__name__}: "
            f"{error}).\n"
            "Puma does not inherit from Panda, so the name-mangled "
            "__remove_missing call inside Panda.processData cannot resolve on a "
            "Puma instance. PANDA supports the same flag; PUMA does not, in any "
            "processing mode. Run without --rm_missing, or filter the priors "
            "before passing them in."
        ) from error


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
    # Passed through, where the legacy script accepted it and threw it away:
    # upstream declared `r` to getopt as taking no argument and then assigned
    # that argument to `rm_missing`, so the value was always the empty string
    # and the flag never did anything. It does something now -- it fails, with
    # the reason, which is what netZooPy's PUMA can currently support. See
    # `_puma` below. Passing it through rather than refusing it here means a
    # fixed upstream simply starts working.
    parser.add_argument("-r", "--rm_missing", action="store_true")
    args = parser.parse_args(argv)

    print("Input data:")
    print("Expression:", args.expression)
    print("Motif data:", args.motif)
    print("PPI data:", args.ppi)
    print("miR file:", args.mir)
    print("Mode process:", args.mode_process)

    print("Start Puma run ...")
    puma_obj = _puma(args)
    puma_obj.save_puma_results(args.out)

    if args.lioness:
        from netZooPy.lioness.lioness_for_puma import LionessPuma

        LionessPuma(puma_obj).save_lioness_results(args.lioness)
    print("All done!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
