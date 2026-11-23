"""Lean decider: the form, the tool text and the four contract rules (no model calls)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.lean import (apply_rules, explain_context, instructions, plan_notes,  # noqa: E402
                                   response_format, tool_names, tools_text)


def raw(**fields):
    base = {"steps": [], "decision": "DO", "unsure_quote": "", "question": "", "decline_quote": "", "settings": [],
            "sample_count": None, "sample_count_quote": "", "reply": "ok"}
    return {**base, **fields}


def test_the_tools_are_the_registry_with_contract_checks(monkeypatch):
    names = tool_names()
    assert set(names) == {"PANDA", "LIONESS-PANDA", "SCORPION", "PORCUPINE", "SPONGE", "NORMALIZE-EXPRESSION"}
    assert "Require at least 8 samples." in tools_text() and "Require at least three expression samples" in tools_text()
    assert instructions().endswith(tools_text())
    monkeypatch.setenv("NETZOO_LEAN_SCOPE", "all")  # every registered workflow, as before 2026-11-20
    assert len(tool_names()) == 17 and "PUMA" in tool_names() and instructions().endswith(tools_text())


def test_the_form_has_eight_answers():
    schema = response_format()["json_schema"]["schema"]
    assert len(schema["required"]) == 9  # eight answers, the sample count with its words
    assert schema["properties"]["steps"]["items"]["enum"] == list(tool_names())
    assert schema["properties"]["decision"]["enum"] == ["DO", "EXPLAIN", "ASK", "DECLINE"]
    assert "SCORPION.assoc_method" in schema["properties"]["settings"]["items"]["properties"]["setting"]["enum"]


def test_r1_a_question_needs_the_users_own_doubt():
    task = "Please run LIONESS on our 64 bulk samples; expression, motif and PPI are ready."
    decided = apply_rules(task, raw(steps=["LIONESS-PANDA"], decision="ASK", question="Did you mean LIONESS-PANDA?"))
    assert decided.kind == "DO" and decided.steps == ["LIONESS-PANDA"] and decided.rules[0].startswith("R1")


def test_r1_keeps_a_question_the_user_asked_for():
    task = "I'm honestly not sure whether the numbers are raw counts or TPM. Can you run SNAIL on it?"
    decided = apply_rules(task, raw(steps=["NORMALIZE-EXPRESSION"], decision="ASK",
                                    unsure_quote="I'm honestly not sure whether the numbers are raw counts or TPM",
                                    question="Raw counts or TPM?"))
    assert decided.kind == "ASK" and decided.question == "Raw counts or TPM?"


def test_r1_without_steps_still_asks():
    decided = apply_rules("Help me with my data.", raw(decision="ASK", question="What result do you want?"))
    assert decided.kind == "ASK"


def test_r2_sample_minimum_from_the_contract():
    task = "We have expression from exactly two thyroid samples and want one network per sample."
    decided = apply_rules(task, raw(steps=["LIONESS-PANDA"], sample_count=2,
                                    sample_count_quote="exactly two thyroid samples"))
    assert decided.kind == "DECLINE" and "at least 3 samples" in decided.reply


def test_r2_ignores_a_count_not_in_the_request():
    task = "We have expression from our thyroid samples and want one network per sample."
    decided = apply_rules(task, raw(steps=["LIONESS-PANDA"], sample_count=2, sample_count_quote="two samples"))
    assert decided.kind == "DO"


def test_r3_sponge_offline_declines_and_missing_species_asks():
    offline = apply_rules("Build human motif and PPI priors for TP53. The server is fully air-gapped.",
                          raw(steps=["SPONGE"]))
    assert offline.kind == "DECLINE" and "internet" in offline.reply
    species = apply_rules("Build motif and PPI priors for SOX2 and MYC.", raw(steps=["SPONGE"]))
    assert species.kind == "DO" and any("human" in note for note in species.notes)  # 2026-11-22: priors only
    mouse = apply_rules("Build mouse motif and PPI priors for Sox2.", raw(steps=["SPONGE"]))
    assert mouse.kind == "DECLINE" and "human priors only" in mouse.reply


def test_r4_porcupine_gets_per_sample_networks():
    task = "Bulk expression for 60 patients, motif, PPI and a GMT: which pathways vary in regulation?"
    decided = apply_rules(task, raw(steps=["PANDA", "PORCUPINE"]))
    assert decided.steps == ["LIONESS-PANDA", "PORCUPINE"] and decided.rules[0].startswith("R4")
    swapped = apply_rules(task, raw(steps=["SCORPION", "PORCUPINE"]))  # 2026-11-22 R12: bulk never goes to SCORPION
    assert swapped.steps == ["LIONESS-PANDA", "PORCUPINE"] and swapped.rules[0].startswith("R12")
    cells = "scRNA-seq of 60 patients, motif, PPI and a GMT: which pathways vary in regulation between patients?"
    kept = apply_rules(cells, raw(steps=["SCORPION", "PORCUPINE"]))
    assert kept.steps == ["SCORPION", "PORCUPINE"] and not kept.rules


def test_do_with_nothing_to_run_asks():
    assert apply_rules("Hello", raw(decision="DO")).kind == "ASK"


def test_explain_passes_through_without_plan_notes():
    task = "Conceptually, how can a regulatory network be attributed to one single sample?"
    decided = apply_rules(task, raw(steps=["LIONESS-PANDA"], decision="EXPLAIN"))
    assert decided.kind == "EXPLAIN" and decided.steps == ["LIONESS-PANDA"] and not decided.notes


def test_explain_context_is_the_contracts_and_docs():
    porcupine = explain_context(("PORCUPINE",))
    assert "Require at least 8 samples." in porcupine and "does not give" in porcupine
    assert "# PORCUPINE integration" in porcupine or "PORCUPINE" in porcupine.split("---")[0]
    every = explain_context(())
    assert all(name in every for name in ("PANDA", "LIONESS-PANDA", "SCORPION", "PORCUPINE", "SPONGE"))
    assert "N_k = n * N_all - (n - 1) * N_without_k" in every


def test_r5_a_setting_the_contract_forbids_stops_and_an_unclear_one_asks():
    task = "Run SCORPION on my snRNA-seq with min_cells 0 and Kendall association."
    forbidden = apply_rules(task, raw(steps=["SCORPION"], settings=[
        {"setting": "SCORPION.min_cells", "value": "0", "quote": "min_cells 0"}]))
    assert forbidden.kind == "DECLINE" and "min_cells" in forbidden.reply
    named = apply_rules(task, raw(steps=["SCORPION"], settings=[
        {"setting": "SCORPION.assoc_method", "value": "Kendall", "quote": "Kendall association"}]))
    assert named.kind == "DECLINE" and "pearson" in named.reply  # 2026-11-22: a named value is refused, not asked
    vague = "Run SCORPION on my snRNA-seq with an association that copes with dropouts."
    unclear = apply_rules(vague, raw(steps=["SCORPION"], settings=[
        {"setting": "SCORPION.assoc_method", "value": "dropout-robust", "quote": "an association that copes with dropouts"}]))
    assert unclear.kind == "ASK" and "pearson" in unclear.question


def test_plan_notes_list_given_settings_defaults_and_file_checks():
    task = "Run SCORPION with Spearman association on my scRNA-seq; then PORCUPINE on the networks."
    stated = [{"setting": "SCORPION.assoc_method", "value": "spearman", "quote": "Spearman association"}]
    notes = plan_notes(task, ["SCORPION", "PORCUPINE"], stated, raw())
    scorpion = next(note for note in notes if note.startswith("SCORPION:"))
    assert "assoc_method = spearman (from your request)" in scorpion and "gamma_value = 10.0 (default)" in scorpion
    assert any("PORCUPINE needs at least 8 samples" in note for note in notes)
    sponge = plan_notes("Build human motif and PPI priors for SOX2 and MYC on hg19.", ["SPONGE-PRIORS"], [], raw())
    assert "SOX2, MYC (from your request)" in sponge[0] and "hg19 (from your request)" in sponge[0]


def test_a_do_carries_its_notes():
    task = "Build human motif and PPI priors for SOX2 and MYC; the server has internet."
    decided = apply_rules(task, raw(steps=["SPONGE"]))
    assert decided.kind == "DO" and decided.notes and decided.notes[0].startswith("SPONGE:")


def test_quotes_are_matched_loosely():
    from netzoo_agent_core.lean import _found

    task = ("We have RNA-seq from 15 Alzheimer's disease samples and want to run PANDA; later we plan to compare it "
            "with single-cell data.\nI'm honestly not sure whether the values are raw counts or TPM. Use min_cells = 50.")
    for quote in ("15 Alzheimer's disease samples", "15 alzheimers disease samples",
                  "single-cell   data.\nI'm honestly not sure", "I'm really not sure whether the values",
                  "15 AD samples", "min_cells 50", "unsure if they are raw counts or TPM"):
        assert _found(task, quote), quote
    for quote in ("", "patients", "three thyroid samples", "we have no priors at all"):
        assert not _found(task, quote), quote
    zh = "我們有 15 個阿茲海默症樣本的 RNA-seq，想跑 PANDA，之後打算再跟 single-cell 資料做比較。"
    for quote in ("15 個阿茲海默症樣本", "15個阿茲海默症樣本", "15 個阿茲海默樣本"):
        assert _found(zh, quote), quote


def test_r2_needs_the_number_itself_in_the_request():
    task = "We have expression from our thyroid samples, only a couple of them, and want one network per sample."
    decided = apply_rules(task, raw(steps=["LIONESS-PANDA"], sample_count=2, sample_count_quote="a couple of them"))
    assert decided.kind == "DO"


def test_r0_preparation_steps_run_first_in_their_own_order():
    task = "Normalize my counts, build priors for FOXA1 on hg38, then run PANDA."
    decided = apply_rules(task, raw(steps=["PANDA", "NORMALIZE-EXPRESSION", "SPONGE"]))
    assert decided.steps == ["NORMALIZE-EXPRESSION", "SPONGE-PRIORS", "PANDA"]
    assert any(rule.startswith("R0") for rule in decided.rules)
    kept = apply_rules(task, raw(steps=["SPONGE", "PANDA"]))
    assert kept.steps == ["SPONGE-PRIORS", "PANDA"] and not any(rule.startswith("R0") for rule in kept.rules)


def test_r1_still_runs_a_contract_chain_without_a_stated_doubt():
    task = "Build per-sample networks for my 64 samples and find pathways that vary with PORCUPINE."
    decided = apply_rules(task, raw(steps=["PANDA", "PORCUPINE"], decision="ASK", question="Which network?"))
    assert decided.kind == "DO" and decided.steps == ["LIONESS-PANDA", "PORCUPINE"]  # R4 first, then R1 sees a chain


def test_an_unregistered_setting_is_noted_not_dropped():
    task = "Run PANDA on my 30 samples with turbo mode on."
    decided = apply_rules(task, raw(steps=["PANDA"], settings=[
        {"setting": "unregistered", "value": "on", "quote": "turbo mode on"}]))
    assert decided.kind == "DO"
    assert any("turbo mode on" in note and "not applied" in note for note in decided.notes)


def test_six_scope_shows_only_the_six_and_snail(monkeypatch):
    from netzoo_agent_core.lean import SIX, prep_steps, scope

    monkeypatch.delenv("NETZOO_LEAN_SCOPE", raising=False)
    assert scope() == "six" and set(tool_names()) == set(SIX)
    assert prep_steps() == {"SPONGE-PRIORS", "NORMALIZE-EXPRESSION"}
    text = tools_text()
    for outside in ("PUMA", "OTTER", "GIRAFFE", "BONOBO", "CONDOR", "RLE", "TMM", "FPKM", "preprocessCore"):
        assert outside not in text, outside
    assert "normalization_method snail;" in text and "inputs that LIONESS-PANDA, PANDA, SCORPION read" in text
    settings = response_format()["json_schema"]["schema"]["properties"]["settings"]["items"]["properties"]
    assert all(name.split(".")[0] in SIX or name == "unregistered" for name in settings["setting"]["enum"])
    assert "SAMBAR.kmin" not in settings["setting"]["enum"] and "PORCUPINE.seed" in settings["setting"]["enum"]


def test_the_result_menu_hides_who_gives_what():
    from netzoo_agent_core.lean import _menu, wanted_format, wanted_instructions

    menu = {text: given for _, text, given in _menu("six")}
    assert menu["One weighted TF-to-gene regulatory network across all the samples given."] == {"PANDA"}
    assert menu["Networks for individual cells."] == frozenset()  # near misses only
    assert menu["One network per sample."] == {"LIONESS-PANDA"}  # OTTER's near miss, given instead by LIONESS-PANDA
    # with_step (NetZoo leaves the step to the user) counts as not given (2026-11-20 user decision)
    assert menu["Edges or targeting scores tested between groups, paired time points, or against clinical "
                "variables (e.g. survival)."] == frozenset()
    assert menu["One TF/miRNA-gene network per sample, plus the aggregate network."] == frozenset()  # LIONESS-PUMA
    assert any("SPONGE-PRIORS" in given for given in menu.values())
    assert any("NORMALIZE-EXPRESSION" in given for given in menu.values())
    shown = wanted_instructions()
    for name in ("PANDA:", "LIONESS", "PORCUPINE", "SPONGE", "Registered workflows"):
        assert name not in shown.split("Result kinds:")[1].replace("built by PANDA", ""), name
    keys = wanted_format()["json_schema"]["schema"]["properties"]["items"]["items"]["properties"]["kind"]["enum"]
    assert keys[-1] == "none" and len(keys) == len(menu) + 1


def _key(text):
    from netzoo_agent_core.lean import _menu

    return next(key for key, shown, _ in _menu("six") if shown == text)


def test_r6_a_result_no_workflow_in_scope_gives_stops_the_run():
    task = ("We have 10x scRNA-seq of 6,500 tumour cells with motif and PPI priors. Build a TF-gene network for every "
            "individual cell, then find the pathways whose regulation varies most between cells.")
    wanted = [{"quote": "Build a TF-gene network for every individual cell", "role": "result",
               "kind": _key("Networks for individual cells.")},
              {"quote": "10x scRNA-seq of 6,500 tumour cells", "role": "data", "kind": "none"}]
    decided = apply_rules(task, raw(steps=["SCORPION", "PORCUPINE"], wanted=wanted))
    # 2026-11-22: R11 refuses a network per cell first, with the contract's reason
    assert decided.kind == "DECLINE" and decided.steps == [] and decided.rules[-1].startswith("R11")
    from netzoo_agent_core.lean import _menu

    weights = next(text for _, text, given in _menu("six") if text.startswith("A motif prior whose TF-gene edges carry"))
    task = "Build a human motif prior for SOX2 and MYC whose edges carry the motif binding strength."
    wanted = [{"quote": "a human motif prior for SOX2 and MYC whose edges carry the motif binding strength",
               "role": "result", "kind": _key(weights)}]
    decided = apply_rules(task, raw(steps=["SPONGE"], wanted=wanted))
    assert decided.kind == "DECLINE" and decided.rules[-1].startswith("R6")
    assert decided.reply.startswith('"a human motif prior for SOX2 and MYC whose edges carry the motif binding strength" '
                                    "-- I couldn't match")


def test_r6_leaves_given_results_purposes_and_unfound_words_alone():
    task = "Run PANDA on our 40 lung samples so we can later cut the network into modules ourselves."
    given = [{"quote": "Run PANDA on our 40 lung samples", "role": "result",
              "kind": _key("One weighted TF-to-gene regulatory network across all the samples given.")},
             {"quote": "so we can later cut the network into modules ourselves", "role": "purpose", "kind": "none"}]
    assert apply_rules(task, raw(steps=["PANDA"], wanted=given)).kind == "DO"
    made_up = [{"quote": "a Cox model of every edge", "role": "result", "kind": "none"}]  # not the user's words
    assert apply_rules(task, raw(steps=["PANDA"], wanted=made_up)).kind == "DO"
    other = [{"quote": "Run PANDA on our 40 lung samples", "role": "result",
              "kind": _key("One TF-gene network per sample, plus the aggregate network.")}]  # LIONESS-PANDA gives it
    assert apply_rules(task, raw(steps=["PANDA"], wanted=other)).kind == "DO"
    assert apply_rules(task, raw(steps=["PANDA"])).kind == "DO"  # a saved form without the reading: unchanged
    asked = apply_rules(task, raw(steps=["PANDA"], decision="EXPLAIN",
                                  wanted=[{"quote": "Run PANDA", "role": "result", "kind": "none"}]))
    assert asked.kind == "EXPLAIN"  # R6 only stops a run


def test_r7_normalization_other_than_snail_is_outside_the_six():
    task = "Convert my raw rat hippocampus counts to FPKM with the gene-length table and send me the matrix."
    decided = apply_rules(task, raw(steps=["NORMALIZE-EXPRESSION"]))
    assert decided.kind == "DECLINE" and decided.rules[-1].startswith("R7") and "SNAIL only" in decided.reply
    snail = apply_rules("Normalize my raw counts across samples with SNAIL.", raw(steps=["NORMALIZE-EXPRESSION"]))
    assert snail.kind == "DO"


def test_the_lean_entries_leave_the_old_sheet_alone():
    from netzoo_agent_core.capability_sheet import lean_entries, sheet_entries

    extra = lean_entries()
    assert {item.workflow for item in extra.values()} == {"SPONGE", "NORMALIZE-EXPRESSION", "PANDA"}
    assert not set(extra) & set(sheet_entries()) and all(item.source for item in extra.values())
    assert all(item.workflow not in ("SPONGE", "NORMALIZE-EXPRESSION") for item in sheet_entries().values())
    assert "panda.adjusted_coexpression_network" not in sheet_entries()  # the old tables never see it
    from netzoo_agent_core.lean import _menu

    assert {"PANDA"} in [given for _, text, given in _menu("six") if "adjusted gene-by-gene co-expression" in text]


def test_r6_a_named_step_or_an_old_key_is_not_evidence():
    task = "Build human motif and PPI priors for ZEB1 and SNAI2 on hg19. SPONGE run please."
    named = [{"quote": "SPONGE run please", "role": "result", "kind": "none"}]
    assert apply_rules(task, raw(steps=["SPONGE"], wanted=named)).kind == "DO"  # the named step gives its result
    old = [{"quote": "Build human motif and PPI priors for ZEB1 and SNAI2 on hg19", "role": "result", "kind": "K03"}]
    assert apply_rules(task, raw(steps=["SPONGE"], wanted=old)).kind == "DO"  # not a key of this list
    communities = _key("Communities in one bipartite network, with regulator-side and gene-side memberships, by "
                       "bipartite modularity.")
    outside = [{"quote": "Run CONDOR on it", "role": "result", "kind": communities}]
    decided = apply_rules("Run PANDA on my 40 samples. Run CONDOR on it.", raw(steps=["PANDA"], wanted=outside))
    assert decided.kind == "DECLINE"  # CONDOR is outside the six: only a name inside the scope is let through
    unread = [{"quote": "give me the edge weights on the 0-1 scale", "role": "result", "kind": "none"}]
    task = "Build SCORPION networks per line and day, and give me the edge weights on the 0-1 scale."
    assert apply_rules(task, raw(steps=["SCORPION"], wanted=unread)).kind == "DO"  # "none of these" stops nothing
    lookalike = [{"quote": "then build one PANDA TF-to-gene network across all 48 placentas", "role": "result",
                  "kind": _key(next(text for _, text, _ in __import__("netzoo_agent_core.lean", fromlist=["_menu"])
                                    ._menu("six") if text.startswith("One weighted TF-to-gene regulatory network across "
                                                                     "all samples, fitted")))}]
    task = "Normalize the counts with SNAIL first, then build one PANDA TF-to-gene network across all 48 placentas."
    assert apply_rules(task, raw(steps=["NORMALIZE-EXPRESSION", "PANDA"], wanted=lookalike)).kind == "DO"


def test_menu_keys_follow_the_text_not_the_order():
    import hashlib

    from netzoo_agent_core.lean import _menu

    for key, text, _ in _menu("six"):
        assert key == "K" + hashlib.sha1(text.encode()).hexdigest()[:6]
    assert len({key for key, _, _ in _menu("six")}) == len(_menu("six"))


def test_r8_snail_needs_raw_counts():
    tpm = ("For our obesity study we quantified adipose biopsies from 30 adults with Salmon, and the only table we kept "
           "is the gene-level TPM matrix; the read counts were not saved. Please run SNAIL across the 30 samples on "
           "these TPM values and give me the normalized matrix.")
    decided = apply_rules(tpm, raw(steps=["NORMALIZE-EXPRESSION"]))
    assert decided.kind == "DECLINE" and decided.rules[-1].startswith("R8") and "raw read counts only" in decided.reply
    array = ("我們有 48 位 AML 病人的 Affymetrix 晶片資料，已經用 RMA 處理成 log2 強度值；這批樣本沒有做定序，也沒有任何 "
             "read counts。請用 SNAIL 對這 48 個樣本做樣本間標準化。")
    assert apply_rules(array, raw(steps=["NORMALIZE-EXPRESSION"])).kind == "DECLINE"
    counts = "Raw HTSeq read counts for 60 tumours (TPM also exported for plots). Normalize the counts with SNAIL first."
    assert apply_rules(counts, raw(steps=["NORMALIZE-EXPRESSION"])).kind == "DO"
    unsure = ("I'm not sure whether the numbers are raw counts or something already processed like TPM. Can you run "
              "SNAIL on it?")
    assert not any(rule.startswith("R8") for rule in apply_rules(unsure, raw(steps=["NORMALIZE-EXPRESSION"])).rules)


def test_r8_drops_a_snail_step_nobody_asked_for():
    task = ("Bulk RNA-seq from 143 liver samples, already TPM-quantified, log-transformed and batch-corrected, with a "
            "motif prior and a PPI file. I'd like a single regulatory network for the whole cohort.")
    decided = apply_rules(task, raw(steps=["NORMALIZE-EXPRESSION", "PANDA"]))
    assert decided.kind == "DO" and decided.steps == ["PANDA"] and decided.rules[-1].startswith("R8")
    done = "已經做過 TPM 標準化並取 log2 的表現矩陣，請建一張 PANDA 網路。"
    assert apply_rules(done, raw(steps=["NORMALIZE-EXPRESSION", "PANDA"])).steps == ["PANDA"]


def test_r9_scorpion_comparison_needs_two_networks_per_side():
    one = ("From one glioblastoma patient we have scRNA-seq of the tumour core and the margin; this is our only "
           "patient, with one library per region. Please build the networks and test which edges differ between core "
           "and margin.")
    decided = apply_rules(one, raw(steps=["SCORPION"]))
    assert decided.kind == "DECLINE" and decided.rules[-1].startswith("R9") and "two built networks" in decided.reply
    donors = ("snRNA-seq of human heart: one donor with heart failure and one healthy donor. Build SCORPION networks "
              "per condition and test which edges differ between failing and healthy.")
    assert apply_rules(donors, raw(steps=["SCORPION"])).kind == "DECLINE"
    replicated = ("One patient, three biopsies from each region (core and margin). Test which edges differ between "
                  "core and margin with SCORPION.")
    assert apply_rules(replicated, raw(steps=["SCORPION"])).kind == "DO"
    per_cell = "一位肝細胞癌病人的單細胞資料，請為每一個細胞各建立網路，找出細胞與細胞之間差異最大的 pathway。"
    assert not any(rule.startswith("R9") for rule in apply_rules(per_cell, raw(steps=["SCORPION"])).rules)
    no_compare = "One patient's 8,000 tumour cells: build one SCORPION network for the tumour."
    assert apply_rules(no_compare, raw(steps=["SCORPION"])).kind == "DO"


def test_r8_r9_review_counterexamples():
    """Counterexamples from the Gemini review (2026-11-21): none may be refused."""
    gene = "Normalize expression of CPM and EGFR across our 30 tumor samples using SNAIL; the counts are in data.tsv."
    assert apply_rules(gene, raw(steps=["NORMALIZE-EXPRESSION"])).kind == "DO"
    earlier = ("We have raw sequencing data from 50 biopsies and want to normalize with SNAIL; previously we published "
               "TPM values.")
    assert apply_rules(earlier, raw(steps=["NORMALIZE-EXPRESSION"])).kind == "DO"
    timepoints = ("From one patient we collected scRNA-seq across 4 timepoints (2 pre-treatment vs 2 post-treatment). "
                  "Compare pre vs post with SCORPION.")
    assert apply_rules(timepoints, raw(steps=["SCORPION"])).kind == "DO"
    output = "Build SCORPION networks for 6 donors, one network per condition, and compare treated vs control."
    assert apply_rules(output, raw(steps=["SCORPION"])).kind == "DO"
    per_side = "snRNA-seq with one donor per condition; test which edges differ between treated and control."
    assert apply_rules(per_side, raw(steps=["SCORPION"])).kind == "DECLINE"


def test_r10_an_input_the_contract_refuses():
    held = ("For 50 psoriasis biopsies I computed sample-specific co-expression networks, stored as a gene1, gene2 table "
            "with one column per biopsy. I want pathway-level heterogeneity of these networks. A Reactome GMT is "
            "available.")
    decided = apply_rules(held, raw(steps=["PORCUPINE"]))
    assert decided.kind == "DECLINE" and decided.rules[-1].startswith("R10") and "co-expression network" in decided.reply
    wanted = ("I have bulk RNA-seq from 72 tumours. Please build a separate gene-by-gene co-expression network for each "
              "tumour.")
    assert not any(r.startswith("R10") for r in apply_rules(wanted, raw(steps=["LIONESS-PANDA"])).rules)
    panda = "I've already computed a covariate-adjusted co-expression matrix and want PANDA to use it. Run PANDA."
    assert apply_rules(panda, raw(steps=["PANDA"])).kind == "DO"  # PANDA's contract takes it (coexpression_file)


def test_r9_no_replicates_stated():
    task = ("scRNA-seq from exactly two biopsies: one lesion from one patient and one healthy sample from one "
            "volunteer. There are no other donors and no replicates. I need the test of which TF-gene edges differ "
            "between lesion and healthy.")
    assert apply_rules(task, raw(steps=["SCORPION"])).rules[-1].startswith("R9")
    many = "30 donors per arm, no replicates per donor. Test which edges differ between treated and control."
    assert apply_rules(many, raw(steps=["SCORPION"])).kind == "DO"


def test_r1_keeps_a_question_when_the_user_states_doubt():
    task = "請幫我建立人類的 motif 和 PPI 先驗，TF 是 STAT3、RELA。不過這台主機我不確定能不能連到外面的網路。"
    asked = apply_rules(task, raw(steps=["SPONGE"], decision="ASK", question="Does the machine have internet access?"))
    assert asked.kind == "ASK"
    plain = "Please build human motif and PPI priors for STAT3 and RELA."
    assert apply_rules(plain, raw(steps=["SPONGE"], decision="ASK", question="Which genome?")).kind == "DO"


def test_review_round4_counterexamples():
    """Gemini review 2026-11-21, round 4: neither may be refused."""
    background = ("Our cohort has whole-exome sequencing mutation calls and RNA-seq. Run PANDA on the RNA-seq data with "
                  "motif and PPI priors.")
    assert apply_rules(background, raw(steps=["PANDA"])).kind == "DO"
    organoids = ("scRNA-seq from one patient across 6 organoids (3 treated vs 3 control), with no technical "
                 "replicates. Compare treated vs control with SCORPION.")
    assert apply_rules(organoids, raw(steps=["SCORPION"])).kind == "DO"


def test_r6_same_typed_result_from_a_planned_step_is_not_missing():
    task = ("Affymetrix expression for 118 tumours, RMA-normalized, plus a motif prior and a PPI network. Please infer a "
            "single cohort-wide network of which transcription factors regulate which genes.")
    look_alike = [{"quote": "Please infer a single cohort-wide network of which transcription factors regulate which genes.",
                   "role": "result",
                   "kind": _key("One weighted TF-to-gene regulatory network across all samples, fitted so that it "
                                "agrees with the PPI network and gene co-expression.")}]
    assert apply_rules(task, raw(steps=["PANDA"], wanted=look_alike)).kind == "DO"
    mirna = [{"quote": "Please infer a single cohort-wide network of which transcription factors regulate which genes.",
              "role": "result", "kind": _key("One weighted network of how TFs and miRNAs regulate genes, across all samples.")}]
    assert apply_rules(task, raw(steps=["PANDA"], wanted=mirna)).kind == "DECLINE"  # TF+miRNA is another result
    otter = ("Please run OTTER on our tumour RNA-seq and PPI data to infer a single cohort-wide network of which "
             "transcription factors regulate which genes.")
    named = [{**look_alike[0], "quote": "infer a single cohort-wide network of which transcription factors regulate "
                                        "which genes"}]
    assert apply_rules(otter, raw(steps=["PANDA"], wanted=named)).kind == "DECLINE"  # OTTER named: not PANDA's


def test_r5_a_named_value_outside_the_contract_is_refused():
    task = ("Run SCORPION on my fly wing disc scRNA-seq (raw counts, 9,500 cells; motif prior and PPI ready). The "
            "association between super-cells has to be Kendall's tau, so Pearson or Spearman won't do.")
    setting = {"setting": "SCORPION.assoc_method", "value": "kendall",
               "quote": "The association between super-cells has to be Kendall's tau"}
    decided = apply_rules(task, raw(steps=["SCORPION"], settings=[setting]))
    assert decided.kind == "DECLINE" and "named and not allowed" in decided.rules[-1]
    assert "pearson, spearman and pcNet" in decided.reply and 'asks for "kendall"' in decided.reply
    vague = "Run SCORPION on my 9,500 cells with motif and PPI priors; use whichever association suits sparse data best."
    unclear = {"setting": "SCORPION.assoc_method", "value": "best for sparse data",
               "quote": "use whichever association suits sparse data best"}
    assert apply_rules(vague, raw(steps=["SCORPION"], settings=[unclear])).kind == "ASK"  # not named: asked


def test_explain_sources_carry_the_scope_card_unless_switched_off(monkeypatch):
    """2026-11-22: EXPLAIN's sources start with every workflow in scope (one line each) and the known limitations, so an
    answer about PANDA can still point a single-cell user to SCORPION (audit F063)."""
    from netzoo_agent_core.lean import explain_context

    panda = explain_context(("PANDA",))
    assert panda.startswith("Everything this system can run") and "- SCORPION:" in panda and "Known limitations" in panda
    assert " Checks: " not in panda.split("---")[0]  # the card has no input checks
    assert panda.count("# Known limitations") == 1
    monkeypatch.setenv("NETZOO_LEAN_EXPLAIN_SCOPE", "off")
    assert "- SCORPION:" not in explain_context(("PANDA",)) and len(explain_context(("PANDA",))) < len(panda)


def test_r3_priors_only_needs_no_species_question():
    only = "Run SPONGE for TP63, SOX2 and KLF5 and write the motif and PPI priors to the default folder."
    assert apply_rules(only, raw(steps=["SPONGE"])).kind == "DO"
    with_data = ("No motif or PPI files yet. Build the priors with SPONGE for MYOD1 and MEF2C, then run LIONESS on my "
                 "20 skeletal muscle samples.")
    assert apply_rules(with_data, raw(steps=["SPONGE", "LIONESS-PANDA"])).kind == "ASK"  # the data's species matters


def test_count_rules_ask_when_the_user_doubts_the_count():
    """2026-11-22 (L111): the user's doubt about a count turns R9's refusal into a question."""
    doubt = ("snRNA-seq of failing versus non-failing hearts, metadata columns donor and status. I'd like the edges that "
             "differ between failing and non-failing. I think the non-failing arm might be a single donor, but I'm not sure.")
    asked = apply_rules(doubt, raw(steps=["SCORPION"]))
    assert asked.kind == "ASK" and "How many donors" in asked.question
    sure = ("snRNA-seq from one donor, failing and non-failing regions. Test the edges that differ between failing "
            "and non-failing.")
    assert apply_rules(sure, raw(steps=["SCORPION"])).kind == "DECLINE"


def test_an_unasked_sponge_step_is_dropped_when_the_user_has_priors():
    """2026-11-22 (L046): mouse motif and PPI priors in hand, no build asked: SPONGE is not run (or refused)."""
    task = ("A mouse thymus counts matrix with about 90 bulk samples. We have mouse motif and PPI priors. I want a "
            "regulatory network for each sample.")
    decided = apply_rules(task, raw(steps=["SPONGE", "LIONESS-PANDA"]))
    assert decided.kind == "DO" and decided.steps == ["LIONESS-PANDA"]
    mirna = ("We have TargetScan miRNA target predictions to use as a prior and mRNA expression for 50 samples; build "
             "a miRNA-to-gene network.")
    assert "SPONGE-PRIORS" in apply_rules(mirna, raw(steps=["SPONGE", "PANDA"])).steps or \
        apply_rules(mirna, raw(steps=["SPONGE", "PANDA"])).kind != "DO"  # a miRNA prior is not a motif/PPI prior
    asked = "We have mouse motif and PPI priors, but please also build human priors for SOX2, then run PANDA."
    assert "SPONGE-PRIORS" in apply_rules(asked, raw(steps=["SPONGE", "PANDA"])).steps or \
        apply_rules(asked, raw(steps=["SPONGE", "PANDA"])).kind != "DO"  # a build asked for stays


def test_r6_does_not_stop_a_planned_steps_own_phrase():
    """2026-11-22 (L024): "pathways whose regulation varies across patients" is PORCUPINE's own selection phrase."""
    task = ("scRNA-seq with a metadata table giving each cell's patient, motif and PPI priors: one network per patient, "
            "then the pathways whose regulation varies across patients, using a Hallmark GMT.")
    wanted = [{"quote": "the pathways whose regulation varies across patients", "role": "result",
               "kind": _key("Pathways differentially expressed or enriched between predefined groups.")}]
    assert apply_rules(task, raw(steps=["SCORPION", "PORCUPINE"], wanted=wanted)).kind == "DO"


def test_r1_the_other_way_stated_doubt_is_asked_before_a_run():
    """2026-11-22 (L175): the user says they are not sure about something the run depends on, so nothing runs yet."""
    task = ("I downloaded an expression matrix of 32 rice panicle samples from GEO, but I'm not sure whether it holds raw "
            "counts or values the authors already normalized. I want to smooth-quantile normalize it.")
    asked = apply_rules(task, raw(steps=["NORMALIZE-EXPRESSION"]))
    assert asked.kind == "ASK" and "not sure whether it holds raw counts" in asked.question
    later = ("Expression matrix, motif prior and PPI are ready for our skin samples; build one network for them as a "
             "group. I haven't decided whether I'll look at individual samples afterwards.")
    assert apply_rules(later, raw(steps=["PANDA"])).kind == "DO"  # a doubt about a later step is not asked now


def test_r11_one_network_per_cell_is_refused_but_a_cell_type_is_a_group():
    task = "10x scRNA-seq of 8,000 organoid cells with priors: a separate PANDA regulatory network for every individual cell."
    decided = apply_rules(task, raw(steps=["SCORPION"]))
    assert decided.kind == "DECLINE" and decided.rules[-1].startswith("R11") and "never one per cell" in decided.reply
    types = "scRNA-seq of 30,000 esophageal cells with priors; we'd like one regulatory network for each cell type."
    assert apply_rules(types, raw(steps=["SCORPION"])).kind == "DO"


def test_r6_snail_method_name_and_data_unit():
    """2026-11-22: "smooth-quantile normalize" names SNAIL (L149); SCORPION's one network across all nuclei is the same
    typed result as the bulk look-alike, the data unit aside (L086)."""
    from netzoo_agent_core.lean import _menu

    batch = next(text for _, text, _ in _menu("six") if text.startswith("An expression matrix with a named batch effect"))
    task = "Smooth-quantile normalize the raw read counts from our 36 tumour libraries, then infer one PANDA network."
    wanted = [{"quote": "Smooth-quantile normalize the raw read counts from our 36 tumour libraries", "role": "result",
               "kind": _key(batch)}]
    assert apply_rules(task, raw(steps=["NORMALIZE-EXPRESSION", "PANDA"], wanted=wanted)).kind == "DO"


def test_r12_scorpion_only_for_single_cells():
    """2026-11-22 (KNOWN_LIMITATIONS): bulk requests never go to SCORPION, single-cell ones never to PANDA/LIONESS."""
    bulk = ("Raw counts from pancreatic islets of 10 mice plus motif and PPI priors; normalize with SNAIL and build a "
            "separate network for each mouse.")
    assert apply_rules(bulk, raw(steps=["NORMALIZE-EXPRESSION", "SCORPION"])).steps == ["NORMALIZE-EXPRESSION",
                                                                                         "LIONESS-PANDA"]
    cells = ("Single-nuclei RNA-seq from 3 explants, 18,000 nuclei, log-normalized, with motif and PPI priors: one "
             "regulatory network across all nuclei.")
    assert apply_rules(cells, raw(steps=["PANDA"])).steps == ["SCORPION"]
    both = ("10x scRNA-seq of 14 donors: I can give you the cell-level matrix or a pseudo-bulk matrix, whichever "
            "works. Motif and PPI priors are ready. One TF-to-gene network for this tissue.")
    assert apply_rules(both, raw(steps=["SCORPION"])).steps == ["SCORPION"]  # both offered: not swapped
    named = "Run SCORPION on my bulk RNA-seq of 30 samples with motif and PPI priors."
    assert apply_rules(named, raw(steps=["SCORPION"])).steps == ["SCORPION"]  # named by the user: not swapped


def test_r4_porcupine_from_expression_gets_its_network_step():
    task = ("Normalized expression for 52 gastric cancer cases, a motif prior, a PPI network and a KEGG GMT: which "
            "pathways show regulatory heterogeneity between patients?")
    assert apply_rules(task, raw(steps=["PORCUPINE"])).steps == ["LIONESS-PANDA", "PORCUPINE"]
    held = ("We computed LIONESS networks for 26 patients (a table with tf and gene columns) and have a Reactome GMT: "
            "which pathways vary most between patients?")
    assert apply_rules(held, raw(steps=["PORCUPINE"])).steps == ["PORCUPINE"]


def test_r12_single_cell_background_does_not_move_bulk_to_scorpion():
    """Review 2026-11-22 (Gemini): single-cell data named only as background keeps a bulk request on LIONESS."""
    for task in ("We did bulk RNA-seq on 20 patients and used single-cell annotations from the same tissue as a "
                 "reference; build an individual network for each patient with our motif and PPI priors.",
                 "Bulk RNA-seq of 20 patients (we also have scRNA-seq of the same tissue, not used here); one network "
                 "per patient with our motif and PPI priors."):
        assert apply_rules(task, raw(steps=["LIONESS-PANDA"])).steps == ["LIONESS-PANDA"]


def test_round4_contract_rules_from_the_acceptance_bank():
    """2026-11-23: rules from the acceptance bank's first-run errors (all by contract text)."""
    few = ("Could you build a TF-gene network from our single-cell RNA-seq of human oocytes? It's Smart-seq2, so there "
           "are only 24 cells in total. Motif and PPI priors are ready.")
    d = apply_rules(few, raw(steps=["SCORPION"]))
    assert d.kind == "DECLINE" and d.rules[-1].startswith("R14") and "at least 30 cells" in d.reply
    many = "scRNA-seq with every cluster over 500 cells and priors; one network per cluster."
    assert apply_rules(many, raw(steps=["SCORPION"])).kind == "DO"
    scaled = ("scRNA-seq of ascites: the only matrix left is the scaled one (centred z-scores, many negative values); "
              "the raw counts and the normalized data are gone. Build a network per malignant state with our priors.")
    assert apply_rules(scaled, raw(steps=["SCORPION"])).kind == "DECLINE"
    gone = ("All we kept from 95 biopsies is a gene-by-gene Spearman correlation matrix; the original expression data "
            "were deleted and can't be recovered. Build the TF-to-gene network with our motif and PPI priors.")
    d = apply_rules(gone, raw(steps=["PANDA"]))
    assert d.kind == "DECLINE" and d.rules[-1].startswith("R13")
    mutation = ("Here's a binary gene-by-sample somatic mutation matrix for 410 tumours. Please run PANDA on it with our "
                "motif and PPI priors. There is no RNA-seq for this cohort.")
    assert apply_rules(mutation, raw(steps=["PANDA"])).kind == "DECLINE"
    own = ("For each of the ~3,000 CD8 T cells in our 10x scRNA-seq, I'd like that cell's own TF-to-gene regulatory "
           "network. Raw counts and priors are available.")
    assert apply_rules(own, raw(steps=["SCORPION"])).rules[-1].startswith("R11")


def test_r11_wins_over_r3_question_and_doubt_turns_a_refusal_into_a_question():
    task = ("We have 3,000 cells from one tumour with scRNA-seq, priors and a GMT. Build a separate regulatory network "
            "for every individual cell and then test which pathways vary across the cells.")
    assert apply_rules(task, raw(steps=["SPONGE", "SCORPION", "PORCUPINE"])).rules[-1].startswith("R11")
    doubt = ("Our core gave us a TF-to-gene network file for 25 biopsies. I honestly don't know if it holds one network "
             "per biopsy or a single consensus network. Find the pathways whose regulation varies across patients.")
    assert apply_rules(doubt, raw(steps=[], decision="DECLINE", decline_quote="x")).kind == "ASK"


def test_r3_non_human_without_priors_asks_for_them():
    task = "Build TF-gene networks for each cluster in our mouse organoid scRNA-seq; cluster labels are in a metadata CSV."
    d = apply_rules(task, raw(steps=["SPONGE", "SCORPION"]))
    assert d.kind == "ASK" and "Do you have mouse motif and PPI prior files?" in d.question
    built = "Build mouse motif and PPI priors for Sox2."
    assert apply_rules(built, raw(steps=["SPONGE"])).kind == "DECLINE"  # a build asked for: still refused


def test_r6_heterogeneity_is_not_a_group_difference():
    from netzoo_agent_core.lean import _menu

    group = next(t for _, t, _ in _menu("six") if t.startswith("Pathways differentially expressed or enriched"))
    task = ("Bulk RNA-seq of 64 resections with priors and a KEGG GMT: a network for each patient, then which pathways "
            "are regulated differently from one patient to the next.")
    w = [{"quote": "which pathways are regulated differently from one patient to the next", "role": "result",
          "kind": _key(group)}]
    assert apply_rules(task, raw(steps=["LIONESS-PANDA", "PORCUPINE"], wanted=w)).kind == "DO"
    two = ("LIONESS networks for 64 patients and a GMT: for each pathway test whether regulation differs between "
           "responders and non-responders.")
    w2 = [{"quote": "test whether regulation differs between responders and non-responders", "role": "result",
           "kind": _key(group)}]
    assert apply_rules(two, raw(steps=["PORCUPINE"], wanted=w2)).kind == "DECLINE"


def test_round4_review_counterexamples():
    """Gemini review 2026-11-23: neither may be refused."""
    qc = ("We have 10,000 single cells in total, but filtered out only 15 cells with high mitochondrial content. Run "
          "SCORPION on the remaining cells with our motif and PPI priors.")
    assert apply_rules(qc, raw(steps=["SCORPION"])).kind == "DO"
    fpkm = ("The microarray expression data were deleted; however, we uploaded the batch-corrected matrix (or FPKM "
            "table) for 40 samples with motif and PPI priors. Run LIONESS.")
    assert apply_rules(fpkm, raw(steps=["LIONESS-PANDA"])).kind == "DO"
