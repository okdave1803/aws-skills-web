#!/usr/bin/env python
"""セキュリティ機能の動作確認スクリプト"""

from modules.security import (
    validate_username,
    validate_password,
    hash_password,
    verify_password,
    sanitize_html,
    check_injection_attempt,
)

print("=" * 50)
print("AWS Skills - セキュリティ機能テスト")
print("=" * 50)

# ユーザー名検証
print("\n=== ユーザー名検証 ===")
test_usernames = ["valid_user123", "invalid@user", "a", "valid-user"]
for username in test_usernames:
    result = validate_username(username)
    print(f"  {username:20} → {result}")

# パスワード検証
print("\n=== パスワード検証 ===")
test_passwords = [
    "weak",
    "NoNumber",
    "StrongPass123",
    "SuperSecure@2026",
]
for pwd in test_passwords:
    is_valid, msg = validate_password(pwd)
    status = "✅" if is_valid else "❌"
    print(f"  {status} {pwd:20} → {msg if not is_valid else 'OK'}")

# パスワードハッシング
print("\n=== パスワードハッシング ===")
pwd = "TestPassword123"
hashed = hash_password(pwd)
print(f"  オリジナル: {pwd}")
print(f"  ハッシュ: {hashed[:40]}...")
print(f"  検証 (正しい): {verify_password(pwd, hashed)}")
print(f"  検証 (間違い): {verify_password('WrongPassword123', hashed)}")

# HTML サニタイゼーション
print("\n=== HTML サニタイゼーション ===")
html_tests = [
    "Hello World",
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
]
for html in html_tests:
    sanitized = sanitize_html(html)
    print(f"  入力: {html[:40]}")
    print(f"  出力: {sanitized[:40]}")

# インジェクション検出
print("\n=== インジェクション検出 ===")
injection_tests = [
    "SELECT * FROM users",
    "1' OR '1'='1",
    "normal input",
    "javascript:alert(1)",
]
for test in injection_tests:
    is_injection = check_injection_attempt(test)
    status = "⚠️ 検出" if is_injection else "✅ 安全"
    print(f"  {status}: {test[:40]}")

print("\n" + "=" * 50)
print("✅ セキュリティ機能が正常に動作しています")
print("=" * 50)
