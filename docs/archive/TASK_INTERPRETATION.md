# 歷史文件：Task 整理


## 1. PANDA / PUMA 了解 input 跟 output

意思不是只知道 `-e -m -p -i -o` 是什麼，而是要能講清楚：

| 工具 | Input | Output |
|---|---|---|
| PANDA | expression matrix、motif prior、PPI network | TF-gene regulatory network |
| PUMA | expression matrix、TF/miRNA-gene prior、PPI network、miRNA 名稱清單 | TF/miRNA-gene regulatory network |

已完成文件：

- [PANDA_PUMA_Docker_入門.md](PANDA_PUMA_Docker_入門.md)

## 2. PANDA / PUMA 建立 Dockerfile

意思是要讓別人不用在自己電腦手動裝 Python、netZooPy、依賴套件，就可以重建同一個環境。

已完成檔案：

- [Dockerfile](Dockerfile)
- [environment.yml](environment.yml)
- [docker-compose.yml](docker-compose.yml)
- [docker/run-panda](docker/run-panda)
- [docker/run-puma](docker/run-puma)

使用者只要：

```bash
docker compose build
docker compose run --rm netzoo
```

就可以進入已安裝好 netZooPy 的環境。

## 3. 寫 Python Script，用 LLM 決定工具

老師說的「實作 LangChain, LangGraph，使用者講我要做什麼事，LLM 要選擇對的工具來 call 他，用 OpenRouter，可以順便執行」大概是：

> 做一個簡單 agent。使用者用自然語言描述任務，LLM 判斷要跑 PANDA、PUMA、只解釋格式、檢查 input，或什麼都不執行。

已完成檔案：

- [scripts/netzoo_agent.py](scripts/netzoo_agent.py)
- [AGENT_USAGE.md](AGENT_USAGE.md)
- [.env.example](.env.example)

## 目前仍需要你確認的事

### Pull request 要送去哪裡

目前這個資料夾的 git repository root 是你的家目錄：

```text
/Users/chenzhonghan
```

這代表它不是一個乾淨的專案 repo，不能直接安全地 commit/push。不然可能會把很多個人檔案一起出現在 git status 裡。

你需要確認老師要你 PR 到哪個 GitHub repo，例如：

```text
https://github.com/your-lab/your-project.git
```

確認後可以把這些檔案複製到正確 repo，再開 branch、commit、push、送 PR。

## 建議 PR 內容

PR title：

```text
Add Dockerized PANDA/PUMA workflow and LangGraph agent
```

PR summary：

```text
- Document PANDA/PUMA input and output formats.
- Add Docker environment for netZooPy PANDA/PUMA execution.
- Add LangChain/LangGraph agent using OpenRouter to select explain/inspect/run tools.
- Add usage documentation for Docker and the agent.
```
