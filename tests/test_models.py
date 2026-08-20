"""
SQLAlchemy ORM モデルのテスト
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.models import Base, User, QuizResult, StudyLog, Session as DBSession, Progress
from modules.security import hash_password


@pytest.mark.integration
class TestUserModel:
    """User モデルのテスト"""
    
    def test_user_creation(self, db_session):
        """ユーザーが作成されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('SecurePass123')
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.created_at is not None
    
    def test_user_default_values(self, db_session):
        """ユーザーのデフォルト値が設定されるか"""
        user = User(
            username='newuser',
            email='new@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.level == 'beginner'
        assert user.xp == 0
        assert user.total_xp == 0
        assert user.badges == '[]'
        assert user.achievements == '[]'
    
    def test_user_password_hash_required(self, db_session):
        """パスワードハッシュが必須か"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=None
        )
        db_session.add(user)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_user_username_unique(self, db_session):
        """ユーザー名が一意か"""
        user1 = User(
            username='testuser',
            email='test1@example.com',
            password_hash=hash_password('Pass123')
        )
        user2 = User(
            username='testuser',
            email='test2@example.com',
            password_hash=hash_password('Pass456')
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_user_timestamp_auto_update(self, db_session):
        """タイムスタンプが自動更新されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        created_at = user.created_at
        
        # ユーザーを更新
        user.level = 'intermediate'
        db_session.commit()
        
        assert user.created_at == created_at
        assert user.updated_at > created_at


@pytest.mark.integration
class TestQuizResultModel:
    """QuizResult モデルのテスト"""
    
    def test_quiz_result_creation(self, db_session, sample_quiz_result_data):
        """クイズ結果が作成されるか"""
        # ユーザーを先に作成
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        # クイズ結果を作成
        result = QuizResult(
            user_id=user.id,
            **sample_quiz_result_data
        )
        db_session.add(result)
        db_session.commit()
        
        assert result.id is not None
        assert result.user_id == user.id
        assert result.is_correct is True
        assert result.time_spent_seconds == 45
    
    def test_quiz_result_user_relationship(self, db_session, sample_quiz_result_data):
        """クイズ結果のユーザー関連付けが正しいか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        result = QuizResult(
            user_id=user.id,
            **sample_quiz_result_data
        )
        db_session.add(result)
        db_session.commit()
        
        # 関連付けを確認
        retrieved_result = db_session.query(QuizResult).filter_by(id=result.id).first()
        assert retrieved_result.user.username == 'testuser'
    
    def test_quiz_result_cascade_delete(self, db_session, sample_quiz_result_data):
        """ユーザー削除時に結果もカスケード削除されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        result = QuizResult(
            user_id=user.id,
            **sample_quiz_result_data
        )
        db_session.add(result)
        db_session.commit()
        
        result_id = result.id
        
        # ユーザーを削除
        db_session.delete(user)
        db_session.commit()
        
        # 結果が削除されたか確認
        deleted_result = db_session.query(QuizResult).filter_by(id=result_id).first()
        assert deleted_result is None


@pytest.mark.integration
class TestStudyLogModel:
    """StudyLog モデルのテスト"""
    
    def test_study_log_creation(self, db_session, sample_study_log_data):
        """学習ログが作成されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        log = StudyLog(
            user_id=user.id,
            **sample_study_log_data
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.user_id == user.id
        assert log.duration_seconds == 3600
        assert log.category == 'S3'
    
    def test_study_log_cascade_delete(self, db_session, sample_study_log_data):
        """ユーザー削除時に学習ログもカスケード削除されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        log = StudyLog(
            user_id=user.id,
            **sample_study_log_data
        )
        db_session.add(log)
        db_session.commit()
        
        log_id = log.id
        
        # ユーザーを削除
        db_session.delete(user)
        db_session.commit()
        
        # ログが削除されたか確認
        deleted_log = db_session.query(StudyLog).filter_by(id=log_id).first()
        assert deleted_log is None


@pytest.mark.integration
class TestSessionModel:
    """Session モデルのテスト"""
    
    def test_session_creation(self, db_session):
        """セッションが作成されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        session = DBSession(
            user_id=user.id,
            token='test-token-12345',
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0'
        )
        db_session.add(session)
        db_session.commit()
        
        assert session.id is not None
        assert session.user_id == user.id
        assert session.token == 'test-token-12345'
        assert session.is_active is True


@pytest.mark.integration
class TestProgressModel:
    """Progress モデルのテスト"""
    
    def test_progress_creation(self, db_session):
        """進捗が作成されるか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        progress = Progress(
            user_id=user.id,
            study_date=datetime.now().date(),
            total_studied_seconds=3600,
            questions_attempted=50,
            accuracy=0.85,
            streak_days=5
        )
        db_session.add(progress)
        db_session.commit()
        
        assert progress.id is not None
        assert progress.user_id == user.id
        assert progress.accuracy == 0.85
        assert progress.streak_days == 5


@pytest.mark.integration
class TestModelRelationships:
    """モデル間の関連付けテスト"""
    
    def test_user_quiz_results_relationship(self, db_session, sample_quiz_result_data):
        """ユーザーと クイズ結果の関連付けが正しいか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        # 複数の結果を追加
        for i in range(3):
            result = QuizResult(
                user_id=user.id,
                question_id=i + 1,
                quiz_mode='study',
                quiz_source='exam_prep',
                selected_indices=[0],
                is_correct=True,
                time_spent_seconds=30 + i * 10,
                category='EC2',
                domain='Compute',
                topic='Instances',
                difficulty='medium'
            )
            db_session.add(result)
        db_session.commit()
        
        # ユーザーの結果を確認
        user_results = db_session.query(QuizResult).filter_by(user_id=user.id).all()
        assert len(user_results) == 3
    
    def test_user_study_logs_relationship(self, db_session, sample_study_log_data):
        """ユーザーと学習ログの関連付けが正しいか"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        # 複数のログを追加
        for i in range(3):
            log = StudyLog(
                user_id=user.id,
                duration_seconds=3600 + i * 600,
                category=['S3', 'EC2', 'RDS'][i],
                exam_code='SAA-C03'
            )
            db_session.add(log)
        db_session.commit()
        
        # ユーザーのログを確認
        user_logs = db_session.query(StudyLog).filter_by(user_id=user.id).all()
        assert len(user_logs) == 3


@pytest.mark.integration
class TestModelConstraints:
    """モデル制約のテスト"""
    
    def test_unique_email(self, db_session):
        """メールアドレスが一意か"""
        user1 = User(
            username='user1',
            email='test@example.com',
            password_hash=hash_password('Pass123')
        )
        user2 = User(
            username='user2',
            email='test@example.com',
            password_hash=hash_password('Pass456')
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_foreign_key_constraint(self, db_session):
        """外部キー制約が機能するか"""
        # 存在しないユーザーIDで結果を作成しようとする
        result = QuizResult(
            user_id=9999,  # 存在しないID
            question_id=1,
            quiz_mode='study',
            quiz_source='exam_prep',
            selected_indices=[0],
            is_correct=True,
            time_spent_seconds=30,
            category='EC2',
            domain='Compute',
            topic='Instances',
            difficulty='medium'
        )
        db_session.add(result)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
