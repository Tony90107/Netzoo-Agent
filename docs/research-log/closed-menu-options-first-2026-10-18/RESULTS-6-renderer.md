# 先給選項第 6 步：選項卡的英文回覆（2026-10-18）

## 結論

- `interpretation/menu_reply.py` 的 `render_menu_reply(decision)`：只從判定結果、預設值表的標籤和合約原文組成英文回覆，回覆時不呼叫模型。沒有接進 live path。
- 不能做的部分，一律寫「NetZoo cannot do "…": …」或「NetZoo cannot run X for this because …」，接著附「The contract says: "…"」（sheet 的 why_not 原文），再列「The nearest options NetZoo can run:」。沒有可替代的就寫「No registered workflow gives this.」。
- 選項逐條列出：結果、How it differs、Good for、「Matches k of the n points you gave」（附使用者原話）、Still to confirm。
- 問題逐題列出：附使用者原話，選項用預設值表的標籤，固定加上「Not sure -- suggest one」「None of these (please describe)」。
- 最後固定一列自由輸入：「Or type the method or package you want, in your own words.」
- DO 一律以「Nothing runs until you approve it.」結尾。

## 為渲染補上的合約資料

`judgment_defaults.yaml` 的 10 個資料條件欄位加上 `options`：給使用者看的選項標籤（例如 input_network：「Regulator-to-gene edges」「Gene-gene edges」）。只是呈現用的文字，不改任何預設值。

## 測試（`tests/test_menu_reply.py`，7 項，不呼叫模型）

- 拒絕：有「NetZoo cannot」、合約原文、最接近的選項。
- 清單外的結果：「No registered workflow gives this.」。
- 平手：有選項說明，並等待同意。
- 追問：有選項、問題、使用者原話、兩個固定選項。
- 模糊：引用讓目標不明的原話。
- 不支援的設定：用合約的話拒絕。
- 讀取失敗：只說無法檢查，不提任何 workflow。
- **接地檢查**：回覆中出現的每個 workflow 名稱，都必須來自判定（選項、最接近、不可行、workflows）或合約自己的選項文字。
  - 第一次跑時就抓到平手選項的 `good_for` 提到 LIONESS-PANDA、CONDOR（使用者確認過的 YAML 文字，屬於後續步驟），所以接地檢查允許「選項原文中出現的名稱」。
- 全英文、沒有中文字元。

全部 741 項通過；第 0 階段門檻 56/56。
