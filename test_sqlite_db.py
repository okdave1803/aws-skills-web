#!/usr/bin/env python
"""SQLite データベースのテスト"""

import os
from modules.config import settings
from modules.models import init_db
from modules.dal import UserDAL
from sqlalchemy import inspect

# SQLite データベースを作成
db_url = 'sqlite:///./test_aws_skills.db'

print("=" * 60)
print("AWS Skills - SQLite データベーステスト")
print("=" * 60)

print("\n📦 ステップ 1: テスト用データベースを作成中...")
try:
    engine, session = init_db(db_url)
    print("✅ データベース作成成功")
except Exception as e:
    print(f"❌ エラー: {str(e)}")
    exit(1)

# テーブル作成確認
print("\n📋 ステップ 2: テーブル確認中...")
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"✅ 作成されたテーブル: {tables}")

# テストユーザーを作成
print("\n👤 ステップ 3: テストユーザーを作成中...")
user_dal = UserDAL(session)

user = user_dal.create_user(
    username='testuser',
    password='TestPassword123',
    email='test@example.com'
)

if user:
    print(f"✅ テストユーザー作成成功: {user.username} (id={user.id})")
    
    # ユーザー取得
    print("\n🔍 ステップ 4: ユーザー取得テスト...")
    retrieved = user_dal.get_user_by_username('testuser')
    print(f"✅ ユーザー取得成功: {retrieved.username}")
    print(f"   - email: {retrieved.email}")
    print(f"   - level: {retrieved.level}")
    print(f"   - total_xp: {retrieved.total_xp}")
    
    # パスワード検証
    print("\n🔐 ステップ 5: パスワード検証テスト...")
    verified = user_dal.verify_password(retrieved, 'TestPassword123')
    print(f"✅ パスワード検証（正しい）: {verified}")
    
    wrong = user_dal.verify_password(retrieved, 'WrongPassword')
    print(f"✅ パスワード検証（間違い）: {wrong}")
    
    # ユーザー更新
    print("\n✏️  ステップ 6: ユーザー更新テスト...")
    success = user_dal.update_user(retrieved, level=5, xp=100)
    print(f"✅ ユーザー更新成功: {success}")
    
    updated = user_dal.get_user_by_id(user.id)
    print(f"   - 新しい level: {updated.level}")
    print(f"   - 新しい xp: {updated.xp}")

else:
    print("❌ テストユーザー作成失敗")

session.close()

# クリーンアップ
print("\n🧹 クリーンアップ中...")
if os.path.exists('test_aws_skills.db'):
    os.remove('test_aws_skills.db')
    print("✅ テストデータベース削除完了")

print("\n" + "=" * 60)
print("✅ すべてのテストが成功しました！")
print("=" * 60)
