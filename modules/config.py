"""AWS Skills - 設定管理モジュール

環境変数、シークレット、設定値を一元管理する。
開発環境と本番環境で異なる設定を切り替える。

設定の優先順位:
1. Streamlit secrets.toml（Community Cloud）
2. 環境変数（.env ファイルまたは OS 環境変数）
3. デフォルト値
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# .env ファイルを読み込む
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


# Streamlit secrets 対応（Community Cloud での読み込み）
def _get_secret(key: str, default: str = "") -> str:
    """設定値を取得（secrets.toml → 環境変数 → デフォルト値の順）"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except (ImportError, Exception):
        # Streamlit が利用不可（テスト環境など）
        pass
    
    return os.getenv(key, default)


class Settings:
    """アプリケーション設定クラス。
    
    環境変数から設定値を読み込み、デフォルト値を提供する。
    Streamlit Community Cloud では secrets.toml から読み込む。
    """
    
    # --- 環境設定 ---
    DEBUG: bool = _get_secret("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = _get_secret("ENVIRONMENT", "development")  # development | staging | production
    
    # --- セキュリティ設定 ---
    SECRET_KEY: str = _get_secret("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_TIMEOUT_MINUTES: int = int(_get_secret("SESSION_TIMEOUT_MINUTES", "30"))
    PASSWORD_MIN_LENGTH: int = int(_get_secret("PASSWORD_MIN_LENGTH", "8"))
    MAX_LOGIN_ATTEMPTS: int = int(_get_secret("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES: int = int(_get_secret("LOCKOUT_DURATION_MINUTES", "15"))
    
    # --- データベース設定 ---
    DATABASE_URL: str = _get_secret(
        "DATABASE_URL",
        "sqlite:///./aws_skills.db"  # デフォルト: SQLite
    )
    
    # PostgreSQL 用
    POSTGRES_USER: str = _get_secret("POSTGRES_USER", "aws_skills")
    POSTGRES_PASSWORD: str = _get_secret("POSTGRES_PASSWORD", "")
    POSTGRES_HOST: str = _get_secret("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(_get_secret("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = _get_secret("POSTGRES_DB", "aws_skills")
    
    # --- ファイルシステム設定 ---
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    BACKUP_DIR: Path = Path(__file__).parent.parent / "backups"
    LOG_DIR: Path = Path(__file__).parent.parent / "logs"
    
    # ディレクトリを作成
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    # --- ロギング設定 ---
    LOG_LEVEL: str = _get_secret("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
    
    # --- アプリケーション設定 ---
    APP_NAME: str = "AWS Skills"
    APP_VERSION: str = "2.1"
    
    # --- Streamlit 設定 ---
    STREAMLIT_PAGE_CONFIG: dict = {
        "page_title": f"{APP_NAME} | AWS認定試験 学習アプリ",
        "page_icon": "🚀",
        "layout": "wide",
        "initial_sidebar_state": "auto",
    }
    
    # --- セッション・クッキー設定 ---
    COOKIE_SECURE: bool = _get_secret("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_HTTPONLY: bool = _get_secret("COOKIE_HTTPONLY", "true").lower() == "true"
    COOKIE_SAMESITE: str = _get_secret("COOKIE_SAMESITE", "Strict")  # Strict | Lax | None
    
    # --- レート制限 ---
    ENABLE_RATE_LIMIT: bool = _get_secret("ENABLE_RATE_LIMIT", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    # --- 機能フラグ ---
    FEATURE_AUTHENTICATION: bool = os.getenv("FEATURE_AUTHENTICATION", "true").lower() == "true"
    FEATURE_DATABASE: bool = os.getenv("FEATURE_DATABASE", "false").lower() == "true"
    FEATURE_BACKUP: bool = os.getenv("FEATURE_BACKUP", "false").lower() == "true"
    
    @classmethod
    def is_production(cls) -> bool:
        """本番環境か判定する。"""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """開発環境か判定する。"""
        return cls.ENVIRONMENT == "development"
    
    @classmethod
    def validate(cls) -> list[str]:
        """設定の検証を行い、問題点をリストで返す。
        
        Returns:
            エラーメッセージのリスト（問題がない場合は空リスト）
        """
        errors = []
        
        # 本番環境でのチェック
        if cls.is_production():
            if cls.SECRET_KEY == "dev-secret-key-change-in-production":
                errors.append("本番環境では SECRET_KEY を変更してください")
            
            if not cls.COOKIE_SECURE:
                errors.append("本番環境では COOKIE_SECURE を true に設定してください")
            
            if cls.DEBUG:
                errors.append("本番環境では DEBUG を false に設定してください")
        
        # データベース設定のチェック
        if cls.FEATURE_DATABASE:
            if cls.DATABASE_URL.startswith("postgresql://"):
                if not cls.POSTGRES_PASSWORD:
                    errors.append("PostgreSQL 使用時は POSTGRES_PASSWORD を設定してください")
        
        return errors
    
    @classmethod
    def get_database_url(cls) -> str:
        """使用するデータベースの URL を取得する。
        
        Returns:
            データベース URL
        """
        if cls.FEATURE_DATABASE and not cls.DATABASE_URL.startswith("sqlite://"):
            # PostgreSQL 設定から URL を構築
            return (
                f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@"
                f"{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
            )
        return cls.DATABASE_URL


# グローバル設定インスタンス
settings = Settings()
