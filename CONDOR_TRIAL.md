# CONDOR toy 試跑紀錄

日期：2026-07-07

## 這次的判斷

CONDOR 用於 bipartite network community detection，因此 trial input 準備成
source-target-weight edge list。這和 PANDA/PUMA 的 expression、motif、PPI
不同；CONDOR 不需要 expression matrix。

## 輸入

Toy data 位於 [data/condor-toy/bipartite.tsv](data/condor-toy/bipartite.tsv)：

- source：TF-like regulator
- target：gene
- weight：edge weight

檔案前面保留兩行 `#` annotation，用來測試 wrapper 會略過前置註解列。

## 重跑

```bash
docker compose build

docker compose run --rm netzoo run-condor \
  -i data/condor-toy/bipartite.tsv \
  -o outputs/condor-toy \
  --prefix toy
```

## 實跑結果

`docker compose run --rm netzoo run-condor ...` 已成功完成。Toy network 結果：

- edges：8
- source nodes：4
- target nodes：6
- modularity：0.5383873456790124
- Qcoms：`[0.16319444 0.10609568 0.16493056 0.10416667]`

輸出：

- `outputs/condor-toy/toy-edges.tsv`
- `outputs/condor-toy/toy-reg_memb.tsv`
- `outputs/condor-toy/toy-tar_memb.tsv`
- `outputs/condor-toy/toy-summary.txt`
