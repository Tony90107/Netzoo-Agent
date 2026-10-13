"""Second-opinion "named" pre-measure: does a bare command get "named", and a named method asked for a result it
cannot give never get it? One call per pair, the production message format, the free check model.

Usage (repository root, provider key in the environment): python docs/research-log/named-workflow-2026-10-13/premeasure.py
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "scripts")
from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, SystemMessage  # noqa: E402
from netzoo_agent_core.contracts.capability_check import second_opinion_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import _SECOND_OPINION, _own_llm  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402

PAIRS = [  # (expected, request words, workflow)
    ("named", "請跑 PANDA", "PANDA"), ("named", "請跑 CONDOR。", "CONDOR"), ("named", "Run PANDA on my files.", "PANDA"),
    ("named", "Please run CONDOR.", "CONDOR"), ("named", "Go ahead and run BONOBO.", "BONOBO"), ("named", "跑 PANDA", "PANDA"),
    ("not named", "Use GIRAFFE to output a different TF-gene regulatory wiring matrix for every patient", "GIRAFFE"),
    ("not named", "請用 SAMBAR 分出 expression-based 病患亞型", "SAMBAR"),
    ("not named", "Use OTTER to give me a separate network for each sample", "OTTER"),
    ("not named", "Run DRAGON on our three omics layers in one network", "DRAGON"),
    ("not named", "Run CONDOR on our gene-gene co-expression network", "CONDOR"),
    ("not named", "Run PUMA to find which lncRNAs sponge miRNAs", "PUMA"),
    ("not named", "Use PANDA scores to prove that TF X causally activates gene Y", "PANDA"),
    ("all", "a cohort-wide TF-to-gene network", "PANDA"),
]


def results(workflow):
    return " ".join(item.text for item in sheet_entries().values() if item.kind == "produces" and item.workflow == workflow
                    and item.level == "direct")


def run(pair):
    expected, words, workflow = pair
    llm = _own_llm(os.environ["OPENROUTER_CAPABILITY_MODEL"], int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "9000")))
    schema = second_opinion_model(1)
    listed = f'1. Request words: "{words}" | {workflow} produces: {results(workflow)}'
    try:
        payload, _ = semantic_payload(llm.with_structured_output(schema, method="function_calling", include_raw=True,
                                                                 strict=True).invoke(
            [SystemMessage(content=_SECOND_OPINION), HumanMessage(content=listed)]))
        answer = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload).a1
    except Exception as error:  # noqa: BLE001
        answer = f"ERROR {type(error).__name__}"
    ok = (answer == "named") if expected == "named" else (answer == "all") if expected == "all" else answer in ("none", "part")
    return f"{'ok ' if ok else 'XX '} expect {expected:9} got {answer:6} | {workflow:7} | {words}"


with ThreadPoolExecutor(4) as pool:
    for line in pool.map(run, PAIRS):
        print(line)
