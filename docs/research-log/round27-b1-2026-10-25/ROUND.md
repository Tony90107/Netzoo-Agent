# ROUND-27 B1：設定連結 2a′（2026-10-25，寫程式之前宣告）

- 計畫：`collab/ROUND-27-PLAN.md` 第 4 節。使用者同意 B1 用 2a 事後看出的改法重新開一輪；開發題組只用來決定要不要進 h10。
- 起點：`bfe711b9`（凍結版加上 C1，C1 的旗標關閉，不影響本輪）。
- 2a 的程式：從 `45022b15`（分支 `round26-settings-links`）移植 `interpretation/settings_links.py` 與 `graph/settings_links_call.py`，再做第 1 節的改動。
- 旗標：`NETZOO_SETTINGS_LINKS=1` 才啟用，預設關閉。
- 模型：gpt-4o-mini。

## 1. 和 2a 的差別（只有這五項）

1. **候選只有首輪讀取 credit 的 workflow。**
   - 也就是需求列 `delivered_by` 裡 produces 類項目所屬的 workflow。
   - 不再包含請求裡點名但沒被 credit 的 workflow，也不包含 `named_method`。
   - 依據：2a 的 Q45、Q14、P01。
2. **不連自由文字類的設定。** 排除 `BONOBO.sample_names`（string_list）與 `CONDOR.prefix`（輸出檔名前綴）。
   - 依據：2a 的 sample_names 多連 10 個。
   - `SAMBAR.distance` 與 `SAMBAR.linkage` 雖然也是 string 型別，但它們是方法選擇，保留。
3. **讀取每個設定多一個 `unsure` 布林欄位：** 使用者說不確定要不要這樣設時為 true。
   - unsure 的連結**不併入**讀取，改成確認提問。
   - 依據：2a 的 U20。
   - 說明文字是 2a 的原文，只加一句定義 `unsure`。寫一次就定稿。
4. **沒有值的新連結，不取代首輪讀取裡同一個設定、而且有值的項目。** 依據：2a 的 J41。
5. **新連結不能製造限制。** 併入之前，程式先用原本的讀取和併入後的讀取各建一次 check（`build_capability_check`，純程式），比較所有需求列的 `limits` 與 `violations`：
   - 併入後多出的限制，找出是哪個連結造成的：一次拿掉一個連結，看新限制會不會消失。
   - 造成新限制的連結**不併入**，改成確認提問。
   - 找不出是哪個連結造成的，就全部不併入，維持原本的讀取。
   - 依據：2a 的 G5 失敗機制。

**確認提問：**
- **何時產生：** 有連結沒併入（第 3 或第 5 項），而且最後判斷是 DO，就改成 ASK，basis 是 `setting_link_fact`。最後判斷不是 DO 時不動。
- **問句由程式產生：**
  - 造成限制的連結：`Did you mean <workflow>'s <setting><= value>? <新限制的文字>`。限制的文字是 check 依合約規則寫出的。
  - unsure 的連結：`Should <workflow>'s <setting> be set<= value>? You were unsure.`，並附上使用者原話。

## 2. 量測（離線）

**讀取：** 每個 (請求, 候選 workflow) 讀一次，範圍是 harness 所有錄製讀取中有候選的那些。預估約 300 次，約 US$0.08，硬上限 US$1.0。

**兩個 arm：**
- 舊 arm：現行程式，不加連結。
- 新 arm：連結經過第 1 節的檢查後併入，沒併入的連結在 DO 時變成提問。
- 兩個 arm 都載入同一批 R22-B 設定讀取快取：`input-constraints-2026-10-21/settings-reads.json`，以及 2a 補問的 `r22b-reads.json`（從 `f7da8cbe` 複製）。
- 兩個 arm 都套用 P2 的金標重標。

**欄位計分：** 用 2a 的 `score` 與 `field-gold-2026-10-22/linking.py`。
- 新 arm 的「讀到的連結」包含已併入的和沒併入（變成提問）的。兩者都是系統讀出的連結，所以精確率把兩者都算進去。

### 門檻（數字與 2a 相同，不放寬）

| | 項目 | 門檻 |
|---|---|---|
| B-G1 | 選項單位，修好 − 改壞 | ≥ 6，單尾符號檢定 p < 0.05 |
| B-G2 | 選項單位精確率 | 下降 ≤ 2 個百分點 |
| B-G3 | 宣告單位 | 改壞 ≤ 修好 |
| B-G4 | 757 份重放 | 對→錯 ≤ 2，每一份逐一說明 |
| B-G5 | 新出現的錯誤理由：新 arm 有、舊 arm 沒有的限制或違反文字 | 0 |

**另外報告（不設門檻）：**
- 金標 DO 卻變成 ASK 的份數（成本）；
- 金標 DECLINE 從 DO 變成 ASK 的份數；
- 每個新問句的內容。

### 停止規則

- 任何一個門檻不過，就撤回 B1：旗標保持關閉，不改寫說明，不做第二版。
- 都過了，才考慮 live 小量檢查（最多 20 個 session，跑之前先公告）和 h10。
