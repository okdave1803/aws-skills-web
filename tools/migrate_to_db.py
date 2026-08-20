#!/usr/bin/env python
"""AWS Skills - JSON から PostgreSQL/SQLite へのマイグレーション

既存の JSON データをデータベースに移行する。
バックアップを取り、段階的にデータを移行する。
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from modules.config import settings
from modules.dal import UserDAL, QuizResultDAL, StudyLogDAL, ProgressDAL
from modules.models import init_db

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def backup_json_data() -> Path:
    """JSON データをバックアップする。
    
    Returns:
        バックアップディレクトリのパス
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = settings.BACKUP_DIR / f"json_backup_{timestamp}"
    backup_dir.mkdir(exist_ok=True)
    
    for filename in settings.DATA_DIR.glob("*.json"):
        shutil.copy2(filename, backup_dir / filename.name)
        logger.info(f"バックアップ: {filename.name} → {backup_dir}")
    
    return backup_dir


def migrate_users(session: Session, data_dir: Path) -> int:
    """ユーザープロフィール JSON からユーザーテーブルへ移行。
    
    Args:
        session: SQLAlchemy セッション
        data_dir: データディレクトリ
        
    Returns:
        移行したユーザー数
    """
    user_profile_file = data_dir / "user_profile.json"
    
    if not user_profile_file.exists():
        logger.warning("user_profile.json が見つかりません")
        return 0
    
    with open(user_profile_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 旧フォーマット（単一ユーザー）をチェック
    if "users" not in data:
        # 旧フォーマット: 単一ユーザープロフィール
        logger.info("旧フォーマットのユーザープロフィールを検出")
        
        user_dal = UserDAL(session)
        
        # デフォルトユーザーを作成（パスワードなし、デモ用）
        existing = user_dal.get_user_by_username("demo_user")
        if not existing:
            user = user_dal.create_user(
                username="demo_user",
                password="DemoPassword123",
                email=None
            )
            if user:
                # プロフィール情報を更新
                user_dal.update_user(
                    user,
                    level=data.get("level", 1),
                    xp=data.get("xp", 0),
                    total_xp=data.get("total_xp", 0),
                    exam_code=data.get("target_exam", "SAA-C03"),
                    exam_date=data.get("exam_date"),
                    badges=data.get("badges", []),
                    achievements=data.get("achievements", []),
                )
                logger.info(f"ユーザー移行: demo_user (id={user.id})")
                return 1
        
        return 0
    
    # Phase 2 フォーマット：複数ユーザー
    user_dal = UserDAL(session)
    migrated = 0
    
    for username, user_data in data.get("users", {}).items():
        existing = user_dal.get_user_by_username(username)
        
        if not existing:
            user = user_dal.create_user(
                username=username,
                password=user_data.get("password_hash", "TempPass123"),  # ハッシュをそのまま使用
                email=user_data.get("email"),
            )
            
            if user:
                user_dal.update_user(
                    user,
                    level=user_data.get("level", 1),
                    xp=user_data.get("xp", 0),
                    total_xp=user_data.get("total_xp", 0),
                    exam_code=user_data.get("exam_code", "SAA-C03"),
                    badges=user_data.get("badges", []),
                    achievements=user_data.get("achievements", []),
                )
                migrated += 1
                logger.info(f"ユーザー移行: {username} (id={user.id})")
        else:
            logger.info(f"ユーザー既に存在: {username} (スキップ)")
    
    logger.info(f"ユーザー移行完了: {migrated} 件")
    return migrated


def migrate_results(session: Session, data_dir: Path) -> int:
    """クイズ結果 JSON からテーブルへ移行。
    
    Args:
        session: SQLAlchemy セッション
        data_dir: データディレクトリ
        
    Returns:
        移行した結果数
    """
    results_file = data_dir / "results.json"
    
    if not results_file.exists():
        logger.warning("results.json が見つかりません")
        return 0
    
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    if not isinstance(results, list):
        logger.warning("results.json が配列形式ではありません")
        return 0
    
    quiz_dal = QuizResultDAL(session)
    migrated = 0
    
    # デフォルトユーザー ID（demo_user）
    default_user_id = 1
    
    for result in results:
        try:
            quiz_dal.create_result(
                user_id=default_user_id,
                question_id=result.get("question_id", 0),
                quiz_mode=result.get("mode", "study"),
                quiz_source=result.get("source", "practice"),
                is_correct=result.get("correct", False),
                time_spent_seconds=result.get("time_spent", None),
                exam_code=result.get("exam", None),
                category=result.get("category", None),
                domain=result.get("domain", None),
                topic=result.get("topic", None),
                difficulty=result.get("difficulty", None),
            )
            migrated += 1
        
        except Exception as e:
            logger.warning(f"結果移行エラー: {str(e)}")
    
    logger.info(f"クイズ結果移行完了: {migrated} 件")
    return migrated


def migrate_study_time(session: Session, data_dir: Path) -> int:
    """学習時間 JSON からテーブルへ移行。
    
    Args:
        session: SQLAlchemy セッション
        data_dir: データディレクトリ
        
    Returns:
        移行したログ数
    """
    study_file = data_dir / "study_time.json"
    
    if not study_file.exists():
        logger.warning("study_time.json が見つかりません")
        return 0
    
    with open(study_file, "r", encoding="utf-8") as f:
        study_logs = json.load(f)
    
    if not isinstance(study_logs, list):
        logger.warning("study_time.json が配列形式ではありません")
        return 0
    
    study_dal = StudyLogDAL(session)
    migrated = 0
    
    # デフォルトユーザー ID
    default_user_id = 1
    
    for log in study_logs:
        try:
            study_dal.create_log(
                user_id=default_user_id,
                duration_seconds=log.get("duration", 0),
                category=log.get("category", "general"),
            )
            migrated += 1
        
        except Exception as e:
            logger.warning(f"学習ログ移行エラー: {str(e)}")
    
    logger.info(f"学習ログ移行完了: {migrated} 件")
    return migrated


def main():
    """マイグレーション実行。"""
    print("=" * 60)
    print("AWS Skills - JSON → データベース マイグレーション")
    print("=" * 60)
    
    # バックアップ作成
    print("\n📦 ステップ 1: JSON データのバックアップを作成中...")
    backup_dir = backup_json_data()
    print(f"✅ バックアップ完了: {backup_dir}")
    
    # データベース初期化
    print("\n🗄️  ステップ 2: データベースを初期化中...")
    db_url = settings.get_database_url()
    print(f"   データベース URL: {db_url}")
    
    try:
        engine, session = init_db(db_url)
        print("✅ データベース初期化完了")
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
        print(f"❌ エラー: {str(e)}")
        return False
    
    # データ移行
    print("\n📋 ステップ 3: データを移行中...")
    
    try:
        user_count = migrate_users(session, settings.DATA_DIR)
        result_count = migrate_results(session, settings.DATA_DIR)
        log_count = migrate_study_time(session, settings.DATA_DIR)
        
        print(f"✅ ユーザー移行: {user_count} 件")
        print(f"✅ クイズ結果移行: {result_count} 件")
        print(f"✅ 学習ログ移行: {log_count} 件")
        
        session.close()
        print("\n✅ マイグレーション完了！")
        
        print("\n📌 次のステップ:")
        print(f"   1. .env ファイルで FEATURE_DATABASE=true に設定")
        print(f"   2. アプリケーションを再起動")
        print(f"   3. ログインして動作確認")
        
        return True
    
    except Exception as e:
        logger.error(f"マイグレーションエラー: {str(e)}")
        print(f"❌ エラー: {str(e)}")
        session.close()
        return False


if __name__ == "__main__":
    import sys
    
    success = main()
    sys.exit(0 if success else 1)
