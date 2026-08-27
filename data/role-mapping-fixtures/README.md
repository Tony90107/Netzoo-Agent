# Content-role mapping 測資

這組測資專門用來測試「檔名沒有語意時，由 LLM 根據內容辨識 role」的流程。
請從 `netzoo_agent/` 目錄執行 agent；需要設定 `OPENROUTER_API_KEY`。

## 1. PANDA：三個完全無語意檔名

```bash
python scripts/netzoo_agent.py --task "用 data/role-mapping-fixtures/unknown-panda/001.tsv、data/role-mapping-fixtures/unknown-panda/002.tsv、data/role-mapping-fixtures/unknown-panda/003.tsv 執行 PANDA"
```

預期：LLM 將三個檔案分別辨識為 `expression_file`、`motif_file`、`ppi_file`，並顯示 confidence/rationale；plan 應停在 `needs_confirmation`。

## 2. PUMA：四個無語意檔名

```bash
python scripts/netzoo_agent.py --task "執行 PUMA，輸入 data/role-mapping-fixtures/unknown-puma/a.tsv、data/role-mapping-fixtures/unknown-puma/b.tsv、data/role-mapping-fixtures/unknown-puma/c.tsv、data/role-mapping-fixtures/unknown-puma/d.tsv"
```

預期：除了 PANDA 的三種 role 外，`d.tsv` 應辨識為 `mirna_file`。

## 3. COBRA：expression/design 內容辨識

```bash
python scripts/netzoo_agent.py --task "用 COBRA 分析 data/role-mapping-fixtures/unknown-cobra/x.tsv 與 data/role-mapping-fixtures/unknown-cobra/y.tsv"
```

預期：`x.tsv` 對應 `expression_file`、`y.tsv` 對應 `design_file`，而不是依賴檔名。

## 4. CONDOR：network 內容辨識

```bash
python scripts/netzoo_agent.py --task "用 CONDOR 分析 data/role-mapping-fixtures/unknown-condor/q.tsv，輸出到 outputs/condor-content-test"
```

預期：`q.tsv` 對應 `network_file`，且 plan 仍要求確認 LLM 的推斷。

## 5. LIONESS co-expression：expression 內容辨識

```bash
python scripts/netzoo_agent.py --task "執行 LIONESS co-expression，使用 data/role-mapping-fixtures/unknown-coexpression/z.tsv"
```

預期：`z.tsv` 對應 `expression_file`，不應被誤判為 PANDA/PUMA prior 或 network。

## 6. 確認後的執行測試

若要測試 `/execute`，請使用互動模式（不要加 `--task`，因為 `--task` 是 one-shot preview）：

```bash
python scripts/netzoo_agent.py
```

接著貼上上述任一 task；看到 preview 後輸入 `/execute`，再確認 `yes`。預期 `/execute` 只會針對目前 approved/ready Work Plan 執行一次；執行完成後輸入 `/status`，應仍是 `Planning`。

若只想測試 planning 與 mapping，不想執行工具，可以在確認畫面輸入 `no`，或不要輸入 `/execute`。
