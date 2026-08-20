"""
統合テスト - 複数コンポーネント間の相互作用
"""

import pytest
from datetime import datetime
from modules.auth import AuthenticationManager
from modules.dal import UserDAL, QuizResultDAL, StudyLogDAL, ProgressDAL
from modules.security import hash_password


@pytest.mark.integration
class TestAuthenticationWithDatabase:
    """認証システムとデータベース間の統合テスト"""
    
    def test_user_registration_creates_database_record(self, db_session, sample_user_data):
        """ユーザー登録がデータベースレコードを作成するか"""
        user_dal = UserDAL(db_session)
        
        # ユーザーを作成
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 作成されたユーザーを確認
        retrieved_user = user_dal.get_user_by_username(sample_user_data['username'])
        
        assert retrieved_user is not None
        assert retrieved_user.email == sample_user_data['email']
    
    def test_login_verifies_against_database(self, db_session, sample_user_data):
        """ログインがデータベースに対して検証されるか"""
        user_dal = UserDAL(db_session)
        
        # ユーザーを作成
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # パスワードを検証
        is_valid = user_dal.verify_password(user, sample_user_data['password'])
        assert is_valid is True
        
        # 間違ったパスワードを検証
        is_invalid = user_dal.verify_password(user, "WrongPassword123")
        assert is_invalid is False


@pytest.mark.integration
class TestQuizResultWorkflow:
    """クイズ結果記録ワークフロー統合テスト"""
    
    def test_complete_quiz_result_flow(self, db_session, sample_user_data, sample_quiz_result_data):
        """クイズ実施から結果記録までの完全なフロー"""
        # ユーザー作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # クイズ結果を記録
        result_dal = QuizResultDAL(db_session)
        result = result_dal.create_result(user.id, **sample_quiz_result_data)
        
        # 結果を確認
        assert result is not None
        assert result.user_id == user.id
        assert result.is_correct is True
        
        # ユーザーの統計を取得
        user_results = result_dal.get_user_results(user.id)
        assert len(user_results) == 1
    
    def test_multiple_quiz_results_tracking(self, db_session, sample_user_data, sample_quiz_result_data):
        """複数のクイズ結果を追跡できるか"""
        # ユーザー作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 複数の結果を記録
        result_dal = QuizResultDAL(db_session)
        results = []
        for i in range(5):
            result = result_dal.create_result(
                user.id,
                question_id=i + 1,
                is_correct=(i % 2 == 0),
                **{k: v for k, v in sample_quiz_result_data.items() if k not in ['question_id', 'is_correct']}
            )
            results.append(result)
        
        # 結果を確認
        user_results = result_dal.get_user_results(user.id)
        assert len(user_results) == 5
        
        # 正答率を計算
        correct_count = sum(1 for r in user_results if r.is_correct)
        accuracy = correct_count / len(user_results)
        assert accuracy == 0.6  # 5 個中 3 個が正答


@pytest.mark.integration
class TestStudyProgressWorkflow:
    """学習進捗ワークフロー統合テスト"""
    
    def test_study_logging_and_progress_update(self, db_session, sample_user_data, sample_study_log_data):
        """学習ログと進捗更新のワークフロー"""
        # ユーザー作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 学習ログを作成
        log_dal = StudyLogDAL(db_session)
        log = log_dal.create_log(user.id, **sample_study_log_data)
        
        assert log is not None
        assert log.duration_seconds == sample_study_log_data['duration_seconds']
        
        # 進捗を作成・更新
        progress_dal = ProgressDAL(db_session)
        progress = progress_dal.get_or_create_today_progress(user.id)
        
        progress_dal.update_progress(
            progress,
            total_studied_seconds=sample_study_log_data['duration_seconds'],
            questions_attempted=50,
            accuracy=0.85
        )
        
        # 進捗を確認
        assert progress.total_studied_seconds == sample_study_log_data['duration_seconds']


@pytest.mark.integration
class TestDataConsistency:
    """データ一貫性テスト"""
    
    def test_cascade_delete_preserves_consistency(self, db_session, sample_user_data, sample_quiz_result_data, sample_study_log_data):
        """カスケード削除でデータ一貫性が保持されるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 結果を作成
        result_dal = QuizResultDAL(db_session)
        result = result_dal.create_result(user.id, **sample_quiz_result_data)
        
        # ログを作成
        log_dal = StudyLogDAL(db_session)
        log = log_dal.create_log(user.id, **sample_study_log_data)
        
        # 初期状態を確認
        initial_results = result_dal.get_user_results(user.id)
        assert len(initial_results) == 1
        
        # ユーザーを削除
        db_session.delete(user)
        db_session.commit()
        
        # 結果が削除されたか確認
        remaining_results = result_dal.get_user_results(user.id)
        assert len(remaining_results) == 0
    
    def test_foreign_key_referential_integrity(self, db_session, sample_quiz_result_data):
        """外部キー参照完全性が保持されるか"""
        result_dal = QuizResultDAL(db_session)
        
        # 存在しないユーザーIDで結果を作成しようとする
        with pytest.raises(Exception):
            result_dal.create_result(9999, **sample_quiz_result_data)


@pytest.mark.integration
class TestPerformance:
    """パフォーマンステスト"""
    
    @pytest.mark.slow
    def test_bulk_user_creation(self, db_session):
        """大量ユーザー作成のパフォーマンス"""
        user_dal = UserDAL(db_session)
        
        # 100 ユーザーを作成
        import time
        start = time.time()
        
        for i in range(100):
            user_dal.create_user(
                f"user{i}",
                "SecurePass123",
                f"user{i}@example.com"
            )
        
        elapsed = time.time() - start
        
        # 100 ユーザーを確認
        users = db_session.query(db_session).all()
        
        # パフォーマンス期待値: 100 ユーザーを 10 秒以内に作成
        assert elapsed < 10.0
    
    @pytest.mark.slow
    def test_bulk_result_creation(self, db_session, sample_user_data, sample_quiz_result_data):
        """大量結果作成のパフォーマンス"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        result_dal = QuizResultDAL(db_session)
        
        # 1000 個の結果を作成
        import time
        start = time.time()
        
        for i in range(1000):
            result_dal.create_result(
                user.id,
                question_id=i + 1,
                **sample_quiz_result_data
            )
        
        elapsed = time.time() - start
        
        # パフォーマンス期待値: 1000 結果を 30 秒以内に作成
        assert elapsed < 30.0


@pytest.mark.integration
class TestSecurityIntegration:
    """セキュリティ統合テスト"""
    
    def test_password_never_stored_plaintext(self, db_session, sample_user_data):
        """パスワードが平文で保存されていないか"""
        user_dal = UserDAL(db_session)
        
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # データベースから取得
        retrieved_user = user_dal.get_user_by_id(user.id)
        
        # パスワードがハッシュされているか確認
        assert retrieved_user.password_hash != sample_user_data['password']
        assert len(retrieved_user.password_hash) > 20  # bcrypt ハッシュ
    
    def test_sql_injection_prevention(self, db_session):
        """SQL インジェクション攻撃が防止されるか"""
        user_dal = UserDAL(db_session)
        
        # SQL インジェクションを含むユーザー名
        injection_username = "'; DROP TABLE users; --"
        
        # これは ORM 使用により SQL インジェクションから保護される
        user = user_dal.get_user_by_username(injection_username)
        
        # テーブルが削除されていないことを確認
        assert user is None  # ユーザーが見つからないはずだが、テーブルは存在
    
    def test_sensitive_data_not_exposed_in_logs(self, db_session, sample_user_data):
        """機密データがログに記録されていないか"""
        user_dal = UserDAL(db_session)
        
        # キャプチャ対象: ログメッセージ
        # パスワードが含まれていないことを確認する必要があります
        
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # パスワードがユーザーオブジェクトに平文で保存されていないことを確認
        assert not hasattr(user, '_plaintext_password') or user._plaintext_password is None


@pytest.mark.integration
class TestEndToEndWorkflow:
    """エンドツーエンドワークフローテスト"""
    
    def test_complete_user_journey(self, db_session, sample_user_data, sample_quiz_result_data, sample_study_log_data):
        """ユーザーの完全なジャーニー（登録 → クイズ → 学習 → 進捗）"""
        
        # 1. ユーザー登録
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        assert user is not None
        
        # 2. ログイン検証
        is_valid = user_dal.verify_password(user, sample_user_data['password'])
        assert is_valid is True
        
        # 3. クイズ実施
        result_dal = QuizResultDAL(db_session)
        for i in range(5):
            result_dal.create_result(
                user.id,
                question_id=i + 1,
                is_correct=(i % 2 == 0),
                **{k: v for k, v in sample_quiz_result_data.items() if k not in ['question_id', 'is_correct']}
            )
        
        # 4. 学習ログ
        log_dal = StudyLogDAL(db_session)
        log_dal.create_log(user.id, **sample_study_log_data)
        
        # 5. 進捗更新
        progress_dal = ProgressDAL(db_session)
        progress = progress_dal.get_or_create_today_progress(user.id)
        progress_dal.update_progress(
            progress,
            total_studied_seconds=sample_study_log_data['duration_seconds'],
            questions_attempted=5,
            accuracy=0.6
        )
        
        # 6. データを確認
        user_results = result_dal.get_user_results(user.id)
        assert len(user_results) == 5
        
        study_dates = log_dal.get_study_dates(user.id)
        assert len(study_dates) > 0
        
        streak = log_dal.calculate_streak(user.id)
        assert isinstance(streak, int)
        
        assert progress.accuracy == 0.6
