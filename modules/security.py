"""AWS Skills - セキュリティモジュール

入力値検証、データ暗号化、パスワード管理など
セキュリティ関連の機能を一元管理する。
"""

import html
import hashlib
import re
from typing import Any, Optional
from pathlib import Path

import bcrypt
from pydantic import BaseModel, Field, validator

# --- パスワード管理 -------------------------------------------------------


def hash_password(password: str) -> str:
    """パスワードを bcrypt でハッシング化する。
    
    Args:
        password: 平文のパスワード
        
    Returns:
        ハッシング化されたパスワード
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """パスワードがハッシュと一致するか確認する。
    
    Args:
        password: 検証する平文のパスワード
        hashed: bcrypt ハッシュ
        
    Returns:
        一致する場合 True
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# --- 入力値検証・サニタイゼーション ----------------------------------------


def sanitize_html(value: str, max_length: int = 1000) -> str:
    """HTML 特殊文字をエスケープする。
    
    XSS 攻撃を防ぐため、ユーザー入力を HTML エスケープしてから表示する。
    
    Args:
        value: サニタイズする文字列
        max_length: 最大文字数（デフォルト 1000）
        
    Returns:
        エスケープされた文字列
    """
    if not isinstance(value, str):
        return ""
    # 長さ制限
    value = value[:max_length]
    # HTML エスケープ
    return html.escape(value)


def sanitize_json_string(value: str) -> str:
    """JSON に安全な文字列に変換する。
    
    Args:
        value: サニタイズする文字列
        
    Returns:
        JSON セーフな文字列
    """
    if not isinstance(value, str):
        return ""
    # 改行やタブをエスケープ
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")
    value = value.replace("\t", "\\t")
    return value


def validate_username(username: str) -> bool:
    """ユーザー名の形式をチェックする。
    
    許可: 英数字、アンダースコア、ハイフン、2〜32文字
    
    Args:
        username: 検証するユーザー名
        
    Returns:
        有効な形式なら True
    """
    if not isinstance(username, str):
        return False
    pattern = r"^[a-zA-Z0-9_-]{2,32}$"
    return bool(re.match(pattern, username))


def validate_email(email: str) -> bool:
    """メールアドレスの形式をチェックする。
    
    Args:
        email: 検証するメールアドレス
        
    Returns:
        有効な形式なら True
    """
    if not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """パスワードの強度をチェックする。
    
    要件:
    - 最小 8 文字
    - 大文字を最低 1 つ含む
    - 小文字を最低 1 つ含む
    - 数字を最低 1 つ含む
    
    Args:
        password: 検証するパスワード
        
    Returns:
        (有効性, エラーメッセージ) のタプル
    """
    if not isinstance(password, str):
        return False, "パスワードは文字列である必要があります"
    
    if len(password) < 8:
        return False, "パスワードは最低8文字である必要があります"
    
    if not re.search(r"[A-Z]", password):
        return False, "パスワードは大文字を含む必要があります"
    
    if not re.search(r"[a-z]", password):
        return False, "パスワードは小文字を含む必要があります"
    
    if not re.search(r"\d", password):
        return False, "パスワードは数字を含む必要があります"
    
    return True, ""


# --- セッション・トークン管理 ----------------------------------------


def generate_session_token(username: str, user_id: int) -> str:
    """簡易的なセッショントークンを生成する（開発用）。
    
    注意: 本番環境では JWT や专门库を使用してください。
    
    Args:
        username: ユーザー名
        user_id: ユーザー ID
        
    Returns:
        セッショントークン
    """
    token_data = f"{username}:{user_id}:{int(__import__('time').time())}"
    token_hash = hashlib.sha256(token_data.encode()).hexdigest()
    return token_hash


def validate_session_token(token: str) -> Optional[tuple[str, int]]:
    """セッショントークンを検証する（簡易版）。
    
    Args:
        token: 検証するトークン
        
    Returns:
        (username, user_id) のタプル、または無効な場合は None
    """
    # 本実装では単なるハッシュチェック。実際には DB から取得して検証する。
    if not isinstance(token, str) or len(token) != 64:
        return None
    return None


# --- Pydantic モデル（データバリデーション）--------------------------------


class UserCredentials(BaseModel):
    """ユーザーの認証情報を表現するモデル。"""
    
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=8)
    
    @validator("username")
    def validate_username_field(cls, v):
        if not validate_username(v):
            raise ValueError("無効なユーザー名形式です")
        return v


class UserProfile(BaseModel):
    """ユーザープロフィールを表現するモデル。"""
    
    username: str = Field(..., min_length=2, max_length=32)
    email: Optional[str] = None
    exam_code: str = Field(default="SAA-C03")
    
    @validator("username")
    def validate_username_field(cls, v):
        if not validate_username(v):
            raise ValueError("無効なユーザー名形式です")
        return v
    
    @validator("email", pre=True, always=True)
    def validate_email_field(cls, v):
        if v is not None and not validate_email(v):
            raise ValueError("無効なメールアドレス形式です")
        return v


class QuizAnswer(BaseModel):
    """クイズの回答を表現するモデル。"""
    
    question_id: int = Field(..., gt=0)
    selected_indices: list[int] = Field(default_factory=list)
    timestamp: str
    
    @validator("selected_indices")
    def validate_indices(cls, v):
        if not all(isinstance(i, int) and i >= 0 for i in v):
            raise ValueError("無効な選択肢インデックスです")
        return v


# --- セキュリティチェック ------------------------------------------------


def check_injection_attempt(value: str) -> bool:
    """SQL インジェクションやコマンドインジェクションの可能性をチェックする。
    
    Args:
        value: チェックする文字列
        
    Returns:
        疑わしい場合 True（ブロック対象）
    """
    if not isinstance(value, str):
        return False
    
    suspicious_patterns = [
        r"(\bor\b|\band\b)\s*1\s*=\s*1",  # SQL injection
        r";\s*drop\b",  # DROP command
        r";\s*delete\b",  # DELETE command
        r"<script",  # XSS
        r"javascript:",  # XSS
        r"\$\{",  # Template injection
    ]
    
    value_lower = value.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            return True
    
    return False


# --- ファイルセキュリティ ------------------------------------------------


def validate_json_file_size(file_path: Path, max_size_mb: int = 50) -> bool:
    """JSON ファイルのサイズを検証する。
    
    Args:
        file_path: ファイルパス
        max_size_mb: 最大サイズ（MB）
        
    Returns:
        有効なサイズなら True
    """
    if not file_path.exists():
        return False
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    return file_size_mb <= max_size_mb


def validate_json_integrity(json_data: Any) -> bool:
    """JSON データの整合性をチェックする（簡易版）。
    
    Args:
        json_data: 検証する JSON データ
        
    Returns:
        有効なら True
    """
    if not isinstance(json_data, (dict, list)):
        return False
    
    # ネストの深さ制限（DoS 対策）
    def check_depth(obj, max_depth=10, current=0):
        if current > max_depth:
            return False
        if isinstance(obj, dict):
            return all(check_depth(v, max_depth, current + 1) for v in obj.values())
        elif isinstance(obj, list):
            return all(check_depth(item, max_depth, current + 1) for item in obj)
        return True
    
    return check_depth(json_data)
