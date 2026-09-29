The first thing to check is whether the analysis preserved the two node types: regulators and targets. In a bipartite representation, edges run between those types. A method whose null model allows within-type edges is comparing the data with a different kind of network. If you first projected onto targets, a shared hub can also create many target-to-target links and make a broad group look dense.

**CONDOR** fits this structural question because it optimizes bipartite modularity. Its null model keeps the two partitions and accounts for node degree, or strength in the weighted case. The question becomes: are these regulators and targets more strongly connected than expected given how connected each node already is? BRIM alternates updates between the two partitions to seek a better community assignment.

A giant community alone does not establish why the previous method failed. Ordinary modularity can already account for degree; resolution limits, graph projection and weight handling also matter. A bipartite method addresses the structural assumption, but biological meaning still needs enrichment or other validation.

To try this, preserve regulator and target identities when converting the weight matrix to a regulator–target edge list. The result is community membership for both node types. Check the meaning and sign of the weights before fitting; do not silently drop signs or take absolute values.

No files were inspected and no analysis ran.

Which community method did you try, and did you use the original bipartite network or a projection? Are the weights signed or nonnegative?
