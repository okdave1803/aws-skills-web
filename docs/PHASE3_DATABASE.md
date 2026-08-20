# AWS Skills - データベース移行ガイド（Phase 3）

**実装日**: 2026-08-19  
**バージョン**: 2.1-database-phase3  
**ステータス**: ✅ 完了（基本実装）

---

## Phase 3: データベース移行の完全実装

### 📋 実装内容

#### 1️⃣ SQLAlchemy ORM モデル定義 (`modules/models.py`)
- ✅ **User テーブル**: ユーザーマスター
  - username, email, password_hash
  - level, xp, total_xp
  - exam_code, exam_date
  - badges, achievements
  - created_at, updated_at, last_login_at

- ✅ **QuizResult テーブル**: クイズ・試験結果
  - user_id (外部キー)
  - question_id, quiz_mode, quiz_source
  - selected_indices, is_correct, time_spent_seconds
  - exam_code, category, domain, topic, difficulty

- ✅ **StudyLog テーブル**: 学習ログ
  - user_id (外部キー)
  - duration_seconds, category, exam_code
  - created_at

- ✅ **Session テーブル**: セッション管理
  - user_id (外部キー)
  - token, expires_at
  - ip_address, user_agent

- ✅ **Progress テーブル**: 学習進捗（日別集計）
  - user_id, study_date
  - total_studied_seconds, questions_attempted, accuracy
  - streak_days

#### 2️⃣ データアクセスレイヤー（DAL）- `modules/dal.py`
- ✅ **UserDAL**: ユーザー管理
  ```python
  create_user()          # ユーザー作成
  get_user_by_username() # ユーザー取得
  get_user_by_id()       # ID からユーザー取得
  verify_password()      # パスワード検証
  update_user()          # ユーザー更新
  update_last_login()    # ラストログイン更新
  ```

- ✅ **QuizResultDAL**: クイズ結果管理
  ```python
  create_result()        # 結果作成
  get_user_results()     # ユーザーの結果取得
  get_category_stats()   # カテゴリ別統計
  ```

- ✅ **StudyLogDAL**: 学習ログ管理
  ```python
  create_log()           # ログ作成
  get_study_dates()      # 学習日を取得
  calculate_streak()     # 連続学習日数計算
  ```

- ✅ **ProgressDAL**: 進捗管理
  ```python
  get_or_create_today_progress()  # 今日の進捗
  update_progress()               # 進捗更新
  ```

#### 3️⃣ マイグレーション実行スクリプト (`tools/migrate_to_db.py`)
- ✅ **JSON バックアップ**: 自動バックアップ作成
- ✅ **ユーザー移行**: user_profile.json → users テーブル
- ✅ **結果移行**: results.json → quiz_results テーブル
- ✅ **学習ログ移行**: study_time.json → study_logs テーブル
- ✅ **段階的移行**: 既存データ損失なし

**実行方法**:
```bash
python tools/migrate_to_db.py
```

#### 4️⃣ ハイブリッド data_manager (`modules/data_manager_hybrid.py`)
- ✅ **自動切り替え**: FEATURE_DATABASE フラグで DB/JSON を切り替え
- ✅ **後方互換性**: 既存の data_manager.py API を完全サポート
- ✅ **段階的マイグレーション**: 開発中に JSON と DB を併用可能

**API**:
```python
init_data()              # 初期化（DB/JSON 自動選択）
get_study_dates()        # 学習日取得
get_streak()             # ストリーク計算
record_exam_result()     # 試験結果記録
add_study_time()         # 学習時間記録
update_user_profile()    # プロフィール更新
add_badge()              # バッジ追加
get_category_stats()     # カテゴリ統計
```

---

## 🗄️ データベーススキーマ

### SQLite（開発環境）
```bash
# 自動作成（初回実行時）
sqlite:///./aws_skills.db
```

### PostgreSQL（本番環境）
```bash
# 手動作成推奨
psql -U postgres -c "CREATE DATABASE aws_skills OWNER aws_skills;"

# .env で設定
DATABASE_URL=postgresql://aws_skills:password@localhost:5432/aws_skills
```

---

## 🔄 マイグレーション手順

### ステップ 1: バックアップ作成
```bash
python tools/migrate_to_db.py
# → backups/json_backup_YYYYMMDD_HHMMSS/ に自動保存
```

### ステップ 2: 設定変更
`.env` ファイルを編集:
```bash
FEATURE_DATABASE=true  # false から true に変更
DATABASE_URL=sqlite:///./aws_skills.db  # または PostgreSQL URL
```

### ステップ 3: アプリケーション再起動
```bash
streamlit run streamlit_app.py
```

### ステップ 4: ロールバック（必要な場合）
```bash
# JSON ファイルを backups/ から復元
cp backups/json_backup_YYYYMMDD_HHMMSS/* data/

# .env を戻す
FEATURE_DATABASE=false
```

---

## ✅ テスト結果

### ORM テスト（SQLite）
```
✅ テーブル作成: users, quiz_results, study_logs, progress, sessions
✅ ユーザー作成: testuser (id=1)
✅ ユーザー取得: 成功
✅ パスワード検証: 成功（正/誤両方）
✅ ユーザー更新: 成功
```

### マイグレーション スクリプト
- ✅ バックアップ機能: 実装完了
- ✅ ユーザー移行: JSON → DB
- ✅ 結果移行: JSON → DB
- ✅ 学習ログ移行: JSON → DB
- ✅ ロールバック機能: 実装完了

---

## 🔧 環境別設定

### 開発環境（推奨）
```env
ENVIRONMENT=development
DEBUG=true
FEATURE_DATABASE=false      # JSON モードで開発
DATABASE_URL=sqlite:///./aws_skills.db
```

### テスト環境（DB テスト用）
```env
ENVIRONMENT=staging
DEBUG=false
FEATURE_DATABASE=true
DATABASE_URL=sqlite:///./aws_skills_test.db
```

### 本番環境
```env
ENVIRONMENT=production
DEBUG=false
FEATURE_DATABASE=true
DATABASE_URL=postgresql://aws_skills:secure_pwd@prod-db:5432/aws_skills
COOKIE_SECURE=true
```

---

## 📊 パフォーマンス最適化

### インデックス設定
- `users(username)` - ユーザー名検索
- `users(email)` - メールアドレス検索
- `users(created_at)` - 日付範囲検索
- `quiz_results(user_id, created_at)` - ユーザー別結果取得
- `quiz_results(category)` - カテゴリ別集計
- `study_logs(user_id, created_at)` - 学習ログ検索
- `progress(user_id, study_date)` - ユーザー別日付検索

### クエリ最適化
- [x] N+1 クエリ防止（relationship eager loading）
- [x] バッチ処理対応（bulk_insert_mappings）
- [x] キャッシング対応（@st.cache_data）
- [ ] 読み取り用レプリカ（本番環境で検討）

---

## 🔐 セキュリティ機能

### データベースレベル
- ✅ パスワード: bcrypt ハッシング
- ✅ セッション: タイムアウト管理
- ✅ トランザクション: 自動ロールバック
- ✅ 接続: SSL/TLS 対応（PostgreSQL 本番）

### アプリケーションレベル
- ✅ 入力値検証: SQL インジェクション対策
- ✅ ORM使用: SQL インジェクション防止
- ✅ ユーザー認証: bcrypt + セッション
- ✅ 監査ログ: created_at, updated_at 自動記録

---

## 📝 次のステップ

### Phase 3 拡張機能
- [ ] パスワードリセット機能
- [ ] メール認証
- [ ] 2FA（二要素認証）
- [ ] OAuth2 / Google ログイン

### Phase 4: テスト・監視
- [ ] ユニットテスト（pytest）
- [ ] 統合テスト（DB を含む）
- [ ] E2E テスト
- [ ] パフォーマンステスト
- [ ] セキュリティテスト

### スケーラビリティ改善
- [ ] クエリキャッシング（Redis）
- [ ] 接続プーリング最適化
- [ ] 読み取り用レプリカ
- [ ] シャーディング戦略
- [ ] バックアップ・リカバリー自動化

---

## 📞 トラブルシューティング

### "データベース接続エラー"
```bash
# PostgreSQL の場合、接続確認
psql -U aws_skills -h localhost -d aws_skills

# SQLite の場合、ファイルアクセス確認
ls -la aws_skills.db
```

### "テーブルが見つからない"
```bash
# テーブル再作成
python -c "from modules.models import init_db; init_db('sqlite:///./aws_skills.db')"
```

### "マイグレーション失敗時"
```bash
# バックアップから復元
cp -r backups/json_backup_YYYYMMDD_HHMMSS/* data/

# FEATURE_DATABASE を false に戻す
sed -i 's/FEATURE_DATABASE=true/FEATURE_DATABASE=false/g' .env
```

---

## 📚 参考資料

- [SQLAlchemy ドキュメント](https://docs.sqlalchemy.org/)
- [PostgreSQL ドキュメント](https://www.postgresql.org/docs/)
- [SQLite ドキュメント](https://www.sqlite.org/docs.html)

---

**最終更新**: 2026-08-19  
**次回更新予定**: Phase 4 テスト実装時
