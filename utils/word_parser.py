# utils/word_parser.py
"""
Парсер Word-файлов для загрузки тестов.
Поддерживает форматы:
1. Таблица (question, type, points, options)
2. Текстовый формат с вариантами ответов (A), B), C), D))
"""
import re
from typing import List, Dict, Optional
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph


class QuestionData:
    """Класс для хранения данных вопроса."""
    
    def __init__(self, text: str, question_type: str = 'single', points: float = 1.0):
        self.text = text
        self.question_type = question_type
        self.points = points
        self.options: List[Dict[str, any]] = []
    
    def add_option(self, text: str, is_correct: bool = False):
        """Добавить вариант ответа."""
        self.options.append({
            'text': text,
            'is_correct': is_correct
        })
    
    def to_dict(self):
        """Преобразовать в словарь."""
        return {
            'question': self.text,
            'type': self.question_type,
            'points': self.points,
            'options': self.options
        }


class WordTestParser:
    """Парсер для обработки Word-документов с тестами."""
    
    @staticmethod
    def detect_format(doc: DocxDocument) -> str:
        """Определить формат документа: 'table' или 'text'."""
        if doc.tables:
            return 'table'
        
        # Проверяем наличие текстовых паттернов (вопросы с вариантами A), B), C))
        full_text = '\n'.join([p.text for p in doc.paragraphs])
        if re.search(r'^[A-Z]\)', full_text, re.MULTILINE):
            return 'text'
        
        return 'text'  # По умолчанию текстовый формат
    
    @staticmethod
    def parse_text_format(doc: DocxDocument) -> List[QuestionData]:
        """
        Парсить текстовый формат с вариантами ответов.
        
        Ожидаемый формат:
        Текст вопроса?
        A) Вариант A
        B) Вариант B
        C) Вариант C [*] - или просто * для обозначения правильного
        D) Вариант D
        
        Тип: single (по умолчанию) или multiple
        Баллы: 1 (по умолчанию)
        ---
        """
        questions = []
        current_question = None
        current_text_lines = []
        
        i = 0
        paragraphs = doc.paragraphs
        
        while i < len(paragraphs):
            para = paragraphs[i]
            text = para.text.strip()
            
            if not text:
                i += 1
                continue
            
            # Разделитель между вопросами
            if text in ('---', '---', '___') or text.startswith('---'):
                if current_question is not None:
                    # Сохраняем предыдущий вопрос
                    current_question.text = '\n'.join(current_text_lines).strip()
                    if current_question.options:
                        questions.append(current_question)
                current_question = None
                current_text_lines = []
                i += 1
                continue
            
            # Проверяем, это ли вариант ответа (A), B), C), D), и т.д.)
            match = re.match(r'^([A-Z])\)\s*(.*?)(\s*\[\*\]|\s*\*)?$', text)
            
            if match:
                if current_question is None:
                    # Начинаем новый вопрос с первого варианта
                    current_question = QuestionData('')
                    current_text_lines = []
                
                letter = match.group(1)
                option_text = match.group(2).strip()
                is_correct_marker = match.group(3)
                is_correct = bool(is_correct_marker and '*' in is_correct_marker)
                
                current_question.add_option(option_text, is_correct)
            else:
                # Это текст вопроса или метаинформация
                if current_question is not None:
                    # Уже есть вопрос - значит это новый вопрос
                    current_question.text = '\n'.join(current_text_lines).strip()
                    if current_question.options:
                        questions.append(current_question)
                    current_question = None
                    current_text_lines = []
                
                # Проверяем метаинформацию
                if text.lower().startswith('тип:'):
                    if current_question:
                        q_type = text.split(':')[1].strip().lower()
                        if q_type in ('single', 'multiple', 'text'):
                            current_question.question_type = q_type
                elif text.lower().startswith('баллы:') or text.lower().startswith('балл:'):
                    if current_question:
                        try:
                            points = float(text.split(':')[1].strip())
                            current_question.points = points
                        except (ValueError, IndexError):
                            pass
                else:
                    current_text_lines.append(text)
            
            i += 1
        
        # Сохраняем последний вопрос
        if current_question is not None:
            current_question.text = '\n'.join(current_text_lines).strip()
            if current_question.options and current_question.text:
                questions.append(current_question)
        
        return questions
    
    @staticmethod
    def parse_table_format(table: Table) -> List[QuestionData]:
        """Парсить формат таблицы."""
        questions = []
        
        if len(table.rows) < 2:
            return questions
        
        # Извлекаем заголовки
        headers = [cell.text.strip().lower() for cell in table.rows[0].cells]
        
        if 'question' not in headers:
            return questions
        
        # Обрабатываем строки таблицы
        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            
            if not any(cells):  # Пустая строка
                continue
            
            row_dict = {}
            for i in range(min(len(headers), len(cells))):
                row_dict[headers[i]] = cells[i]
            
            q_text = row_dict.get('question', '').strip()
            if not q_text:
                continue
            
            q_type = row_dict.get('type', 'single').strip().lower()
            if q_type not in ('single', 'multiple', 'text'):
                q_type = 'single'
            
            try:
                points = float(row_dict.get('points', 1))
            except (ValueError, TypeError):
                points = 1.0
            
            question = QuestionData(q_text, q_type, points)
            
            # Обрабатываем варианты ответов
            options_raw = row_dict.get('options', '')
            for opt in options_raw.split('||'):
                opt = opt.strip()
                if not opt:
                    continue
                is_correct = False
                if opt.startswith('*'):
                    is_correct = True
                    opt_text = opt.lstrip('*').strip()
                else:
                    opt_text = opt
                question.add_option(opt_text, is_correct)
            
            if question.options or q_type == 'text':
                questions.append(question)
        
        return questions
    
    @staticmethod
    def parse_document(doc: DocxDocument) -> List[QuestionData]:
        """
        Автоматически определить формат и парсить документ.
        
        Возвращает список объектов QuestionData.
        """
        # Сначала проверяем таблицы
        if doc.tables:
            questions = WordTestParser.parse_table_format(doc.tables[0])
            if questions:
                return questions
        
        # Если таблиц нет или они пусты, парсим текстовый формат
        return WordTestParser.parse_text_format(doc)
