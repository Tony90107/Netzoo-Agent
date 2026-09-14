# Gene validation and cross-file matching manual tests

這組資料用來測試目前新增的完整流程：

1. expression header / gene namespace observation。
2. gene identifier 的 cache-first 驗證。
3. cache miss 時的 Websearch fallback。
4. expression gene 與 motif target 的匹配。
5. motif regulator 與 PPI node 的匹配。
6. unknown、invalid、ambiguous gene 的處理。

這些案例會要求 agent 執行 PANDA dry-run，因此會先做 `inspect_inputs` / preflight。這不是實際分析；在 Planning mode 下只會產生 dry-run，只有輸入 `/execute` 才會真正執行。

## 先建立離線 fixture cache

為了讓 canonical matching、invalid 與 taxon ambiguity 可以穩定重現，先建立一個只含測試 metadata 的 SQLite cache：

```bash
cd "/work"
python manual_tests/gene_validation_flow/seed_cache.py \
  --output manual_tests/gene_validation_flow/fixture_gene_cache.sqlite3

# ./netzoo-chat 的 repository mount 是 /work
export NETZOO_GENE_CACHE_PATH=/work/manual_tests/gene_validation_flow/fixture_gene_cache.sqlite3
export NETZOO_GENE_ONLINE_LOOKUP=off
```

如果只在 macOS host 直接執行 Python，把 cache path 改成 host 路徑：

```bash
export NETZOO_GENE_CACHE_PATH="$PWD/manual_tests/gene_validation_flow/fixture_gene_cache.sqlite3"
```

不要把 host 的 `/tmp/...` 路徑直接傳給 `./netzoo-chat`：container 有自己的 `/tmp`，看不到 host 的 `/tmp` 檔案。Compose 現在會把 `NETZOO_GENE_*` 設定傳入 container。

cache 只保存 identifier、namespace、taxon、canonical ID 和 authority metadata，不保存這些 TSV 的內容。

## 案例與預期結果

| 案例 | 測試重點 | 預期 |
| --- | --- | --- |
| `valid_canonical_match` | Ensembl expression、symbol motif、Ensembl PPI | 通過，顯示 canonical gene match |
| `expression_motif_conflict` | motif target 不在 expression | error：沒有 target overlap |
| `motif_ppi_conflict` | motif TF 不在 PPI nodes | error：沒有 TF/PPI overlap |
| `unknown_gene` | cache 中明確標為 invalid 的 identifier | error：authority 不認識 |
| `taxon_ambiguous` | `QSOX1` 同時有 human/mouse cache record | 沒指定 taxon 時 warning；指定 `Homo sapiens` 後 valid |

`unknown_gene` 特別用來區分兩種情況：如果完全沒有 cache record、線上又查不到，現在的 policy 是 `unverified` warning，不會自行宣稱 invalid；本案例因為 seed script 明確放入 `invalid` record，所以才會產生 error。

## 執行離線 direct checks

```bash
cd "/work"
python manual_tests/gene_validation_flow/run_manual_flow.py
```

預期最後看到：

```text
Summary: 6/6 direct checks passed.
```

## 用 agent prompt 測試

將 [prompts.md](prompts.md) 中的 prompt 逐一貼給 agent。每個 prompt 都要求先做 input inspection；通過後允許顯示 dry-run plan，但不會要求你執行 `/execute`。

第二次重跑 `valid_canonical_match` 時，report 應該顯示 cache hit，且不需要再次查 Websearch。

若要專門測試 cache miss 的線上 fallback，請看 [prompts.md](prompts.md) 的第 7 個案例；它需要已設定 `TAVILY_API_KEY` 或 `WEBSEARCH_MCP_URL`，而且結果會受當時 Websearch 回傳內容影響。
