# Known limitations and trade-offs

Last updated 2026-11-06. These are deliberate trade-offs or known gaps, not hidden behaviour.

## Trade-offs

- **Named producer workflows are trusted.** When a request says the input comes from a registered workflow
  (for example "the LIONESS-PANDA networks"), the agent types the file by that workflow's registered output
  (a regulatory network) and drops a conflicting data-type reading. If the user names the wrong producer, the
  conversation does not catch it; the file checks at run time are the remaining safeguard.
- **BONOBO no longer requires centered input.** netZooPy's BONOBO subtracts each gene's mean itself, so the
  agent no longer asks or refuses on centering. In the project's earlier internal evaluation sets, three items
  whose gold answer was "ask whether it is centered" are now "run BONOBO", and about ten more items drop centering
  from their gold reason. Scores reported before 2026-11-06 on those items are not comparable with current ones.
- **Named runs bypass a failed or empty interpretation.** "Run X ..." that names exactly one workflow (other
  named workflows only as input producers, not a question) goes to X's input flow even when the semantic reading
  failed or matched nothing.

## Unverified assumptions

- RSEM-style expected counts are flagged as raw counts when at least half of the non-zero values are whole
  numbers. This threshold has not been checked on a real RSEM output file.
- SNAIL's group-preserving effect is small on raw counts (group weights near plain quantile); whether SNAIL should
  take raw counts or CPM, and whether it stays the default, are open questions.

## Known gaps

- PUMA with a precomputed co-expression matrix: upstream netZooPy appears to recompute correlation from the
  expression file and ignore the matrix (read from source, not yet run).
- PORCUPINE: if dropping constant edges empties pathways, the error blames the gene namespace.
- Folder autofill asks when two files share a name.
- "Run PANDA then CONDOR" still asks "Did you mean CONDOR's result?".
