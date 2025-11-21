#!/usr/bin/env python3
"""
Скрипт для полной очистки всех баз данных.
Очищает SQLite БД и ChromaDB векторное хранилище.
"""
import sys
import os
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.common.config import settings

def clear_databases():
    """Очищает SQLite и ChromaDB."""
    
    # 1. Очистка SQLite БД
    db_path = settings.DB_PATH
    if os.path.exists(db_path):
        print(f"Удаляю SQLite БД: {db_path}")
        os.remove(db_path)
        print("✅ SQLite БД удалена")
    else:
        print(f"⚠️  SQLite БД не найдена: {db_path}")
    
    # 2. Очистка ChromaDB
    chroma_path = settings.CHROMA_PATH
    if os.path.exists(chroma_path):
        print(f"Удаляю ChromaDB: {chroma_path}")
        shutil.rmtree(chroma_path)
        print("✅ ChromaDB удалена")
    else:
        print(f"⚠️  ChromaDB не найдена: {chroma_path}")
    
    # 3. Очистка медиа файлов (опционально)
    media_path = settings.MEDIA_PATH
    if os.path.exists(media_path):
        response = input(f"\n⚠️  Также удалить медиа файлы из {media_path}? (y/N): ")
        if response.lower() == 'y':
            print(f"Удаляю медиа файлы: {media_path}")
            shutil.rmtree(media_path)
            os.makedirs(media_path, exist_ok=True)
            print("✅ Медиа файлы удалены")
        else:
            print("⏭️  Медиа файлы сохранены")
    
    print("\n✅ Очистка завершена!")
    print("Теперь перезапусти API и бота для создания новых БД.")

if __name__ == "__main__":
    print("🗑️  Скрипт очистки баз данных\n")
    print("ВНИМАНИЕ: Это удалит ВСЕ данные!")
    print(f"  - SQLite БД: {settings.DB_PATH}")
    print(f"  - ChromaDB: {settings.CHROMA_PATH}")
    
    confirm = input("\nПродолжить? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_databases()
    else:
        print("❌ Отменено")
