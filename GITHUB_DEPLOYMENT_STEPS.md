# GitHub & Streamlit Cloud デプロイ 実行ガイド

**実行日**: 2026-08-20  
**対象**: AWS Skills Web プロジェクト

---

## 🔧 **前提条件チェック**

実行前に以下を確認してください：

- [ ] GitHub アカウントがある（https://github.com）
- [ ] GitHub Desktop または git がインストール済み
- [ ] Streamlit Community Cloud アカウントがある（https://share.streamlit.io）
- [ ] Streamlit Community Cloud に GitHub 連携済み

---

## 📋 **ステップ 1: GitHub でリポジトリを作成**

### 1.1 GitHub にログイン
- ブラウザで https://github.com にアクセス
- ログイン

### 1.2 新規リポジトリを作成
1. **右上の「+」マークをクリック** → **「New repository」**
2. **リポジトリ名**: `aws-skills-web`
3. **説明**: `AWS認定試験 学習アプリ（Streamlit）`
4. **プライバシー**: **Public**（Community Cloud でデプロイするため）
5. **Initialize this repository with**:
   - ❌ Add a README file（チェックなし）
   - ❌ Add .gitignore（チェックなし）
   - ❌ Choose a license（チェックなし）
6. **「Create repository」をクリック**

### 1.3 リポジトリの URL をコピー
```
https://github.com/your-username/aws-skills-web.git
```
（後で使用するのでメモしておく）

---

## 📤 **ステップ 2: ローカルで Git 初期化と push**

### 2.1 PowerShell/Terminal を開く
```powershell
cd c:\Users\dokechukwu\Documents\aws-skills-web
```

### 2.2 Git 初期化
```powershell
git init
git add .
git commit -m "Initial commit: AWS Skills Web - Phase 1-5 completed with Streamlit Cloud ready"
```

**入力例**:
```
Git user name: <あなたの GitHub ユーザー名>
Git user email: <あなたの GitHub メールアドレス>
```

### 2.3 リモートリポジトリを追加
```powershell
git remote add origin https://github.com/your-username/aws-skills-web.git
```

⚠️ **`your-username` を自分の GitHub ユーザー名に置き換えてください**

### 2.4 ブランチ名を main に変更
```powershell
git branch -M main
```

### 2.5 GitHub に push
```powershell
git push -u origin main
```

**認証画面が出たら**:
- **ユーザー名**: your-github-username
- **パスワード**: Personal Access Token（GitHub Settings → Developer settings → Personal access tokens で作成）

**または** GitHub Desktop を使用:
1. **Add → Add Existing Repository** を選択
2. ローカルフォルダを選択: `c:\Users\dokechukwu\Documents\aws-skills-web`
3. **Publish repository** をクリック
4. **GitHub.com** を選択
5. リポジトリ情報を入力して **Publish** をクリック

---

## 🚀 **ステップ 3: Streamlit Cloud でデプロイ**

### 3.1 Streamlit Community Cloud にアクセス
- ブラウザで https://share.streamlit.io にアクセス
- GitHub アカウントでログイン

### 3.2 新規アプリをデプロイ
1. **「New app」ボタンをクリック**
2. **次の情報を入力**:
   - **Repository**: `your-username/aws-skills-web`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
3. **「Deploy」をクリック**

**デプロイ開始** 🚀
- Streamlit Cloud がリポジトリをクローン
- 依存パッケージをインストール
- アプリを起動

デプロイには 1-3 分かかります。

### 3.3 ログを監視
- **「Manage app」** → **「Logs」** でログを確認
- エラーが表示される場合は、後述のトラブルシューティングを参照

---

## 🔐 **ステップ 4: Secrets（シークレット）を設定**

### 4.1 アプリ設定にアクセス
1. **Streamlit Cloud のアプリダッシュボード**
2. **アプリの右上メニュー** → **「Settings」**
3. **「Secrets」タブをクリック**

### 4.2 Secrets の内容を入力
以下をコピー&ペーストしてください：

```toml
# セキュリティ設定
SECRET_KEY = "your-production-secret-key-min-32-chars-change-this-to-random-string"
ENVIRONMENT = "production"
DEBUG = false

# データベース設定
DATABASE_URL = "sqlite:///./aws_skills.db"

# 認証設定
FEATURE_AUTHENTICATION = true
FEATURE_DATABASE = false

# その他
LOG_LEVEL = "INFO"
```

⚠️ **`SECRET_KEY` は必ず強力なランダム文字列に変更してください**

### 4.3 Secrets を保存
**「Save」ボタンをクリック**

---

## ✅ **ステップ 5: デプロイ確認**

### 5.1 アプリにアクセス
- Streamlit Cloud のダッシュボードからアプリのリンクをクリック
- または URL: `https://share.streamlit.io/your-username/aws-skills-web`

### 5.2 動作確認チェックリスト

- [ ] **ページがロードされる**（ロード画面から移行）
- [ ] **ログイン画面が表示される**（未認証時）
- [ ] **新規ユーザー登録ができる**
  - ユーザー名: `testuser`
  - パスワード: `TestPass123`
  - メール: `test@example.com`
- [ ] **ログインできる**
- [ ] **ホーム画面が表示される**
- [ ] **モバイル表示で確認**（DevTools で Responsive Mode に変更）
  - iPhone 12 (390px)
  - iPhone 11 (414px)
  - iPhone SE (375px)

### 5.3 各ページの動作確認

- [ ] **Practice** ページ: 問題が表示される
- [ ] **Exam** ページ: 試験モードが動作する
- [ ] **Analytics** ページ: 統計画面が表示される
- [ ] **Settings** ページ: 設定変更ができる
- [ ] **ログアウト**: ログアウト後、ログイン画面に戻る

---

## ⚠️ **トラブルシューティング**

### ❌ `ModuleNotFoundError: No module named 'streamlit'`

**原因**: パッケージがインストールされていない

**解決**:
1. Streamlit Cloud の Logs を確認
2. `requirements.txt` が正しく配置されているか確認
3. Streamlit Cloud の **「Reboot app」** をクリック

### ❌ `ConnectionError: database is locked`

**原因**: SQLite ファイルがロックされている

**解決**:
1. ローカルで `.db` ファイルを削除
2. GitHub に再度 push
3. Streamlit Cloud を再デプロイ

### ❌ ログイン後に `session_state error`

**原因**: Streamlit のセッション状態が初期化されていない

**解決**:
1. ブラウザキャッシュをクリア
2. Streamlit Cloud の **「Reboot app」** をクリック
3. ページをリロード

### ❌ `SECRET_KEY not found in secrets`

**原因**: Secrets が正しく設定されていない

**解決**:
1. Streamlit Cloud の Settings → Secrets を確認
2. `SECRET_KEY` が正しく入力されているか確認
3. **「Save」** をクリック
4. Streamlit Cloud の **「Reboot app」** をクリック

### ❌ モバイル表示が崩れている

**原因**: CSS が読み込まれていない

**解決**:
1. ブラウザを再度開く
2. DevTools → キャッシュをクリア → ページリロード
3. `.streamlit/config.toml` に `enableCORS = true` があるか確認

---

## 🔄 **更新・再デプロイ方法**

### コードを更新した場合

```powershell
# 1. 変更をコミット
git add .
git commit -m "Update: <変更内容>"

# 2. GitHub に push
git push origin main

# 3. Streamlit Cloud が自動的に再デプロイ（数分かかる場合あり）
#    または手動で「Reboot app」をクリック
```

### リアルタイムログを確認

Streamlit Cloud ダッシュボード → アプリ → **「Logs」**

---

## 📊 **デプロイメント チェックリスト**

```
[ ] GitHub リポジトリ作成
[ ] ローカルで git init と push 実行
[ ] Streamlit Cloud でリポジトリ選択
[ ] Main file path に streamlit_app.py を指定
[ ] デプロイ実行
[ ] Secrets に SECRET_KEY を設定
[ ] アプリがロードされることを確認
[ ] ログイン機能をテスト
[ ] モバイル表示を確認
[ ] 各ページが動作することを確認
```

---

## 🎯 **本番環境への推奨設定**

### PostgreSQL への移行（オプション、高性能化用）

**Secrets に以下を設定**:
```toml
DATABASE_URL = "postgresql://user:password@host:5432/database"
FEATURE_DATABASE = true
```

**対応サービス**:
- **Supabase** (推奨): https://supabase.com
  ```
  postgresql://user:password@db.supabase.co:5432/postgres
  ```
- **AWS RDS**
  ```
  postgresql://user:password@db-instance.xxx.rds.amazonaws.com:5432/awsskills
  ```
- **Azure Database**
  ```
  postgresql://user@server:password@server.postgres.database.azure.com:5432/db
  ```

---

## 📞 **サポート・参考リンク**

- **Streamlit 公式ドキュメント**: https://docs.streamlit.io
- **Streamlit Community Cloud**: https://discuss.streamlit.io
- **GitHub**: https://github.com
- **AWS Skills プロジェクト**: 本ローカルディレクトリ

---

## 📝 **デプロイ完了後のタスク**

- [ ] ユーザーへのアナウンス
- [ ] ユーザー登録の受け付け開始
- [ ] 学習データのバックアップ設定
- [ ] ログ監視の設定
- [ ] エラー報告の窓口設定
- [ ] フィードバック収集の開始

---

**デプロイ完了！AWS Skills Web が本番環境で稼働します！** 🎉
