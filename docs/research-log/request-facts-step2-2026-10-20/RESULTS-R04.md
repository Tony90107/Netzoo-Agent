# ROUND-04：撤掉要求層重填（shape 2）——gpt-4o-mini 除錯重讀（2026-10-20）

計畫：`collab/ROUND-04-PLAN.md`。程式：`f70d2f84`（shape 2 放在 `NETZOO_CHECK_SCHEMA=2` 之後，預設仍是 shape 1）。題目凍結：`items.json`（`e83db9c3`，在任何 shape 2 讀取之前；26 題，全部看過，只用來除錯）。  
費用：**US$0.112**（50 次成功呼叫；U12 兩組各 2 次被供應商在讀取前拒絕，不計費）。上限 US$0.32。

## 結論

**shape 2 不建議採用。** gpt-4o-mini 在 shape 2 下大多沒有填整段的 `sample_counts` 清單，事實召回從 53/67 掉到 29/67，還造成一個錯誤放行（N11）。輸出 token 沒有下降。輸入 token 反而降了 27%，這是計畫沒預料到的，來源應另外處理（見最後一節）。

## 四個判準

| 判準 | shape 1 | shape 2 | 結果 |
|---|---|---|---|
| G1 輸出 token（25 題合計） | 13,366 | 13,271（−0.7%） | **沒過**：幾乎沒變 |
| G2 事實召回（值） | 53/67 | 29/67 | **沒過** |
| G3 誤套用 | 1（C47：150 套到風險模型） | 0 | 過，但主要因為什麼都沒讀到 |
| G4 判定 | — | 見下表 | N11 錯誤放行 |
| 輸入 token（附帶） | 369,975 | 269,439（−27%） | 計畫預估「幾乎不降」，**估錯了** |

整段樣本數有填的題數：shape 1 有 22 題，shape 2 只有 10 題。例如 K01「12 log-centered expression samples」：shape 1 整段 12、要求層 12；shape 2 的 `sample_counts` 是空的。M23、C45 也一樣。

## 判定差異（G4）

| 題 | 金標 | shape 1 | shape 2 | 說明 |
|---|---|---|---|---|
| N11 | （m3 開發題，2 個樣本跑 LIONESS-DRAGON） | not_available | **available** | 沒讀到「two paired samples」，樣本下限沒套用：**錯誤放行** |
| H18 | dont | 有一列 not_available | 只剩 available 的 DRAGON | 沒讀到未註冊的 lambda_inter |
| M39 | ask | available | needs_fact | 讀取差異（分組中心不確定），方向符合金標 |
| MX03、P13、P24、L13、U11、J11 | | 列的切法不同 | | 結果列切法的讀取變異，與數量無關 |

## 好的部分

- 有讀到的時候，`belongs_to` 讀得對：L10 為 RNA-seq／RPPA，L13 為 transcripts／proteins。
- 範圍（applies_to）沒有造成誤套用。
- 離線部分全部成立：979 筆舊讀取轉換後判定 0 改變；全套測試 4708 passed。

## 輸入為什麼降了 27%

降幅隨句數增加（K01 −2.7k、M23 −7.1k token），應該來自每個要求的 `settings` 欄位：它的說明列出所有已註冊設定（約 3.8k 字元）。送給供應商的 strict schema 會展開引用，所以每一句都重複一次。計畫時我只看了 pydantic 的 `$defs`（只出現一次），因此估錯。**這是推論，尚未單獨驗證。**

## 不能宣稱的地方

- 26 題都看過，每組各讀 1 次；只用來除錯，不能代表泛化。
- 只測了 gpt-4o-mini。production 的能力核對是 nemotron，本輪沒有測。
- U12 兩組都失敗：12 句的請求超過供應商 1,000 個 enum 的上限。production 會改用 compact schema，本 harness 沒有，因此兩組都跳過。

## 檔案

`reread.py`（harness 與計分）、`live/arm1.json`、`live/arm2.json`（原始讀取與 token）、`live/*.log`、`score.json`。
