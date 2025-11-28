# Спека 04: Обновление Правил в .agent/rules/

## Цель
Обновить правила в `.agent/rules/` после спек 01-03 с учётом best practices Antigravity IDE.

## Часть 1: Изучение (обязательно!)

### Изучить Проект
- `.agent/rules/` (все файлы), `specs/` (все файлы)
- `AGENTS.md`, `docs/requirements/`, `docs/architecture/`, `docs/antigravity-rules-reglament.md`

### Изучить Best Practices Antigravity IDE
Ресурсы:
- antigravity.im (документация)
- https://codelabs.developers.google.com/getting-started-google-antigravity#6
- YouTube: "Google Antigravity IDE rules"

Принципы Antigravity:
- Чёткость, модульность, ≤50 строк, русский язык

## Часть 2: Создание Правил

### Запрет Прямого Изменения
**ЗАПРЕЩЕНО** редактировать `.agent/rules/` напрямую!

### Создать Папку
```bash
mkdir -p .antigravity/tmp_rules/
```

### Создать Файлы (в .antigravity/tmp_rules/)

**`00-rules-about-rules.md`** (≤50 строк): Best practices из Antigravity.
**`01-project-overview.md`** (≤50 строк): Убрать ChromaDB, FastAPI, Streamlit, CLI, QA Agent.
**`02-architecture.md`** (≤50 строк): Телеграм Бот + AI Core, SQLite
- если посчитаешь нужным, то можешь и другие правила обновить

### Скрипт
`.antigravity/tmp_rules/apply_rules.sh`:
```bash
#!/bin/bash
echo "🔄 Применение правил"
read -p "Продолжить? (yes/no): " c
[ "$c" != "yes" ] && echo "❌ Отменено" && exit 1
cp .antigravity/tmp_rules/*.md .agent/rules/ && echo "✅ Готово!"
```
Chmod: `chmod +x .antigravity/tmp_rules/apply_rules.sh`
