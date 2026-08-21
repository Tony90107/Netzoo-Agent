# Historical Snapshot: Pull Request Draft

## Title

Add Dockerized PANDA/PUMA workflow and LangGraph agent

## Summary

- Document PANDA/PUMA input and output formats.
- Add Docker environment for running netZooPy PANDA and PUMA.
- Add wrapper commands `run-panda` and `run-puma`.
- Add LangChain/LangGraph agent using OpenRouter for tool selection.
- Add docs explaining Docker, expression preprocessing, and usage examples.

## Files Added / Changed

- `README.md`
- `Dockerfile`
- `environment.yml`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `docker/run-panda`
- `docker/run-puma`
- `scripts/netzoo_agent.py`
- `PANDA_PUMA_Docker_入門.md`
- `AGENT_USAGE.md`
- `TASK_INTERPRETATION.md`
- `NetworkZoo_工具導覽.md`
- `data/.gitkeep`
- `outputs/.gitkeep`

## Validation

```bash
docker compose build
docker compose run --rm netzoo netzoopy --help
docker compose run --rm netzoo run-panda --help
docker compose run --rm netzoo run-puma --help
docker compose run --rm netzoo python scripts/netzoo_agent.py --help
```

Also validated PANDA and PUMA with official netZooPy toy data:

```bash
docker compose run --rm netzoo run-panda \
  -e /opt/netZooPy/tests/puma/ToyData/ToyExpressionData.txt \
  -m /opt/netZooPy/tests/puma/ToyData/ToyMotifData.txt \
  -p /opt/netZooPy/tests/puma/ToyData/ToyPPIData.txt \
  -o /tmp/smoke_panda.txt \
  --old_compatible

docker compose run --rm netzoo run-puma \
  -e /opt/netZooPy/tests/puma/ToyData/ToyExpressionData.txt \
  -m /opt/netZooPy/tests/puma/ToyData/ToyMotifData.txt \
  -p /opt/netZooPy/tests/puma/ToyData/ToyPPIData.txt \
  -i /opt/netZooPy/tests/puma/ToyData/ToyMiRList.txt \
  -o /tmp/smoke_puma.txt
```

## Notes

- `setuptools<81` is pinned because `netZooPy` currently imports `pkg_resources`.
- The LangGraph agent defaults to dry-run mode. Add `--execute` to actually run PANDA/PUMA.
- A real OpenRouter API key is required to use the LLM agent.
