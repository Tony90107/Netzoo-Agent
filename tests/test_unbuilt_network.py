"""ROUND-22 (R22-A): a CONDOR the request names, with no network given, is not available as asked unless the request
also names the workflow that builds the network first."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.ruled_out import without_unbuilt_network  # noqa: E402

H27 = ("I need CONDOR run directly on rnaseq_tpm.tsv (genes by 48 samples) so I get gene communities without building "
       "any network first.")
L48 = ("Run CONDOR right away on counts/brain_rnaseq_counts.tsv to get gene communities. We haven't built any network "
       "yet.")


def _check(network="none", named="CONDOR", ruled_out=None, quote="CONDOR run directly on rnaseq_tpm.tsv", **check):
    row = CheckedRequirement(quote=quote, kind="result", status="available",
                             delivered_by=["condor.communities"], attrs={"input_network": network},
                             method={"named": named, "named_quote": named} if named else {})
    return CapabilityCheck(requirements=[row], ruled_out=ruled_out or {}, **check)


def test_a_named_condor_with_no_network_is_not_available_as_asked():
    held = without_unbuilt_network(_check(), H27)
    row = held.results()[0]
    assert (row.status, row.delivered_by, row.blocks) == ("not_available", [], ["CONDOR"])
    assert row.limits == ["CONDOR runs only on a regulator-gene (source-target-weight) network; building one first "
                          "(OTTER, PANDA, PUMA) is a separate run the request does not name"]
    assert held.full_gap


def test_the_users_own_words_ruling_out_a_network_are_quoted():
    # L48: the reading typed a regulator-gene network, but the user said they have none.
    held = without_unbuilt_network(_check("regulator_gene", ruled_out={"network": "We haven't built any network yet"}),
                                   L48)
    assert held.results()[0].limits[0].startswith('You said "We haven\'t built any network yet"; CONDOR runs only on')


def test_a_route_the_user_names_a_given_network_or_no_named_condor_stands():
    check = _check()
    assert without_unbuilt_network(check, "Build a PANDA network from my expression, then run CONDOR on it.") is check
    given = _check("regulator_gene")
    assert without_unbuilt_network(given, "Run CONDOR on panda_net.tsv to get communities.") is given
    unnamed = _check(named=None)
    assert without_unbuilt_network(unnamed, "I want gene communities from my expression data.") is unnamed


def test_the_readings_no_network_counts_only_on_the_result_naming_the_workflow():
    # Held-out h5 Q13-2: "no network" typed on the output-folder clause, though the user named an edge list.
    q13 = ("Run CONDOR on panda_psoriasis_edges.csv (columns source, target, weight) and write the communities to "
           "condor_psoriasis/.")
    folder = _check(quote="write the communities to condor_psoriasis/")
    assert without_unbuilt_network(folder, q13) is folder  # the folder holds "condor", not the user's "CONDOR"


def test_an_only_statement_leaving_out_a_network_counts_for_any_result():
    # C18: "I don't have any motif or PPI files, just this expression table."
    c18 = ("Run CONDOR directly on expr_kidney_fibrosis.tsv to get gene communities. I don't have any motif or PPI "
           "files, just this expression table.")
    held = without_unbuilt_network(_check(quote="to get gene communities", only_inputs=["expression"],
                                          only_inputs_quote="just this expression table"), c18)
    assert held.results()[0].limits[0].startswith('You said "just this expression table"; CONDOR runs only on')

