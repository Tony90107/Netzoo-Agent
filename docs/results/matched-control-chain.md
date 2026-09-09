# Matched-control 機制鏈：可放進論文的兩項

> 對象：NetZoo agent 語意路由的**修復階段**（第二次 LLM 呼叫）。
> 本檔只收兩件事：**(1) 機制鏈及其歸因依據**、**(2) 這個設計能否證**。
> 完整的十項發現在 [`quantified-findings.md`](quantified-findings.md)；
> 每一步的事前判準在 [`../research-log/sambar-agent-routing.md`](../research-log/sambar-agent-routing.md)
> Log 111–120。
>
> 資料日期：2026-09-09。模型：`gpt-4o-mini`（temperature 0，經 OpenRouter）。
> 語料 `tests/routing_scenarios.json`（27 題，`corpus_sha256=a43c2baec7…`）。
>
> **⚠ 本檔曾經以一組 Fisher p 值為主結果。那些 p 值已於 Log 120 全部撤回。**
> **撤回的理由、以及撤回這件事本身，都寫在下面——第 3 節就是為它而寫的。**

---

## 0. 一段話

固定 LLM 的第一次呼叫、只變動程式碼的 matched-control 設計下，
修復階段的正確率從 **2/36** 提升到 **35/36**，同碼替身另量到 **24/36**。
差距（22–33）遠大於實測的同碼差距（11），
**所以「大幅改善」成立，但逐步的分數歸因與所有 p 值不成立、已撤回。**
三個機制步驟的歸因改為完全建立在**結構性計數器**上——那是程式碼的確定後果，
不受抽樣影響。同一設計在六次量測中**三次產出否定結果**，
其中一次推翻的是本研究自己的主結果。

---

## 1. 設計，以及它實際的解析度

### 1.1 為什麼要 matched control

全語料 live 輪次無法分辨小效果：同一份程式碼、同語料、同參數，連跑多輪，
`passed` 波動 **±3**、accepted **±4**、tool-correct **±1**，
27 題中有 **6 題**在兩輪之間翻面（Log 98，n = 81）。

**設計**：把第一次 LLM 呼叫的輸出**固定成一個離線建構的解讀**，
使其唯一缺陷屬於待測類別，然後只變動程式碼，量第二次呼叫的修復是否正確。
第一次呼叫的變異因此被移除；剩下的變異只來自審查層那一次呼叫。

**對象類別**：第一次解讀把角色（regulator／target／entity）寫進 outcome，
卻沒有對應的證據條目。這在拼字問題修好之後是最大的損失來源——
`missing_evidence` 有 **126/165（76%）** 屬角色維度，而角色正是把預期能力
和它的相容鄰居分開的那個維度。四題的判別維度皆為角色。

**規模**：4 題 × 3 repeat = 12 trial／輪，3 輪 = **n = 36**。

### 1.2 實際的解析度（Log 120，推翻了本檔前一版的說法）

| 配置 | 時間 | 逐輪 | 合計 |
| --- | --- | --- | --- |
| 現行碼 | 01:57 | 12, 11, 12 | 35/36 |
| 抽掉②（ablation） | 10:24 | 9, 12, 8 | 29/36 |
| 抽掉②（ablation） | 11:02 | 6, 7, 6 | 19/36 |
| 現行碼 | 11:03 | 7, 8, 9 | **24/36** |

兩對都離線核對過是**同一份 runtime**（現行碼那一對：`f7400ef..HEAD` 排除
`docs/` 與 `tests/` 後零檔案；ablated 那一對：同一個 `git revert 2e03a24`，
其間 `router_invocation.py` 零差異）。

**同碼差距：現行 11、ablated 10。輪內離散只有 1／4／1／2。**

> **輪內小、量測間大**，代表**背靠背連續跑的三輪不是獨立樣本**：
> 它們共用一個隨時間漂移的 provider 狀態。
> 把三輪當成 n = 36 的獨立試驗會高估有效樣本數，
> **因此本設計先前報出的每一個 Fisher p 值在統計上無效。**

同碼差距的相對尺度：全語料 ±3～4／81 ≈ **5%**；matched control 10–11／36 ≈ **30%**。
**「matched control 解析度更高」是錯的，撤回。**
它真正買到的不是解析度，而是**把第一次呼叫的變異移走，使結構性計數器乾淨可讀**。

### 1.3 因此，可用的作法

1. 分數只用來排除「差距小於同碼差距」的假象；
2. **逐步歸因一律以結構性計數器為準**；
3. 若真要主張 p 值，同碼替身必須與候選在**時間上交錯**，不是各跑一批。

---

## 2. 第一項：機制鏈，以結構性計數器歸因

「結構性計數器」＝程式碼的確定後果（該類別在該版程式下**不可能發生**），
對比「分數型指標」＝受抽樣支配。**歸因靠前者。**

| 步驟 | 機制（一句話） | 結構性計數器 | 合計分數 |
| --- | --- | --- | --- |
| 原始 | — | — | 2/36 |
| ① | `missing_evidence` 說的是「這個值沒有引用」，不是「這個值錯了」；<br>issue 全屬該碼時，patch 只套用證據增刪，不套用 outcome 覆寫 | `role_entity` **38 → 0**<br>`missing_evidence:entity_type=sample` **26 → 0** | 22/36 |
| ② | 一條指名不存在維度的移除、或根／巢狀兩份互相矛盾的清單，<br>**不可能產生任何效果**；不該為它丟掉整份格式正確的修復 | `removal_dim` **10 → 0**<br>`list_conflict` **6 → 0**<br>ablation 重跑再現：**17 個 trial → 0** | 25/36 |
| ③ | ①的路徑上 outcome 不變，**故沒有任何證據會變成過時的**；<br>該路徑的移除只能撤回一個 outcome 仍在主張的值 | 「移除項與抱怨項重疊」**8 → 0**<br>attempt-2 `missing_evidence` **36 → 0** | 35/36（同碼替身 24/36） |

### 2.1 分數能支持什麼、不能支持什麼

- **能**：原始 2/36 對現行的兩次量測 {35, 24}，差 **33** 與 **22**，
  遠大於同碼差距 **11**。**「這三步合起來大幅改善了修復階段」成立。**
- **不能**：逐步歸因。①的 Δ20 只比同碼差距大 9，②的 Δ3 與③的 Δ10 都在其內。
  **不得說「①值 20 分、③值 10 分」。**
- **不能**：任何 p 值（§1.2）。

### 2.2 ③ 的成因是實測，不是推論

② 的副作用是讓失敗**可診斷**。逐試驗比對 11 次殘留失敗，**8 次**是 patch
移除了 attempt 2 隨後抱怨缺少的那幾條證據——`('operation','infer')` 與
`('artifact_type','regulatory_network')` 各 8 次，典型形狀是「移除 6 條、新增 2 條」。
③ 是從這裡查出來的。**這個 8/11 是逐試驗的比對計數，不是分數指標。**

### 2.3 ② 的 leave-one-out 對照：結構性成立，分數不成立

抽掉②（`git revert`，只動 `router_invocation.py`）跑了兩次，
第一次因我自己的閘門寫錯而作廢（§3.2），第二次閘門換成結構性後通過。

- **結構性（成立）**：`schema_validation` 家族在現行碼下**恆為 0 個 trial**
  （四次量測皆然），因為那兩種形狀在驗證前就被挑掉——這是程式保證。
  抽掉②後回到 **4** 與 **17** 個 trial，且**全部**屬②宣告處理的形狀，沒有第三種。
  離線決定性測試 7 項在現行碼全過、在 ablated 碼全敗。
- **分數（不成立）**：時間最相鄰的一對——ablated 19（11:02）對現行 24（11:03）
  ——只差 5，單尾 p = 0.17。

**② 的地位不變：只以「不該為一個必然無效的指令丟掉整份格式正確的修復」的
正當性保留，不主張改善修復率。**

### 2.4 必須一併陳述的限度

- **模型行為沒有改變。** 候選組的 patch **仍有 18/25 動了 ≥9 個 outcome 欄位**。
  效果全部來自**套用階段的限制**，不是模型端的改善。
- **未使用 prompt 措辭。** 三步都是程式碼層的合併規則。
- **35/36 的那 1 次殘留是契約在正常工作**：審查層為 `target_type=gene` 補了一條
  **explicit** 證據，而該請求（`…mi-rna regualtor network, what toosl do i need?`）
  從未提到 gene。**不應該去修它。**
- **這是修復階段的內部指標**，不是端到端路由正確率。

### 2.5 論文可直接使用的句子

> Fixing the first LLM call and varying only the merge rules, the repair stage
> went from 2/36 to 35/36; a same-code replicate of the final state returned
> 24/36. Against a measured same-code span of 11, a gap of 22–33 supports the
> direction and order of magnitude of the improvement but not a step-by-step
> attribution, and every Fisher p value this design reported has been withdrawn:
> three consecutive rounds share a drifting provider state and are not
> independent samples, so n = 36 overstates the effective sample size.
> Attribution therefore rests on structural counters — for each step, the
> rejection class it targets becomes unreachable by construction (`role_entity`
> 38 → 0; the two malformed-removal shapes 10 → 0 and 6 → 0, reproduced as
> 17 trials → 0 under ablation; withdrawal/complaint overlap 8 → 0) — none of
> which is a sampled quantity. The model's output did not change: 18 of 25
> candidate patches still rewrite nine or more outcome fields.

---

## 3. 第二項：這個設計能否證

一個只會產出好消息的評估設計沒有證據力。本設計在六次量測中**三次擋下了作者**。

### 3.1 否證一：介入未達自己的事前門檻（步驟②，Log 113／114）

② 精準達成了它宣告的機制目標（`removal_dim` 10→0、`list_conflict` 6→0），卻同時：

- **未達統計門檻**：25/36，p = 0.31，門檻 30/36；且
- **違反了事前寫下的 Z3「不得換位置」判準**：11 次失敗只有 3 次真的修好，
  其餘 8 次把失敗從**線路層**搬到**語意層**
  （attempt 2 出現基線沒有的 `missing_evidence` **36 次**）。

**處置**：保留，但只以正當性保留，不主張它改善修復率。事後不得美化成「它也有效」。

### 3.2 否證二：有效性閘門判掉一輪對作者有利的數據（Log 116／117）

leave-one-out 輪次算出 **29/36**，單尾 p = 0.0276，**符合我事前寫下的預測**。
但同時宣告的有效性閘門 M1（線路層形狀須回來合計 ≥ 8）**實測 7**。
**依事前規則，該輪作廢，p 值不得引用。**

**M1 本身是設計錯誤，這才是那一輪的產出**：它把硬性下限架在一個**分數型**計數上，
而下限（8）來自單次觀測、無凍結基線。
> **補上的規則：有效性檢查只能架在結構性計數器上
> （例如「該家族在現行程式碼下恆為 0」），不得對受抽樣影響的計數設下限。**

換成結構性閘門重跑（Log 118／119），得 19/36，W1 的算術成立——
但緊接著的 §3.3 把它的 p 值也一併帶走。

### 3.3 否證三：同碼替身推翻了本研究自己的主結果（Log 119／120）

因為兩次 ablated 量測（29 與 19）在**已離線確認 runtime 完全相同**的情況下差了 10，
我事前宣告了一輪現行碼的同碼替身，並寫下撤回分支：

| 判準（事前） | 內容 |
| --- | --- |
| **R0** 結構性閘門 | 現行碼 `schema_validation` 家族須為 0 個 trial |
| **R1** 穩定 | ≥ 32/36 → 主結果保留 |
| **R2** 不穩定 | ≤ 28/36 → **③ 的 p = 0.0015 與累計 5.3×10⁻¹⁷ 撤回** |
| **R3** 不可評 | 29–31/36 |
| 事前預測 | 我預測 R1 |

**結果：24/36（逐輪 7／8／9）。R0 通過，R2 觸發，我的預測是錯的。**
依事前規定，**③ 的 p、累計 p、①的 p、W1 的 p、以及更早 1c 的 p 全部撤回**，
「n = 36 分得出 3／分得出 10」兩句撤回，
「matched control 解析度優於全語料」撤回，
「現行碼對 provider 擺盪結構性免疫」這個假說也被推翻（現行臂擺盪 11）。

**前兩次否證擋下的是一個介入和一輪數據；這一次擋下的是主結果。**

### 3.4 論文可直接使用的句子

> The design is capable of returning negative results and did so three times,
> the last of them against the study's own headline. One intervention met its
> mechanistic target exactly yet missed its pre-registered threshold (25/36,
> p = 0.31 against 30/36) and violated a pre-registered criterion forbidding
> failures from merely relocating; it is retained on a proportionality argument
> and explicitly not claimed as an improvement. A leave-one-out round produced a
> score supporting the author's written prediction (29/36) but was voided by its
> own pre-declared validity gate — whose post-mortem showed the gate had been
> badly typed, placing a hard floor on a sampling-dependent count. Finally, a
> pre-declared same-code replicate of the final configuration returned 24/36
> against a recorded 35/36, triggering the withdrawal branch written before the
> round ran: three consecutive rounds are not independent samples, and every
> Fisher p value this design had reported was withdrawn. What survived is
> exactly what the study had already argued should be relied on — the structural
> counters.

---

## 4. 不能主張的（本檔範圍內）

1. **不能**引用本設計報出的任何 Fisher p 值。全部撤回（Log 120）。
2. **不能**做逐步的分數歸因（「①值 20 分、③值 10 分」）。
3. **不能**說 ② 改善了修復率（p = 0.31，違反 Z3，且時間相鄰對只差 5）。
4. **不能**把 35/36 當成端到端路由正確率——它是修復階段的內部指標，
   而且同碼替身另量到 24/36。
5. **不能**說模型變好了——模型行為沒變，變的是套用規則。
6. **不能**說 matched control 解析度優於全語料——相對尺度上更差。

**可以主張的只有兩件事**：
(a) 三步合起來使修復階段大幅改善（Δ22–33 對同碼差距 11）；
(b) 每一步的機制以結構性計數器歸零為據，且該歸零是程式的確定後果。

---

## 5. 可重現指令

```bash
# matched-control replay（會付費，約 24 次呼叫／輪；跑 3 輪 = n 36）
set -a && . ./.env && set +a && ~/.venvs/netzoo-qa/bin/python \
  scripts/evaluate_routing.py --live --repair-replay \
  --repair-replay-suite role-evidence --repeat 3 --max-calls 24 --json \
  | tee docs/research-log/replay-roundN.json

# leave-one-out（抽掉②）
git worktree add --detach /tmp/ablate HEAD
cd /tmp/ablate && git revert --no-commit 2e03a24   # 只動 router_invocation.py
git checkout HEAD -- tests/test_unhonourable_removals_do_not_cost_the_repair.py
#  ...再跑同一條 replay 指令三次

# 結構性閘門（決定性、不花錢）：現行碼全過、ablated 碼全敗
~/.venvs/netzoo-qa/bin/python -m pytest -q \
  tests/test_citation_only_repair_keeps_the_outcome.py \
  tests/test_unhonourable_removals_do_not_cost_the_repair.py
```

存檔：`docs/research-log/replay-role-evidence-*.json`
（`nowithdraw-*` = 現行碼 35/36；`samecode-current-*` = 現行碼 24/36；
`ablate-step2-*` = 29/36；`ablate-step2-rerun-*` = 19/36）。
