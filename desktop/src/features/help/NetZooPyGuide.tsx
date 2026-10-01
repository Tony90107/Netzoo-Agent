import { useState } from "react";
import { ExternalLink } from "./ExternalLink";

const PINNED_REF = "60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822";

const METHODS = [
  {
    name: "PANDA",
    family: "Integrative gene regulatory network",
    principle:
      "Starts with a transcription-factor motif prior, then uses message passing to combine expression co-variation and TF protein-interaction evidence to refine a weighted TF-to-gene network.",
    inputs: "Gene-by-sample expression matrix, TF-to-gene motif prior, and TF–TF protein–protein interactions (PPI).",
    outputs: "A weighted TF-to-gene regulatory network.",
  },
  {
    name: "PUMA",
    family: "Gene regulatory network with miRNAs",
    principle:
      "Extends PANDA's message-passing framework with miRNAs, integrating miRNA target predictions, motif evidence, PPI, and expression co-variation.",
    inputs: "Gene-by-sample expression matrix, motif prior, TF–TF PPI, and miRNA-to-gene prior.",
    outputs: "A weighted regulator-to-gene network containing TFs and miRNAs.",
  },
  {
    name: "LIONESS",
    family: "Sample-specific network estimation",
    principle:
      "Uses leave-one-out linear interpolation to estimate each sample's contribution to the aggregate network. It can be paired with PANDA, PUMA, or a co-expression network.",
    inputs: "Expression matrix and any priors required by the selected base network method.",
    outputs: "One network per sample; output file count grows with the number of samples.",
  },
  {
    name: "CONDOR",
    family: "Bipartite community detection",
    principle:
      "Uses bipartite modularity to describe community structure on both the regulator and target sides, rather than treating the data as a single-layer network.",
    inputs: "A weighted bipartite edge list of regulators and targets.",
    outputs: "Community assignments and module information for regulators and targets.",
  },
  {
    name: "COBRA",
    family: "Covariate-aware co-expression analysis",
    principle:
      "Models how covariance changes with sample covariates, addressing batch-related artifacts that can remain after correcting individual gene distributions alone.",
    inputs: "Gene-by-sample expression matrix and a design/covariate table aligned to the samples.",
    outputs: "A covariate association decomposition and an adjusted, annotated gene-by-gene co-expression matrix.",
  },
  {
    name: "SAMBAR",
    family: "Pathway-level mutation analysis",
    principle:
      "Aggregates sparse gene mutations into biological pathways while accounting for gene length and pathway representation to produce scores for comparing cancer samples.",
    inputs: "Sample-by-gene mutation matrix, gene lengths, cancer gene list, and GMT pathways.",
    outputs: "Gene and pathway mutation scores, sample distances, and optional sample clusters.",
  },
  {
    name: "DRAGON",
    family: "Multi-omics conditional association network",
    principle:
      "Uses a shrinkage precision model across two omics layers to estimate within-layer and between-layer conditional associations. The resulting network represents associations, not causality.",
    inputs: "Two continuous sample-by-feature omics tables aligned to the same samples.",
    outputs: "An undirected multi-omics partial-correlation network.",
  },
  {
    name: "LIONESS-DRAGON",
    family: "Sample-specific multi-omics conditional association networks",
    principle:
      "Estimates DRAGON's shrinkage once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample (LIONESS).",
    inputs: "The same two continuous sample-by-feature omics tables as DRAGON, with at least three shared samples.",
    outputs: "The all-sample DRAGON matrix and one partial-correlation network per sample, as an edge-by-sample table.",
  },
  {
    name: "OTTER",
    family: "Graph-matching regulatory network inference",
    principle:
      "Formulates TF-to-gene network inference as relaxed graph matching, optimizing consistency between TF PPI and gene co-expression with adjustable sparsity.",
    inputs: "TF-to-gene seed/motif prior, TF–TF PPI, and an expression matrix or validated co-expression matrix.",
    outputs: "An optimized weighted TF-to-gene network.",
  },
  {
    name: "GIRAFFE",
    family: "Joint regulatory-effect and TF-activity inference",
    principle:
      "Uses biological priors to constrain matrix factorization, jointly fitting gene expression, TF activity, and signed partial regulatory effects.",
    inputs: "Gene-by-sample expression matrix, TF-to-gene motif prior, and TF–TF PPI.",
    outputs: "An aggregate signed TF-to-gene effect matrix and a TF-by-sample activity matrix.",
  },
  {
    name: "BONOBO",
    family: "Bayesian sample-specific co-expression network",
    principle:
      "Combines a prior built from the other samples with one sample's expression profile to estimate its co-expression matrix and capture between-individual network differences.",
    inputs: "A labeled gene-by-sample expression matrix.",
    outputs: "A gene-by-gene co-expression matrix for each selected sample, with optional p-values.",
  },
];

const AGENT_TOOLS = [
  { name: "Inspect workflow inputs", purpose: "Checks file formats, table axes, numeric values, biological identifiers, and cross-file compatibility before planning an analysis.", inputs: "The input files required by the selected workflow.", outputs: "Validation findings, missing fields, and correction guidance. Input files are not rewritten.", access: "Runs locally in the project container." },
  { name: "Format expression", purpose: "Prepares an expression matrix's orientation and header for a supported workflow.", inputs: "expression_file, output_file, and the intended genes_axis / with_header settings.", outputs: "A separate formatted expression file at the reviewed output path.", access: "Runs locally; review the conversion plan before execution." },
  { name: "Convert expression", purpose: "Converts supported expression data to the workflow's expected representation.", inputs: "expression_file and a separate output_file.", outputs: "A converted expression file. The original input is preserved.", access: "Runs locally; review the conversion plan before execution." },
  { name: "Context7 documentation lookup", purpose: "Retrieves library documentation to answer API and usage questions.", inputs: "library_name and docs_query; library_id can identify a resolved library.", outputs: "Documentation excerpts used in the agent's explanation.", access: "Uses the configured Context7 service and sends the library name and documentation query. It does not connect your GitHub account." },
  { name: "Web search", purpose: "Looks up external references for a question.", inputs: "web_query.", outputs: "Search results and source links for the agent's explanation.", access: "Uses the configured search service and sends the search query. Availability depends on the service configuration." },
];

export function NetZooPyGuide() {
  const [query, setQuery] = useState("");
  const search = query.trim().toLowerCase();
  const visible = METHODS.filter((method) => Object.values(method).join(" ").toLowerCase().includes(search));
  const visibleTools = AGENT_TOOLS.filter((tool) => Object.values(tool).join(" ").toLowerCase().includes(search));
  return (
    <section className="pane guide" aria-labelledby="guide-title">
      <header className="pane__header" id="guide-title">NetZooPy Method Guide</header>
      <div className="pane__scroll guide__scroll">
        <div className="guide__intro">
          <p>
            NetZooPy is Network Zoo's Python package for network biology. NetZoo Agent
            runs these methods in Docker. This guide summarizes each method's core idea, typical inputs, and outputs.
          </p>
          <p>
            The project's default image pins netZooPy to commit <code>{PINNED_REF.slice(0, 12)}</code>. The summaries below describe that version.
            For any run, use the required fields and preflight results shown in the Work Plan.
          </p>
        </div>

        <section className="guide__start" aria-labelledby="guide-start">
          <h2 id="guide-start">Prepare your first analysis</h2>
          <ol>
            <li>Open Environment to check Docker, the image, and the installed package.</li>
            <li>Choose a method below and provide the matching input files in Conversation.</li>
            <li>Review the Work Plan, required fields, validation results, and output paths.</li>
            <li>Request <code>/execute</code>, then approve the specific plan. Follow Run activity and open Outputs when it finishes.</li>
          </ol>
          <p>Use <code>/planning</code> for strict validation, <code>/test</code> for synthetic data, <code>/doctor</code> for environment checks, and <code>/help</code> for commands. Synthetic results are for software testing.</p>
          <details className="guide__connection">
            <summary>GitHub access and data</summary>
            <p>No GitHub account connection or repository permissions are required. The image build reads the public <ExternalLink href="https://github.com/netZoo/netZooPy">netZoo/netZooPy repository</ExternalLink> at the pinned commit. Source and documentation links open in your browser; they do not authorize repository access.</p>
            <p>The agent reads the input paths you provide in the mounted project and writes results to the paths shown in the Work Plan. Review those paths before execution.</p>
          </details>
          <p><ExternalLink href="https://netzoopy.readthedocs.io/en/latest/">Official documentation</ExternalLink> · <ExternalLink href={`https://github.com/netZoo/netZooPy/tree/${PINNED_REF}`}>Pinned source</ExternalLink></p>
        </section>
        <label className="guide__search">Find a method
          <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Method, purpose, or input type" />
        </label>
        <p className="guide__results" role="status">{visible.length} of {METHODS.length} methods · {visibleTools.length} agent tools</p>
        {visible.length === 0 && visibleTools.length === 0 ? <p className="pane__empty">No matching method or tool. Try a method name or an input such as expression.</p> : null}
        <div className="guide__methods">
          {visible.map((method) => (
            <details className="guide__method" key={method.name}>
              <summary>
                <span className="guide__method-name">{method.name}</span>
                <span className="guide__method-family">{method.family}</span>
              </summary>
              <p className="guide__principle">{method.principle}</p>
              <dl className="guide__io">
                <div><dt>Typical inputs</dt><dd>{method.inputs}</dd></div>
                <div><dt>Main outputs</dt><dd>{method.outputs}</dd></div>
              </dl>
              <ExternalLink href={`https://github.com/netZoo/netZooPy/tree/${PINNED_REF}/netZooPy/${method.name.toLowerCase()}`}>View {method.name} source</ExternalLink>
            </details>
          ))}
        </div>
        {visibleTools.length > 0 ? <>
          <h2 className="guide__tools-title">Agent tools</h2>
          <div className="guide__methods">{visibleTools.map((tool) => (
            <details className="guide__method" key={tool.name}>
              <summary><span className="guide__method-name">{tool.name}</span></summary>
              <p className="guide__principle">{tool.purpose}</p>
              <dl className="guide__io">
                <div><dt>Inputs</dt><dd>{tool.inputs}</dd></div>
                <div><dt>Outputs</dt><dd>{tool.outputs}</dd></div>
                <div><dt>Access</dt><dd>{tool.access}</dd></div>
              </dl>
            </details>
          ))}</div>
        </> : null}
      </div>
    </section>
  );
}
