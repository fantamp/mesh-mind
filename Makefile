.PHONY: api bot install test ui adk-web eval


bot:
	python -m telegram_bot.main

bot-tmux:
	python -m telegram_bot.main 2>&1 | tee -a mesh-mind.log

install:
	pip install -r requirements.txt

test:
	pytest

adk-web:
	cd ai_core/agents && PYTHONPATH=$(shell pwd) adk web

.PHONY: demo
demo:
	@echo "Running Multi-Agent Demo..."
	python scripts/demo/demo_agents.py

# Универсальный запуск eval
eval:
	@python scripts/run_all_evals.py
