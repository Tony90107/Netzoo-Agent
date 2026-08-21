# PANDA / PUMA / LIONESS / CONDOR 快速回想筆記

這份筆記的目標是幫你快速想起：每個工具在做什麼、需要什麼 input、會產生什麼 output、每個欄位代表什麼，以及它們怎麼被串成一條有邏輯的分析流水線。

可以先記住一句話：

> Expression 是原始觀察資料；PANDA/PUMA 用 expression 加上先驗知識推 regulatory network；LIONESS 把整體 network 拆成每個 sample 的 network；CONDOR 在 bipartite network 裡找模組。

---

## 1. 整體流水線

```text
Expression data
每個 gene 在每個 sample 的表現量
        |
        | 搭配 motif / prior / PPI / miRNA 等先驗知識
        v
PANDA 或 PUMA
推斷 regulator -> target gene 的 regulatory network
        |
        | 如果想知道每個 sample 自己的 network
        v
LIONESS
產生 sample-specific networks
        |
        | 如果想在雙分網路中找功能群組 / 模組
        v
CONDOR
找 bipartite communities / modules
```

這條線的邏輯是：

1. 我們先有很多 sample 的 gene expression。
2. 只看 expression 只能知道哪些 gene 的表現一起變動，但不知道誰可能調控誰。
3. PANDA / PUMA 會加入生物先驗知識，例如 TF 可能結合哪些 gene、TF 之間是否有 protein interaction、miRNA 可能調控哪些 gene。
4. PANDA / PUMA 的輸出是「regulator 和 target gene 之間的邊分數」。
5. LIONESS 可以把 PANDA / PUMA 這種群體網路拆成每個 sample 各自的網路。
6. CONDOR 可以拿 bipartite network，例如 TF-gene 或 miRNA-gene network，找出哪些 regulator 和 genes 形成同一個模組。

---

## 2. Expression 是什麼

Expression 是最基本的資料，通常表示：

> 每個 gene 在每個 sample 裡的表現量是多少。

常見格式：

```text
gene    sample1 sample2 sample3
GeneA   1.2     1.5     0.9
GeneB   4.1     3.8     4.4
GeneC   0.2     0.3     0.1
```

欄位意義：

| 欄位 | 意義 |
|---|---|
| gene | 基因名稱 |
| sample1, sample2, sample3 | 不同樣本、病人、細胞、條件或時間點 |
| 數值 | 該 gene 在該 sample 的 expression level |

如果用「學生 / 老師」比喻：

| 生物資料 | 比喻 |
|---|---|
| gene | 學生 |
| sample | 不同班級、不同考試、不同情境 |
| expression value | 學生在某個情境下的分數或表現 |

Expression 自己不是 network。它只是原始表格。  
後續工具會用它推論「哪些 gene 互相有關係」或「哪個 regulator 可能影響哪個 gene」。

---

## 3. Co-expression 是什麼

Co-expression 是從 expression 算出來的 gene-gene 關係。

例如：

```text
gene1   gene2   weight
GeneA   GeneB   0.87
GeneA   GeneC  -0.12
```

欄位意義：

| 欄位 | 意義 |
|---|---|
| gene1 | 第一個 gene |
| gene2 | 第二個 gene |
| weight | 兩個 gene expression pattern 的相似程度，常見是 correlation |

意義：

- 正相關高：兩個 gene 常常一起變高或一起變低。
- 負相關低：一個變高時，另一個可能變低。
- 接近 0：沒有明顯共同變化。

但 co-expression 的限制是：

> 它只能說兩個 gene 的表現有關，不能直接說誰調控誰。

用比喻來說：

兩個學生每次考試分數都一起高，不代表 A 學生教了 B 學生，只代表他們的表現模式很像。可能是同一位老師教、同一種教材、同一個環境造成。

---

## 4. PANDA 是什麼

PANDA 的全名是 Passing Attributes between Networks for Data Assimilation。

它的目標是：

> 推斷 TF -> target gene 的 gene regulatory network。

也就是回答：

> 哪些 transcription factors 可能調控哪些 genes？

### PANDA 的 input

PANDA 通常需要三種 input：

| Input | 格式概念 | 意義 |
|---|---|---|
| Expression | gene x sample matrix | gene 在不同 sample 的表現量 |
| Motif prior | TF, gene, weight | 哪個 TF 理論上可能 bind 到哪個 gene |
| PPI | TF, TF, weight | TF 之間的 protein-protein interaction 或功能關係 |

Expression 範例：

```text
gene    s1  s2  s3
GeneA   1   2   3
GeneB   4   3   2
```

Motif prior 範例：

```text
tf      gene    weight
TF1     GeneA   1
TF1     GeneB   0
TF2     GeneB   1
```

PPI 範例：

```text
tf1     tf2     weight
TF1     TF2     0.8
TF2     TF3     0.4
```

### PANDA 的 output

PANDA 的輸出通常是 TF-gene edge list：

```text
tf      gene    weight
TF1     GeneA   2.31
TF1     GeneB  -0.45
TF2     GeneB   1.72
```

欄位意義：

| 欄位 | 意義 |
|---|---|
| tf | transcription factor，也就是 regulator |
| gene | target gene |
| weight | PANDA 推斷出的 regulatory edge strength |

weight 越高，代表 PANDA 越支持這個 TF-gene 調控關係。  
weight 低或負值，不一定代表完全沒有關係，而是代表在整合資料後支持度較低。

### 為什麼 PANDA 要用 PPI？

PPI 在 PANDA 裡不是說「老師互相合作會直接改變學生分數」。  
比較合理的理解是：

> 如果兩個 TF 在蛋白層級上有互動，或功能上接近，它們可能會共同調控相似的 target genes。

用比喻：

| PANDA 裡的東西 | 比喻 |
|---|---|
| TF | 老師 |
| target gene | 學生 |
| motif prior | 課表上寫某位老師可能教某位學生 |
| PPI | 老師之間是否同科、合作備課、教學內容相近 |
| expression | 學生在多次考試中的分數 |

如果兩位老師合作很密切，而學生群的表現也顯示出一致模式，PANDA 會重新調整「老師-學生」關係的可信度。

所以 PPI 的作用是提供 regulator 之間的背景關係，幫助 PANDA 不只依賴 motif prior，而能用 network consistency 去修正結果。

### 為什麼這樣用能成功？

PANDA 成功的核心邏輯是資料整合：

1. Motif prior 給出可能的 TF-gene 關係。
2. Expression 告訴我們 target genes 在樣本中是否有相似表現。
3. PPI 告訴我們 TF 之間是否有功能或蛋白互動關係。
4. PANDA 讓這三種 network 彼此調整，最後得到比較一致的 TF-gene network。

換句話說，PANDA 不是只相信一種資料，而是用三種證據互相校正。

---

## 5. PUMA 是什麼

PUMA 可以理解成 PANDA 的延伸版本。

它的目標也是推 regulatory network，但它特別加入：

> miRNA regulators。

PANDA 主要處理 TF-gene regulatory network。  
PUMA 可以同時處理 TF 和 miRNA 對 genes 的調控。

### PUMA 的 input

PUMA 常見 input：

| Input | 格式概念 | 意義 |
|---|---|---|
| Expression | gene x sample matrix | gene expression |
| Prior | regulator, gene, weight | TF-gene 和 miRNA-gene 的先驗關係 |
| PPI | TF, TF, weight | TF 之間的 interaction |
| miRNA list | miRNA names | 告訴工具哪些 regulator 是 miRNA |

Prior 範例：

```text
regulator   gene    weight
TF1         GeneA   1
TF2         GeneB   1
miR-1       GeneA   1
miR-2       GeneC   1
```

miRNA list 範例：

```text
miR-1
miR-2
```

### PUMA 的 output

PUMA 的輸出也是 regulator-gene edge list：

```text
regulator   gene    weight
TF1         GeneA   1.91
miR-1       GeneA   0.84
TF2         GeneB  -0.20
```

欄位意義：

| 欄位 | 意義 |
|---|---|
| regulator | TF 或 miRNA |
| gene | target gene |
| weight | 推斷出的 regulatory edge strength |

### PUMA 跟 PANDA 的差別

| 工具 | 主要 regulator | 適合回答的問題 |
|---|---|---|
| PANDA | TF | 哪些 TF 可能調控哪些 genes？ |
| PUMA | TF + miRNA | TF 和 miRNA 共同形成怎樣的 regulatory network？ |

如果資料只有 TF、motif、PPI，通常用 PANDA。  
如果資料還有 miRNA-gene prior，而且你想把 miRNA 也放進 regulatory network，就用 PUMA。

---

## 6. LIONESS 是什麼

LIONESS 的目標是：

> 從 group-level network 推出 sample-specific network。

PANDA / PUMA 通常會用全部 samples 產生一個整體 network。  
但有時候我們想問：

> 每個 sample 自己的 regulatory network 是不是不同？

這時候就用 LIONESS。

### LIONESS 的 input

LIONESS 不是完全獨立的 network inference 方法。  
它通常需要：

| Input | 意義 |
|---|---|
| Expression | 多個 samples 的 gene expression |
| Network method | 例如 PANDA、PUMA、coexpression |
| 該 method 需要的其他 input | 例如 motif、PPI、prior、miRNA list |

所以如果是 LIONESS PANDA：

```text
Expression + motif + PPI
        |
        v
PANDA as base method
        |
        v
LIONESS sample-specific PANDA networks
```

如果是 LIONESS PUMA：

```text
Expression + prior + PPI + miRNA list
        |
        v
PUMA as base method
        |
        v
LIONESS sample-specific PUMA networks
```

### LIONESS expression 格式

在 netZooPy / wrapper 裡，LIONESS 常常比較喜歡 headerless expression：

```text
GeneA   1   2   3
GeneB   4   3   2
```

意思是：

| 欄位 | 意義 |
|---|---|
| 第 1 欄 | gene name |
| 後面每一欄 | 一個 sample 的 expression value |

如果原始 CSV 是：

```text
# annotation
gene,s1,s2,s3
GeneA,1,2,3
GeneB,4,3,2
```

我們的 helper 會做幾件事：

1. 移除前面的 annotation。
2. 判斷它是 CSV 還是 TSV。
3. 讀成 pandas dataframe。
4. 轉成 LIONESS / PANDA / PUMA 相容的 TSV。
5. 必要時移除 header，變成：

```text
GeneA   1   2   3
GeneB   4   3   2
```

### LIONESS 的 output

LIONESS 的輸出通常長這樣：

```text
gene1   gene2   1       2       3       4
GeneA   GeneB  -0.768  -0.871  -0.856  -0.853
```

欄位意義：

| 欄位 | 意義 |
|---|---|
| gene1 / gene2 | network edge 的兩端 |
| 1, 2, 3, 4 | sample index，不是 expression value |
| 每個數值 | 該 edge 在該 sample 的 sample-specific edge score |

如果是 LIONESS PANDA / PUMA，前兩欄也可能是：

```text
regulator   gene   sample1_score sample2_score ...
```

重點是：

> LIONESS output 的 sample 欄位表示「每個 sample 裡這條 edge 的分數」。

不是原始 expression。  
它已經是 network edge score。

### 為什麼 LIONESS 至少需要多個 samples？

LIONESS 的核心想法是比較：

1. 用全部 samples 算出來的 network。
2. 拿掉某一個 sample 後算出來的 network。
3. 兩者差異可以估計那個 sample 對 network 的貢獻。

因此如果 sample 太少，LIONESS 沒有足夠的群體背景可以比較。

---

## 7. CONDOR 是什麼

CONDOR 的目標是：

> 在 bipartite network 裡找 communities / modules。

Bipartite network 是「兩種不同類型節點」組成的 network。  
例如：

```text
TF -> gene
miRNA -> gene
drug -> target
teacher -> student
```

它不是要推新的 regulatory edge，而是拿已經存在的 edge list 去分群。

### CONDOR 的 input

CONDOR input 是 bipartite edge list：

```text
source  target  weight
TF1     GeneA   1.8
TF1     GeneB   1.2
TF2     GeneC   2.0
```

欄位意義：

| 欄位 | 意義 |
|---|---|
| source | 第一種類型節點，例如 TF、miRNA、regulator |
| target | 第二種類型節點，例如 gene |
| weight | 這條邊的強度，可選但常用 |

CONDOR 很在意 input 是 bipartite。  
也就是 source 和 target 應該是兩種不同類型，不應該混在一起。

### CONDOR 的 output

我們 wrapper 目前會輸出幾類檔案：

| Output | 意義 |
|---|---|
| `*-edges.tsv` | 清理後的 bipartite edges |
| `*-reg_memb.tsv` | source/regulator 端節點被分到哪個 community |
| `*-tar_memb.tsv` | target/gene 端節點被分到哪個 community |
| `*-summary.txt` | 總結，例如 modularity |

membership 範例：

```text
node    community
TF1     1
TF2     2
```

意思是 TF1 被分到 community 1，TF2 被分到 community 2。

### CONDOR 的意義

如果 PANDA / PUMA 輸出一堆 regulator-gene edges，CONDOR 可以進一步問：

> 哪些 regulators 和 genes 常常形成同一組模組？

用比喻：

PANDA / PUMA 先推測「哪些老師可能影響哪些學生」。  
CONDOR 再把老師和學生一起分群，找出：

> 哪一群老師和哪一群學生形成一個比較緊密的教學模組？

這可以幫你從一大張 network 裡找出比較容易解釋的 functional modules。

---

## 8. 四個工具的 input / output 總表

| 工具 | 主要目的 | Input | Output |
|---|---|---|---|
| Expression | 原始資料 | gene x sample matrix | 還不是 network |
| Co-expression | 看 genes 是否一起變動 | expression | gene-gene correlation network |
| PANDA | 推 TF-gene regulatory network | expression + motif prior + PPI | TF-gene edge scores |
| PUMA | 推 TF/miRNA-gene regulatory network | expression + prior + PPI + miRNA list | regulator-gene edge scores |
| LIONESS | 產生 sample-specific network | expression + base network method | 每個 sample 的 edge score |
| CONDOR | 找 bipartite modules | bipartite edge list | source/target community membership |

---

## 9. 怎麼決定該用哪一個

如果你只有 expression，想看 genes 是否一起變動：

```text
Expression -> Co-expression
```

如果你有 expression、TF motif、PPI，想推 TF-gene regulatory network：

```text
Expression + motif + PPI -> PANDA
```

如果你還有 miRNA prior，想把 miRNA 也放進 regulatory network：

```text
Expression + TF/miRNA prior + PPI + miRNA list -> PUMA
```

如果你想看每個 sample 的 network 差異：

```text
Expression + PANDA/PUMA/coexpression -> LIONESS
```

如果你已經有一個 regulator-gene network，想找模組：

```text
PANDA/PUMA output -> CONDOR
```

---

## 10. 一條完整可講的故事

可以在 demo 或報告時這樣講：

> 我們一開始有 expression matrix，代表每個 gene 在不同 samples 裡的表現量。  
> 但 expression 本身只是觀察資料，不能直接告訴我們誰調控誰。  
> 所以如果要推 transcription factor 到 gene 的調控關係，我們用 PANDA，把 expression、motif prior 和 PPI 合在一起。  
> motif prior 告訴我們 TF 理論上可能 bind 哪些 genes，PPI 告訴我們 TF 之間是否有 protein interaction 或功能關係，expression 則提供 genes 在 samples 裡的實際變化模式。  
> PANDA 會整合這三種證據，輸出 TF-gene edge scores。  
> 如果我們還想加入 miRNA，就用 PUMA，因為 PUMA 可以把 TF 和 miRNA 都視為 regulators，一起推 regulator-gene network。  
> 如果我們不只想要整體 network，而是想知道每個 sample 自己的 network，就用 LIONESS。LIONESS 會用 PANDA、PUMA 或 coexpression 當 base method，估計每個 sample 對每條 edge 的貢獻。  
> 最後，如果我們已經有 regulator-gene 的 bipartite network，想找哪些 regulators 和 genes 組成共同模組，就可以用 CONDOR 做 bipartite community detection。

---

## 11. 最容易混淆的地方

### 1. Expression 不是 network

Expression 是 gene x sample 的原始表格。  
PANDA / PUMA / coexpression 才會把它變成 network。

### 2. Co-expression 不是調控關係

Co-expression 只代表 genes 表現模式相似。  
它不能直接證明 A gene 調控 B gene。

### 3. PANDA 的 PPI 不是 target gene 之間的關係

PANDA 裡的 PPI 是 TF-TF 關係。  
它用來描述 regulators 之間是否有 protein interaction 或功能相關。

### 4. PUMA 不是取代 PANDA，而是擴充 regulator 類型

PANDA 偏 TF-gene。  
PUMA 可以放入 TF 和 miRNA。

### 5. LIONESS output 裡的 `1 2 3 4` 是 sample index

例如：

```text
gene1   gene2   1       2       3       4
GeneA   GeneB  -0.768  -0.871  -0.856  -0.853
```

這裡的 `1 2 3 4` 是第 1、2、3、4 個 sample。  
下面的數值是每個 sample 對這條 edge 的 sample-specific score。

### 6. CONDOR 不負責推 network

CONDOR 是拿已經存在的 bipartite network 去找 communities。  
它比較像是 network 後處理或模組分析。

---

## 12. 最短記憶版

```text
Expression:
  gene 在每個 sample 的表現量，原始資料，不是 network。

Co-expression:
  用 expression 算 gene-gene correlation，只能說一起變動。

PANDA:
  expression + motif + PPI -> TF-gene regulatory network。

PUMA:
  expression + TF/miRNA prior + PPI + miRNA list -> TF/miRNA-gene regulatory network。

LIONESS:
  用 PANDA/PUMA/coexpression 當 base method -> 每個 sample 的 network。

CONDOR:
  bipartite edge list -> regulator/gene modules。
```

---

## 13. Demo 時可以用的順序

推薦 demo 順序：

1. 先展示 expression input。
2. 說明 annotation / CSV / TSV 需要先被清理成工具可讀格式。
3. 跑 PANDA，展示 TF-gene output。
4. 跑 PUMA，展示多了 miRNA regulator。
5. 跑 LIONESS PANDA 或 LIONESS PUMA，展示 sample-specific edge scores。
6. 跑 CONDOR，展示 regulator 和 target genes 被分到 modules。

這樣講會很順，因為它符合資料分析的自然邏輯：

```text
raw expression
-> cleaned compatible input
-> inferred regulatory network
-> sample-specific networks
-> network modules
```

