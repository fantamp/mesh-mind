.PHONY: api bot install test ui adk-web

api:
	uvicorn ai_core.api.main:app --reload

ui:
	streamlit run ai_core/ui/main.py

bot:
	python telegram_bot/main.py

install:
	pip install -r requirements.txt

test:
	pytest

adk-web:
	cd ai_core/agents && adk web
