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


def _check(network="none", named="CONDOR", ruled_out=None):
    row = CheckedRequirement(quote="gene communities", kind="result", status="available",
                             delivered_by=["condor.communities"], attrs={"input_network": network},
                             method={"named": named, "named_quote": named} if named else {})
    return CapabilityCheck(requirements=[row], ruled_out=ruled_out or {})


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
