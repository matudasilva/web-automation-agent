.PHONY: codex-log test-log snapshot

codex-log:
	./scripts/codex_logged.sh
#command: make codex-log

test-log:
	./scripts/run_logged.sh pytest -q

snapshot:
	./scripts/project_snapshot.sh

# after close an important blok execute on terminal
# make snapshot && make test-log