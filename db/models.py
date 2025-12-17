# db/models.py
"""
Модели базы данных для бота тестирования.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

Base = declarative_base()


class User(Base, AsyncAttrs):
    """Модель пользователя."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=True)
    name = Column(String(100))
    age = Column(Integer, nullable=True)
    phone = Column(String(20), unique=True)
    photo = Column(String(500), nullable=True)
    document = Column(String(500), nullable=True)
    # language can be unset initially; default is None so bot can ask user to choose on first start
    language = Column(String(2), nullable=True, default=None)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    test_results = relationship("TestResult", back_populates="user")
    # enrolled_courses removed — courses feature deprecated


# Course and CourseEnrollment removed — courses feature deprecated


class Test(Base, AsyncAttrs):
    """Модель теста."""
    __tablename__ = 'tests'
    
    id = Column(Integer, primary_key=True)
    # course_id removed — tests are no longer tied to courses
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    total_questions = Column(Integer, default=50)
    max_score = Column(Integer, default=100)
    time_limit = Column(Integer, nullable=True)  # в минутах
    scheduled_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    # course relationship removed
    questions = relationship("Question", back_populates="test")
    results = relationship("TestResult", back_populates="test")


class Question(Base, AsyncAttrs):
    """Модель вопроса теста."""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('tests.id'))
    text = Column(Text, nullable=False)
    question_type = Column(String(20), default='single')  # single, multiple, text
    points = Column(Float, default=2.0)
    order_num = Column(Integer, default=0)
    
    # Отношения
    test = relationship("Test", back_populates="questions")
    options = relationship("Option", back_populates="question")


class Option(Base, AsyncAttrs):
    """Модель варианта ответа."""
    __tablename__ = 'options'
    
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    # Отношения
    question = relationship("Question", back_populates="options")


class TestResult(Base, AsyncAttrs):
    """Модель результата теста."""
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    test_id = Column(Integer, ForeignKey('tests.id'))
    score = Column(Float, default=0)
    max_score = Column(Integer, default=100)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    answers_data = Column(Text, nullable=True)  # JSON данные ответов
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="test_results")
    test = relationship("Test", back_populates="results")
