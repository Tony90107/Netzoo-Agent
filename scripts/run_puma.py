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


def _reach_upstreams_remove_missing() -> None:
    """Make netZooPy's own gene filter reachable from a Puma instance.

    `Puma` does not inherit from `Panda`; it calls `Panda.processData(self, ...)`
    unbound. Inside that function `self.__remove_missing()` mangles to
    `self._Panda__remove_missing`, which a `Puma` instance does not have --
    while `Puma`'s own definition mangles to `_Puma__remove_missing` and is
    therefore unreachable from the only place that calls it. The flag has never
    worked for PUMA in any release, and the legacy CLI script hid that by
    accepting the option and dropping it.

    The alias binds one name to the other. No filtering logic is added here:
    what runs is upstream's own `Puma.__remove_missing`, which it plainly meant
    to be called. The result is corroborated rather than merely plausible --
    PUMA and PANDA reduce the same priors to the same 913 genes, as two filters
    keeping "genes present in the motif prior" must.
    """
    if not hasattr(Puma, "_Panda__remove_missing"):
        Puma._Panda__remove_missing = Puma._Puma__remove_missing


def _puma(args) -> Puma:
    """Build the network, honouring `--rm_missing` only where it can work.

    Upstream's own docstring says the filter "Works only if
    modeProcess='legacy'", and that is exactly what the other modes do: they
    fail deep inside with a `TypeError` about integral indices. Refusing up
    front states a documented limit instead of surfacing it as an accident.
    """
    if args.rm_missing:
        if args.mode_process != "legacy":
            raise SystemExit(
                f"--rm_missing needs --mode_process legacy (got "
                f"{args.mode_process}). netZooPy's own documentation limits the "
                "filter to that mode, and the others fail inside the priors "
                "rather than ignoring it."
            )
        _reach_upstreams_remove_missing()
    return Puma(
        args.expression, args.motif, args.ppi, args.mir,
        modeProcess=args.mode_process,
        save_tmp=True,
        remove_missing=args.rm_missing,
        keep_expression_matrix=bool(args.lioness),
    )


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
    # Works now, where the legacy script accepted it and threw it away:
    # upstream declared `r` to getopt as taking no argument and then assigned
    # that argument to `rm_missing`, so the value was always the empty string.
    # See `_reach_upstreams_remove_missing`. Only `legacy` can honour it.
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
