.PHONY: api bot install test

api:
	uvicorn ai_core.api.main:app --reload

bot:
	python telegram_bot/bot.py

install:
	pip install -r requirements.txt

test:
	pytest
