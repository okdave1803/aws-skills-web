"""
pytest フィクスチャと共通設定
"""

import os
import sys
import pytest
import tempfile
import logging
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_env():
    """テスト環境変数を設定"""
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['DEBUG'] = 'true'
    os.environ['FEATURE_AUTHENTICATION'] = 'true'
    os.environ['FEATURE_DATABASE'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key-12345'
    os.environ['SESSION_TIMEOUT_MINUTES'] = '30'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    return os.environ


@pytest.fixture(scope="session")
def temp_db():
    """一時的なテスト用データベースを作成"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:///{db_path}"
    logger.info(f"テスト用データベース作成: {db_path}")
    
    yield db_url
    
    # クリーンアップ
    try:
        os.unlink(db_path)
        logger.info(f"テスト用データベース削除: {db_path}")
    except Exception as e:
        logger.warning(f"データベース削除失敗: {e}")


@pytest.fixture(scope="function")
def db_session(temp_db):
    """テスト用のデータベースセッションを作成
    
    各テスト関数ごとに独立したセッションを提供し、
    テスト終了後に自動的にロールバックとクリーンアップを実行する。
    """
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
    from modules.models import Base
    
    # エンジン作成
    engine = create_engine(temp_db, echo=False, isolation_level="SERIALIZABLE")
    
    # テーブル作成
    Base.metadata.create_all(engine)
    
    # セッション作成
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    
    try:
        yield session
    finally:
        # ロールバック（テスト中の変更をクリア）
        try:
            session.rollback()
        except Exception as e:
            logger.warning(f"Session rollback 失敗: {e}")
        
        # セッションクローズ
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Session close 失敗: {e}")
        
        # テーブルドロップ（テストデータ削除）
        try:
            Base.metadata.drop_all(engine)
        except Exception as e:
            logger.warning(f"Table drop 失敗: {e}")
        
        # エンジンディスポーズ（接続プール解放）
        try:
            engine.dispose()
        except Exception as e:
            logger.warning(f"Engine dispose 失敗: {e}")


@pytest.fixture
def mock_config(monkeypatch, test_env):
    """モック設定を作成"""
    from modules import config
    
    # 設定をリロード
    monkeypatch.setenv('ENVIRONMENT', 'testing')
    monkeypatch.setenv('DEBUG', 'true')
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    
    return config.Settings


@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータ"""
    return {
        'username': 'testuser',
        'password': 'SecurePass123',
        'email': 'test@example.com'
    }


@pytest.fixture
def sample_quiz_result_data():
    """サンプルクイズ結果データ"""
    return {
        'question_id': 1,
        'quiz_mode': 'study',
        'quiz_source': 'exam_prep',
        'selected_indices': [0, 1],
        'is_correct': True,
        'time_spent_seconds': 45,
        'category': 'EC2',
        'domain': 'Compute',
        'topic': 'Instances',
        'difficulty': 'medium'
    }


@pytest.fixture
def sample_study_log_data():
    """サンプル学習ログデータ"""
    return {
        'duration_seconds': 3600,
        'category': 'S3',
        'exam_code': 'SAA-C03'
    }


@pytest.fixture
def auth_manager():
    """認証マネージャーをモック化"""
    from modules.auth import AuthenticationManager
    return AuthenticationManager()


# マーカー定義
def pytest_configure(config):
    """pytest 初期化"""
    config.addinivalue_line(
        "markers", "unit: ユニットテスト（外部依存なし）"
    )
    config.addinivalue_line(
        "markers", "integration: 統合テスト（データベース含む）"
    )
    config.addinivalue_line(
        "markers", "security: セキュリティテスト"
    )
    config.addinivalue_line(
        "markers", "performance: パフォーマンステスト"
    )
    config.addinivalue_line(
        "markers", "slow: 長時間実行テスト"
    )
