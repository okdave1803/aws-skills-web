"""AWS Skills - データアクセスレイヤー（DAL）

ORM モデルを使用したデータベース操作を提供する。
JSON インターフェース（data_manager.py）との互換性を保つ。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from modules.models import User, QuizResult, StudyLog, Progress, Session as DBSession
from modules.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserDAL:
    """ユーザーテーブルの操作を管理する。"""
    
    def __init__(self, session: Session):
        """初期化。
        
        Args:
            session: SQLAlchemy セッション
        """
        self.session = session
    
    def create_user(self, username: str, password: str, email: Optional[str] = None) -> Optional[User]:
        """新規ユーザーを作成する。
        
        Args:
            username: ユーザー名
            password: パスワード（平文）
            email: メールアドレス
            
        Returns:
            作成されたユーザー、またはエラーの場合 None
        """
        try:
            # ユーザー名の重複チェック
            existing = self.session.query(User).filter_by(username=username).first()
            if existing:
                logger.warning(f"ユーザー名が既に存在: {username}")
                return None
            
            # メールアドレスの重複チェック
            if email:
                existing_email = self.session.query(User).filter_by(email=email).first()
                if existing_email:
                    logger.warning(f"メールアドレスが既に存在: {email}")
                    return None
            
            # ユーザー作成
            user = User(
                username=username,
                password_hash=hash_password(password),
                email=email,
            )
            
            self.session.add(user)
            self.session.commit()
            logger.info(f"ユーザー作成成功: {username} (id={user.id})")
            return user
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"ユーザー作成エラー: {str(e)}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """ユーザー名でユーザーを取得する。
        
        Args:
            username: ユーザー名
            
        Returns:
            ユーザー、または見つからない場合 None
        """
        return self.session.query(User).filter_by(username=username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID でユーザーを取得する。
        
        Args:
            user_id: ユーザー ID
            
        Returns:
            ユーザー、または見つからない場合 None
        """
        return self.session.query(User).filter_by(id=user_id).first()
    
    def verify_password(self, user: User, password: str) -> bool:
        """ユーザーのパスワードを検証する。
        
        Args:
            user: ユーザーオブジェクト
            password: パスワード（平文）
            
        Returns:
            一致する場合 True
        """
        return verify_password(password, user.password_hash)
    
    def update_user(self, user: User, **kwargs) -> bool:
        """ユーザー情報を更新する。
        
        Args:
            user: ユーザーオブジェクト
            **kwargs: 更新するフィールド
            
        Returns:
            成功時 True
        """
        try:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.session.commit()
            logger.info(f"ユーザー更新成功: {user.username}")
            return True
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"ユーザー更新エラー: {str(e)}")
            return False
    
    def update_last_login(self, user: User) -> bool:
        """ユーザーのラストログイン時刻を更新する。
        
        Args:
            user: ユーザーオブジェクト
            
        Returns:
            成功時 True
        """
        return self.update_user(user, last_login_at=datetime.utcnow())


class QuizResultDAL:
    """クイズ結果テーブルの操作を管理する。"""
    
    def __init__(self, session: Session):
        """初期化。
        
        Args:
            session: SQLAlchemy セッション
        """
        self.session = session
    
    def create_result(self, user_id: int, **kwargs) -> Optional[QuizResult]:
        """クイズ結果を作成する。
        
        Args:
            user_id: ユーザー ID
            **kwargs: その他のフィールド
            
        Returns:
            作成されたクイズ結果、またはエラーの場合 None
        """
        try:
            result = QuizResult(user_id=user_id, **kwargs)
            self.session.add(result)
            self.session.commit()
            return result
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"クイズ結果作成エラー: {str(e)}")
            return None
    
    def get_user_results(self, user_id: int, limit: int = 100) -> List[QuizResult]:
        """ユーザーのクイズ結果を取得する。
        
        Args:
            user_id: ユーザー ID
            limit: 取得件数の上限
            
        Returns:
            クイズ結果のリスト
        """
        return (
            self.session.query(QuizResult)
            .filter_by(user_id=user_id)
            .order_by(desc(QuizResult.created_at))
            .limit(limit)
            .all()
        )
    
    def get_category_stats(self, user_id: int, category: str) -> Dict[str, Any]:
        """ユーザーのカテゴリ別統計を取得する。
        
        Args:
            user_id: ユーザー ID
            category: カテゴリ
            
        Returns:
            統計情報（correct, total, accuracy）
        """
        results = (
            self.session.query(QuizResult)
            .filter(and_(
                QuizResult.user_id == user_id,
                QuizResult.category == category
            ))
            .all()
        )
        
        if not results:
            return {"correct": 0, "total": 0, "accuracy": 0}
        
        correct = sum(1 for r in results if r.is_correct)
        total = len(results)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return {"correct": correct, "total": total, "accuracy": accuracy}


class StudyLogDAL:
    """学習ログテーブルの操作を管理する。"""
    
    def __init__(self, session: Session):
        """初期化。
        
        Args:
            session: SQLAlchemy セッション
        """
        self.session = session
    
    def create_log(self, user_id: int, duration_seconds: int, **kwargs) -> Optional[StudyLog]:
        """学習ログを作成する。
        
        Args:
            user_id: ユーザー ID
            duration_seconds: 学習時間（秒）
            **kwargs: その他のフィールド
            
        Returns:
            作成されたログ、またはエラーの場合 None
        """
        try:
            log = StudyLog(
                user_id=user_id,
                duration_seconds=duration_seconds,
                **kwargs
            )
            self.session.add(log)
            self.session.commit()
            return log
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"学習ログ作成エラー: {str(e)}")
            return None
    
    def get_study_dates(self, user_id: int) -> set:
        """ユーザーの学習日を取得する。
        
        Args:
            user_id: ユーザー ID
            
        Returns:
            学習日の set（date オブジェクト）
        """
        logs = (
            self.session.query(StudyLog.created_at)
            .filter_by(user_id=user_id)
            .all()
        )
        
        study_dates = set()
        for log in logs:
            study_dates.add(log[0].date())
        
        return study_dates
    
    def calculate_streak(self, user_id: int) -> int:
        """ユーザーの連続学習日数を計算する。
        
        Args:
            user_id: ユーザー ID
            
        Returns:
            連続学習日数
        """
        study_dates = self.get_study_dates(user_id)
        
        if not study_dates:
            return 0
        
        today = datetime.utcnow().date()
        streak = 0
        check_date = today
        
        for _ in range(365):
            if check_date in study_dates:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return streak


class ProgressDAL:
    """進捗テーブルの操作を管理する。"""
    
    def __init__(self, session: Session):
        """初期化。
        
        Args:
            session: SQLAlchemy セッション
        """
        self.session = session
    
    def get_or_create_today_progress(self, user_id: int) -> Optional[Progress]:
        """今日の進捗を取得、なければ作成する。
        
        Args:
            user_id: ユーザー ID
            
        Returns:
            進捗オブジェクト
        """
        today = datetime.utcnow().date()
        
        progress = (
            self.session.query(Progress)
            .filter(and_(
                Progress.user_id == user_id,
                func.date(Progress.study_date) == today
            ))
            .first()
        )
        
        if not progress:
            progress = Progress(
                user_id=user_id,
                study_date=datetime.utcnow()
            )
            self.session.add(progress)
            self.session.commit()
        
        return progress
    
    def update_progress(self, user_id: int, **kwargs) -> bool:
        """ユーザーの進捗を更新する。
        
        Args:
            user_id: ユーザー ID
            **kwargs: 更新するフィールド
            
        Returns:
            成功時 True
        """
        try:
            progress = self.get_or_create_today_progress(user_id)
            
            for key, value in kwargs.items():
                if hasattr(progress, key):
                    setattr(progress, key, value)
            
            self.session.commit()
            return True
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"進捗更新エラー: {str(e)}")
            return False
