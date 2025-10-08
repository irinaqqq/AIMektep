from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, JSON, ARRAY,
    Float, SmallInteger, Index, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.orm import relationship

from core.database import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(32), unique=True, nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company_id = Column(Integer, nullable=True)
    role = Column(String(32), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    materials = relationship("Material", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("QuizSubmission", back_populates="user", cascade="all, delete-orphan")
    mastery = relationship("UserSkillMastery", back_populates="user", cascade="all, delete-orphan")
    review_cards = relationship("ReviewCard", back_populates="user", cascade="all, delete-orphan")
    events = relationship("ProgressEvent", back_populates="user", cascade="all, delete-orphan")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="materials")
    summary = relationship("Summary", back_populates="material", uselist=False, cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="material", uselist=False, cascade="all, delete-orphan")
    review_cards = relationship("ReviewCard", back_populates="material", cascade="all, delete-orphan")
    events = relationship("ProgressEvent", back_populates="material", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_materials_user", "user_id"),
    )


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    material = relationship("Material", back_populates="summary")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), unique=True, nullable=False)
    question_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    material = relationship("Material", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    submissions = relationship("QuizSubmission", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # ["A","B","C","D"]
    correct_index = Column(Integer, nullable=False)
    difficulty = Column(String(10), nullable=False, default="medium")
    tags = Column(ARRAY(Text), nullable=False, server_default="{}")
    bloom = Column(String(16), nullable=False, default="understand")
    hints = Column(JSON, nullable=False, server_default="[]")
    rationales = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quiz = relationship("Quiz", back_populates="questions")

    __table_args__ = (
        Index("idx_qq_quiz_id", "quiz_id"),
    )


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    answers = Column(JSON, nullable=False)
    calibration = Column(JSON)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quiz = relationship("Quiz", back_populates="submissions")
    user = relationship("User", back_populates="submissions")

    __table_args__ = (
        Index("idx_qs_user", "user_id"),
        Index("idx_qs_quiz", "quiz_id"),
        # UniqueConstraint("quiz_id", "user_id", name="uq_quiz_user")  # если одна попытка на пользователя
    )


class UserSkillMastery(Base):
    __tablename__ = "user_skill_mastery"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tag = Column(Text, primary_key=True)
    mastery = Column(Float, nullable=False, default=0.5)

    user = relationship("User", back_populates="mastery")

    __table_args__ = (
        CheckConstraint("mastery >= 0 AND mastery <= 1", name="ck_mastery_range"),
    )


class ReviewCard(Base):
    __tablename__ = "review_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    tag = Column(Text)
    prompt = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    next_review_at = Column(DateTime(timezone=True), nullable=False)
    ease = Column(SmallInteger, nullable=False, default=2)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="review_cards")
    material = relationship("Material", back_populates="review_cards")


class ProgressEvent(Base):
    __tablename__ = "progress_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"))
    event_type = Column(String(50), nullable=False)
    details = Column(JSON, nullable=False, server_default="{}")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="events")
    material = relationship("Material", back_populates="events")

    __table_args__ = (
        Index("idx_pe_user", "user_id"),
    )
