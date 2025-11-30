.PHONY: bot
bot:
	python -m telegram_bot.main

.PHONY: bot-tmux
bot-tmux:
	./run_forever.sh 2>&1 | tee -a mesh-mind.log

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	pytest

.PHONY: adk-web
adk-web:
	cd ai_core/agents && PYTHONPATH=$(shell pwd) adk web

.PHONY: demo
demo:
	@echo "Running Multi-Agent Demo..."
	python scripts/demo/demo_agents.py

.PHONY: eval
eval:
	@python scripts/run_all_evals.py

.PHONY: get-prod-db
get-prod-db:
	ssh vp "sudo -u mesh_mind tar -C /home/mesh_mind/mesh-mind/data/db -cf - mesh_mind.db" | tar -C ./data/db -xf -
