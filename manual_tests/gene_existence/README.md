# 基因存在性對照測試（答案卡，不要給 agent 看）

兩份測資的**結構完全一樣**——同樣的行列數、同樣的檔案格式、同樣的
motif↔expression↔PPI 對應關係。唯一的差別是基因標籤在不在 NCBI 裡。
所以 agent 表現出的任何差異，都只能來自基因存在性，不會是別的原因。

## 答案

| | dataset_a | dataset_b |
|---|---|---|
| 表達矩陣基因 | MDM2、BAX、PTEN、CCND1、RB1 | MDM7、BAXP2、CDKN1F、CCND8、RB7 |
| 調控因子 | E2F1、NFKB1 | E2F9、NFKB4 |
| 在 NCBI | **全部都有** | **全部都沒有** |

dataset_b 的名字是刻意仿造的：`MDM1/2/4` 存在但沒有 `MDM7`，`E2F1`～`E2F8`
存在但沒有 `E2F9`，`CDKN1A/B/C` 存在但沒有 `CDKN1F`。光看名字猜不出來，
一定要真的去查 NCBI 才會知道——這正是要測的東西。

## 怎麼跑

每次都換一個新快取，否則前一輪的結果會直接回答這一輪：

```bash
export NETZOO_GENE_CACHE_PATH="/tmp/netzoo-ge-$(date +%s).sqlite3"
```

三個 prompt 的內容在 `prompt_a.txt`、`prompt_b.txt`、`prompt_c_no_taxon.txt`，
直接複製貼進 agent 即可。

**prompt_c 一定要在全新快取下單獨跑。** 它用的是跟 prompt_a 同一份測資，
如果先跑過 prompt_a，那些基因已經以 `human` 存進快取；沒給物種的查詢會沿用
那筆結果直接通過，題目就失效了。實測確認過：冷快取會要求補物種，熱快取會直接放行。

## 預期結果

**prompt_a（真基因）** — 通過驗證，走到 Work Plan，等你 `/execute`。
不該出現任何跟基因有關的錯誤。

**prompt_b（假基因）** — 擋下來，而且要**逐一點名** MDM7、BAXP2、CDKN1F、
CCND8、RB7、E2F9、NFKB4。四條軸（表達基因、motif 目標、motif 調控子、
PPI 調控子）都要報。

失敗的樣子有兩種，都要記下來：
- 放行了 → 驗證根本沒生效
- 只說「驗證失敗」但講不出是哪幾個基因 → 訊息沒有可行動性

**prompt_c（真基因但沒講物種）** — 應該要求你補上物種，訊息裡要提到
`human` / `Homo sapiens` / `9606` 這類例子。

失敗的樣子：說這些基因「不存在」。MDM2、BAX、PTEN 都是真基因，
把「我們沒問清楚」講成「你的資料有問題」是誣賴。

## 比對重點

跑完 a 和 b 之後，把兩邊的輸出擺在一起看：

1. a 過、b 擋 —— 這是最基本的
2. b 的錯誤訊息有沒有**指名道姓**，還是只給一句籠統的失敗
3. b 有沒有**誤傷**——訊息裡不該出現任何 dataset_a 的基因
4. 兩邊花的時間差多少（b 要多做幾次 NCBI 查詢是正常的）

---

## Router regression（已修正，2026-09-16）

原本 semantic router 輸出驗證失敗時，deterministic fallback 無法把「用三個檔案跑
PANDA」辨識為執行指令，也會丟失三個輸入檔、物種與輸出檔。現在 fallback 會：

- 將這種中文句型恢復為明確的 `run_panda`。
- 以檔名提示保留 `expression_file` / `motif_file` / `ppi_file`，再由 preflight
  檢查內容與基因標籤。
- 正確保留 `taxon=human` 與 `.tsv` `output_file`，包含檔案角色確認後的第二次規劃。

prompt_a 可能會先要求確認三個由檔名推定的角色；輸入 `y` 後應通過並產生
Work Plan。prompt_b 應在 preflight 直接被擋下。下面的無 router 比對仍保留作為
gene-authority 層的獨立診斷工具。

## 不經過 router 的跑法

```bash
python manual_tests/gene_existence/run_comparison.py
```

直接對兩份測資跑輸入驗證，每次自動用全新快取，輸出三個案例的結果。
測的就是 prompt 原本想測的那一段。
