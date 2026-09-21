# PANDA / PUMA 輸入輸出格式與 Docker 入門

整理日期：2026-06-13

這份文件有兩個目的：

1. 讓你看懂 PANDA 和 PUMA 到底吃什麼檔案、吐什麼結果。
2. 讓你第一次使用 Docker 時，知道 Docker 在這裡的意義，不只是照貼指令。

## 一句話理解 PANDA 與 PUMA

### PANDA

PANDA 用三種資料推論 gene regulatory network：

| 資料 | 白話意思 |
|---|---|
| expression matrix | 實際觀察到每個基因在每個樣本中的表現量 |
| motif prior | 先驗知識：某個 TF 理論上可能調控某個 gene |
| PPI network | 先驗知識：哪些 TF 之間可能互相合作 |

PANDA 的輸出是一張 TF-gene 網路：

```text
TF      Gene    Motif   Force
MYC     CCND1   1       2.31
TP53    BAX     1       1.84
```

白話：`MYC -> CCND1` 這條邊的 PANDA score 多強。

### PUMA

PUMA 是 PANDA 的延伸版，多加入 miRNA：

| 資料 | 白話意思 |
|---|---|
| expression matrix | gene expression |
| motif prior | TF-gene 先驗調控關係 |
| PPI network | TF-TF 合作關係 |
| miRNA target prior | 放在 motif/prior 檔中的 miRNA-gene 先驗調控關係 |

PUMA 的輸出也是 regulatory network，但 regulator layer 會包含 TF 與 miRNA：

```text
Regulator   Gene    Prior   Score
MYC         CCND1   1       2.31
hsa-miR-21  PTEN    1       1.77
```

實際欄位名稱可能因 netZooPy 版本與輸出選項而略有不同；核心概念是：每一列代表一條 regulator-to-gene 邊。

## PANDA input 格式

PANDA 主要需要三個檔案：

```bash
run-panda \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -o outputs/panda_network.txt
```

### 1. `-e` expression file

官方 CLI 預設 expression 檔案沒有 header，欄位用 tab 分隔。實務上最常用的概念是：

- row：gene
- column：sample
- value：expression value，例如 TPM、log2 TPM、normalized count

概念範例：

```tsv
GeneA   8.1   7.9   8.4
GeneB   2.0   2.2   1.8
GeneC   5.5   5.1   5.8
```

如果你的 expression 檔案第一列有 sample 名稱，PANDA 新版 CLI 可加：

```bash
--with_header
```

有 header 的概念範例：

```tsv
gene    sample_1    sample_2    sample_3
GeneA   8.1         7.9         8.4
GeneB   2.0         2.2         1.8
GeneC   5.5         5.1         5.8
```

注意：不同版本對 row name/header 的處理有差異。正式資料建議先用官方 toy data 跑通，再把自己的資料整理成相同形狀。

### 2. `-m` motif file

這是 TF-gene prior。官方文件描述為 pair file，格式是：

```text
TF    Gene    Weight
```

通常 `Weight` 是 `0` 或 `1`：

```tsv
MYC     CCND1   1
MYC     CDK4    1
TP53    BAX     1
```

白話：這個檔案在告訴 PANDA「哪些 TF 理論上可能調控哪些 gene」。

### 3. `-p` PPI file

這是 TF-TF protein-protein interaction。格式是：

```text
TF1    TF2    Weight
```

範例：

```tsv
MYC     MAX     1
TP53    EP300   1
FOS     JUN     1
```

PANDA 會把 PPI 當作 TF 之間合作或互動的先驗網路。官方文件也提到，如果 PPI 不是對稱的，程式會轉成對稱 adjacency matrix。

## PANDA output 格式

PANDA 輸出是一個文字檔。新版 `netzoopy panda` CLI 的官方文件說明輸出欄位為：

```text
TF    Gene    Motif    Force
```

| 欄位 | 意思 |
|---|---|
| `TF` | transcription factor |
| `Gene` | target gene |
| `Motif` | 原本 motif prior 裡的邊權重 |
| `Force` | PANDA 推論後的 edge score |

你真正會看的通常是 `Force`。分數越高，代表這條 TF-gene 調控邊越被資料支持。

## PUMA input 格式

PUMA 比 PANDA 多一個 miRNA file：

```bash
run-puma \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -i data/official-toy/ToyMiRList.txt \
  -o outputs/puma_network.txt
```

### 1. `-e` expression file

同 PANDA。基因表現矩陣。

### 2. `-m` motif/prior file

可同時包含 TF-gene 與 miRNA-gene prior，每列格式都是
`Regulator<TAB>Gene<TAB>Weight`。

### 3. `-p` PPI file

同 PANDA。TF-TF interaction prior。

### 4. `-i` miRNA file

這是 PUMA 用來辨識哪些 regulator 屬於 miRNA 的單欄清單，每行一個名稱：

```text
hsa-miR-21
hsa-miR-34a
hsa-miR-155
```

清單內的名稱必須出現在 motif/prior 檔案第一欄；真正的 miRNA-gene 邊放在
`-m` 指定的 motif/prior 檔案中。

## PUMA output 格式

PUMA 輸出的是 regulator-gene network。跟 PANDA 的差別是：

- PANDA 的 regulator 幾乎都是 TF
- PUMA 的 regulator 包含 TF 和 miRNA

概念輸出：

```text
Regulator    Gene    Prior    Score
MYC          CCND1   1        2.31
hsa-miR-21   PTEN    1        1.77
```

分數越高，代表這條 regulator-gene 邊越被資料支持。

## Docker 在這裡到底在幹嘛？

如果不用 Docker，你可能會遇到這些問題：

- 你的 Python 版本不合
- `numpy`、`pandas`、`scipy`、`netzoopy` 版本互相衝突
- 你的 macOS / Windows / Linux 行為不一樣
- 今天跑得動，半年後換電腦跑不動

Docker 的概念是：

> 把「作業系統環境 + Python + netZooPy + 依賴套件」包成一個小型可重建環境。

你可以把 Docker image 想成一個食譜做出來的分析小房間：

| Docker 概念 | 在這個專案裡的意思 |
|---|---|
| image | 已安裝好 netZooPy 的執行環境 |
| container | 從 image 啟動出來的一次分析工作區 |
| volume mount | 把你本機資料夾掛進 container，讓 container 讀你的 input、寫 output |
| Dockerfile | 建立 image 的食譜 |
| docker-compose.yml | 幫你少打很多 docker run 參數 |

重要的是：Docker 不會讓你的資料自動消失。這裡的設定會把目前資料夾掛到 container 裡的 `/work`，所以 container 寫出的 `outputs/*.tsv` 會留在你的本機資料夾。

## 本專案建立的 Docker 環境

我幫你建立了這些檔案：

```text
Dockerfile
environment.yml
docker-compose.yml
docker/run-panda
docker/run-puma
```

這個 Docker image 會做幾件事：

1. 建立 Python / conda 環境。
2. 安裝 `netzoopy`。
3. 下載官方 `netZooPy` repo 到 `/opt/netZooPy`，讓 legacy `run_puma.py` 可以被呼叫。
4. 建立兩個方便使用的 wrapper：
   - `run-panda`
   - `run-puma`

## 第一次使用 Docker 的流程

### 1. 建立 image

在本資料夾執行：

```bash
docker compose build
```

這一步是在照 `Dockerfile` 做出一個名叫 `netzoo_agent:latest` 的環境。第一次會花比較久，因為要下載套件。

### 2. 進入 container

```bash
docker compose run --rm netzoo
```

進去後，你會在 container 的 `/work` 目錄，但它其實對應到你本機這個專案資料夾。

可以檢查：

```bash
pwd
ls
python --version
netzoopy --help
```

### 3. 準備資料夾

在本機專案資料夾建立：

```text
data/
outputs/
```

專案已附一組官方 toy data，可直接使用：

```text
data/official-toy/ToyExpressionData.txt   expression
data/official-toy/ToyMotifData.txt        motif prior
data/official-toy/ToyPPIData.txt          PPI prior
data/official-toy/ToyMiRList.txt          PUMA 的 miRNA 清單
```

自己的資料放在 `data/` 底下即可，下面的指令換成你的檔名。

### 4. 跑 PANDA

在 container 裡：

```bash
run-panda \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -o outputs/panda_network.txt
```

或不進 container，直接從本機執行：

```bash
docker compose run --rm netzoo run-panda \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -o outputs/panda_network.txt
```

### 5. 跑 PUMA

在 container 裡：

```bash
run-puma \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -i data/official-toy/ToyMiRList.txt \
  -o outputs/puma_network.txt
```

或不進 container：

```bash
docker compose run --rm netzoo run-puma \
  -e data/official-toy/ToyExpressionData.txt \
  -m data/official-toy/ToyMotifData.txt \
  -p data/official-toy/ToyPPIData.txt \
  -i data/official-toy/ToyMiRList.txt \
  -o outputs/puma_network.txt
```

## 你需要特別注意的資料整理問題

### Gene 名稱要對得上

Expression 裡的 gene 名稱要出現在 motif / miRNA prior 裡。

例如 expression 有：

```text
CCND1
BAX
PTEN
```

那 motif/prior file 裡的 target gene 也要叫 `CCND1`、`BAX`、`PTEN`，不要一邊是 Ensembl ID、一邊是 gene symbol。

### TF 名稱要對得上

Motif file 裡的 TF 要能和 PPI file 裡的 TF 對上。

例如 motif 有 `MYC`，PPI 裡卻只有 `c-Myc`，那程式會把它們當成不同東西。

### 先用小資料測試

正式資料可能很大。建議先只取：

- 20 到 100 個 genes
- 少量 TF
- 少量 samples

確定格式正確、能產生 output 後，再跑完整資料。

## 常見錯誤

### `Error when creating the motif network`

常見原因：expression genes 和 motif target genes 沒有交集。

處理方式：檢查 gene identifier 是否一致。

### output 是空的或很小

常見原因：

- motif prior 太少
- PPI 的 TF 和 motif 的 TF 對不上
- motif/prior 內的 miRNA target gene 和 expression gene 對不上

### 跑很久

PANDA/PUMA 是矩陣運算。genes、TFs、samples 越多會越慢。先用小資料確認流程，再跑完整資料。

## 參考來源

- netZooPy CLI 文件：[https://netzoopy.readthedocs.io/en/latest/functions/cli.html](https://netzoopy.readthedocs.io/en/latest/functions/cli.html)
- netZooPy functions 文件：[https://netzoopy.readthedocs.io/en/latest/functions/](https://netzoopy.readthedocs.io/en/latest/functions/)
- netZooPy GitHub：[https://github.com/netZoo/netZooPy](https://github.com/netZoo/netZooPy)
