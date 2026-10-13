# 判定層第 1 步：run 路徑 shadow 量測結果

## r17（2026-10-13，dc00b58，只用第一次讀取）

90/90 個 session 都完成，檢查全部確認成功（0 次 provisional），共用 109 次免費呼叫。

| 量測 | 結果 | 事前規則 |
|---|---|---|
| M0：run 措辭下真正走 run 路徑的 session | 15/90（neg 5、mixed 2、pos 8） | — |
| M1：現行 run 路徑誤接受 | 5 | — |
| M2：shadow 抓到的誤接受 | 5/5 | ≥ 60%，成立 |
| M3：正確的 run 被 shadow 誤判 | 1/8 | ≤ 10%，**不成立** |

### 誤接受（現行程式直接排進 run）

- NM11 ×2：證明因果方向，排了 GIRAFFE。
- NM13：用甲基化資料分型，排了 SAMBAR。這和評測 F32 是同一種錯。
- NV2 ×2：每個基因的 embedding，排了 PANDA。

shadow 把這 5 個都判為 gap（沒有任何 workflow 做得到），判斷正確。

### shadow 的錯

- **PQ3-2（M3 的 1/8）**：第一次讀取沒有把「one network including both TF and miRNA regulators」對到任何 workflow。詢問路徑遇到「routing exact、檢查判做不到」的衝突，會再問一次第二意見（Log 390），但 shadow 沒有走這一步。
- **MX1 ×2（mixed 題）**：第一次讀取漏掉「uploaded to a public repository」這項需求，所以判為 agrees。詢問路徑會對漏讀的長段落再讀一次（Log 406），shadow 同樣沒有走。

### 結論

- 依事前規則，M3 不成立，所以不做會實際作用的候選。
- 三個錯都出在 shadow 只用了第一次讀取，沒有走詢問路徑的完整流程。
- 修正方式不是加規則，而是讓 run 路徑走**同一個**完整檢查：`_with_capability_check(shadow_status=...)`，見下一個 commit。之後在同一組題目上再量一次（r17b）。

### 另一個發現（不屬於第 1 步）

- 「幫我跑」的命令中，75/90 被 routing 當成詢問來回答。例如「Run the analysis now: build a cohort-wide TF-to-gene network ...」的回覆，只介紹了 PANDA 和 OTTER 兩個方法。
- 這就是評測 G5 第 3 點說的「把執行請求轉成諮詢」，留到判定層第 2 步處理：verdict 要記住使用者要的是執行，不能把它弄丟。
