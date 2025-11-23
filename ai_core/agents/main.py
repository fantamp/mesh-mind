#!/usr/bin/env python3
"""
Пример main.py для тестирования агентов из директории ai_core/agents/

Этот файл добавляет project root в PYTHONPATH, чтобы работали абсолютные импорты.
"""

import sys
from pathlib import Path

# Добавляем project root (mesh-mind) в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Теперь можно импортировать агентов
from ai_core.agents.qa.agent import agent as qa_agent
from ai_core.agents.summarizer.agent import agent as summarizer_agent

def main():
    print("QA Agent loaded:", qa_agent.name)
    print("Summarizer Agent loaded:", summarizer_agent.name)
    
    # Можешь тут тестировать агентов
    # Например:
    from ai_core.services.agent_service import run_qa
    answer = run_qa("What is ADK?", chat_id="test")
    print(answer)

if __name__ == "__main__":
    main()
