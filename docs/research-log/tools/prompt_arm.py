"""Run the traced harness with the semantic prompt of before or after `b670faa` (Log 228).

Usage: python docs/research-log/tools/prompt_arm.py <pre|post|no1|no2|pad> <harness args...>
       python docs/research-log/tools/prompt_arm.py <pre|post|no1|no2|pad> --fingerprint
       python docs/research-log/tools/prompt_arm.py pad --show

The code is the checkout's; only the semantic prompt text changes. `pre` removes
the two paragraphs `b670faa` added to the semantic interpreter prompt, so its
fingerprint must equal the recorded pre-`b670faa` value (legacy `b9b01cd2db6f`);
`post` leaves the prompt as it is (`d2a9afddad86`). `no1` and `no2` remove only
the first (regulator roles of a selected prior) or only the second (a file's
stated input role) paragraph (Log 230). `pad` replaces both, in place, with
neutral padding of the same line count, indentation and near-equal length and
token count, to separate a length/position effect from their content (Log 232).
The paragraphs were removed from the prompt in Log 236, so only `post` runs on
later commits; the other arms need a checkout from b670faa up to 5e631e7.
"""
import runpy
import sys
from dataclasses import replace

from traces import RESEARCH, ROOT

sys.path.insert(0, str(ROOT / "scripts"))

import netzoo_agent_core.graph.prompts as graph_prompts  # noqa: E402

ADDED = (
    """  When reconstructing a network from a user-selected regulatory prior, preserve
  the regulator and target roles described for that prior unless the user asks
  to exclude them. "Contains not only transcription factors but also predicted
  targets of small RNAs" describes the small RNAs as regulators, not target nodes.
  Small RNAs are not automatically miRNAs; distinguish explicit biological
  descriptions from filename hints and leave only genuinely unknown subtypes
  unresolved. Do not invent a TF-only alternative that discards stated regulators.
  Apply this input-to-output role reasoning to every artifact, not to a named tool.
""",
    """Preserve a file's stated input role independently of its name: a user-selected
prior table is a prior, not an already inferred regulatory network. Expression,
design, PPI, regulator lists, mutation, pathway and omics-layer files likewise
remain current inputs when explicitly supplied. Other files in the same folder
do not create competing scientific goals or override a selected input.
""",
)

_PAD_WORDS = (
    "This padding line is intentionally neutral and carries no instruction. "
    "It keeps the prompt the same length for a controlled comparison only. "
).split()


def neutral_padding(paragraph: str) -> str:
    """Neutral words, line for line, matching each line's indentation and length."""
    words = iter(_PAD_WORDS * 40)
    lines = []
    for line in paragraph.rstrip("\n").split("\n"):
        indent = line[: len(line) - len(line.lstrip())]
        text = indent
        while len(text) < len(line) - 3:
            text += ("" if text == indent else " ") + next(words)
        lines.append(text)
    return "\n".join(lines) + "\n"


arm = sys.argv.pop(1)
REMOVED = {"pre": ADDED, "post": (), "no1": ADDED[:1], "no2": ADDED[1:], "pad": ADDED}
if arm not in REMOVED:
    raise SystemExit("arm must be pre, post, no1, no2 or pad")
if REMOVED[arm]:
    original = graph_prompts.build_graph_prompts

    def pre_prompts(policy):
        prompts = original(policy)
        semantic = prompts.semantic
        for paragraph in REMOVED[arm]:
            if semantic.count(paragraph) != 1:
                raise SystemExit("the b670faa paragraph is not in the prompt exactly once")
            semantic = semantic.replace(
                paragraph, neutral_padding(paragraph) if arm == "pad" else "", 1,
            )
        return replace(prompts, semantic=semantic)

    graph_prompts.build_graph_prompts = pre_prompts
    import evaluate_routing  # noqa: E402

    evaluate_routing.build_graph_prompts = pre_prompts

if sys.argv[1:] == ["--show"]:
    import tiktoken

    encoding = tiktoken.get_encoding("o200k_base")
    for paragraph in ADDED:
        padding = neutral_padding(paragraph)
        print(padding)
        print("chars", len(paragraph), "->", len(padding), "lines",
              paragraph.count("\n"), "->", padding.count("\n"), "tokens",
              len(encoding.encode(paragraph)), "->", len(encoding.encode(padding)), "\n")
elif sys.argv[1:] == ["--fingerprint"]:
    sys.argv = [sys.argv[0]]
    runpy.run_path(str(RESEARCH / "tools" / "fingerprint.py"), run_name="__main__")
else:
    runpy.run_path(str(RESEARCH / "live-semantic-trace-2026-09-23-harness.py"), run_name="__main__")
