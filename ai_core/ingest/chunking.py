"""
Модуль для разбиения текста на чанки.
Простая реализация без LangChain для MVP.
"""
from typing import List


def recursive_character_split(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: List[str] = None
) -> List[str]:
    """
    Разбивает текст на чанки с перекрытием.
    
    Args:
        text: Исходный текст
        chunk_size: Размер чанка в символах
        chunk_overlap: Перекрытие между чанками
        separators: Разделители (по умолчанию: параграфы, переносы строк, пробелы)
    
    Returns:
        Список чанков
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    chunks = []
    
    # Рекурсивно разбиваем текст по разделителям
    def _split_text(text: str, seps: List[str]) -> List[str]:
        if not seps:
            # Если разделителей не осталось, разбиваем по символам
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
        
        separator = seps[0]
        remaining_seps = seps[1:]
        
        if not separator:
            # Пустой разделитель - разбиваем по символам
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
        
        splits = text.split(separator)
        result = []
        current_chunk = ""
        
        for split in splits:
            # Если сплит сам по себе больше chunk_size, рекурсивно разбиваем его
            if len(split) > chunk_size:
                if current_chunk:
                    result.append(current_chunk)
                    current_chunk = ""
                result.extend(_split_text(split, remaining_seps))
            elif len(current_chunk) + len(split) + len(separator) > chunk_size:
                # Текущий чанк полон, сохраняем и начинаем новый
                if current_chunk:
                    result.append(current_chunk)
                current_chunk = split
            else:
                # Добавляем к текущему чанку
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
        
        if current_chunk:
            result.append(current_chunk)
        
        return result
    
    # Разбиваем текст
    raw_chunks = _split_text(text, separators)
    
    # Добавляем перекрытие
    for i, chunk in enumerate(raw_chunks):
        if i > 0 and chunk_overlap > 0:
            # Берем последние chunk_overlap символов из предыдущего чанка
            prev_chunk = raw_chunks[i - 1]
            overlap = prev_chunk[-chunk_overlap:] if len(prev_chunk) >= chunk_overlap else prev_chunk
            chunk = overlap + " " + chunk
        
        chunks.append(chunk.strip())
    
    return [c for c in chunks if c]  # Убираем пустые чанки
