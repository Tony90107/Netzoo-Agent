# 必要條件漏讀與句子歸屬修復報告

**已修改並通過回歸測試。T01 的背景誤列產出已修正；T02 的漏讀不再無條件放行，但原本應直接 DECLINE 的目標尚未完成。** 目前固定的漏讀紀錄改為 ASK，不能宣稱已做到完整的正確判斷。

- 起點：`4f08b3c8ecaf835f222bd06b5234b74d834aa96f`。
- 程式與測試提交：`704712224a1fea1ab1c262f90209b3bc724e94a9`。
- 工作樹：`.worktrees/netzoo-closed-menu`，分支 `closed-menu-phase0`；未修改 main，未推送。
- 計畫：`collab/2026-10-20_必要條件漏讀修復計畫.md`。本輪模型呼叫 0、費用 $0，沒有新增 live 或盲測。

## 1. 修改了什麼

### T01：先核對引文的句子歸屬

來源：`hb-judgment20261020e-T01-1/t1` 的 `routing.capability_checked`。模型把人數與 motif／PPI 兩句背景塞進 `s1.asks`；它們實際位於被標為 background 的 s2／s3。兩個空白 ask 後續被 second opinion 都回答 all，最後呈現為「可由 LIONESS-PANDA 提供」。

現在先按原始句界、精確引文與 sentence role 修正歸屬：只有放錯容器、而且沒有 delivered_by 或 not_by 證據的空白 ask，才移回實際背景句的 has。保留原始模型資料不變；被移動的項目記錄 `ask_in_other_background_sentence`、source_sentence、owner_sentence。重複引文、跨句引文或沒有可靠 owner 時，不猜歸屬。

明確配有支持／否決證據的要求仍保留，不因 role 矛盾而移除。逐項稽核發現 C47「which genes drive the risk」屬於這種情況，已加測試保護；不能只看核心類別沒變就把真實要求刪掉。

證據：`sentence_ownership.py:37`、`capability_check.py:408`、`tests/test_reading_coverage.py`。分句函式移至同一模組並維持原入口相容；capability_check.py 保持 990 行。

### T02：背景抄到了，不等於必要條件已核對

來源：`hb-judgment20261020e-T02-1/t1` 的 `routing.capability_checked`。原文「either one or two biological samples」存在背景，sample_count、count_alternatives、unknown_facts 都空白。原先沒有任何樣本數判斷，最後 core.decision 為 DO。

現在在 DO 前檢查：如果背景中有尚未被既有共用事實紀錄解釋的數值，該結果又對應有最低樣本數要求的 workflow，而且沒有該結果已核對的樣本數，就交由既有 count_fact 追問路徑保留，撤銷 action／should_execute／execution_requested。門檻從 workflow_conditions 讀取 preflight 的既有來源，不硬寫 3。

這是讀取完整性的保守護欄，不從原文數字猜其種類：沒有把蛋白、批次、時間直接變成樣本。程式產生的問題明說資料說明中的樣本數尚未核對；minimum 是程式計算的條件，不偽裝成逐字引用的合約句子。

同一資料說明中已有符合門檻、且適用於該結果的樣本數時，不因另有批次數而再問；別份資料、不適用的 scope 或 feature_count 不能拿來滿足它。一般沒有未解釋數值背景的方法問題不觸發；既有 CLARIFY、DECLINE、UNCHECKED 優先序維持。

證據：`sample_coverage.py:43`、`sample_coverage.py:68`、`core_decision.py:283`。新診斷存在 `core.evidence.unread_sample_conditions`。沒有新增模型讀取欄位、模型呼叫或 prompt 字詞規則。

## 2. 對照結果

| 固定輸入 | 修改後結果 | 意義 |
| --- | --- | --- |
| attempt-05 T01 原始 proposal，加回仍存活要求對應的已存 second-opinion 答案 | DO；理解段落只列真正要求的 TF-to-gene network | 已存背景不再被宣稱為產出；沒有重新產生模型答案 |
| attempt-05 T02 原始漏讀 | ASK；執行與規劃旗標關閉 | 不再誤放行；仍不是原本應得的 DECLINE |
| 合成控制：讀取正確提供 1／2 個樣本候選 | DECLINE | 仍用既有共用門檻規則 |
| 合成控制：9／17 個樣本候選 | DO | 不製造無意義追問 |
| 合成控制：2／14 個樣本候選 | ASK | 問決定性的候選數量 |
| 補答並正確讀出 14 個樣本 | DO | 缺少的條件核對可以解除；不代表已完成真實對話 live 驗證 |

證據：`targeted-replay.json`、`tests/test_reading_coverage.py`。這些題已看過，不是盲測。

## 3. 測試與離線重放

- 先用原始 T01／T02 建最初 9 個回歸測試：修改前 5 failed、4 passed（`regression-before.log`）。
- 最終新增 18 個測試；連同既有相關測試 **150 passed**（`focused-tests.log`）。包含門檻跟隨 preflight 常數、已知樣本旁的 batch 數、不適用 scope、其他資料來源、句子引文重複與否決證據保留。
- 全套 **4,778 passed、51 skipped、0 failed**（`full-tests.log`）。跳過沒有算通過。
- 凍結 999 份原始讀取、reread 與已存 routing／fact-agent／run-verdict，重放 999 份，跳過 0。
- **14 份 DO → ASK**；其餘核心類別不變。13 個空白 ask 的句子歸屬修正另存於 `sentence-ownership.json`。
- 741 份有金標的核心類別吻合 **561 → 563**，原本吻合而退步的 0。這只是類別比較，不代表新問題內容都正確，也不是端到端準確率；例如 M01／C34 的類別吻合不能據此當成完整語意修復。
- 14 個新的 ASK 都經過 with_core 撤銷執行與規劃旗標；`verify.py` 檢查凍結資料、程式 SHA256 與重放可重現性。

### 每個核心類別變化

| Session | 金標 | 固定讀取重放 |
| --- | --- | --- |
| `ve-m3-live-U21-2` | 未標 | DO → ASK |
| `hb-h2hyb-J11-1` | 未標 | DO → ASK |
| `hb-judgment20261020b-T02-1` | 未標 | DO → ASK |
| `hb-h2main-J44-1` | DECLINE | DO → ASK |
| `hb-h2hyb-J07-1` | 未標 | DO → ASK |
| `ve-m3-live-U21-1` | 未標 | DO → ASK |
| `cj-p1-C23-1` | CLARIFY | DO → ASK |
| `hb-judgment20261020e-T02-1` | 未標 | DO → ASK |
| `hb-judgment20261020d-T02-1` | 未標 | DO → ASK |
| `cj-p0-C23-1` | CLARIFY | DO → ASK |
| `ve-m3-live-U09-1` | 未標 | DO → ASK |
| `ve-m3-live-P04-1` | 未標 | DO → ASK |
| `hb-h4main-M01-1` | ASK | DO → ASK |
| `cj-p5-C34-1` | ASK | DO → ASK |

所有變化的完整原文、前後核心與觸發背景見 `changed-calls.json`。有些是保守追問，可能增加不必要的問題，不能把 14 個變化全部當成 14 題正確修復。

## 4. 尚未完成與適用範圍

**第一次模型讀取漏讀尚未根治。** 本輪沒有把 T02 空白欄位補成 1／2，也沒有用數字或生物字詞特判硬判 DECLINE。模型完全漏讀時，現在停下確認；要在該題第一次就正確拒絕，仍需讓語意讀取正確產生可核對事實，再經新盲題驗證。

這個護欄只涵蓋已抄入背景、又含現有數字解析器可辨識數值的情況；完全未抄到背景、未被辨識的數量、被錯分為其他維度或語意完全相反的讀取，不能宣稱已被涵蓋。它也可能在檔案實際足夠時多問一次。實際執行的檔案／格式／識別碼與 Plan Evaluator 門檻仍須通過。

本輪沒有跑新 live、正式盲測或科學 Executor，沒有更新模型設定；不能把這份離線報告改寫成新的 7／7 live 成績。

## 5. 可重現命令與保存檔案

```text
/opt/anaconda3/bin/python3 -m pytest -q tests/test_reading_coverage.py tests/test_capability_check.py tests/test_core_decision.py tests/test_count_consistency.py tests/test_count_doubts.py
/opt/anaconda3/bin/python3 -m pytest -q tests
/opt/anaconda3/bin/python3 -I docs/research-log/reading-coverage-2026-10-20/replay.py
/opt/anaconda3/bin/python3 docs/research-log/reading-coverage-2026-10-20/verify.py
```

最初比較沿用 request-facts-round03 的 checks 與 count-scope-r09 的 cores／compare 命令，修改前先保存基線；之後凍結成 `inputs.json.gz`，以本輪 replay.py 重建。凍結檔已包含原始 proposal、reread、基線 check／core 與固定 decision，避免依賴之後會增加的紀錄目錄掃描。T01 的顯示驗證另外使用 manifest 列出的 attempt-05 來源，僅把已存 all 答案對回仍存在的同一段結果引文。

修改的程式與測試：interpretation/capability_check.py、core_decision.py、新增 sample_coverage.py、sentence_ownership.py；tests/test_reading_coverage.py 與三份 tests/fixtures/reading_coverage/*.json。本輪資料、程式與雜湊清單全在 `docs/research-log/reading-coverage-2026-10-20/`。
