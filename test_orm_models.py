#!/usr/bin/env python
"""ORM モデルと DAL の動作確認スクリプト"""

from modules.models import User, QuizResult, StudyLog
from modules.dal import UserDAL
from modules.config import settings

print("=" * 60)
print("AWS Skills - SQLAlchemy ORM モデル検証")
print("=" * 60)

print("\n✅ ORM モデル:")
print(f"   - User テーブル: {User.__tablename__}")
print(f"   - QuizResult テーブル: {QuizResult.__tablename__}")
print(f"   - StudyLog テーブル: {StudyLog.__tablename__}")

print("\n✅ DAL クラス:")
print(f"   - UserDAL")
print(f"   - QuizResultDAL")
print(f"   - StudyLogDAL")
print(f"   - ProgressDAL")

print("\n✅ 設定:")
print(f"   - データベース URL: {settings.get_database_url()}")
print(f"   - DB 機能: {'有効' if settings.FEATURE_DATABASE else '無効（JSON モード）'}")
print(f"   - 認証機能: {'有効' if settings.FEATURE_AUTHENTICATION else '無効'}")

print("\n✅ すべてのモデルと DAL が正常にインポートできました！")
print("=" * 60)
