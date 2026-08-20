"""AWS Skills - 認証・セッション管理モジュール（Phase 2）

ユーザー認証、セッション管理、アクセス制御を管理する。
現在は簡易実装。本番環境では JWT または OAuth2 に置き換える。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

import streamlit as st

from modules.security import (
    hash_password,
    verify_password,
    validate_username,
    validate_password,
    check_injection_attempt,
)
from modules.config import settings
from modules import data_manager

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """ユーザー認証を管理するクラス。"""
    
    def __init__(self):
        """初期化。"""
        self.session_key = "authenticated_user"
        self.session_timeout_key = "session_timeout"
    
    def is_authenticated(self) -> bool:
        """ユーザーが認証されているか確認する。
        
        Returns:
            認証済みなら True
        """
        if self.session_key not in st.session_state:
            return False
        
        # セッションタイムアウトをチェック
        if self.session_timeout_key in st.session_state:
            timeout = st.session_state[self.session_timeout_key]
            if datetime.now() > timeout:
                self.logout()
                return False
        
        return True
    
    def get_current_user(self) -> Optional[Dict]:
        """現在認証されているユーザー情報を取得する。
        
        Returns:
            ユーザー情報、または認証されていない場合は None
        """
        if not self.is_authenticated():
            return None
        
        return st.session_state.get(self.session_key)
    
    def register_user(self, username: str, password: str, email: Optional[str] = None) -> Tuple[bool, str]:
        """新規ユーザーを登録する。
        
        Args:
            username: ユーザー名
            password: パスワード
            email: メールアドレス（オプション）
            
        Returns:
            (成功フラグ, メッセージ) のタプル
        """
        # 入力値検証
        if not validate_username(username):
            return False, "無効なユーザー名形式です（英数字、アンダースコア、ハイフンのみ、2-32文字）"
        
        if check_injection_attempt(username):
            logger.warning(f"インジェクション攻撃の試行: username={username}")
            return False, "不正な入力が検出されました"
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return False, error_msg
        
        # ユーザー情報を取得（開発版は JSON ベース）
        user_profile = data_manager.load_json("user_profile.json", {})
        
        # ユーザー名の重複チェック
        if "users" in user_profile and user_profile["users"].get(username):
            return False, "このユーザー名は既に使用されています"
        
        # ユーザーデータを作成
        hashed_password = hash_password(password)
        new_user = {
            "username": username,
            "password_hash": hashed_password,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "level": 1,
            "xp": 0,
            "total_xp": 0,
            "badges": [],
            "achievements": [],
        }
        
        # ユーザーを保存
        if "users" not in user_profile:
            user_profile["users"] = {}
        
        user_profile["users"][username] = new_user
        
        if data_manager.save_json("user_profile.json", user_profile):
            logger.info(f"新規ユーザー登録: {username}")
            return True, "登録に成功しました"
        else:
            logger.error(f"ユーザー登録失敗: {username}")
            return False, "登録に失敗しました。もう一度お試しください"
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """ユーザーをログインさせる。
        
        Args:
            username: ユーザー名
            password: パスワード
            
        Returns:
            (成功フラグ, メッセージ) のタプル
        """
        # 入力値検証
        if not validate_username(username):
            return False, "ユーザー名またはパスワードが正しくありません"
        
        if check_injection_attempt(username):
            logger.warning(f"インジェクション攻撃の試行: username={username}")
            return False, "不正な入力が検出されました"
        
        # ユーザー情報を取得（開発版は JSON ベース）
        user_profile = data_manager.load_json("user_profile.json", {})
        
        if "users" not in user_profile or username not in user_profile["users"]:
            logger.warning(f"ログイン失敗（ユーザーなし）: {username}")
            return False, "ユーザー名またはパスワードが正しくありません"
        
        user_data = user_profile["users"][username]
        
        # パスワード検証
        if not verify_password(password, user_data["password_hash"]):
            logger.warning(f"ログイン失敗（パスワード不一致）: {username}")
            return False, "ユーザー名またはパスワードが正しくありません"
        
        # セッションにユーザー情報を保存
        st.session_state[self.session_key] = {
            "username": username,
            "email": user_data.get("email"),
            "level": user_data.get("level", 1),
            "xp": user_data.get("xp", 0),
            "total_xp": user_data.get("total_xp", 0),
        }
        
        # セッションタイムアウトを設定
        timeout = datetime.now() + timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        st.session_state[self.session_timeout_key] = timeout
        
        logger.info(f"ユーザーログイン: {username}")
        return True, "ログインに成功しました"
    
    def logout(self) -> None:
        """ユーザーをログアウトさせる。"""
        if self.session_key in st.session_state:
            username = st.session_state[self.session_key].get("username", "unknown")
            del st.session_state[self.session_key]
        
        if self.session_timeout_key in st.session_state:
            del st.session_state[self.session_timeout_key]
        
        logger.info(f"ユーザーログアウト: {username}")


# グローバルインスタンス
auth_manager = AuthenticationManager()
