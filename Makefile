REMOTE_USER_FILE := .get_prod_db_user

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
	@REMOTE_USER_FILE="$(REMOTE_USER_FILE)"; \
	STORED_USER=""; \
	[ -f $$REMOTE_USER_FILE ] && STORED_USER=$$(cat $$REMOTE_USER_FILE); \
	SHOULD_SAVE=0; \
	if [ -n "$$STORED_USER" ]; then \
		printf "Use stored remote username '$$STORED_USER'? [Y/n]: "; \
		read USE_STORED; \
		case $$USE_STORED in \
			n*|N*) \
				printf "Remote username: "; \
				read REMOTE_USER; \
				SHOULD_SAVE=1; \
				;; \
			*) \
				REMOTE_USER=$$STORED_USER; \
				;; \
		esac; \
	else \
		printf "Remote username: "; \
		read REMOTE_USER; \
		SHOULD_SAVE=1; \
	fi; \
	test -n "$$REMOTE_USER" || (echo "Remote username is required." && exit 1); \
	if [ "$$SHOULD_SAVE" = "1" ]; then \
		echo "$$REMOTE_USER" > $$REMOTE_USER_FILE; \
	fi; \
	ssh vp "sudo -u $$REMOTE_USER tar -C /home/$$REMOTE_USER/mesh-mind/data/db -cf - mesh_mind.db" | tar -C ./data/db -xf -
