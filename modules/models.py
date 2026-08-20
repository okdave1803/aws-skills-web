"""AWS Skills - SQLAlchemy ORM モデル定義

ユーザー、結果、学習時間などをデータベースで管理する。
SQLite（開発）と PostgreSQL（本番）の両対応。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    Boolean, JSON, ForeignKey, Table, UniqueConstraint,
    Index, create_engine, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

Base = declarative_base()


# --- ユーザーテーブル -----------------------------------------------


class User(Base):
    """ユーザーマスター。"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    
    exam_code = Column(String(10), default="SAA-C03")  # 目標試験コード
    exam_date = Column(String(10), nullable=True)
    
    badges = Column(JSON, default=list)  # バッジリスト
    achievements = Column(JSON, default=list)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # 関連テーブル
    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    study_logs = relationship("StudyLog", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_username_active", "username", "is_active"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, level={self.level})>"


# --- クイズ結果テーブル -----------------------------------------------


class QuizResult(Base):
    """クイズ・試験の結果を記録。"""
    
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    question_id = Column(Integer, nullable=False)  # questions.json の id
    quiz_mode = Column(String(20), nullable=False)  # "study" or "exam"
    quiz_source = Column(String(50), nullable=False)  # "practice", "mock_exam", etc.
    quiz_title = Column(String(200), nullable=True)
    
    selected_indices = Column(JSON, nullable=True)  # 選択した選択肢のインデックス
    is_correct = Column(Boolean, nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)
    
    exam_code = Column(String(10), nullable=True)  # CLF-C02, SAA-C03, etc.
    category = Column(String(50), nullable=True)  # カテゴリ（弱点分析用）
    domain = Column(String(100), nullable=True)  # 出題分野
    topic = Column(String(100), nullable=True)  # トピック
    difficulty = Column(String(10), nullable=True)  # 基礎/標準/応用/難関
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="quiz_results")
    
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_question", "question_id"),
        Index("idx_category", "category"),
    )
    
    def __repr__(self) -> str:
        return f"<QuizResult(id={self.id}, user_id={self.user_id}, is_correct={self.is_correct})>"


# --- 学習ログテーブル -----------------------------------------------


class StudyLog(Base):
    """学習時間や学習セッションを記録。"""
    
    __tablename__ = "study_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    duration_seconds = Column(Integer, nullable=False)
    category = Column(String(100), nullable=True)  # 学習カテゴリ
    exam_code = Column(String(10), nullable=True)  # 対象試験コード
    
    note = Column(Text, nullable=True)  # メモ
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="study_logs")
    
    __table_args__ = (
        Index("idx_user_date", "user_id", "created_at"),
        Index("idx_date", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<StudyLog(id={self.id}, user_id={self.user_id}, duration={self.duration_seconds}s)>"


# --- セッション管理テーブル -----------------------------------------------


class Session(Base):
    """ユーザーセッション管理（JWT トークンベース）。"""
    
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    token = Column(String(500), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_user_active", "user_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id})>"


# --- 進捗トラッキングテーブル -----------------------------------------------


class Progress(Base):
    """ユーザーの学習進捗を日別に記録（集計用）。"""
    
    __tablename__ = "progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    study_date = Column(DateTime, nullable=False)  # 学習日（日付）
    
    total_studied_seconds = Column(Integer, default=0)
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    accuracy = Column(Float, nullable=True)  # 正答率（%）
    
    streak_days = Column(Integer, default=0)  # 連続学習日数
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "study_date", name="uq_user_date"),
        Index("idx_user_date", "user_id", "study_date"),
    )
    
    def __repr__(self) -> str:
        return f"<Progress(user_id={self.user_id}, accuracy={self.accuracy}%)>"


# --- ユーティリティ関数 -----------------------------------------------


def init_db(database_url: str) -> tuple[None, Session]:
    """データベースを初期化してセッションを返す。
    
    Args:
        database_url: SQLAlchemy データベース URL
        
    Returns:
        (None, Session) のタプル
    """
    engine = create_engine(
        database_url,
        echo=False,  # SQL ログを出力しない（必要に応じて True に）
        pool_pre_ping=True,  # 接続の有効性チェック
    )
    
    # テーブル作成
    Base.metadata.create_all(engine)
    
    # セッション作成
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    return engine, session


def get_session(database_url: str) -> Session:
    """データベースセッションを取得する。
    
    Args:
        database_url: SQLAlchemy データベース URL
        
    Returns:
        データベースセッション
    """
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
