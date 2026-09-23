# NetZoo Agent Semantic Routing 與 Outcome–Evidence 契約研究報告

日期：2026-09-23  
研究分支：`evidence-contract-grounding`  
主要模型：`openai/gpt-4o-mini`  
文件性質：本次 Codex session 的工程研究紀錄，可作為論文討論與後續實驗設計的基礎

## 1. 一句話結論

本次問題不是單一原因，而是兩層問題疊在一起：

1. **第一層是 outcome–evidence 契約矛盾。** 模型被要求輸出一種在 strict JSON Schema 下實際上無法成立的 `inferred` evidence，導致它不是產生不合法資料，就是被迫把推論內容偽裝成 `explicit` 引文。
2. **第二層是語意路由與 evidence grounding 品質。** 結構性契約矛盾修正後，仍有角色、目前輸入與歷史輸入、aggregate 與 sample-specific 的路由錯誤；最新 live A/B 也顯示 claims contract 的 evidence reviewer/validation 尚不穩定。

因此，現在不能說「全部修好」。比較準確的說法是：

> outcome–evidence 的「schema 不可能滿足」矛盾已大致修好，但不能說 evidence 問題全消失；最新 live 結果仍顯示 claims 的 evidence validation 與 semantic routing 都需要改善。

實驗版 `claims` 契約也還沒有超過現行 `legacy` 契約，所以目前不適合升為預設值。

> **第二輪更新（§19）：** 以保存 raw trial 的方式重跑並逐一重放後，aggregate 0/3 被確定為確定性 matcher 問題（PUMA 與 LIONESS-PUMA 在「已陳述 aggregate」時仍打平），claims reviewer 0/11 被確定為 repair 契約形狀問題（允許重複 `hypothesis_index`，並因此撞到 1,200 token 輸出上限）。修正後原 8-case：legacy 14→20/24、claims 13→21/24；新 32-case 四家族語料：legacy 69/96、claims 56/96，claims 仍不升為 default。

---

## 2. 本次 session 做了什麼

這個 session 最初從 NetZoo Agent 的桌面介面架構開始，之後研究重心轉到 semantic routing 與 outcome–evidence 契約。桌面介面已有獨立架構文件，本報告只簡要記錄；主要篇幅放在有實驗數據的 routing 問題。

本次工作的順序如下：

1. 檢查 semantic routing 是否存在契約矛盾。
2. 區分「模型理解錯誤」與「資料契約本身不可能滿足」。
3. 修正 claims schema、prompt、production binding 與 evaluation harness。
4. 執行離線測試與 `gpt-4o-mini` live provider A/B evaluation。
5. 比較 `legacy` 與實驗版 `claims` 契約。
6. 找出修完契約後仍存在的 semantic routing 問題。

系統可簡化為：

```text
使用者文字
  → 模型產生 SemanticClaims
  → outcome / evidence 驗證
  → capability matching
  → 回答、澄清或工作流建議
```

這個流程中，模型負責「理解文字」，確定性程式負責「驗證與匹配」。模型不應直接取得執行授權。

---

## 3. 研究問題

本次研究主要回答四個問題：

1. 原本失敗的主因是 semantic routing，還是 outcome–evidence 衝突？
2. 增加 token budget 到 25,000 或 30,000，能不能解決問題？
3. `gpt-4o-mini` 是否有能力遵守修正後的契約？
4. 契約修正後，還剩下哪些 semantic routing 問題？

---

## 4. 實驗方法與範圍

### 4.1 Live evaluation 設定

本次主要 live evaluation 使用：

- 語料：`tests/routing_semantic_variants.json`
- 案例數：8
- 模型：`openai/gpt-4o-mini`
- temperature：0
- review policy：`when_needed`
- repeat：1
- 比較契約：`legacy` 與 `claims`

每一個案例分成三種核心結果：

- **Passed**：整體驗收通過，包括 routing、semantic 與互動要求。
- **Route passed**：最後路由狀態或推薦工作流符合預期。
- **Semantic passed**：模型產生的科學語意欄位符合預期。

安全性另外計算：若系統在不應執行時取得執行授權，才算 unsafe execution。

### 4.2 這次沒有測什麼

本次 evaluation 明確沒有執行：

- planner；
- executor；
- 真正的生物資訊分析；
- 生物學輸出正確性。

所以本報告只能支持「routing 與契約層」的結論，不能宣稱 NetZoo 工作流的科學結果已被驗證。

---

## 5. 問題的真正主因

### 5.1 第一個根因：Claim 的 support 規則前後矛盾

舊設計允許：

```text
Claim.support = null
```

但下游 outcome validator 又要求已知的 outcome value 必須有 evidence。這代表模型可以通過前面的資料模型，卻在後面的驗證被拒絕。

Prompt 也同時出現兩種互相衝突的要求：

- 每一個 claim 都需要 support；
- unknown 或沒有結果時可以使用 null support。

小模型面對這種矛盾時，沒有唯一正確答案。

### 5.2 第二個根因：Strict schema 讓 inferred evidence 成為不可能的分支

`Support` 原本有兩種形式：

- `explicit`：必須附上原文 `text_span`；
- `inferred`：用 rationale 說明推論，不必附原文。

但舊的自訂 JSON Schema 同時保留外層 optional `text_span` 與內層 `anyOf`。LangChain/OpenAI 的 strict schema 轉換會把外層 object 的每個 property 標成 required；同時 inferred 分支又不允許 `text_span`。

結果是：

```text
strict 模式要求 inferred 一定有 text_span
              ＋
inferred 分支禁止 text_span
              ＝
inferred 永遠無法合法成立
```

這是邏輯上的不可滿足條件，不是單純「模型不夠聰明」。再強的模型也無法穩定滿足互相排斥的規則。

### 5.3 第三個根因：Production 與 evaluation 的 provider binding 不一致

Production claims contract 使用 strict function calling，但原本 `scripts/evaluate_routing.py` 重建 provider adapter 時沒有加上相同的 `strict=True`。

這會造成一個研究方法問題：測試環境量到的不是 production 真正使用的契約，因此 A/B 結果無法完全代表正式路徑。

### 5.4 第四個根因：Evaluation scorer 只理解 legacy repair event

Claims repair event 使用 `repairs`，舊 scorer 卻只讀 `changed_fields`、`evidence_added` 等 legacy 欄位。當 claims repair 真正發生時，evaluation 可能因讀不到舊欄位而失敗。

也就是說，部分錯誤不是 agent routing 失敗，而是評估工具無法正確記錄新的 repair 格式。

---

## 6. 如何修復

主要修復集中在 commit `9876a67`（`Fix strict semantic claims evidence contract`）。

### 6.1 讓每一個 Claim 都必須有 support

將：

```python
support: Support | None = None
```

改成：

```python
support: Support
```

這使 provider schema、Pydantic runtime validation 與下游 evidence validation 使用同一條規則。

### 6.2 Unknown 與 not_applicable 不再變成科學證據

`unknown` 和 `not_applicable` 仍要有 support，因為模型必須說明「為什麼不知道」或「為什麼不適用」。但它們不應被投影成某個已確認的科學事實。

因此投影 outcome 時：

- known value 會產生 evidence；
- `unknown` / `not_applicable` 不會被當成 scientific evidence。

這分開了兩件事：

- **結構完整性**：每個 claim 都有 support；
- **科學承諾**：unknown 不等於已知事實。

### 6.3 重寫 Support provider schema

新的 schema 直接回傳兩個可滿足的 alternatives：

- explicit branch：必須有 `text_span`；
- inferred branch：不要求 `text_span`。

測試會實際把兩種 payload 放入 strict provider schema 驗證，確認兩條分支都可成立。

### 6.4 統一 production 與 evaluation

Production factory 與 live evaluation 都在 claims contract 使用：

```text
method = function_calling
include_raw = true
strict = true
```

因此 evaluation 現在測到的是 production-equivalent provider contract。

### 6.5 移除 prompt 內的矛盾並縮短指令

Prompt 改成明確規定：

- every claim requires support；
- explicit 必須引用原文；
- inferred 應省略 `text_span` 或設為 null，不能放空字串；
- unknown/not_applicable 使用 inferred support；
- 歷史、假設與未來中間資料不能當成目前 input；
- aggregate 與 sample-specific 依結果粒度判定，不依關鍵字。

含完整 29 個 selection tags 時，最後 prompt 為：

- 4,191 characters；
- 433 words；
- 測試上限 4,200 characters。

Strict OpenAI tool schema 完整序列化大小為 7,220 bytes。

Prompt 變短不是主要修復，而是降低小模型同時處理互相重疊規則的負擔。真正關鍵仍是 schema 變得可滿足。

### 6.6 讓 evaluation 支援 claims repair

Scorer 現在同時接受：

- legacy patch fields；
- claims 的 `repairs` payload。

這避免把「評估工具自己崩潰」誤算成「模型 routing 失敗」。

---

## 7. 為什麼這樣修會成功

修復成功的核心不是加入更多 prompt，而是讓三層規則一致：

| 層級 | 修復前 | 修復後 |
| --- | --- | --- |
| 模型面對的 JSON Schema | inferred 分支不可滿足 | explicit、inferred 都可滿足 |
| Runtime validation | support 可為 null | 每個 claim 都必須有 support |
| 下游 evidence validation | known value 又要求 evidence | 與 Claim 規則一致 |
| Production / evaluation | strict 設定不同 | claims 都使用 strict mode |

Strict mode 只能保證結構，不會自動提高語意理解。修正前 strict mode 把模型逼進錯誤的 explicit 分支；修正後 strict mode 才真正發揮作用，能阻止 malformed 或巢狀位置錯誤的輸出。

因此本次結果支持以下因果順序：

```text
先修正不可滿足的 schema
  → strict mode 能穩定控制輸出形狀
  → outcome/evidence 才能被可靠驗證
  → 剩下的失敗才可歸類為 semantic routing 品質
```

---

## 8. 可量化結果

### 8.1 Claims 修復過程

以下都是 8-case、`gpt-4o-mini` 的診斷結果，但中間有多項程式修改，因此適合說明「問題如何被定位」，不應全部當成嚴格單變量實驗。

| 階段 | Overall | Route | Semantic | 關鍵觀察 |
| --- | ---: | ---: | ---: | --- |
| 初始 claims | 0/8（0%） | 0/8（0%） | 0/8（0%） | 大量 terminal goal / schema failure |
| 只壓縮 prompt、尚未完成 strict/schema 修復 | 0/8（0%） | 0/8（0%） | 0/8（0%） | 證明縮短 prompt 本身不足 |
| Strict，但 inferred schema 仍矛盾 | 2/8（25%） | 2/8（25%） | 2/8（25%） | 結構錯誤歸零，但 evidence 被迫假裝 explicit |
| Strict ＋可滿足的 Support schema | 3/8（37.5%） | 3/8（37.5%） | 4/8（50%） | 契約層恢復可用，殘餘轉為語意錯誤 |

Strict 但 schema 尚未修好時：

- schema issues：0；
- explicit evidence entries：56；
- inferred entries：0；
- 找不到原文的 explicit spans：25。

最終 claims round：

- provider calls：19；
- review 新增的 schema issues：0；
- unsafe execution：0；
- evidence spans：65；
- inferred entries：0；
- 找不到原文的 spans：2；
- review repair attempts：2；
- 成功 repair：0。

從 25 個 unmatched spans 降到 2 個，是 evidence grounding 明顯改善；但「inferred 仍為 0」顯示模型仍偏好 explicit，這是需要繼續觀察的訊號，不能解讀成 evidence 問題已完全消失。

### 8.2 先前 repeat=1 的 claims 與 legacy 比較（較早一輪）

程式後續修改前，同一組 8-case corpus 的一輪 repeat=1 結果如下。此數字是較早快照，不應與本報告新增的 repeat=3 live A/B 混為同一輪：

| 契約 | Overall | Route | Semantic | Provider calls | Unsafe execution |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy | 5/8（62.5%） | 7/8（87.5%） | 5/8（62.5%） | 23 | 0 |
| Claims | 3/8（37.5%） | 3/8（37.5%） | 4/8（50%） | 19 | 0 |

這個結果代表：

- claims 已從完全不可用的 0/8 改善到 3/8；
- claims 仍低於 legacy；
- claims 目前不應升為 production default；
- 安全閘門在兩種契約下都沒有出現 unsafe execution。

本次 session 最早的 A/B round 中，legacy 為 3/8 overall、3/8 route、6/8 semantic；claims 為 0/8，合計 42 provider calls、143,005 tokens。之後程式已變更，所以不能把最早與最終數字當成單一因素的直接前後測。

### 8.3 離線驗證

最終修復完成後：

- Pytest：2,005 passed、35 skipped、5 warnings；
- 執行時間：53.66 秒；
- Ruff：通過；
- `git diff --check`：通過。

這些結果證明修改沒有破壞現有離線契約，但不等於證明 live model routing 已達 production 品質。

### 8.4 舊研究對本次結論的補強

2026-09-16 的 297-trial 歷史分析發現：第一次 interpretation 完全沒有 evidence/contract issue 的 trial，最後也只有 15/33（45.5%）通過。另有 38 個 trial 的底層 `match_requested_outcome` 已得到正確 exact match，但較高層 `match_semantic_request` 最後仍回傳 ambiguous 或沒有候選。

這批舊數據不是本次 8-case A/B，不能混在一起計算效果量；但它支持同一個方向：

> evidence 契約不是唯一瓶頸；契約修好後，semantic wrapper、clarification 與 capability matching 仍可能丟掉正確結果。

---

## 9. Budget 與模型能力的判斷

### 9.1 是否需要把 budget 拉到 25,000 或 30,000？

目前沒有證據顯示需要。

本次根因是規則矛盾與 routing 判斷，不是模型沒有足夠輸出空間。增加 token budget 無法讓互相排斥的 JSON Schema 變合法，也無法自動修正 aggregate/sample-specific 的錯誤匹配。

合理策略是：

1. 先修 deterministic contract 與 matcher；
2. 再量測每次呼叫的實際 token 分布；
3. 只有觀察到截斷或 budget exhaustion，才提高上限。

直接提高到 25,000 或 30,000，最可能增加成本與 latency，而不是提高正確率。

### 9.2 問題是不是模型不夠好？

答案是「部分是，但不是主要契約錯誤的原因」。

- Schema 不可能滿足：不是模型能力問題。
- Prompt 自相矛盾：主要是系統設計問題。
- 中文、歷史語境、角色補全：模型能力會影響結果。
- Matcher 丟掉底層 exact result：是確定性程式問題，不是模型問題。

`gpt-4o-mini` 在 schema 修正後可以穩定輸出合法結構，證明它不是完全無法使用。但更強模型可能提高語意理解率，不能取代 deterministic validation 與 routing 規則。

---

## 10. 哪些已修好，哪些還沒有

### 10.1 已大致修好的部分

- Claim support 的 optional/required 矛盾。
- Unknown/not_applicable 被錯投影為 scientific evidence。
- Inferred support 在 strict schema 中不可滿足。
- Claims production 與 evaluation strict binding 不一致。
- Prompt 同時要求 support 又允許 null support。
- Evaluation 不認得 claims repair event。
- 新 schema 是否同時接受 explicit 與 inferred 的離線測試。
- 安全閘門：本次 live rounds 沒有 unsafe execution。

### 10.2 尚未修好的部分

- role/entity 欄位偶爾不一致。
- history 中過去資料被誤判為目前 input。
- aggregate 與 sample-specific 偶爾產生不必要歧義。
- 中文 evidence grounding 與 unknown roles 較不穩定。
- Claims reviewer 做了 2 次 repair，但本次 0 次成功。
- 最終 claims 效能仍低於 legacy。
- 8 cases、repeat 1 太小，尚不能做穩定的統計推論。
- 尚未評估 planner、executor 與生物學輸出正確性。

---

## 11. 四個剩餘 semantic routing 問題：是否能修、如何修

本節只討論方案，不在本次修改程式。

### 11.1 Role/entity 欄位偶爾不一致

#### 問題是什麼

對 regulatory network 而言，若：

```text
regulator_types = [mirna]
target_types = [gene]
```

那麼 `entity_types` 至少應包含 `mirna` 與 `gene`。目前模型偶爾填了角色，卻漏掉對應 entity，觸發 `role_entity:regulatory_network`。

#### 能不能修好

**可修性高。** 這是一個明確的跨欄位 invariant，不必完全依賴模型。

#### 建議做法

1. 把規則寫成 runtime invariant：已知 role 必須包含在 entity_types。
2. 若角色已明確且有證據，可由角色推導缺少的 entity。
3. 推導時記錄 provenance，例如 `derived_from_roles`，避免看起來像模型原本就有填。
4. 只補「被既有角色直接蘊含」的 entity，不猜測新角色。

#### 風險

自動補欄位可能掩蓋模型遺漏。因此不能無條件補值，也不能把 `unknown` 自動變成已知 entity。

#### 驗收指標

- 針對 miRNA→gene、TF→gene、unknown role、mixed role 建立成對測試；
- targeted corpus 的 `role_entity` issue 降到 0；
- wrong-route 數量不能上升。

### 11.2 History 案例把過去資料誤判成目前 input

#### 問題是什麼

例如使用者說「以前用 expression matrix 做過 PANDA，現在想用 mutation data 做另一個分析」，模型可能把歷史中的 expression matrix 也放進目前 `input_artifacts`。

#### 能不能修好

**有界情況下可修性中高，但無法保證所有自然語言都零錯誤。** 明確時間詞與轉折句可以用確定性規則處理；非常含蓄的上下文仍需要模型或澄清。

#### 建議做法

1. 在 capability matching 前先標記 current、historical、hypothetical input。
2. 只有 deterministic witness 明確判定為歷史，且沒有 current witness 時，才從 current inputs 排除。
3. 若同一 artifact 同時可能是過去與現在使用，不要自動刪除，改問一次澄清。
4. 加入中英文 history 對照案例，並保留「現在仍沿用舊資料」的反例。

#### 風險

過度積極排除，可能把真正的目前 input 刪掉。這一項應採 fail-closed：不確定時澄清，不靜默改寫。

#### 驗收指標

- 明確 history cases 的 route 與 input 全部正確；
- current-input control cases 的錯誤刪除率為 0；
- 中英文各自報告結果，不只看合併平均。

### 11.3 Aggregate 與 sample-specific 產生不必要歧義

#### 問題是什麼

當使用者已明確要求一個 cohort network 或每個 sample 一個 network，granularity 理論上已能區分：

- aggregate → PUMA；
- sample-specific → LIONESS-PUMA。

但目前高層 matcher 偶爾仍保留兩個候選，或因「method 未指定」而詢問不必要的澄清。

歷史分析也發現 38 個 trial 的底層 matcher 已有 exact result，高層 semantic wrapper 卻沒有採用。

#### 能不能修好

**可修性高，而且應優先處理。** 這看起來較像 deterministic wrapper/matcher 問題，而不是要求模型再讀得更準。

#### 建議做法

1. 逐步 trace `match_semantic_request` 與 `match_requested_outcome` 的輸入與輸出。
2. 當 artifact、granularity 與 roles 已完整時，把 granularity 當成 hard discriminator。
3. 不要因為使用者沒有指定方法名稱，就把已完整的科學結果視為不確定。
4. 把「exact terminal route」與「可延伸的 multi-step pipeline 建議」分開，避免 pipeline 候選污染單一步驟 routing。
5. 建立只改一個詞的 matched-pair 測試：aggregate 與 sample-specific 其他內容完全相同。

#### 風險

如果規則太強，可能錯誤排除合法的 multi-step workflow。解法不是保留所有候選，而是把 terminal match 與 pipeline suggestion 分成不同欄位。

#### 驗收指標

- 已完整 granularity 的案例不再出現 unnecessary clarification；
- aggregate/sample-specific matched pairs 都選到唯一正確 route；
- genuinely ambiguous controls 仍會要求澄清。

### 11.4 中文 evidence grounding 與 unknown roles 不穩定

#### 問題是什麼

Explicit support 必須引用原始請求中的連續文字。模型有時會：

- 把中文翻成英文後當成原文引用；
- 改寫中文詞句，造成 span 對不上；
- 已辨識出 miRNA/gene role，卻又額外加入 `unknown` role。

#### 能不能修好

**Exact grounding 的可修性高；完整語意角色推論的可修性中等。** 原文 span 是否存在可以確定性檢查，但含蓄中文的生物角色仍可能需要模型理解。

#### 建議做法

1. Explicit span 必須是原文精確 substring；對不上就不能標 explicit。
2. 若內容是合理推論但不是原文，必須使用 inferred support。
3. 建立小型、可稽核、ontology-backed 的中英詞彙對照，例如 miRNA、基因、樣本、病人、個別、群體。
4. 如果同一 role dimension 已有明確 known role，不要再無理由加入 `unknown`；但只能在 deterministic evidence 足夠時移除。
5. 擴充中文 paraphrase corpus，並對每個案例重複執行多次。

#### 風險

大型關鍵字表容易過度擬合。詞彙表應保持小、可解釋，並由 ontology 限制，而不是無限制加入同義詞。

#### 驗收指標

- 中文與英文的 semantic/route pass-rate gap；
- unmatched explicit quote 數量；
- 已知角色旁額外插入 unknown role 的比率；
- 每個指標都用多次 repeat 報告平均與範圍。

---

## 12. 建議優先順序

若以「最快提升 routing 正確率」排序：

1. **Aggregate/sample-specific ambiguity**：可能是 deterministic wrapper 丟掉 exact match，影響路由最直接。
2. **Role/entity invariant**：規則小而清楚，容易用測試封住。
3. **History/current input**：很重要，但自然語言情境較多，需保守設計。
4. **中文 grounding/unknown roles**：exact span 可先修，整體品質需要擴充 corpus 才能可靠判斷。

若研究目標最重視「避免錯用資料」，可以把 history/current input 提到第一順位。

我建議每次只處理一個問題，先寫 matched controls，再跑同一模型。不要四項一起改，否則即使分數提高，也無法知道是哪個修復造成的。

---

## 13. 論文中應如何解讀這些數據

### 13.1 可以合理寫的結論

可以寫：

> 本研究發現，結構化輸出的失敗不一定代表語言模型缺乏領域理解。當 provider JSON Schema、runtime validation 與下游 evidence validation 之間存在矛盾時，模型可能被迫產生形式合法但語意不實的 evidence。修正契約後，實驗版 claims contract 的整體通過率由 0/8 提升至 3/8，semantic pass 由 0/8 提升至 4/8；同時 strict schema issue 維持為 0，未匹配原文的 evidence spans 由 25 降至 2。這表示契約一致性是必要條件，但不是充分條件，因為剩餘失敗主要集中在角色一致性、時間語境、粒度消歧與跨語言 grounding。

也可以寫：

> 在相同的 8-case corpus 與 gpt-4o-mini 設定下，最終 experimental claims contract 的 overall/route/semantic 通過數為 3/8、3/8、4/8，仍低於 legacy contract 的 5/8、7/8、5/8。因此本研究保留 legacy 為預設契約，並將 claims 視為尚未達到 promotion gate 的實驗設計。

### 13.2 不應過度解讀的地方

不應寫成：

- 「claims 提升了 37.5 percentage points，所以已證明一定有效」；
- 「temperature 0 代表每次結果完全相同」；
- 「unsafe execution 為 0，所以整個 agent 絕對安全」；
- 「所有 evidence 問題都已修好」；
- 「增加 token budget 一定沒有任何幫助」。

原因是：

- n=8、repeat=1 太小；
- 中間有多項程式修改，不是所有 round 都是單變量；
- provider 即使 temperature 0 仍可能有執行差異；
- 沒有執行 planner、executor 與生物學分析；
- 目前語料集中於 miRNA/PUMA/LIONESS 類型，不能代表全部 NetZoo workflows。

### 13.3 下一輪適合論文使用的實驗設計

建議下一輪：

1. 每個剩餘問題建立 matched-pair corpus；
2. 英文與中文分層；
3. 每個 case 至少 repeat 3；
4. 固定模型、prompt、policy、code commit；
5. 每次只改一個 deterministic rule；
6. 同時報告 overall、route、semantic、clarification、unmatched span、unsafe execution；
7. 保留 raw JSON report 與 corpus hash。

這樣才能從「工程除錯紀錄」提升為更接近論文可重現的對照實驗。

---

## 14. 研究限制

- 本次最終 live corpus 只有 8 cases。
- repeat 為 1，不能估計穩定變異。
- 不同診斷 round 之間並非都只有一個變因。
- 最終 session live output 沒有另外保存成 committed JSON；本報告記錄其摘要，後續應用固定檔名保存 raw report。
- 安全評估只涵蓋 routing boundary。
- 沒有測生物學結果是否正確。
- 沒有比較更強模型在本次完全相同 commit 上的結果。

因此這批數據適合做 thesis discussion、failure analysis 與下一步實驗依據，不適合單獨作為大規模效能結論。

---

## 15. 重現方式

在專案根目錄、已設定 provider credentials 的環境中執行：

```bash
set -a
. ./.env
set +a
~/.venvs/netzoo-qa/bin/python scripts/evaluate_routing.py \
  --scenarios tests/routing_semantic_variants.json \
  --live \
  --model openai/gpt-4o-mini \
  --semantic-contract claims \
  --review-policy when_needed \
  --repeat 1 \
  --max-calls 24 \
  --timeout 60 \
  --json
```

建議後續把輸出存成帶日期、commit SHA、model、contract 與 repeat 的 JSON 檔案，但不要把 `.env` 或 API key 納入版本控制。

---

## 16. 相關檔案與 commit

主要程式：

- `scripts/netzoo_agent_core/contracts/semantic_claims.py`
- `scripts/netzoo_agent_core/interpretation/claim_prompt.py`
- `scripts/netzoo_agent_core/graph/factory.py`
- `scripts/evaluate_routing.py`

主要測試與語料：

- `tests/test_semantic_claims.py`
- `tests/test_routing_evaluation.py`
- `tests/routing_semantic_variants.json`
- `scripts/compare_semantic_contracts.py`

本次 session 相關 commits：

- `ccdf96b` — Harden semantic contract promotion gates
- `c35e558` — Tighten package contracts and routing adapters
- `586de78` — Verify bundled demo provenance offline
- `9a55732` — Update verified demo conversation snapshot
- `04d9468` — Clarify synthetic fixture test contracts
- `ec6a1fe` — Split oversized core modules by responsibility
- `9876a67` — Fix strict semantic claims evidence contract

背景研究：

- `docs/research-log/2026-09-16-routing-failure-distribution.md`
- `docs/research-log/2026-09-07-semantic-routing-controls.md`
- `docs/results/netzoo-routing-findings.md`

---

## 17. 第一輪研究結論（本輪修復前）

目前最合理的判斷是：

- **Outcome–evidence 衝突：主要結構性矛盾已修正。**
- **Semantic routing：仍是現在的主要品質瓶頸。**
- **Claims contract：已可測、可驗證，但尚未優於 legacy。**
- **Budget：目前沒有理由直接提高到 25,000 或 30,000。**
- **模型：gpt-4o-mini 不是唯一問題；換強模型可能改善語意，但不能修 deterministic bug。**
- **四個剩餘問題：都有改善路徑，其中 role/entity 與 granularity 最適合先用 deterministic rule 修；history 與中文語意需要更保守的規則及更大的對照語料。**

因此，本次修復是成功的「契約層修復」，但還不是完成的「routing 品質修復」。

---

## 18. 追加修復與評估解讀（2026-09-23）

本節記錄後續針對四個 semantic routing 剩餘問題所做的修正，以及如何解讀前一輪的 reviewer 與小樣本數字。

### 18.1 本輪修正

1. **role/entity 一致性：** 已由證據支持的 regulator/target role，會連同必然對應的 entity 一起補齊；明確的 TF/miRNA 對 gene 片語也會以同一個驗證後的變更補上兩個 role 與 entity。沒有證據或明確片語時，不會猜未知角色。
2. **歷史與目前輸入：** 加入「this time / 這次／本次」等目前範圍提示，讓「以前用 expression，這次用 mutation」分別保留正確的時間範圍。
3. **aggregate 與 sample-specific：** 增加中英文自然說法，例如「整群病患共用一張網路」、「每位病患各自估計網路」及「one independently inferred network per sample」。若同一個請求明確同時表達兩種粒度，仍不由規則自行選一種。
4. **中文 evidence grounding 與 unknown roles：** reviewer 指示要求引文必須是原文連續片段、不能翻譯或改寫；推論應標為 inferred。空 patch 不算修復，並會被丟棄而保留第一個已通過驗證的 interpretation。
5. **量測方式：** evaluation 報告新增 reviewer 呼叫原因、驗證率與最終 semantic/routing 成功率；另按 prompt 本身去重，明確分開 unique prompts 與 repeats，避免把重跑誤算成更多獨立案例。

### 18.2 如何理解 reviewer 0/2

前一輪的「2 次修復、0 次成功」應寫成：**觀察到 2 次修復機會，該輪 0 次符合預先設定的成功條件。** 不能寫成「reviewer 修復能力是 0%」或「模型不會修復」。樣本只有 2 次；若勉強套用獨立二項試驗的雙側 95% exact interval，成功率範圍約為 0%–84%。而同一模型與相似錯誤案例通常也不完全獨立，所以這個區間只能說明資料太少，不能當作模型的可靠能力區間。

後續 reviewer 測試應以**不同的失敗案例**作為分母，並事先定義成功必須同時滿足：修正目標錯誤、修復結果通過 schema/evidence 驗證、沒有引入新的錯誤。每次失敗還要記錄原因類別，例如空 patch、格式/驗證失敗、引用不在原文、或修正後仍語意錯誤。建議先蒐集至少 30 個不同的修復機會並按錯誤類型分層作工程診斷；若論文要對成功率差異作強推論，仍需依預期效果與檢定力分析決定樣本數，30 不是自動足夠的保證。

### 18.3 如何理解 8 cases、repeat 1

8 個不同 prompt、每個只跑一次，是**failure analysis / pilot**，適合列出哪種錯誤發生、用來找修正方向；不適合宣稱某版本普遍較好，也不適合用單一百分比推論模型整體能力。

重跑同一題只能觀察該題的變動性，不能增加獨立 prompt 數。例如 8 題 × repeat 3 是 24 次 trial，但統計上的不同 prompt 仍最多只有 8 題；如果題目只是大小寫或表面改寫，實際上還可能更相似。因此建議分兩階段：

- **工程診斷：** 建立 32 個具內容差異的案例，每個問題家族 8 個（role/entity、history/current、granularity、中文 grounding/unknown），並加入方向相反的配對案例；每題 repeat 3，用來找不穩定案例。這仍應稱為診斷性評估，不稱為強統計證據。
- **論文比較：** 以 unique prompt 為分析單位，對同一批 prompt 做配對 A/B；報告各問題類別分數與信賴區間，並在看結果前決定成功定義及樣本數。要做顯著性／強推論時，先做 power analysis，不能用 repeat 數代替 prompt 數。

evaluation 現在會輸出 `unique_prompts`、`repeat_count`、`prompts_passed_every_repeat` 與 `prompt_repeat_disagreements`，讓這兩種數量不再混在一起。

### 18.4 本輪驗證狀態

- 完整 pytest：**2,013 passed、35 skipped、5 warnings**，本次重跑用時 55.59 秒。
- Ruff：通過；`git diff --check`：通過。
- 8-case corpus schema：通過。
- 當時尚未執行 live GPT-4o-mini A/B；後續已由使用者載入本機 provider credentials 並回傳 repeat=3 結果，詳見 18.5。

因此，本輪程式與離線契約修復已通過測試；四項語意改善能否提升 live routing 表現，須以新增的 A/B 結果及更大的去重語料一併判讀。

### 18.5 使用者執行的 live A/B（repeat=3）

使用者在本機載入 provider credentials 後，以相同 8-case corpus、`openai/gpt-4o-mini`、`review_policy=when_needed`、每個案例 repeat=3，分別執行 `legacy` 與 `claims`。每個設定共 24 次 trial，但只有 8 個不同 prompt；重複只用來觀察同題穩定性，不能當成 24 個獨立樣本。

| 指標 | Legacy | Claims | 解讀 |
| --- | ---: | ---: | --- |
| Overall 通過 | 13/24（54.2%） | 13/24（54.2%） | 整體相同，claims 沒有勝出 |
| Route 通過 | 16/24（66.7%） | 13/24（54.2%） | 此輪 legacy 較高 |
| Semantic 通過 | 15/24（62.5%） | 14/24（58.3%） | 此輪 legacy 略高 |
| Semantic reviewer 成功 | 6/17（35.3%） | 0/11（0%） | claims reviewer 本輪沒有成功案例 |
| Reviewer validation | 16/17（94.1%） | 2/11（18.2%） | claims 的 reviewer 輸出較常未通過驗證 |
| 未匹配 evidence 形狀 | 0 | 15（4 個全 unmatched 群組） | claims 仍有 live evidence-grounding 問題 |
| Provider calls | 68 | 55 | claims 少 13 次呼叫，但不能單獨視為效率提升；它也少做 reviewer 嘗試 |
| 三次都通過的不同 prompt | 4/8 | 3/8 | claims 的穩定通過題數沒有增加 |

分案例通過次數：

| 案例 | Legacy | Claims |
| --- | ---: | ---: |
| `mirna-case-lower` | 3/3 | 2/3 |
| `mirna-case-upper` | 3/3 | 3/3 |
| `mirna-per-person` | 1/3 | 3/3 |
| `mirna-heterogeneity` | 3/3 | 3/3 |
| `mirna-chinese` | 0/3 | 0/3 |
| `mirna-history` | 3/3 | 2/3 |
| `mirna-cohort` | 0/3 | 0/3 |
| `mirna-cohort-zh` | 0/3 | 0/3 |

主要觀察：

1. **Claims 沒有整體提升。** Overall 同為 13/24；`mirna-per-person` 從 1/3 提升到 3/3，但 `mirna-case-lower` 和 `mirna-history` 各少一次通過，總分抵銷。
2. **原先最關心的中文與粒度問題仍在。** 中文 sample-specific、中文 aggregate、英文 aggregate 在兩種契約下都 0/3。輸出多次把本來完整的目標標成 `ambiguous`，不提供預期 workflow，或在 claims 下落入 semantic fallback。
3. **這不等於最初的 schema 矛盾復發。** 兩輪 `unsafe_execution_count` 都是 0，且 reviewer 沒有引入 schema issue；但 claims 的 unmatched evidence（15 個）及 reviewer validation（2/11）顯示，結構合法不代表 evidence span 對得上原文，也不代表 reviewer 能修好。
4. **目前可定位到失敗表徵，還不足以證明單一根因。** 下一步應先保存並比對失敗 trial 的原始 semantic claims、evidence span、review request/response 及 validator 診斷，確認 unmatched 是 span 選取、claims 投影還是 reviewer 修補造成，再針對該環節設計測試；暫時不應只靠加 prompt 或換更大模型推論能解決。

此結果適合作為工程 failure analysis：每個案例只有 3 次重複、8 個 unique prompts，不能用來做強統計推論或宣稱 claims 一般性地優於/劣於 legacy。論文可報告為本次診斷性 paired A/B 結果，並明確揭露樣本數與限制。

---

## 19. 根因追查（traced live capture）與修正（2026-09-23，第二輪）

### 19.1 事前宣告（在跑修正後的 live round 之前寫下）

下列判準在執行修正後的 live round **之前**寫入。依本專案既有量測經驗（same-code 單輪差距 3–4、consecutive rounds 不是獨立樣本），**分數差 ≤ 3 不作任何結論**；判準以結構性計數為主。

- **S1（repair 形狀）**：claims reviewer 輸出中「重複 `hypothesis_index`」的次數必須為 0（新 schema 已無法表達）；「指向不存在 hypothesis 的 index」預測 ≤ 1。
- **S2（輸出截斷）**：reviewer 呼叫中 `output_tokens == 1200`（撞到 router 輸出上限）的次數，預測每個契約每輪 ≤ 1（修正前 claims 為 2/11 與 3/7）。
- **S3（aggregate 不必要澄清）**：第一次 interpretation 已是 `granularity=aggregate` 的 miRNA 請求，最後仍以 “Should the result be aggregate or sample-specific?” 結束的 trial 數必須為 0。若 > 0，F1 視為不完整，先查原因、不宣稱修好。
- **S4（假 witness）**：兩份語料中與 expected granularity 矛盾的 granularity witness 數必須為 0（離線已驗證，live 前後不變）。
- **計分指標**：只報告 paired（同一 unique prompt）結果與各問題家族分數，不做顯著性推論；claims 是否升為 default **不在本輪決定**。

### 19.2 方法：保存原始 trial，而不是只看彙總

18.5 的 repeat=3 A/B 沒有保存 raw report，且既有 report 本來就不含 raw claims 與 reviewer request/response。因此本輪先用一個 scratch harness（包住 `evaluate_routing.evaluate`，**不改 production 路徑**）重跑同一 8-case、repeat=3、`gpt-4o-mini`、`when_needed`，逐 trial 記錄：每次 structured-output 呼叫的 schema、輸入 messages、raw tool-call arguments、parsed/parsing_error、`finish_reason`、token usage、`invalid_tool_calls`，以及所有 routing events。重跑結果與 18.5 相近（legacy 14/24、claims 13/24），代表失敗型態可重現；之後所有根因都由**把記錄下來的模型輸出離線重放**過目前的 decode → apply → restore → validate → match 程式確認，不靠推測。

### 19.3 根因一：aggregate 案例 0/3 是確定性 matcher 問題，不是模型問題

- 完全正確的 aggregate outcome（`regulatory_network`、`aggregate`、miRNA→gene、無 input）直接丟給 `match_requested_outcome`，得到 `ambiguous` 與 “Should the result be aggregate or sample-specific?”——使用者已經回答的問題。
- 原因：`run_lioness_puma` 宣告 `granularities: [aggregate, sample_specific]`（它在計算 per-sample 網路途中會產生 PUMA 的 cohort 網路）。aggregate 請求因此同時符合 PUMA 與 LIONESS-PUMA；兩者 `stated_dimension_score` 相同（2 vs 2），唯一差異是 LIONESS-PUMA 有 `guidance_predecessors: [run_puma]`，而該維度依設計不可 certify exact。
- 舊語料 `aggregate-mirna-network` 過去能過，是靠 legacy 專有的第 4 次 `semantic_discriminator` 呼叫補上 `selection_tags: [aggregate_network]`；claims 契約沒有 discriminator，因此 claims 在 aggregate 上沒有路可走。
- Legacy `mirna-cohort` 三次的因果鏈：第一次 interpretation **完全正確** → matcher tie → `registry_ambiguity` 觸發 reviewer → reviewer 補對了 tag，但同時把 `input_artifacts` 寫成 `[regulatory_network]`（引用的是「輸出」那句話，逐字存在所以通過 grounding）→ 路由崩潰。Reviewer 的錯是 matcher tie 的下游結果。
- `mirna-cohort-zh` 另有一層：「不需要每位病患各自的網路」中的 `不需要` 不在否定詞表，因此被當成**明確陳述**的 sample-specific witness，請求同時帶兩種粒度，witness 不能使用。

### 19.4 根因二：中文 / per-person sample-specific 失敗，來自「inferred 的 granularity 被當成未陳述」

- Legacy `mirna-chinese` 與 `mirna-per-person` 失敗 trial 與通過 trial 的 outcome **完全相同**；唯一差別是失敗者把 `granularity=sample_specific` 的 evidence 標為 `inferred`。
- 離線重放：同一 outcome，`match_requested_outcome` → exact LIONESS-PUMA；`match_semantic_request` → ambiguous {PUMA, LIONESS-PUMA}。這正是 2026-09-16 歷史分析中「38 個 trial 底層 exact、wrapper ambiguous」的機制：guidance 模式把 `operation` 抹成 `unknown` → 走 explicit-evidence 分支 → inferred 的 granularity 不被計入 → aggregate-only 的 PUMA 也被列為候選 → tie。
- 依 `3ca0dc3` 的原則（exact 必須由請求陳述的維度決定），忽略 inferred 值本身是設計；真正的缺陷在前一步：請求**確實逐字陳述了**粒度（「每位病患…網路」），deterministic witness 也找得到，但 `restore_stated_fields` 只在「沒有任何同值 evidence」時才補 explicit witness，一個 inferred（或引文對不上）的同值 claim 反而把 witness 擋掉。

### 19.5 根因三：claims reviewer 0/11 是 repair 契約形狀問題

逐一重放 claims 的 11 次 reviewer 輸出（另以 finish_reason 重跑受影響案例共 9 次）：

| 失敗機制 | 第一輪 | 重跑 | 說明 |
| --- | ---: | ---: | --- |
| `repairs` 重複同一 `hypothesis_index`（`[0,0]`、`[0,0,0]`）或指向不存在的 hypothesis（`[0,1]`、`[0,1,2]`） | 7 | 7 | 模型把整個 outcome 重寫 2–3 次；`apply()` 在驗證前就丟 ValueError |
| 沒有 tool call（輸出截斷） | 2 | 3 | `output_tokens` 剛好 1,200（`DEFAULT_ROUTER_MAX_TOKENS`），arguments 是被截斷的 JSON，LangChain 丟進 `invalid_tool_calls` |
| 引文錯誤（真正的模型 grounding 失誤） | 1 | 0 | 例：`"mi-r-na"` 對 `mi-rna`，且把 operation 改成 `acquire` |
| 通過驗證 | 0 | 1 | 但仍落在 PUMA/LIONESS-PUMA tie |

結論：截斷與重複 index 是同一個失敗——claims 的 `repairs: list[{hypothesis_index, outcome}]` 允許重複 index，模型就把同一個 outcome 反覆寫，既違反 apply 也撐爆輸出上限。Legacy `SemanticPatch` 一直只有單一 `hypothesis_index`，這正是 legacy reviewer validation 16/17 而 claims 2/11 的主因。另外，7 次 shape failure 中有 5 次若去重即可通過驗證——但仍會卡在根因一的 tie，所以即使 reviewer 完美也修不好 aggregate。

### 19.6 根因四：claims 第一次 interpretation 的 unmatched evidence

9 個 unmatched 形狀中 5 個是中文**壓縮引用**（`建立調控網路的方法` 對原文 `建立一張調控網路的方法`；`每位病患的調控網路` 在原文中不連續存在），1 個是完全捏造的 tag 引文（`jointly inferred TF-gene regulatory network`）。這些是真正的模型引用錯誤；`aligned_span` 依設計不對非 ASCII 字詞容錯（刪字會把 `不` 之類的否定也刪掉），因此本輪**不放寬**中文比對。可由 deterministic witness 覆蓋的維度（granularity）改由 witness 提供逐字引文（見 19.7 F3）；operation 的中文壓縮引用仍會讓 claims 的中文案例進入 reviewer。

### 19.7 修正（每項都對應一個已重放確認的根因）

| 代號 | 修正 | 檔案 | 對應根因 |
| --- | --- | --- | --- |
| F1 | 若候選 pipeline 的已宣告 `guidance_predecessors` 也在候選集中、且該 predecessor 已能產出**被陳述的**粒度，移除該 pipeline（LIONESS-PUMA 的 cohort 網路就是 PUMA 的結果）。只用 registry 既有宣告；粒度 unknown 時不作用。同一規則套用在 strict matcher 與 hypothesis-level advisory ranking。 | `routing/requested_outcome_matching.py`、`routing/outcome_matching.py` | 19.3 |
| F2 | 否定詞加入 `不需要／不要／不用／無需`；中文 granularity witness 必須連到網路名詞（與英文 witness 一致），移除三個假 witness：「整體突變負荷量」、「單一樣本網路」、「每個樣本狀態的 TFA 矩陣」；補上語料中已出現的英文句型（“separate … network for each person”、“one … network shared across the whole cohort”）。 | `interpretation/request_integrity.py` | 19.3、19.4 |
| F3 | 唯一 witness 存在時，取代同值但 `inferred` 或引文對不上的 granularity evidence；已逐字 grounded 的 explicit evidence 保留不動；不同值絕不改寫。 | `interpretation/stated_field_restoration.py` | 19.4、19.6 |
| F4 | `SemanticClaimRepair` 改為單一 `hypothesis_index` + `outcome`（與 legacy patch 同形），重複 index 在 schema 上無法表達；事件仍以一元素 `repairs` 清單記錄，舊 report 讀法不變。代價：一次 review 只能修一個 hypothesis。 | `contracts/semantic_claims.py`、`graph/claim_invocation.py` | 19.5 |

**這是對既有設計決定的反轉，需明確記錄：** `tests/test_exact_needs_a_stated_discriminator.py` 原本把「aggregate 的 PUMA vs LIONESS-PUMA」釘為 ambiguous，理由是兩者只差未陳述的 predecessor 維度。F1 的立場是：被陳述的 aggregate 本身就能區分兩者。該測試保留原則（未陳述的維度不能 certify exact），改用 `granularity=unknown` 的同形案例釘住，並新增一個測試釘住 stated aggregate → PUMA。`tests/test_capability_corpus_coverage.py` 的 reachability helper 改為選擇「predecessor 無法提供」的粒度作為該 capability 自身定義。

**沒有做的事：** 沒有修改任何 system prompt 措辭（本專案禁止以 prompt 措辭誘導行為；見 `sambar-agent-routing.md`）。另外注意：前一個 session 已在工作樹中（未 commit）對 claims reviewer prompt 加入 “Do not return an empty patch … Do not translate or paraphrase a quote” 等措辭；traced 結果顯示那段文字沒有阻止重複 index、截斷或中文壓縮引用（claims reviewer 仍 0/11）。本輪保留該修改未動，建議日後依既有規則評估是否撤回。

### 19.8 離線驗證

- **Generated grid**（10,395 個 outcome × 5 種 matcher 視角：base、guidance/execute × explicit/inferred granularity）：F1 改變 162 個 outcome，**全部**是 aggregate `regulatory_network`；類型只有兩種——PUMA/LIONESS-PUMA ambiguous → exact PUMA，或 ambiguous 候選集移除 LIONESS-*。沒有任何 exact 結果被改變或失去（0 violations）。Aggregate TF 請求仍是 PANDA/OTTER/GIRAFFE 的真實方法選擇（ambiguous）。
- **重放已記錄的第一次 interpretation**（模型輸出固定、只換確定性程式）：claims 24 個第一次 interpretation 中 18 個直接得到正確 exact route（整輪原本 13/24 通過），`mirna-cohort-zh` 3/3、`mirna-cohort` 2/3；legacy 16/24 直接 exact，其餘 8 個是 legacy 已知的 `missing_evidence`（通常由 legacy reviewer 修好）。
- **Witness 稽核**：兩份語料所有 prompt 的 granularity witness 與 expected granularity 無矛盾（S4 = 0）。
- **Pytest（最終狀態，含 F5/N1）**：2,057 passed、35 skipped（修正前 2,013 passed）；新增 `tests/test_granularity_history_role_regressions.py` 41 個測試（aggregate/sample-specific 配對、witness 真陰性、history/current 配對與反例、hypothetical 目標、role/entity 蘊含、`sample` 非節點）；另更新 `test_semantic_claims.py`、`test_stated_field_restoration.py`、`test_exact_needs_a_stated_discriminator.py`、`test_capability_corpus_coverage.py` 中被本輪刻意改變的期望。Ruff：本輪所有變更檔案通過；`scripts/netzoo_agent_core/routing/candidate_ranking.py` 有一個 `HEAD` 既存的 F401（未使用的 `Sequence`），非本輪引入。

### 19.9 Live 結果（修正後；`gpt-4o-mini`、`when_needed`、repeat=3，兩契約同時段執行）

**時序注意：** 下列兩輪是在 F1–F4 完成後啟動；F5（見 19.10）與 N1 修正（見 19.10）是在這兩輪**之後**才加入，因此 live 數字只量到 F1–F4。F5/N1 的效果目前只有離線重放證據。

#### 原 8-case 語料（與 19.2 的修正前 traced round 同 prompts）

| 指標 | Legacy 修正前 → 後 | Claims 修正前 → 後 |
| --- | ---: | ---: |
| Overall | 14/24 → **20/24** | 13/24 → **21/24** |
| Route | 14/24 → 21/24 | 13/24 → 21/24 |
| Semantic | 18/24 → 23/24 | 13/24 → 21/24 |
| 三次都通過的 prompt | 4/8 → 6/8 | 3/8 → 6/8 |
| Reviewer validation | 16/16 → 11/12 | 0/11 → **4/5** |
| Reviewer 呼叫數 | 16 → 12 | 11 → 5 |
| `mirna-cohort` / `mirna-cohort-zh` | 0/3、0/3 → 3/3、3/3 | 0/3、0/3 → 3/3、3/3 |
| `mirna-chinese` | 0/3 → 0/3 | 0/3 → 1/3 |
| unsafe execution | 0 → 0 | 0 → 0 |

差距（+6、+8）大於本專案量測過的 same-code 單輪差距（3–4），而且與結構性計數一致；但這仍是**連續兩輪**、非交錯重複，不報 p 值。

#### 新 32-case 四家族語料（`tests/routing_semantic_families.json`，每家族 8 題，含方向相反的配對與真正歧義的對照題）

事後發現一個**語料錯誤**並已更正：`hist-agg-then-ss-en/zh` 把 `run_puma` 列為 forbidden，但 scorer 檢查 `recommended_actions`，而 LIONESS-PUMA 的已註冊 guidance 序列本來就以 PUMA 為第一步。重新計分**只移除這一項檢查**，原始與更正後的 report 都已保存（見 19.12）。

| 家族（各 24 trials） | Legacy pass / route / sem | Claims pass / route / sem |
| --- | ---: | ---: |
| granularity | 15 / 16 / 15 | 13 / 14 / 15 |
| history/current | 19 / 19 / 20 | 15 / 15 / 15 |
| role/entity | 14 / 17 / 14 | **8 / 10 / 9** |
| 中文 grounding | 21 / 22 / 22 | 20 / 20 / 20 |
| **合計（96）** | **69 / 74 / 71** | **56 / 59 / 59** |

- 以 unique prompt 為單位配對：claims 較好 6 題、較差 9 題、相同 17 題；三次都通過的 prompt：legacy 20/32、claims 15/32。
- Reviewer validation：legacy 47/62（75.8%）、claims 30/59（50.8%）；reviewer success：legacy 35/62、claims 19/59。
- Unmatched evidence：legacy 3、claims 41（claims 最多的是 `operation` 21 個，其次 `entity_type` 6、`granularity` 5、`regulator_type` 5）。
- unsafe execution：兩者皆 0。

#### 事前判準結果

- **S1**：claims 重複 index 0、out-of-range 0（兩份語料皆然）。成立。
- **S2**：reviewer `output_tokens == 1200` 0 次（兩份語料、兩契約）。成立。
- **S3**：原 8-case 兩契約皆 0（修正前 legacy 3、claims 5）。32-case：legacy 0；claims 字面計數 **1**，該 trial 是 `gran-mirna-unstated-control`（請求**沒有**陳述粒度，模型第一次卻寫 `aggregate`，最後的粒度澄清正是該對照題的期望行為）。依事前寫法 S3 字面上不是 0；在「請求有陳述 aggregate」的 prompts 上為 0。兩個數字並列，不改寫判準。
- **S4**：0。成立。

### 19.10 語料擴充後新發現的失敗類別

| 代號 | 現象 | 根因層 | 本輪處理 |
| --- | --- | --- | --- |
| N1 | `terminal_goal_conflict:sample_cluster_assignment` 強加在 “If I later obtain … I might cluster patients, but right now … a TF-to-gene network for each sample” 上（兩契約 6/6 trials） | 確定性 witness：`patient_clustering_goal` 只排除 historical，未排除 hypothetical | **已修**：與 `input_mentions` 相同的 `_UNCERTAIN` 規則；`_UNCERTAIN` 加入 `也許／或許`（`might` 的直接對應；刻意不加 `可能`）。未經 live 驗證 |
| F5 | Legacy `mirna-chinese` 修正後三次都把「每位病患」讀成 `sample` entity，使完整請求 unsupported | 確定性 normalization 缺口：`sample` 不是任何 regulator→target 網路的節點 | **已修**：`regulatory_network`／`signed_regulatory_effect_network` 移除 `sample` entity（`regulatory_network_and_tf_activity` 的 TF×sample 矩陣除外）。離線重放三次皆變為 exact LIONESS-PUMA；未經 live 驗證 |
| N2 | Claims 把 TF 請求判成 `regulatory_network_and_tf_activity`（`artifact_granularity` 14 次） | 模型 artifact 分類 | 未修；不以 prompt 措辭處理 |
| N3 | 「同時包含 miRNA 與 TF 調控」被判成 `multi_omic_network`（兩契約；`role-both-*` 兩契約皆 0/3） | 模型 artifact 分類 | 未修 |
| N4 | Claims 對 SAMBAR 歷史題把 `artifact_type` 寫成輸入的 `mutation_matrix`；reviewer 三次原樣重寫 | Claims reviewer 只收到 issue 代碼；legacy 會收到結構化 `repair_feedback`（actual／expected 欄位約束）並 3/3 修好 | 未修；建議下一步（診斷資料的契約形狀，不是措辭） |
| N5 | Claims 的 unmatched evidence 集中在 `operation`（21/41） | Guidance matching 本來就把 `operation` 抹成 unknown，但 `operation` 的引文錯誤仍會讓整個 interpretation 被拒 | 未修；是否讓 guidance 模式的 operation 引文錯誤降為非致命，屬於驗證政策決定，需另行決定 |

### 19.11 對待辦 1–6 的結論

1. **Claims unmatched evidence 與 reviewer 修補失敗：** 根因已由 raw trial 重放確定（19.5、19.6）。Reviewer 失敗主要是 repair 契約形狀（F4 修正後 S1/S2 歸零，8-case reviewer validation 0/11 → 4/5）；unmatched evidence 主要是模型的引用壓縮／捏造，claims 仍明顯多於 legacy（32-case：41 vs 3），尚未解決。
2. **Aggregate vs sample-specific：** 根因是確定性 matcher（19.3），F1 修正；原 8-case 的兩個 aggregate prompt 兩契約皆 0/3 → 3/3。
3. **中文 routing/grounding：** 中文 aggregate 已修（F1＋F2）；中文 sample-specific 的 witness 升級（F3）與 `sample` 節點（F5）已修，但 `mirna-chinese` live 仍為 legacy 0/3、claims 1/3（legacy 的失敗形狀已由 F5 離線修正，尚待 live 確認；claims 仍受 `operation` 中文壓縮引用影響）。32-case 中文家族：legacy 21/24、claims 20/24。
4. **History/current 與 role/entity：** 已加入配對與反例測試（新測試檔共 41 個）；語料擴充另外找到並修正 N1。Role/entity 家族是 claims 相對 legacy 最弱的一族（8/24 vs 14/24），主因是 N2/N3 的 artifact 分類，而不是 role→entity 補齊規則。
5. **擴充語料與 paired A/B：** 已建立 32 個不同 prompt、四家族各 8 題並完成 paired A/B（19.9）。仍屬工程診斷：只有一輪、repeat 為同題穩定性，不是獨立樣本。
6. **Claims 是否升為 default：** **不升。** 在較大的 32-case 上 claims 明顯低於 legacy（56/96 vs 69/96；配對 6 勝 9 負 17 平；reviewer validation 50.8% vs 75.8%；unmatched evidence 41 vs 3）。

### 19.12 保存的資料與重現

- Traced reports（每個 trial 含 provider I/O 與 routing events；system prompt 以 SHA-256 取代以縮小檔案，內容可由程式與 `prompt_schema_sha256` 重建）：
  - `docs/research-log/live-semantic-trace-2026-09-23-prefix-orig8-{legacy,claims}.json`（修正前）
  - `docs/research-log/live-semantic-trace-2026-09-23-postfix-orig8-{legacy,claims}.json`
  - `docs/research-log/live-semantic-trace-2026-09-23-postfix-families32-{legacy,claims}.json`（已套用 19.9 的語料更正，metadata 註明）
- 擷取 harness：`docs/research-log/live-semantic-trace-2026-09-23-harness.py`（只檢查 `OPENROUTER_API_KEY` 是否存在，不讀取、不輸出其值）。
- 建議下一輪的最小變因順序：先 live 確認 F5／N1（原 8-case＋32-case，與一個 same-code replicate 交錯）；再處理 N4（claims reviewer 取得與 legacy 相同的結構化 repair feedback）；N5 需先做政策決定。

---

## 20. F5／N1 的 live 驗證（第三輪）

### 20.1 事前宣告（執行前寫下）

程式狀態：§19 的 F1–F5 與 N1 全部在內；與 §19.9 那兩輪相比，只多了 F5 與 N1。語料、模型、policy、repeat 都相同（原 8-case＋32-case、`gpt-4o-mini`、`when_needed`、repeat=3、兩契約同時段）。

- **V1（N1）**：`hist-hypothetical-control-en` 帶有 `terminal_goal_conflict:sample_cluster_assignment` issue 的 trial 數必須為 0（§19.9 為兩契約 6/6）。若 > 0，N1 視為無效。
- **V2（N1 不誤殺）**：真正要分群的題目（`hist-expression-then-mutation-en/zh`）第一次 interpretation 若 `artifact_type ≠ sample_cluster_assignment`，仍必須收到 `terminal_goal_conflict`；此類 trial 中沒收到的數必須為 0。
- **V3（F5）**：最終被接受的 outcome 中，`artifact_type ∈ {regulatory_network, signed_regulatory_effect_network}` 且 `entity_types` 含 `sample` 的 trial 數必須為 0。同時報告 F5 實際觸發的 trial 數（`source=artifact_ontology`、`value=sample` 的 restoration）；若觸發數為 0，V3 只是空成立，不能宣稱 F5 在 live 有效。
- **V4（F5 不誤殺）**：`artifact_type = regulatory_network_and_tf_activity` 的最終 outcome 中，`sample` 被移除的次數必須為 0。
- **計分**：與 §19.9 比較時，差距 ≤ 3 不作結論；本輪與 §19.9 為連續兩輪、非交錯重複。依使用者指示（實際操作以英文為主），中文結果另列、不作為主要判讀依據。

### 20.2 結果

| 判準 | 結果 | 對照（§19.9） |
| --- | --- | --- |
| **V1**（N1）`hist-hypothetical-control-en` 帶 `terminal_goal_conflict` 的 trial | legacy 0/3、claims 0/3 → **成立** | 3/3、3/3 |
| **V2**（N1 不誤殺）真正分群題中 artifact 寫錯卻沒被標記 | 0/3（claims 3 次寫錯、全部被標記；legacy 本輪沒有寫錯）→ **成立** | 0/5 |
| **V3**（F5）最終 regulator→target outcome 殘留 `sample` | 0 → 成立，但**幾乎是空成立**：F5 全輪只觸發 **1 次**（claims `role-mirna-ss-en` t3，英文）；該次確實移除 `sample`，但 trial 仍因 `registry_guidance_fallback` 失敗 | claims 殘留 2 |
| **V4**（F5 不誤殺）TF-activity artifact 被移除 `sample` | 0 → 成立 | — |

- **N1：live 確認有效。** `hist-hypothetical-control-en` 兩契約都由 0/3 → 3/3，且結構計數與機制一致（衝突 issue 歸零、真正的分群題仍被標記）。
- **F5：live 證據不足，不能宣稱有效。** 本輪模型幾乎沒有再把 `sample` 寫成網路節點；legacy `mirna-chinese` 從 0/3 變 3/3，但該題 F5 **一次都沒觸發**，所以這個提升是模型取樣差異，不是 F5 的效果。F5 目前只有離線重放證據與單次 live 觸發（行為正確）。
- 這也再次顯示同一 prompt 在連續兩輪之間可從 0/3 擺到 3/3，§19 與本節的分數差都應以此理解。

整體分數（與 §19.9 相比，只多 F5＋N1）：

| 語料 | Legacy | Claims |
| --- | ---: | ---: |
| 原 8-case | 20/24 → 22/24 | 21/24 → 21/24 |
| 32-case 合計 | 69/96 → 74/96 | 56/96 → 62/96 |
| 32-case 英文題（66 trials） | 42 → 46 | 33 → 41 |
| 32-case 非英文題（30 trials） | 27 → 28 | 23 → 21 |

- 可歸因於 N1 的只有 `hist-hypothetical-control-en` 的 +3／+3；其餘變動雙向都有（例如 claims `hist-ss-then-agg-en` 3→2、`role-target-first-en` 兩契約都 3→2），不歸因於本輪修正。
- 32-case 配對：claims 較好 4 題、較差 10 題、相同 18 題；reviewer validation legacy 51/60（85%）、claims 33/58（56.9%）；unmatched evidence legacy 5、claims 67。**Claims 仍不升為 default。**
- 依使用者指示（實際以英文操作），後續優先順序改以英文失敗為主；中文題保留在語料中作為回歸防護、另列報告。

Traced reports：`docs/research-log/live-semantic-trace-2026-09-23-round3-{orig8,families32}-{legacy,claims}.json`。

---

## 21. Claims reviewer 的結構化 repair feedback（F6）

### 21.1 動機（來自 §19–20 的 traced rounds）

兩輪 32-case 中，claims reviewer 對**只有引文錯誤**的 rejection 修得很好（36/36 通過驗證），但對**本體衝突類**（`terminal_goal_conflict`、`artifact_granularity/entity/roles`、`conflicting_evidence`、input 範圍）只有 4/27 與 5/27 通過。Legacy reviewer 會收到 `repair_feedback`（被拒欄位應取的值、artifact 允許值、witness 找到的 span），claims 只收到 issue 代碼；例：SAMBAR 歷史題 claims reviewer 三次原樣回傳 `artifact_type = mutation_matrix`。

### 21.2 修改（`interpretation/claim_prompt.py`，只影響 claims 的 repair 呼叫）

- 新增 `claim_repair_feedback`：只對本體衝突類 issue 產生結構化資料，放進既有的 diagnostics 資料訊息（`repair_feedback`、`request_facts`）。
- 每個項目只含：issue 代碼、`hypothesis_index`、該規則宣告的可修欄位（`Issue.fields`）、`terminal_goal_conflict` 的目標值、目標 artifact 的本體欄位約束、input 的增刪目標、evidence pair 與 validator 實際判定（restoration 之後）的欄位值。
- `request_facts`：deterministic witness 在請求中找到的輸入（含時間範圍）、粒度、角色，全部是原文逐字 span。用途是讓本體衝突可以判斷該改欄位還是改 artifact，而不是為了滿足約束去改寫請求明說的值。
- **刻意不移植** legacy 的散文 `instruction` 字串（屬於以措辭誘導行為，本專案禁止）；**system prompt 沒有任何修改**。
- 只有引文錯誤的 rejection 送出的訊息與修改前**完全相同**。
- 沒有同時擴充 witness（例如 "separately in each patient"），以免與本變因混在一起；代價是部分題目的 `request_facts` 是空的。

### 21.3 事前宣告（執行前寫下）

同 §20 設定（原 8-case＋32-case、`gpt-4o-mini`、`when_needed`、repeat=3、兩契約同時段）。Legacy 程式自 §20 起沒有變動，因此本輪 legacy 即為 **same-code 對照**，其分數變動用來估計本輪漂移。

- **R1（主要）**：32-case 中本體衝突類的 claims review 通過驗證數。基準 4/27、5/27；預測 **≥ 12**（高於較高基準的兩倍）。若 ≤ 7，視為 F6 無效果。
- **R2（不回歸）**：只有引文錯誤的 claims review 通過率必須 ≥ 95%（基準 36/36；此類訊息未變，任何差異都來自取樣）。
- **R3（安全防護）**：claims 錯誤 exact 路由（exact 但 action 與期望不同）必須 ≤ 2（基準 0、1）。若 ≥ 3，視為 feedback 把 reviewer 推向錯誤工具，F6 需撤回或修改後才能保留。
- **R4（N4）**：SAMBAR 歷史題（`hist-expression-then-mutation-en/zh`）中收到 `terminal_goal_conflict` 的 claims trial，最終 `artifact_type = sample_cluster_assignment` 的比例；預測 ≥ 1/2（基準 0）。
- **R5**：S1（重複 index）與 S2（1,200 token 截斷）仍為 0。
- **計分**：claims 分數變動若不大於 legacy 同輪的變動幅度，不作結論。

### 21.4 結果

| 判準 | 結果 | 基準 |
| --- | --- | --- |
| **R1** 本體衝突類 claims review 通過驗證 | **13/25** → 依事前寫法成立（≥ 12） | 4/27、5/27 |
| 同類 review **真正正確**（事前未列為判準，事後補報） | **4/25**，沒有改善 | 2/27、4/27 |
| **R2** 只有引文錯誤的 review 通過率 | 22/22 → 成立 | 36/36 |
| **R3** 錯誤 exact 路由 | 0 → 成立 | 0、1 |
| 錯誤 **fallback** 推薦（事前未列為判準，事後補報） | **4**（DRAGON×3、未陳述粒度對照題→LIONESS-PUMA×1） | 1、0 |
| **R4** SAMBAR 歷史題 artifact 被修成 `sample_cluster_assignment` | **2/5** → 依事前寫法**不成立**（預測 ≥ 1/2） | 0/5、0/3 |
| **R5** 重複 index／1,200 token 截斷 | 0／0 → 成立 | — |

**通過驗證 ≠ 修對。** 9 個「通過驗證但不正確」的本體衝突 review 全部是從錯的一邊化解衝突，而且是削弱、不是更正：

- `gran-mirna-*-terse`（5 次）：保留 `multi_omic_network`、刪掉角色 evidence；其中 aggregate 三次 fallback 推薦 **DRAGON**（錯誤工具）。`request_facts` 裡有 `miRNA-gene` 角色 witness，reviewer 沒有據此改 artifact。
- `hist-expression-then-mutation-en`（2 次）：artifact 改成 `sample_cluster_assignment`（正確），但粒度寫 `unknown` 而非約束的 `aggregate`，結果是 fallback SAMBAR（工具對、狀態不是 exact）。
- `role-tf-ss-en`（2 次）：保留 TF-activity artifact、把粒度改成 `unknown`，結果 ambiguous GIRAFFE；這題的 witness 抓不到 "separately in each patient"，`request_facts` 是空的。

機制：`artifact_constraints` 的允許值都包含 `unknown`，reviewer 可以把被陳述的值降成 `unknown`，或刪掉 evidence，來滿足約束而不必改對 artifact。這正是 §21.2 預先擔心的方向；R3 只量 exact，沒有涵蓋「錯誤 fallback」，是判準設計的漏洞。

**分數**：legacy（程式未變的 same-code 對照）32-case 74→70、8-case 22→23；claims 32-case 62→66、8-case 21→20。Claims 的變動（+4）沒有超過 legacy 本輪的漂移（−4），**不作分數結論**。32-case 配對：claims 較好 7、較差 8、相同 17。Claims 仍不升為 default。

### 21.5 判讀與建議

- F6 依事前判準**沒有觸發撤回條件**（R1 ≤ 7 或 R3 ≥ 3），因此保留在工作樹中；但它的效果是「更多 review 通過驗證」，**不是**「更多 review 修對」，而且出現了新的錯誤 fallback。不應把 R1 的提升寫成 reviewer 能力改善。
- 建議的下一步（尚未實作，需決定）：以確定性規則拒絕「用降級化解本體衝突」的 review。當 review 把一個有 request witness 支持的維度（粒度、角色）改成 `unknown` 或刪掉其 evidence 時，丟棄該 review、保留第一次 interpretation 的失敗狀態。專案已有 `outcome_downgrade` 的比對機制可沿用。這是契約／驗證層的改動，不是措辭。
- 另外，錯誤 fallback 應列入往後所有 round 的安全計數（與錯誤 exact 並列）。

Traced reports：`docs/research-log/live-semantic-trace-2026-09-23-round4-{orig8,families32}-{legacy,claims}.json`。

---

## 22. 請求一致性規則（F7）與錯誤推薦計數

### 22.1 根因（由 §21 round 4 traces 與 legacy 錯誤 exact 追出）

- **DRAGON 錯誤推薦**：「miRNA-gene network」、「both miRNA and TF regulation of genes」被判成 `multi_omic_network`。Restoration 依本體清掉角色，review 再刪掉衝突 evidence，於是驗證通過並推薦 DRAGON：claims 為 fallback，legacy 為 **exact**（round 3、4 各 2 次錯誤 exact 之中的一類）。
- **F1 引入的回歸**：`gran-mirna-unstated-control`（請求明說尚未決定粒度）被模型選成 aggregate，F1 之後會變成 exact PUMA（legacy round 3 兩次）。F1 之前是 PUMA/LIONESS-PUMA 打平，所以碰巧會回問。
- 錯誤 fallback 過去沒有被計數，所以 §21 的 R3 只看 exact，漏掉了 DRAGON。

### 22.2 修改

| 代號 | 規則 | 位置 |
| --- | --- | --- |
| F7a | 請求有目前、非否定的 regulator→target 片語，而 outcome 選了無角色的網路（`coexpression_network`、`multi_omic_network`）→ `stated_roles_conflict`（可修欄位：`artifact_type`）。`community_assignment` 等不同產出不在內（`bipartite-communities` 的 TF-to-gene 屬合法用法）。 | `interpretation/request_integrity.py` |
| F7b | 同一句同時提到兩種粒度並帶有「尚未決定」標記，而**所有** hypothesis 都選了同一個具體粒度 → `undecided_granularity`（可修欄位：`granularity`）。在 interpretation 層級判斷：`[unknown, sample_specific]` 這種保留不確定性的回答不受影響。 | `interpretation/outcome_validation.py` |
| — | Claims 結構化 feedback 認得上述兩個 issue；`undecided_granularity` 的目標值為 `unknown`。 | `interpretation/claim_prompt.py` |
| — | Evaluator 每個 trial 記錄 `wrong_recommendation`（exact／fallback／None），summary 新增 `wrong_exact_recommendations`、`wrong_fallback_recommendations`。 | `scripts/evaluate_routing.py` |

**離線驗證：**
- 對所有已記錄的最終 outcome 重放（14 份 trace）：F7a 會攔下 6 個、F7b 會攔下 3 個，**全部是原本失敗的 trial**；原本通過的 0 個受影響。
- 第一版 F7b 是逐 hypothesis 判斷，重放發現會誤拒 5 個原本通過的 trial（模型以 `[unknown, sample_specific]` 表達未決定），已改為 interpretation 層級。
- 語料稽核：`granularity_left_open` 在三份語料中只對 `missing-granularity` 與 `gran-mirna-unstated-control` 成立，兩者期望皆為 ambiguous。
- Pytest 2,085 passed、35 skipped。

### 22.3 事前宣告（執行前寫下）

設定同 §21（原 8-case＋32-case、`gpt-4o-mini`、`when_needed`、repeat=3、兩契約同時段）。F7 改的是兩契約共用的驗證層，**本輪沒有 same-code 對照**，分數變動不作結論，只看下列計數。

- **W1（主要）**：錯誤推薦（exact＋fallback，兩份語料合計）。基準 round 4：legacy 2＋0、claims 0＋4。預測 legacy ≤ 1、claims ≤ 1。若任一契約不低於其基準，F7 視為無效。
- **W2（安全）**：錯誤 **exact** 推薦兩契約合計 ≤ 1。
- **W3**：`gran-mirna-unstated-control` 產生任何推薦（exact 或 fallback）的 trial 數 = 0（基準：legacy round 3 為 2、claims round 4 為 1）。
- **W4（誤殺）**：`stated_roles_conflict` 出現在期望 artifact 不是調控網路的 prompt 上的次數 = 0。

### 22.4 Round 5 結果（F7a／F7b）

| 判準 | Legacy | Claims | 基準（round 4） |
| --- | --- | --- | --- |
| **W1** 錯誤推薦（exact＋fallback） | 2＋0 → **不成立**（未低於基準） | **0＋0** → 成立 | legacy 2＋0、claims 0＋4 |
| **W2** 錯誤 exact 合計 ≤ 1 | 2 → **不成立** | | |
| **W3** 未決定粒度對照題產生推薦 | 0 | 0 | legacy 2（round 3）、claims 1 |
| **W4** `stated_roles_conflict` 誤殺 | 0 | 0（觸發 6 次） | — |

- **Legacy 的 2 次錯誤 exact 都不是 F7 誤判，而是覆蓋缺口：** F7 在 legacy 整輪一次都沒觸發。
  - `role-both-agg-en`："both miRNA and TF **regulation of** genes" 這種名詞化說法，角色 witness 抓不到（round 4、5 共 3 次 exact DRAGON）。
  - `zh-both-regulators-agg`：選了 TF-activity artifact，它屬於調控類但本體不允許 miRNA；restoration 想補請求陳述的 miRNA 角色時因本體衝突被拒，角色就無聲消失，結果 exact GIRAFFE。
- **分數**：legacy 原 8-case 23→18、32-case 70→75；claims 8-case 20→21、32-case 66→67。Legacy 8-case 的下降中**沒有任何 F7 issue**（失敗是 `conflicting_evidence`、`missing_evidence` 與 review 失敗），legacy 8-case 各輪依序為 20、22、23、18，屬漂移，不歸因於 F7。

### 22.5 F7c：補上兩個覆蓋缺口

- 角色 witness 加入名詞化構句 “X regulation of genes”（`request_integrity._REGULATORY_ROLE_PAIR`）。以**不在任何語料中**的句子驗證：兩個正例抓到；"gene regulation of metabolism"、"TF regulation of pathways"、否定句都不觸發。
- `stated_roles_conflict` 擴及「調控類 artifact 的本體排除了請求陳述的 regulator」：`regulatory_network_and_tf_activity`、`signed_regulatory_effect_network` 不含 miRNA。
- 重放 19 份 trace 的最終 outcome：攔下 10 個，其中 8 個是錯誤推薦，**原本通過的 0 個**。
- Pytest 2,094 passed。

### 22.6 Round 6 事前宣告（執行前寫下）

設定同 §22.3。

- **V1**：錯誤 exact 兩契約合計 ≤ 1（round 5：legacy 2、claims 0）。
- **V2**：錯誤推薦（exact＋fallback）每個契約 ≤ 1。
- **V3**：`role-both-agg-en` 與 `zh-both-regulators-agg` 的錯誤推薦 = 0（round 5：legacy 各 1）。
- **V4**：`stated_roles_conflict` 誤殺 = 0；未決定粒度對照題產生推薦 = 0。
- 若 V1 或 V4 不成立，先查原因再決定是否保留 F7c。

### 22.7 Round 6 結果（F7c）

| 判準 | Legacy | Claims | 結論 |
| --- | --- | --- | --- |
| **V1** 錯誤 exact 合計 ≤ 1 | 0 | 0 | 成立（round 5 為 2） |
| **V2** 錯誤推薦每契約 ≤ 1 | 0 | 0 | 成立 |
| **V3** `role-both-agg-en`、`zh-both-regulators-agg` 錯誤推薦 | 0 | 0 | 成立 |
| **V4** `stated_roles_conflict` 誤殺；對照題推薦 | 0；0 | 0；0 | 成立 |

- 本 session 首次在兩契約、兩份語料上同時達到**錯誤推薦 = 0**（round 4：legacy 2、claims 4；round 5：legacy 2、claims 0）。`stated_roles_conflict` 觸發 legacy 6 次、claims 14 次，`undecided_granularity` 觸發 legacy 2 次。
- 但 F7 的作用是把**錯誤推薦變成拒絕／不推薦**，不是把它們修對：`role-both-agg-en`、`role-both-ss-en` 兩契約仍為 0/3。
- 分數：legacy 8-case 18→22、32-case 75→75；claims 8-case 21→20、32-case 67→**59**。Claims 下降的 7 題中，失敗 trial **沒有任何 F7 issue**；F7 觸發都落在原本就失敗的題目上，因此歸為 claims 自身的取樣波動（約 ±4 的 same-code 漂移之外，claims 本身跨輪變動也大），不歸因於 F7c。
- Traced reports：`docs/research-log/live-semantic-trace-2026-09-23-round{5,6}-{orig8,families32}-{legacy,claims}.json`。
