# PORCUPINE toy bundle

`lioness_panda_network.txt` uses the netZooPy LIONESS-PANDA text export layout:
space-delimited, header `tf gene <sample IDs...>`, one row per unique TF->gene
edge (10 TFs x 60 genes = 600 edges) and one column per sample (12 samples).
`pathways.gmt` is a tab-separated GMT (name, description, genes) whose gene IDs
match the network's target column. Genes in `P_DRIVEN` carry one planted,
coordinated cross-sample signal; the other pathways are noise. `P_TOO_SMALL`
falls below the default minimum pathway size.

For planning and test coverage only; the agent must still request confirmation
before using this discovered or demo-selected bundle.
