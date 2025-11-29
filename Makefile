.PHONY: api bot install test ui adk-web eval


bot:
	python -m telegram_bot.main

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

# Универсальный запуск eval: make eval AGENT=chat_observer
# Для других агентов добавьте свою ветку ниже с seed/eval/summary
eval:
	@if [ "$(AGENT)" = "chat_observer" ]; then \
		PYTHONPATH=$(shell pwd) ./venv/bin/python tests/agents/eval/seed_eval_db.py; \
		log=/tmp/adk_eval_$(AGENT).log; \
		echo "Запускаю adk eval (лог: $$log)..."; \
		PYTHONPATH=$(shell pwd) GEMINI_MODEL_SMART=gemini-2.5-flash-lite ./venv/bin/adk eval ai_core/agents/chat_observer tests/agents/eval/chat_observer/fetch_messages_eval.evalset.json --config_file_path tests/agents/eval/chat_observer/test_config.json > $$log 2>&1 || (echo "❌ adk eval упал, см. $$log"; tail -n 40 $$log; exit 1); \
		PYTHONPATH=$(shell pwd) ./venv/bin/python scripts/adk_eval_utils/adk_eval_summary.py --agent chat_observer --history-dir ai_core/agents/chat_observer/.adk/eval_history --eval-set chat_observer_fetch_messages_v1; \
	elif [ "$(AGENT)" = "qa" ]; then \
		PYTHONPATH=$(shell pwd) ./venv/bin/python tests/agents/eval/seed_eval_db.py; \
		log=/tmp/adk_eval_$(AGENT).log; \
		echo "Запускаю adk eval (лог: $$log)..."; \
		PYTHONPATH=$(shell pwd) GEMINI_MODEL_SMART=gemini-2.5-flash-lite ./venv/bin/adk eval ai_core/agents/qa tests/agents/eval/qa/qa_eval.evalset.json --config_file_path tests/agents/eval/qa/test_config.json > $$log 2>&1 || (echo "❌ adk eval упал, см. $$log"; tail -n 40 $$log; exit 1); \
		PYTHONPATH=$(shell pwd) ./venv/bin/python scripts/adk_eval_utils/adk_eval_summary.py --agent qa --history-dir ai_core/agents/qa/.adk/eval_history --eval-set qa_eval_v1; \
	elif [ "$(AGENT)" = "chat_summarizer" ]; then \
		PYTHONPATH=$(shell pwd) ./venv/bin/python tests/agents/eval/seed_eval_db.py; \
		log=/tmp/adk_eval_$(AGENT).log; \
		echo "Запускаю adk eval (лог: $$log)..."; \
		PYTHONPATH=$(shell pwd) GEMINI_MODEL_SMART=gemini-2.5-flash-lite ./venv/bin/adk eval ai_core/agents/chat_summarizer tests/agents/eval/chat_summarizer/chat_summarizer_eval.evalset.json --config_file_path tests/agents/eval/chat_summarizer/test_config.json > $$log 2>&1 || (echo "❌ adk eval упал, см. $$log"; tail -n 40 $$log; exit 1); \
		PYTHONPATH=$(shell pwd) ./venv/bin/python scripts/adk_eval_utils/adk_eval_summary.py --agent chat_summarizer --history-dir ai_core/agents/chat_summarizer/.adk/eval_history --eval-set chat_summarizer_eval_v1; \
	elif [ "$(AGENT)" = "orchestrator" ]; then \
		PYTHONPATH=$(shell pwd) ./venv/bin/python tests/agents/eval/seed_eval_db.py; \
		log=/tmp/adk_eval_$(AGENT).log; \
		echo "Запускаю adk eval (лог: $$log)..."; \
		PYTHONPATH=$(shell pwd) GEMINI_MODEL_SMART=gemini-2.5-flash-lite ./venv/bin/adk eval ai_core/agents/orchestrator tests/agents/eval/orchestrator/orchestrator_eval.evalset.json --config_file_path tests/agents/eval/orchestrator/test_config.json > $$log 2>&1 || (echo "❌ adk eval упал, см. $$log"; tail -n 40 $$log; exit 1); \
		PYTHONPATH=$(shell pwd) ./venv/bin/python scripts/adk_eval_utils/adk_eval_summary.py --agent orchestrator --history-dir ai_core/agents/orchestrator/.adk/eval_history --eval-set orchestrator_eval_v1; \
	elif [ "$(AGENT)" = "summarizer" ]; then \
		PYTHONPATH=$(shell pwd) ./venv/bin/python tests/agents/eval/seed_eval_db.py; \
		log=/tmp/adk_eval_$(AGENT).log; \
		echo "Запускаю adk eval (лог: $$log)..."; \
		PYTHONPATH=$(shell pwd) GEMINI_MODEL_SMART=gemini-2.5-flash-lite ./venv/bin/adk eval ai_core/agents/summarizer tests/agents/eval/summarizer/summarizer_eval.evalset.json --config_file_path tests/agents/eval/summarizer/test_config.json > $$log 2>&1 || (echo "❌ adk eval упал, см. $$log"; tail -n 40 $$log; exit 1); \
		PYTHONPATH=$(shell pwd) ./venv/bin/python scripts/adk_eval_utils/adk_eval_summary.py --agent summarizer --history-dir ai_core/agents/summarizer/.adk/eval_history --eval-set summarizer_eval_v1; \
	else \
		echo "AGENT=$(AGENT) не поддержан в Makefile. Добавьте ветку в цели eval."; \
		exit 1; \
	fi
