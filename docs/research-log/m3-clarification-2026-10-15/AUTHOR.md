# Independent heldout author record

Author role: blind scientific-contract scenario author. Date: 2026-10-15.
Repository verified as `/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`; branch verified as `evidence-contract-grounding`. No commits or implementation edits were made.

## Isolation and evidence

I did not read the capability sheet, routing/interpretation/contracts modules, implementation tests, previous research logs, previous evaluation prompts/results, or run the agent. I created the scenarios independently from the allowed workflow contracts. The allowed `scripts/workflow_registry.py` was read, although its full tool output was truncated; all gold notes rely on the complete relevant current YAML text, not an unobserved portion of that output. The 13 workflow YAML files were read directly; the two LIONESS YAML files affected by output truncation were read separately. No external factual research was used.

Graph tier: Verify. Project: `Users-chenzhonghan-Documents-LLM-AGENT-netzoo_agent`. Parent evidence and this author's index/coverage check identify generation `2026-10-09T10:34:45Z`. Coverage reported `no_recorded_issue` for workflows and registry, with registry `metadata_changed`. This is a stale, best-effort index, not proof of completeness. Current allowed source is the evidence used. Bounded graph searches for CONDOR validator/executor definitions returned zero results and no additional pages; a permitted fallback path listing found `docker/run-condor`, but its contents were not needed or read. An uncertain overlap-based CONDOR case was replaced with a numeric-weight case grounded explicitly in YAML.

## Corpus and scoring

The JSON contains 120 scenarios and 140 separately scored requirements: P30, N30, MX20 (two requirements each), U30, K10. The K cases have two turns and must be judged on the final turn with unchanged first-turn constraints retained; five end supported and five end not_supported. All 13 registered workflows are represented. There are 42 run-form prompts (35%), including 15 unknown run prompts, and eight prompts of at least 100 whitespace-separated words. Traditional Chinese and English scenarios are included.

`words` is an exact substring of the prompt or the persistent conversation. `supported` means the specified behavior is in the declared workflow contract, assuming explicitly stated valid inputs; it is not a claim that synthetic local paths exist or an execution succeeded. `needs_input` is reserved for known absent required artifacts. `with_step` denotes an explicitly permitted conversion or multi-workflow sequence requiring the declared validation. `needs_fact` denotes a scientifically or contractually deciding unknown (for example sample count, data modality, preprocessing state, shape, setting, hardware constraint, or intended output), with an explicit `deciding_fact`; it is not mere absence of a filename. `not_supported` concerns the precise requested behavior/constraint in the current registered workflow, not all conceivable external software.

Mixed cases must be scored independently: a feasible artifact does not validate a stronger requested artifact, interpretation, or setting. Unknown cases should remain conditional until the deciding fact is established; the corpus does not prescribe a particular clarification sentence or prohibit discovering a fact by validated inspection when available.

## Validation and limitations

Programmatic validation passed for exact counts, unique IDs, all exact quote substrings, valid K turn shape, K positive/negative balance, two requirements per mixed case, deciding facts for all unknowns, all 13 workflows, run balance, and eight long prompts. No agent execution or result-aware editing occurred.

No unresolved gold uncertainty is known. External conversion feasibility in with_step cases is limited to the conversion/validation explicitly described by the YAML; no automatic handoff is implied. The known minimum sample counts and LIONESS-DRAGON output cap are treated as hard current adapter limits. Novelty means independent construction without access to old cases; literal cross-corpus deduplication was deliberately not performed because it would violate blindness. A separate reviewer should audit gold after implementation freeze before evaluating outputs.

## Current workflow source SHA-256

- `workflows/bonobo.yaml`: `7fdaac0232026179c54150b4652adb28ef16b5a2d543ac2f9a71aee4c1da0a2f`
- `workflows/cobra.yaml`: `31f921ab1dfad0b6315bd9d20c80dc53c5e66058f7696dac1d6159ba712354d5`
- `workflows/condor.yaml`: `1d3e8419183972f81b46d7dcb93a6a49a6bfffdaf84b5958c413f0ee42f10cb8`
- `workflows/dragon.yaml`: `f9cde02da7226c555ab4768e85089a85c2a4a1345e54e6ac32f3e9b5574414b9`
- `workflows/giraffe.yaml`: `8bd86d05e83d914a31d2b6fb17b8d5a309bd4c029b2b1be37b71c84a9d20385a`
- `workflows/lioness-coexpression.yaml`: `c89eea7c8162e0ad8e17c7c97a56572f9770e603edbd1a139c8180b7636e0968`
- `workflows/lioness-dragon.yaml`: `8140a2c15422ff320ffc8931c66cb283c08200fa74e99de1c66b1daf5de0ba45`
- `workflows/lioness-panda.yaml`: `cb027a1a130a887845eb6e42a2d6743ff408b68b46e756ca5b1d2433f22aad8b`
- `workflows/lioness-puma.yaml`: `d1840293773d84c2a14405f5331b7e1279c9c77954b231d72494f1d0191ec397`
- `workflows/otter.yaml`: `d372fd1df202ef30578263c333b484af7676407b0721d382b4d3306642c898df`
- `workflows/panda.yaml`: `242e953beae9f8b4cdf642e8efb4f680027411296ff7dc94613e5a7255a22a66`
- `workflows/puma.yaml`: `6db378f2a5522f02f58b779ffdb51dc45171265ac7fa97f89a9c195186d890af`
- `workflows/sambar.yaml`: `950d29c4b2f90dc427e726d39cba09586ee5591204cb1ba414fff0cb9610d10b`

Heldout SHA-256: `b991c9385278da5ca79e82a246a9b4071408e87f2627d2254ac4e9d8a8a2f7fb`.
