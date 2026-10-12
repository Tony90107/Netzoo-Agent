# Log 416 結果：未決的結果選擇（G2）——撤回

## 判定

| 判定 | base | cand | 結果 |
|---|---|---|---|
| V1（o16） | 112/112，0 空回覆 | 同左 | 成立 |
| G0 已決定請求有回答（22） | 22 | 22 | 成立 |
| G0 `open_choice` 誤觸發 ≤ 1 | 0 | **2** | **不成立** |
| G1 目標成功（OC＋ON，22） | 7 | 21（人工複核後 20） | 成立（+13） |
| G2 替使用者選／整題拒絕 | 6／2 | 0／0 | 成立 |
| G3 OP 拒絕；OP1 問 type | 0；2 | 0；2 | 成立 |
| GB0（b16）DECIDED 回答／IMPOSSIBLE 說明做不到 | 14/14；6/6 | 14/14；6/6 | 成立 |
| GB1（b16）OPEN 成功 ≥ base + 5 | 11/16 | 12/16 | **不成立；量測無效（見下）** |

**結論：G0 不成立，候選撤回（revert 3ceef22）。**

## G0 為何不成立

- 誤觸發的是 XM1：「For per-sample co-expression networks of 50 samples, should we use LIONESS or BONOBO?」，cand 兩次都觸發。
- 規則會跳過「選項是 workflow 名稱」的選擇，但名單只有完整的 sheet 名稱（LIONESS-PANDA、LIONESS-COEXPRESSION…）。
- 使用者寫的是方法家族名「LIONESS」，沒被認出來，結果被當成一個結果選擇。
- 通用的修法：名單改成「workflow 名稱，加上兩個以上 workflow 共用的連字號前綴」。依目前的 sheet，只會多出 LIONESS。

## 人工複核（兩臂全部 OC、ON）

- 程式判讀大致和實際內容一致，只有一處高估：
  - ON1-1（cand）程式判為成功，但回覆說「network per cell -- available from LIONESS-PANDA」。這是把做不到的單細胞網路說成做得到。
  - 原因：兩個選項都被對到同一個 workflow，所以 `open_choice` 沒觸發，改由既有的 reading 回覆回答。
  - 同一題 base 整題拒絕，連做得到的 per donor 也拒絕，同樣不對。
- ON1-2、ON2、ON3（cand）都正確：做不到的選項說明了原因，做得到的選項列出 workflow。
- OC6-2（cand）失敗，是 semantic routing 驗證失敗，屬 provider 雜訊。
- 下一輪 ON 類題要再加一個程式判讀：做不到的選項有沒有被明說做不到。

## b16 盲測回合量測無效

- b16 期間，nemotron `:free` 的每日額度（1000 次）用完。38 次檢查失敗中有 37 次是 HTTP 429，錯誤訊息是 `free-models-per-day-high-balance`，額度在 2026-10-13 08:00 重置。
- 檢查改由備援模型讀取，依 Log 401 的設計，備援的讀取一律不採取行動。
  - b16：provisional 的 session 數 base 35/60、cand 38/60。
  - o16：0/112。
- 所以 GB1 量到的主要是「檢查模型離線時，兩臂都退回舊行為」。
- 只看檢查有確認的 session（樣本太小，只供參考）：
  - OPEN：base 6/7 成功；cand 5/5 成功，其中 4 次觸發 `open_choice`。
  - UNKNOWN_INPUT：兩臂都是 0/3。
- 凍結時 b16 沒有設 provider 失敗上限，這是凍結的缺漏。往後的 V1 要計入 provisional／unavailable 的檢查數。

## 仍成立的觀察（全部 b16 session，兩臂一致）

- **UNKNOWN_INPUT 兩臂都是 0/10，大多直接替使用者選了 workflow**（base 8、cand 9）。例如節點角色未知、cell 或 bulk 未知、兩層資料是否同一批樣本未知。這才是 G2 的主要缺口；這個候選只處理「使用者自己列出選項」的形態。
- 在 OPEN 題上，base 本來就有 11/16，大多靠既有的 reading／hypothesis 路由。
- 盲測題的措辭比 heldout416 多樣，heldout416 是在知道修法後寫的，偏向這個機制，這和使用者的擔心一致。

## 對下一版的影響

1. 不再做單點修補。把 insufficient_information 做成 harness 裡正式的 verdict 狀態：
   - 模型讀取兩件事：使用者明說「沒決定」的結果選擇，以及「不知道」的資料性質，後者對應既有的型別維度（data_unit、input_network、samples_matched、regulator_kinds、layers）。
   - 程式依 capability sheet 判定：這一點是否會改變能不能做、或該選哪一個 workflow；會的話就問這一點。
   - 所有 renderer 都只讀這個 verdict。run 路徑也要經過同一個判定。
2. 方法家族名的規則照上面的通用修法。
3. 選項追問沒觸發時，不能讓其他回覆把做不到的選項說成做得到（ON1-1）。
4. 量測方面：
   - 每輪前先確認免費模型的額度。一輪兩臂、120 個 session，約需 300–500 次檢查呼叫，所以每天最多只能跑約兩輪。
   - V1 要計入 provisional／unavailable 的檢查數。
   - 驗證要用全新的盲測題，由獨立撰寫者出題；heldout416 和 heldout416b 都已經看過。
