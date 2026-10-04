from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(300), nullable=False)
    stream = Column(String(100), default="")
    student_class = Column(String(20), default="12")
    reward_points = Column(Integer, default=0)
    current_tier = Column(Integer, default=1)
    tier_progress = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON list of 4 strings
    answer = Column(Integer, nullable=False)  # index 0-3
    subject = Column(String(100), nullable=False, index=True)
    stream = Column(String(100), nullable=False, index=True)
    topic = Column(String(150), default="")
    difficulty = Column(String(20), default="medium", index=True)
    expected_time = Column(Integer, default=20)
    explanation = Column(Text, default="")
    hint = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    quiz_id = Column(String(50), index=True, default="")
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_answer = Column(Integer, default=-1)
    correct = Column(Boolean, default=False)
    response_time = Column(Float, default=0.0)
    difficulty = Column(String(20), default="medium")
    subject = Column(String(100), default="")
    topic = Column(String(150), default="")
    reward_earned = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="attempts")


class Mistake(Base):
    __tablename__ = "mistakes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_answer = Column(Integer, default=-1)
    understood = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
