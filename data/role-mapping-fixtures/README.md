# Content-based role mapping fixtures

These fixtures test the flow in which the LLM identifies each file's role from
its content when the file names carry no meaning. Run the agent from the
repository root with `OPENROUTER_API_KEY` set.

## 1. PANDA: three meaningless file names

```bash
python scripts/netzoo_agent.py --task "Run PANDA with data/role-mapping-fixtures/unknown-panda/001.tsv, data/role-mapping-fixtures/unknown-panda/002.tsv, and data/role-mapping-fixtures/unknown-panda/003.tsv"
```

Expected: the LLM identifies the three files as `expression_file`,
`motif_file`, and `ppi_file`, shows a confidence and rationale for each, and the
plan stops at `needs_confirmation`.

## 2. PUMA: four meaningless file names

```bash
python scripts/netzoo_agent.py --task "Run PUMA with inputs data/role-mapping-fixtures/unknown-puma/a.tsv, data/role-mapping-fixtures/unknown-puma/b.tsv, data/role-mapping-fixtures/unknown-puma/c.tsv, and data/role-mapping-fixtures/unknown-puma/d.tsv"
```

Expected: besides the three PANDA roles, `d.tsv` is identified as `mirna_file`.

## 3. COBRA: expression and design by content

```bash
python scripts/netzoo_agent.py --task "Analyze data/role-mapping-fixtures/unknown-cobra/x.tsv and data/role-mapping-fixtures/unknown-cobra/y.tsv with COBRA"
```

Expected: `x.tsv` maps to `expression_file` and `y.tsv` to `design_file`,
without relying on the file names.

## 4. CONDOR: network by content

```bash
python scripts/netzoo_agent.py --task "Analyze data/role-mapping-fixtures/unknown-condor/q.tsv with CONDOR and write the output to outputs/condor-content-test"
```

Expected: `q.tsv` maps to `network_file`, and the plan still asks the user to
confirm the LLM's inference.

## 5. LIONESS co-expression: expression by content

```bash
python scripts/netzoo_agent.py --task "Run LIONESS co-expression using data/role-mapping-fixtures/unknown-coexpression/z.tsv"
```

Expected: `z.tsv` maps to `expression_file` and is not mistaken for a PANDA/PUMA
prior or a network.

## 6. Execution after confirmation

To test `/execute`, use interactive mode (omit `--task`, which is a one-shot
preview):

```bash
python scripts/netzoo_agent.py
```

Paste any task above; after the preview, enter `/execute` and confirm with `y`.
`/execute` runs the current approved, ready Work Plan exactly once; afterwards
`/status` should still report `Planning`.

To test only planning and role mapping without running tools, answer `n` at the
confirmation or simply do not enter `/execute`.
