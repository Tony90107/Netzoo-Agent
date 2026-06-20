#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from pathlib import Path
from typing import Annotated

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict


EXECUTE_TOOLS = False


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _run_command(command: list[str], output_file: str | None = None) -> str:
    rendered = _quote_command(command)
    if not EXECUTE_TOOLS:
        return (
            "Dry run only. The agent selected this command but did not execute it.\n\n"
            f"```bash\n{rendered}\n```\n\n"
            "Add `--execute` if you want the script to actually run the tool."
        )

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result = [
        f"Command: `{rendered}`",
        f"Exit code: {completed.returncode}",
    ]
    if completed.stdout.strip():
        result.append("\nSTDOUT:\n" + completed.stdout.strip())
    if completed.stderr.strip():
        result.append("\nSTDERR:\n" + completed.stderr.strip())
    if completed.returncode == 0 and output_file:
        result.append(f"\nOutput file: `{output_file}`")
    return "\n".join(result)


def _read_table(path: str, nrows: int | None = None) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", header=None, nrows=nrows, dtype=str)


def _expression_genes(expression_file: str) -> set[str]:
    frame = _read_table(expression_file)
    if frame.empty:
        return set()
    first_value = str(frame.iloc[0, 0]).strip().lower()
    if first_value in {"gene", "genes", "gene_id", "geneid", "symbol"}:
        frame = frame.iloc[1:, :]
    return set(frame.iloc[:, 0].dropna().astype(str))


@tool
def explain_panda_puma_io(topic: str = "overview") -> str:
    """Explain PANDA/PUMA input and output formats in plain language."""
    return f"""
PANDA needs:
- expression file: rows are genes, columns are samples, values are processed gene expression.
- motif file: TF, target gene, weight. Example: MYC<TAB>CCND1<TAB>1
- PPI file: TF1, TF2, weight. Example: MYC<TAB>MAX<TAB>1
- output: TF, Gene, Motif, Force. Force is the PANDA edge score.

PUMA needs everything PANDA needs plus:
- miRNA file: miRNA, target gene, weight. Example: hsa-miR-21<TAB>PTEN<TAB>1
- output: regulator-to-gene network. Regulators can be TFs or miRNAs.

Important preprocessing point:
Raw sequencing reads are not expression data yet. In a real RNA-seq workflow, FASTQ reads usually go through QC, trimming, alignment or pseudoalignment, quantification, gene ID mapping, filtering, and normalization before becoming the expression matrix used by PANDA/PUMA.

Requested topic: {topic}
""".strip()


@tool
def inspect_netzoo_inputs(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
) -> str:
    """Inspect PANDA/PUMA input files and report basic shape plus ID overlaps."""
    expression_genes = _expression_genes(expression_file)
    expression = _read_table(expression_file, nrows=5)
    motif = _read_table(motif_file)
    ppi = _read_table(ppi_file)

    motif_tfs = set(motif.iloc[:, 0].dropna().astype(str)) if motif.shape[1] >= 1 else set()
    motif_genes = set(motif.iloc[:, 1].dropna().astype(str)) if motif.shape[1] >= 2 else set()
    ppi_tfs = set(ppi.iloc[:, 0].dropna().astype(str)) | set(ppi.iloc[:, 1].dropna().astype(str))

    lines = [
        "Input inspection:",
        f"- expression genes: {len(expression_genes)}",
        f"- expression preview shape: {expression.shape[0]} rows x {expression.shape[1]} columns",
        f"- motif rows: {len(motif)}",
        f"- PPI rows: {len(ppi)}",
        f"- motif target genes overlapping expression genes: {len(motif_genes & expression_genes)}",
        f"- motif TFs overlapping PPI TFs: {len(motif_tfs & ppi_tfs)}",
    ]

    if mirna_file:
        mirna = _read_table(mirna_file)
        mirna_genes = set(mirna.iloc[:, 1].dropna().astype(str)) if mirna.shape[1] >= 2 else set()
        lines.extend(
            [
                f"- miRNA rows: {len(mirna)}",
                f"- miRNA target genes overlapping expression genes: {len(mirna_genes & expression_genes)}",
            ]
        )

    if not motif_genes & expression_genes:
        lines.append("Warning: motif target genes do not overlap expression genes. Check gene IDs.")
    if not motif_tfs & ppi_tfs:
        lines.append("Warning: motif TF names do not overlap PPI TF names. Check TF IDs.")

    return "\n".join(lines)


@tool
def run_panda(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    output_file: str,
    with_header: bool = False,
    extra_args: str = "",
) -> str:
    """Run PANDA through the container wrapper."""
    command = [
        "run-panda",
        "-e",
        expression_file,
        "-m",
        motif_file,
        "-p",
        ppi_file,
        "-o",
        output_file,
    ]
    if with_header:
        command.append("--with_header")
    if extra_args:
        command.extend(shlex.split(extra_args))
    return _run_command(command, output_file=output_file)


@tool
def run_puma(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str,
    output_file: str,
    extra_args: str = "",
) -> str:
    """Run PUMA through the container wrapper."""
    command = [
        "run-puma",
        "-e",
        expression_file,
        "-m",
        motif_file,
        "-p",
        ppi_file,
        "-i",
        mirna_file,
        "-o",
        output_file,
    ]
    if extra_args:
        command.extend(shlex.split(extra_args))
    return _run_command(command, output_file=output_file)


TOOLS = [explain_panda_puma_io, inspect_netzoo_inputs, run_panda, run_puma]


def build_llm(model_name: str, temperature: float):
    try:
        from langchain_openrouter import ChatOpenRouter

        return ChatOpenRouter(model=model_name, temperature=temperature)
    except ImportError:
        from langchain_openai import ChatOpenAI

        api_key = os.environ.get("OPENROUTER_API_KEY")
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )


def build_graph(model_name: str, temperature: float):
    llm = build_llm(model_name, temperature).bind_tools(TOOLS)
    tool_node = ToolNode(TOOLS)

    system_prompt = f"""
You are a bioinformatics workflow assistant for netZoo PANDA and PUMA.

Your job:
1. Understand the user's natural-language task.
2. Choose the correct tool:
   - explain_panda_puma_io for conceptual questions or format questions.
   - inspect_netzoo_inputs before running when file paths are provided.
   - run_panda only for PANDA regulatory network inference.
   - run_puma only for PUMA regulatory network inference with miRNA prior.
3. If required files are missing, ask for the missing paths instead of guessing.
4. If the task is unrelated to PANDA/PUMA, say no tool should be executed.

Execution mode: {"ON" if EXECUTE_TOOLS else "OFF / dry-run"}.
When execution mode is off, tools may return commands without running them.

Use concise Traditional Chinese unless the user asks otherwise.
""".strip()

    def call_model(state: AgentState):
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = llm.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LangGraph/OpenRouter assistant for choosing and running PANDA/PUMA tools."
    )
    parser.add_argument("--task", help="Task written in natural language. If omitted, ask interactively.")
    parser.add_argument("--execute", action="store_true", help="Actually run PANDA/PUMA commands.")
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        help="OpenRouter model name.",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    global EXECUTE_TOOLS

    args = parse_args()
    EXECUTE_TOOLS = args.execute

    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit(
            "Missing OPENROUTER_API_KEY. Export it first, for example:\n"
            "export OPENROUTER_API_KEY='sk-or-v1-...'"
        )

    task = args.task or input("今天要做什麼？請描述你的 PANDA/PUMA 任務：\n> ").strip()
    if not task:
        raise SystemExit("No task provided.")

    app = build_graph(args.model, args.temperature)
    result = app.invoke({"messages": [HumanMessage(content=task)]})
    print(result["messages"][-1].content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
