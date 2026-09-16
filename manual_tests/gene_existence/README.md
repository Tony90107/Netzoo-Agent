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

## 目前 prompt 走不到基因驗證（已實測，2026-09-16）

三個 prompt 都會被 router 擋在最前面，根本進不到基因檢查。實測紀錄：

- 同一個 prompt 連跑三次，三種不同結果：router schema 驗證失敗 / 直接要求澄清 /
  成功路由但列出六個相容 workflow 要你選。溫度是 0，但仍不穩定。
- router 失敗時，deterministic fallback **把三個輸入檔全部丟掉**，只抓到
  `output_dir: outputs/ge_a.tsv`（那是個 .tsv 檔案，不是資料夾）。
  澄清訊息寫「captured inputs will be carried forward」，但其實沒有東西可以 carry。
- 用中文回答它的澄清問題會被拒絕（「Please enter a concrete follow-up question…」），
  英文同義句會被接受。各試兩次，結果一致。
- 即使英文答案成功路由到 PANDA，原本給的三個檔案已經遺失，所以只吐出一段
  「PANDA 需要哪些輸入」的說明，不是可執行的 Work Plan。

這是路由層的問題，跟基因驗證無關。在修好之前，用下面的方式跑這個比對。

## 不經過 router 的跑法

```bash
python manual_tests/gene_existence/run_comparison.py
```

直接對兩份測資跑輸入驗證，每次自動用全新快取，輸出三個案例的結果。
測的就是 prompt 原本想測的那一段。
