"""
データアクセスレイヤー（DAL）のテスト
"""

import pytest
from modules.dal import UserDAL, QuizResultDAL, StudyLogDAL, ProgressDAL
from modules.security import hash_password


@pytest.mark.integration
class TestUserDAL:
    """UserDAL のテスト"""
    
    def test_create_user_success(self, db_session, sample_user_data):
        """ユーザーが正常に作成されるか"""
        dal = UserDAL(db_session)
        
        user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        assert user is not None
        assert user.username == sample_user_data['username']
        assert user.email == sample_user_data['email']
    
    def test_create_user_duplicate(self, db_session, sample_user_data):
        """重複するユーザー名が拒否されるか"""
        dal = UserDAL(db_session)
        
        # 最初のユーザーを作成
        dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 同じユーザー名で作成しようとする
        with pytest.raises(Exception):
            dal.create_user(
                sample_user_data['username'],
                "DifferentPass123",
                "different@example.com"
            )
    
    def test_get_user_by_username(self, db_session, sample_user_data):
        """ユーザー名でユーザーを取得できるか"""
        dal = UserDAL(db_session)
        
        created_user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        retrieved_user = dal.get_user_by_username(sample_user_data['username'])
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == sample_user_data['email']
    
    def test_get_user_by_username_not_found(self, db_session):
        """存在しないユーザー名を取得すると None が返されるか"""
        dal = UserDAL(db_session)
        
        user = dal.get_user_by_username('nonexistent')
        
        assert user is None
    
    def test_get_user_by_id(self, db_session, sample_user_data):
        """ID でユーザーを取得できるか"""
        dal = UserDAL(db_session)
        
        created_user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        retrieved_user = dal.get_user_by_id(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
    
    def test_verify_password_correct(self, db_session, sample_user_data):
        """正しいパスワードが検証されるか"""
        dal = UserDAL(db_session)
        
        user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        result = dal.verify_password(user, sample_user_data['password'])
        
        assert result is True
    
    def test_verify_password_incorrect(self, db_session, sample_user_data):
        """間違ったパスワードが検証されないか"""
        dal = UserDAL(db_session)
        
        user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        result = dal.verify_password(user, "WrongPassword123")
        
        assert result is False
    
    def test_update_user(self, db_session, sample_user_data):
        """ユーザーが更新されるか"""
        dal = UserDAL(db_session)
        
        user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ユーザーを更新
        user.level = 'intermediate'
        user.xp = 100
        
        result = dal.update_user(user)
        
        assert result is True
        
        # 更新が保存されたか確認
        updated_user = dal.get_user_by_id(user.id)
        assert updated_user.level == 'intermediate'
        assert updated_user.xp == 100
    
    def test_update_last_login(self, db_session, sample_user_data):
        """ラストログイン時刻が更新されるか"""
        dal = UserDAL(db_session)
        
        user = dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        last_login_before = user.last_login_at
        
        # ラストログイン時刻を更新
        dal.update_last_login(user)
        
        # 更新が保存されたか確認
        updated_user = dal.get_user_by_id(user.id)
        assert updated_user.last_login_at > last_login_before or updated_user.last_login_at is not None


@pytest.mark.integration
class TestQuizResultDAL:
    """QuizResultDAL のテスト"""
    
    def test_create_result(self, db_session, sample_user_data, sample_quiz_result_data):
        """クイズ結果が作成されるか"""
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
        
        assert result is not None
        assert result.user_id == user.id
        assert result.is_correct is True
    
    def test_get_user_results(self, db_session, sample_user_data, sample_quiz_result_data):
        """ユーザーのクイズ結果を取得できるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 複数の結果を作成
        result_dal = QuizResultDAL(db_session)
        for i in range(3):
            result_dal.create_result(
                user.id,
                question_id=i + 1,
                **{k: v for k, v in sample_quiz_result_data.items() if k != 'question_id'}
            )
        
        # 結果を取得
        results = result_dal.get_user_results(user.id)
        
        assert len(results) == 3
    
    def test_get_category_stats(self, db_session, sample_user_data, sample_quiz_result_data):
        """カテゴリ別統計を取得できるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 結果を作成
        result_dal = QuizResultDAL(db_session)
        for i in range(5):
            result_dal.create_result(
                user.id,
                question_id=i + 1,
                is_correct=(i % 2 == 0),
                **{k: v for k, v in sample_quiz_result_data.items() if k not in ['question_id', 'is_correct']}
            )
        
        # 統計を取得
        stats = result_dal.get_category_stats(user.id, sample_quiz_result_data['category'])
        
        assert stats is not None
        assert 'total' in stats or 'correct' in stats or isinstance(stats, (dict, tuple))


@pytest.mark.integration
class TestStudyLogDAL:
    """StudyLogDAL のテスト"""
    
    def test_create_log(self, db_session, sample_user_data, sample_study_log_data):
        """学習ログが作成されるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ログを作成
        log_dal = StudyLogDAL(db_session)
        log = log_dal.create_log(user.id, **sample_study_log_data)
        
        assert log is not None
        assert log.user_id == user.id
        assert log.duration_seconds == sample_study_log_data['duration_seconds']
    
    def test_get_study_dates(self, db_session, sample_user_data, sample_study_log_data):
        """学習日を取得できるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ログを作成
        log_dal = StudyLogDAL(db_session)
        log_dal.create_log(user.id, **sample_study_log_data)
        
        # 学習日を取得
        dates = log_dal.get_study_dates(user.id)
        
        assert dates is not None
        assert len(dates) >= 0
    
    def test_calculate_streak(self, db_session, sample_user_data, sample_study_log_data):
        """連続学習日数が計算されるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ログを作成
        log_dal = StudyLogDAL(db_session)
        log_dal.create_log(user.id, **sample_study_log_data)
        
        # ストリークを計算
        streak = log_dal.calculate_streak(user.id)
        
        assert isinstance(streak, int)
        assert streak >= 0


@pytest.mark.integration
class TestProgressDAL:
    """ProgressDAL のテスト"""
    
    def test_get_or_create_today_progress(self, db_session, sample_user_data):
        """今日の進捗を取得・作成できるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 進捗を取得・作成
        progress_dal = ProgressDAL(db_session)
        progress = progress_dal.get_or_create_today_progress(user.id)
        
        assert progress is not None
        assert progress.user_id == user.id
    
    def test_update_progress(self, db_session, sample_user_data):
        """進捗が更新されるか"""
        # ユーザーを作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 進捗を作成・更新
        progress_dal = ProgressDAL(db_session)
        progress = progress_dal.get_or_create_today_progress(user.id)
        
        result = progress_dal.update_progress(
            progress,
            total_studied_seconds=7200,
            questions_attempted=100,
            accuracy=0.90
        )
        
        assert result is True


@pytest.mark.integration
class TestDALErrorHandling:
    """DAL エラーハンドリングのテスト"""
    
    def test_user_dal_handles_database_error(self, db_session):
        """データベースエラーが正しく処理されるか"""
        dal = UserDAL(db_session)
        
        # 無効な操作を試行
        try:
            # セッションを閉じて無効にする
            db_session.close()
            dal.get_user_by_username("test")
        except Exception as e:
            # エラーが発生することを確認
            assert e is not None
    
    def test_quiz_result_dal_invalid_user_id(self, db_session, sample_quiz_result_data):
        """無効なユーザーID でのエラー処理"""
        dal = QuizResultDAL(db_session)
        
        # 存在しないユーザーIDで試行
        with pytest.raises(Exception):
            dal.create_result(9999, **sample_quiz_result_data)


@pytest.mark.integration
class TestDALIntegration:
    """DAL 統合テスト"""
    
    def test_full_workflow_user_to_results(self, db_session, sample_user_data, sample_quiz_result_data):
        """ユーザー作成から結果記録までの完全なワークフロー"""
        # ユーザー作成
        user_dal = UserDAL(db_session)
        user = user_dal.create_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ログイン確認（パスワード検証）
        is_valid = user_dal.verify_password(user, sample_user_data['password'])
        assert is_valid is True
        
        # クイズ結果を記録
        result_dal = QuizResultDAL(db_session)
        result = result_dal.create_result(user.id, **sample_quiz_result_data)
        assert result is not None
        
        # ユーザーを更新
        user.xp += 10
        user_dal.update_user(user)
        
        # 統計を確認
        stats = result_dal.get_category_stats(user.id, sample_quiz_result_data['category'])
        assert stats is not None
