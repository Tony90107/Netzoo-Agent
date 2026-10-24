# 修補 B：主要讀取失敗後的暫停（2026-10-24，寫程式前宣告）

起因：錯誤歸因（[attribution/ATTRIBUTION.md](attribution/ATTRIBUTION.md)）裡，replay 的 143 筆錯誤中有 26 筆是「主要讀取失敗，只剩備援讀取，程式暫停」（UNCHECKED）。使用者要求寫計畫並實作。

## 調查結果（不呼叫模型）

1. **26 筆全部來自 nemotron 時期的錄製。** 那時主要的 capability check 用 `nvidia/nemotron-3-super-120b-a12b:free`：
   - 25 筆是結構化輸出無法解碼（每次 177–285 秒）；
   - 1 筆是 provider 502。
2. **這兩個原因都已經處理過：**
   - 10-16 把 check 的輸出上限調到 16,000 tokens：nemotron 把上限耗在推理上，所以無法解碼，那批 27 筆調高後全部可以解碼；
   - 10-20 nemotron 唯一的 provider 下架，主要 check 改成 `openai/gpt-4o-mini-2024-07-18`。
3. **現在的設定下幾乎不會發生。** P5 兩輪 live 共 195 次 capability check，主要讀取失敗 **0** 次，暫停 **0** 次。
4. **但規則還停在 nemotron 時期。** 主要讀取失敗時，程式用 study-purpose 模型（`openai/gpt-4o-mini`）再讀一次，並把這份讀取標為 provisional：不採用、不說出、只能暫停（Log 401：當時備援模型被認為比主要模型弱）。現在主要和備援是**同一個模型**（gpt-4o-mini，一個寫日期、一個是別名），備援讀取與主要讀取一樣可信，暫停只是白白損失。
5. **replay 高估了現行系統的錯誤。** replay 依錄製當時的 provisional 事件重建暫停，所以這 26 筆在 replay 裡永遠是 UNCHECKED，即使今天的系統不會這樣處理。

## 要做什麼

**B1（產品程式）：同一個模型的備援讀取不算 provisional。**

- 在 `graph/capability_check_call.py`：主要讀取失敗、改用備援時，若備援模型和主要模型是同一個（比對時去掉結尾的日期版本，例如 `-2024-07-18`），而且這次沒有因為 enum 上限改用 compact schema，就把結果當成一般讀取（status `ok`）。
- 只要兩個模型不同，或改用了 compact schema，就照舊標為 provisional 並暫停。
- 只在主要讀取失敗時才會觸發；現行設定下主要讀取從未失敗過，所以 live 行為幾乎不變，只是 provider 偶發錯誤時不再白白暫停。

**B2（研究工具）：加一個「現行設定」的 replay 模式**，預設關閉，所以既有的 replay 結果不受影響。

- 開啟 `NETZOO_REPLAY_CURRENT_MODELS=1` 時，若錄製的 provisional 事件來自「主要模型與今天的主要模型不同，而且備援讀取由今天的主要模型所屬的同一模型完成」，就不採用那個 provisional 事件，改用錄下的備援讀取照常判定。
- 這代表「今天的系統讀到同一份讀取時會怎麼判」。限制：真正的主要讀取若重讀一次，內容可能和錄下的備援讀取略有不同。
- **（選做，需另外核准，約 US$0.08）** 用今天的主要模型真的把這 26 份重讀一次，驗證這個近似。

## 門檻

1. **單元測試**：
   - 同模型的備援 → `ok`；
   - 不同模型 → `fallback`（provisional）；
   - 同模型但改用 compact schema → `fallback`；
   - 模型名稱比對去掉日期版本：`openai/gpt-4o-mini` 等於 `openai/gpt-4o-mini-2024-07-18`，不等於 `nvidia/nemotron…`。
2. **完整 `tests/` 通過**，不新增略過項。
3. **標準 B2 replay：判定 0 改變**。它依錄製事件重建，B1 不影響。
4. **「現行設定」replay**：列出 26 筆的新判定，逐筆對金標，算出對、錯，以及錯誤類型；**新出現的 FA 逐筆列出**由使用者判斷。現行設定下的整體分數另外報告，不取代標準 replay 的數字。
5. **不跑 live**：B1 只在主要讀取失敗時觸發，現行設定下 195 次都沒失敗過，live 無從觸發。
