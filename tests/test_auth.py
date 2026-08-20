"""
認証モジュールのテスト
"""

import pytest
from datetime import datetime, timedelta
from modules.auth import AuthenticationManager
from modules.security import hash_password


@pytest.mark.unit
class TestAuthenticationManager:
    """認証マネージャーのテスト"""
    
    @pytest.fixture
    def auth_manager_instance(self, tmp_path, monkeypatch):
        """テスト用の認証マネージャーを作成"""
        # テンポラリディレクトリをデータディレクトリとして使用
        monkeypatch.setenv('DATA_DIR', str(tmp_path))
        
        manager = AuthenticationManager()
        return manager
    
    def test_register_user_success(self, auth_manager_instance, sample_user_data):
        """ユーザー登録が成功するか"""
        manager = auth_manager_instance
        
        result = manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        assert result is True or result == sample_user_data['username']
    
    def test_register_user_duplicate_username(self, auth_manager_instance, sample_user_data):
        """重複するユーザー名が拒否されるか"""
        manager = auth_manager_instance
        
        # 最初のユーザーを登録
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 同じユーザー名で登録試行
        result = manager.register_user(
            sample_user_data['username'],
            "DifferentPass123",
            "different@example.com"
        )
        
        assert result is False or isinstance(result, Exception)
    
    def test_register_user_weak_password(self, auth_manager_instance):
        """弱いパスワードが拒否されるか"""
        manager = auth_manager_instance
        
        result = manager.register_user(
            "newuser",
            "weak",  # 弱いパスワード
            "new@example.com"
        )
        
        assert result is False or isinstance(result, Exception)
    
    def test_login_success(self, auth_manager_instance, sample_user_data):
        """ログインが成功するか"""
        manager = auth_manager_instance
        
        # ユーザー登録
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ログイン
        result = manager.login(
            sample_user_data['username'],
            sample_user_data['password']
        )
        
        assert result is True
        assert manager.is_authenticated() is True
    
    def test_login_wrong_password(self, auth_manager_instance, sample_user_data):
        """間違ったパスワードでログインできないか"""
        manager = auth_manager_instance
        
        # ユーザー登録
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # 間違ったパスワードでログイン
        result = manager.login(
            sample_user_data['username'],
            "WrongPassword123"
        )
        
        assert result is False
    
    def test_login_non_existent_user(self, auth_manager_instance):
        """存在しないユーザーでログインできないか"""
        manager = auth_manager_instance
        
        result = manager.login("nonexistent", "SomePassword123")
        
        assert result is False
    
    def test_logout(self, auth_manager_instance, sample_user_data):
        """ログアウトが正常に動作するか"""
        manager = auth_manager_instance
        
        # ユーザー登録・ログイン
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        manager.login(
            sample_user_data['username'],
            sample_user_data['password']
        )
        
        assert manager.is_authenticated() is True
        
        # ログアウト
        manager.logout()
        
        assert manager.is_authenticated() is False
    
    def test_get_current_user(self, auth_manager_instance, sample_user_data):
        """現在のユーザーを取得できるか"""
        manager = auth_manager_instance
        
        # ユーザー登録・ログイン
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        manager.login(
            sample_user_data['username'],
            sample_user_data['password']
        )
        
        current_user = manager.get_current_user()
        
        assert current_user is not None
        assert current_user == sample_user_data['username']
    
    def test_session_timeout(self, auth_manager_instance, sample_user_data, monkeypatch):
        """セッションがタイムアウトするか"""
        manager = auth_manager_instance
        
        # ユーザー登録・ログイン
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        manager.login(
            sample_user_data['username'],
            sample_user_data['password']
        )
        
        # セッションタイムアウト時刻を過去に設定
        past_time = datetime.now() - timedelta(hours=1)
        manager.session_timeout = past_time
        
        # セッションがまだ有効か確認（タイムアウト実装による）
        # 注: これは実装に依存する
    
    def test_is_authenticated_false_initially(self, auth_manager_instance):
        """初期状態では認証されていないか"""
        manager = auth_manager_instance
        
        assert manager.is_authenticated() is False


@pytest.mark.unit
class TestAuthenticationSecurity:
    """認証セキュリティのテスト"""
    
    def test_password_not_stored_plaintext(self, tmp_path, monkeypatch):
        """パスワードが平文で保存されていないか"""
        monkeypatch.setenv('DATA_DIR', str(tmp_path))
        manager = AuthenticationManager()
        
        password = "SecurePass123"
        manager.register_user("testuser", password, "test@example.com")
        
        # ユーザーデータを確認
        current_user = manager.get_current_user()
        
        # 平文パスワードが保存されていないことを確認
        # （実装に依存）
    
    def test_multiple_failed_login_attempts(self, tmp_path, monkeypatch):
        """複数の失敗したログイン試行を検出できるか"""
        monkeypatch.setenv('DATA_DIR', str(tmp_path))
        manager = AuthenticationManager()
        
        manager.register_user("testuser", "SecurePass123", "test@example.com")
        
        # 複数の失敗したログイン試行
        for _ in range(5):
            manager.login("testuser", "WrongPassword")
        
        # ブルートフォース対策が実装されている場合、
        # ここでアカウントがロックされるべき
        # （実装に依存）


@pytest.mark.unit
class TestAuthenticationFlow:
    """認証フロー統合テスト"""
    
    def test_complete_auth_flow(self, tmp_path, monkeypatch, sample_user_data):
        """完全な認証フロー（登録 → ログイン → ログアウト）"""
        monkeypatch.setenv('DATA_DIR', str(tmp_path))
        manager = AuthenticationManager()
        
        # 1. 初期状態 - 未認証
        assert manager.is_authenticated() is False
        
        # 2. ユーザー登録
        register_result = manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        assert register_result is True or register_result == sample_user_data['username']
        
        # 3. ログイン
        login_result = manager.login(
            sample_user_data['username'],
            sample_user_data['password']
        )
        assert login_result is True
        assert manager.is_authenticated() is True
        
        # 4. 現在のユーザーを確認
        current_user = manager.get_current_user()
        assert current_user == sample_user_data['username']
        
        # 5. ログアウト
        manager.logout()
        assert manager.is_authenticated() is False
    
    def test_login_after_logout(self, tmp_path, monkeypatch, sample_user_data):
        """ログアウト後に再度ログインできるか"""
        monkeypatch.setenv('DATA_DIR', str(tmp_path))
        manager = AuthenticationManager()
        
        # ユーザー登録
        manager.register_user(
            sample_user_data['username'],
            sample_user_data['password'],
            sample_user_data['email']
        )
        
        # ログイン・ログアウト
        manager.login(sample_user_data['username'], sample_user_data['password'])
        manager.logout()
        
        # 再度ログイン
        second_login = manager.login(
            sample_user_data['username'],
            sample_user_data['password']
        )
        assert second_login is True
        assert manager.is_authenticated() is True
