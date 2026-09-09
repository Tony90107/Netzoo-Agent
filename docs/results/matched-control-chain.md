# Matched-control 機制鏈：可放進論文的兩項

> 對象：NetZoo agent 語意路由的**修復階段**（第二次 LLM 呼叫）。
> 本檔只收兩件事：**(1) 主結果與其可分別歸因的機制**、**(2) 這個設計能否證**。
> 完整的十項發現在 [`quantified-findings.md`](quantified-findings.md)；
> 每一步的事前判準在 [`../research-log/sambar-agent-routing.md`](../research-log/sambar-agent-routing.md)
> Log 111–117。
>
> 資料日期：2026-09-09。模型：`gpt-4o-mini`。語料 `tests/routing_scenarios.json`
> （27 題，`corpus_sha256=a43c2baec7…`）。

---

## 0. 一段話

固定 LLM 的第一次呼叫、只變動程式碼的 matched-control 設計下，
修復階段的正確率從 **2/36 提升到 35/36**（單尾 Fisher exact **p = 5.3×10⁻¹⁷**），
分三個機制步驟達成，每一步都伴隨一個**結構性計數器歸零**作為歸因依據。
同一設計在四次量測中**兩次產出否定結果**——一次是介入未達自己的事前門檻，
一次是我自己的有效性判準把一輪對我有利的數據判為作廢。

---

## 1. 為什麼需要 matched-control

**問題**：全語料 live 輪次無法分辨小效果。同一份程式碼、同一語料、同一參數，
連跑多輪，`passed` 波動 **±3**、accepted **±4**、tool-correct **±1**，
27 題中有 **6 題**在兩輪之間翻面（Log 98）。
在 n = 81 的全語料上，任何 ≤3 的差異都在噪音裡。

**設計**：把第一次 LLM 呼叫的輸出**固定成一個離線建構的解讀**，
使其唯一缺陷屬於待測類別，然後只變動程式碼，量第二次呼叫的修復是否正確。
第一次呼叫的模型變異因此被完全移除；剩下的變異只來自審查層那一次呼叫。

**對象類別**：第一次解讀把角色（regulator／target／entity）寫進 outcome，
卻沒有對應的證據條目。這在拼字問題修好之後是最大的損失來源——
兩輪 162 次試驗中，`missing_evidence` 有 **126/165（76%）** 屬角色維度，
而角色正是把預期能力和它的相容鄰居分開的那個維度。
四題的判別維度皆為角色（兩題有輸入、兩題沒有）。

**規模**：4 題 × 3 repeat = 12 trial／輪，3 輪 = **n = 36**。

**解析度的實測**：本設計**五次**量測的逐輪離散為 **1／0／3／1／4**
（最後一個是 §3.2 的 leave-one-out 輪次，也是最大的一次）。
對照全語料輪次的 ±3～±4。

已達顯著的合計差異是 **20**（2→22）與 **10**（25→35）；
未達的是 **3**（22→25）；差 **6** 的那一次（35 對 29）被自己的閘門作廢。

> **固定第一次呼叫之後，n = 36 分得出 10 以上的差異、分不出 3；
> 6 這個量級目前沒有一次通過完整判準的量測。**
> 全語料輪次（n = 81）從未達到顯著。

---

## 2. 第一項強化：主結果與可分別歸因的機制鏈

### 2.1 結果

每一步的門檻都在跑該步之前、由凍結的基線與 Fisher exact 算出並寫死。

| 程式狀態 | 逐輪 | 合計 | 事前門檻 | 對前一步 | 對原始 |
| --- | --- | --- | --- | --- | --- |
| 原始 | 1, 1, 0 | **2 / 36** | — | — | — |
| ① citation-only 不改 outcome | 8, 7, 7 | **22 / 36** | — | p = 3.1×10⁻⁷ | p = 3.1×10⁻⁷ |
| ② 移除項指令正規化 | 8, 7, 10 | **25 / 36** | 30/36 | **p = 0.31（未達）** | — |
| ③ citation-only 忽略移除項 | 12, 11, 12 | **35 / 36** | 32/36 | p = 0.0015 | **p = 5.3×10⁻¹⁷** |

### 2.2 三個機制，以及各自的結構性計數器

「結構性計數器」＝程式碼的確定後果，不受抽樣噪音支配（相對於 pass rate 這類分數指標）。
**歸因靠的是這一欄，不是分數。**

| 步驟 | 機制（一句話） | 結構性計數器 |
| --- | --- | --- |
| ① | `missing_evidence` 說的是「這個值沒有引用」，不是「這個值錯了」；<br>因此當 issue 全屬該碼時，patch 只套用證據增刪，不套用 outcome 覆寫 | `role_entity` **38 → 0**<br>`missing_evidence:entity_type=sample` **26 → 0** |
| ② | 一條指名不存在維度的移除、或根／巢狀兩份互相矛盾的清單，<br>**不可能產生任何效果**；不該為它丟掉整份格式正確的修復 | `removal_dim` **10 → 0**<br>`list_conflict` **6 → 0** |
| ③ | ①的路徑上 outcome 不變，**故沒有任何證據會變成過時的**；<br>該路徑的移除只能撤回一個 outcome 仍在主張的值 | 「移除項與抱怨項重疊」**8 → 0**<br>attempt-2 `missing_evidence` **36 → 0** |

### 2.3 ③ 的成因是實測，不是推論

② 的副作用是讓失敗**可診斷**。逐試驗比對 11 次殘留失敗，
**8 次**是 patch 移除了 attempt 2 隨後抱怨缺少的那幾條證據
——`('operation','infer')` 與 `('artifact_type','regulatory_network')` 各 8 次，
典型形狀是「移除 6 條、新增 2 條」。③ 是從這裡查出來的，不是猜的。

### 2.4 必須一併陳述的限度

- **模型行為沒有改變。** 候選組的 patch **仍有 18/25 動了 ≥9 個 outcome 欄位**。
  效果全部來自**套用階段的限制**，不是模型端的改善。
- **未使用 prompt 措辭。** 三步都是程式碼層的合併規則。
  （本研究先前有六次以 prompt 措辭嘗試修復的失敗紀錄，已列為硬性禁止。）
- **唯一殘餘的 1/36 是契約在正常工作**：審查層為 `target_type=gene` 補了一條
  **explicit** 證據，而該請求（`…mi-rna regualtor network, what toosl do i need?`）
  從未提到 gene。`ungrounded_evidence` 是對的。**不應該去修它。**
- **這是修復階段的內部指標**，不是端到端路由正確率。
  這三步在真實請求上的合計效果尚未量測（需要同碼替身輪才能主張任何分數差異）。

### 2.5 論文可直接使用的句子

> Fixing the first LLM call and varying only the merge rules, the repair stage
> went from 2/36 to 35/36 (one-sided Fisher exact, p = 5.3×10⁻¹⁷) in three steps,
> each accompanied by a structural counter falling to zero: the rejection class
> the step targets becomes unreachable by construction, so attribution does not
> rest on the score alone. The model's output did not change — 18 of 25 candidate
> patches still rewrite nine or more outcome fields; what changed is that a
> request for a citation no longer licenses the reviewer to rewrite the value or
> to withdraw its support.

---

## 3. 第二項強化：這個設計能否證

一個只會產出好消息的評估設計沒有證據力。本設計在四次量測中**兩次擋下了我自己**。

### 3.1 否證一：介入未達自己的事前門檻（步驟 ②，Log 113／114）

② 精準達成了它宣告的機制目標（`removal_dim` 10→0、`list_conflict` 6→0），
卻同時：

- **未達統計門檻**：25/36，p = 0.31，門檻 30/36；且
- **違反了事前寫下的 Z3「不得換位置」判準**：11 次失敗只有 3 次真的修好，
  其餘 8 次把失敗從**線路層**搬到**語意層**
  （attempt 2 出現基線沒有的 `missing_evidence` **36 次**）。

**處置**：保留，但**只以「不該為一個必然無效的指令丟掉整份格式正確的修復」的
正當性保留，不主張它改善修復率。** 這一點事後不得美化成「它也有效」。

> **沒有這一步，「matched control 優於全語料分數」就只有正面案例支撐。**

### 3.2 否證二：有效性判準把一輪對我有利的數據判為作廢（Log 116／117）

因為 ② 是一個**放寬**（忽略模型給的指令），專案規則要求它配一個**負向對照**，
而它當時只有離線的範圍測試，沒有量測過的對照。同時，「三段可分別歸因」這件事
本身從未被測過——三步都只跟前一步比，沒有任何一步被單獨抽掉。

於是做 leave-one-out：`git revert` 掉 ②，得到 **①＋③**，其餘完全不變。
**事前**宣告（Log 116，跑之前寫入）：

| 判準 | 內容 |
| --- | --- |
| **W1** ②承重 | `abl ≤ 29/36`（單尾 Fisher p < 0.05） |
| **W2** ②多餘 | `abl ≥ 33/36` 且 p > 0.05 |
| **W3** 不可評 | 30–32/36 |
| **M1** 有效性閘門 | 兩種線路層形狀必須回來，合計 **≥ 8**；**不通過則本輪作廢** |
| 事前預測 | 我預測 W1 |

**結果：`abl = 29/36`（逐輪 9／12／8），p = 0.0276——W1 的算術達標。
但 M1 實測 7 < 8。依我自己寫下的規則，這一輪作廢，p = 0.0276 不得引用。**

**M1 本身才是這一輪真正的產出。** 它把硬性數字下限套在一個**受抽樣影響的計數**上，
而那個下限（8）來自單次觀測，沒有凍結基線。依本研究自己的分類，
`removal_dim` 出現幾次取決於審查層那一輪寫了什麼——它是**分數型**指標，
我卻拿它當硬閘門。
> **規則補充：有效性檢查只能架在結構性計數器上
> （例如「該家族在現行程式碼下恆為 0」），不得對分數型計數設下限。**

**不依賴 M1、因此仍成立的部分**（結構性）：`schema_validation` 這個 issue 家族
在現行程式碼下是 **0 個 trial**——那兩種形狀在驗證之前就被挑掉，不可能出現。
抽掉 ② 之後回到 **4 個 trial**，且 4 個**全部**是 ② 宣告要處理的兩種形狀，沒有第三種。
7 次失敗的組成：

| 類別 | 抽掉② | 現行 |
| --- | --- | --- |
| ②的線路層形狀 | 4 | 0 |
| 正確的拒絕（虛構 gene 引文） | 3 | 1 |

**這一輪不能主張**：不能說②承重（閘門未過），不能說②多餘（29 遠低於 33），
也不能把 29 與 35 相減當效果量——逐輪離散 **4** 是本設計最大的一次，
差距 6 只比它大 2。

### 3.3 論文可直接使用的句子

> The design is capable of returning negative results, and did so twice. One
> intervention met its mechanistic target exactly (two wire-level rejection
> shapes went to zero) yet missed its pre-registered statistical threshold
> (25/36, p = 0.31 against 30/36) and violated a pre-registered criterion
> forbidding failures from merely relocating; it is retained on a
> proportionality argument and is explicitly **not** claimed as an improvement
> to the repair rate. A later leave-one-out round produced a score that would
> have supported the author's written prediction (29/36, p = 0.0276), but was
> voided by its own pre-declared validity gate (7 observed against a required
> 8) — and the post-mortem showed the gate had been badly typed, placing a hard
> floor on a sampling-dependent count.

---

## 4. 不能主張的（本檔範圍內）

1. **不能**說 ② 改善了修復率（p = 0.31，且違反 Z3）。
2. **不能**引用 leave-one-out 的 p = 0.0276（M1 未過，該輪作廢）。
3. **不能**把 35/36 當成端到端路由正確率——它是修復階段的內部指標。
4. **不能**說模型變好了——模型行為沒變，變的是套用規則。
5. **不能**跨設計比較：全語料輪次與 matched-control 輪次的 n 與變異來源不同。

---

## 5. 可重現指令

```bash
# matched-control replay（會付費，約 24 次呼叫／輪；跑 3 輪 = n 36）
set -a && . ./.env && set +a && ~/.venvs/netzoo-qa/bin/python \
  scripts/evaluate_routing.py --live --repair-replay \
  --repair-replay-suite role-evidence --repeat 3 --max-calls 24 --json \
  | tee docs/research-log/replay-roundN.json

# leave-one-out（抽掉②）
git worktree add -b ablation/no-step2 /tmp/ablate HEAD
cd /tmp/ablate && git revert --no-commit 2e03a24   # 只動 router_invocation.py
#  ...再跑同一條 replay 指令三次

# 三步的機制計數器（決定性、不花錢）
~/.venvs/netzoo-qa/bin/python -m pytest -q \
  tests/test_citation_only_repair_keeps_the_outcome.py \
  tests/test_unhonourable_removals_do_not_cost_the_repair.py
```

Fisher exact 一律單尾（H1：候選 > 基線），`scipy.stats.fisher_exact(..., alternative='greater')`。
