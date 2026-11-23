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


def test_the_tools_are_the_registry_with_contract_checks():
    names = tool_names()
    assert len(names) == 17 and {"PANDA", "LIONESS-PANDA", "SCORPION", "PORCUPINE", "SPONGE",
                                 "NORMALIZE-EXPRESSION"} <= set(names)
    assert "Require at least 8 samples." in tools_text() and "Require at least three expression samples" in tools_text()
    assert instructions().endswith(tools_text())


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
    assert species.kind == "ASK" and "human" in species.question
    mouse = apply_rules("Build mouse motif and PPI priors for Sox2.", raw(steps=["SPONGE"]))
    assert mouse.kind == "DECLINE" and "human priors only" in mouse.reply


def test_r4_porcupine_gets_per_sample_networks():
    task = "Bulk expression for 60 patients, motif, PPI and a GMT: which pathways vary in regulation?"
    decided = apply_rules(task, raw(steps=["PANDA", "PORCUPINE"]))
    assert decided.steps == ["LIONESS-PANDA", "PORCUPINE"] and decided.rules[0].startswith("R4")
    kept = apply_rules(task, raw(steps=["SCORPION", "PORCUPINE"]))
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
    unclear = apply_rules(task, raw(steps=["SCORPION"], settings=[
        {"setting": "SCORPION.assoc_method", "value": "Kendall", "quote": "Kendall association"}]))
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
