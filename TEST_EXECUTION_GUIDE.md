# Phase 4 テスト実行ガイド

## 🚀 クイックスタート

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. テスト実行

#### すべてのテストを実行
```bash
pytest
```

#### セキュリティテストのみ
```bash
pytest tests/test_security.py -v
```

#### 統合テストのみ
```bash
pytest tests/test_integration.py -v
```

#### カバレッジ付き実行
```bash
pytest --cov=modules --cov=tools --cov-report=term-missing
```

#### HTML カバレッジレポート生成
```bash
pytest --cov=modules --cov=tools --cov-report=html
# → htmlcov/index.html をブラウザで開く
```

#### 特定のテストクラスを実行
```bash
pytest tests/test_security.py::TestPasswordHashing -v
```

#### 特定のテストメソッドを実行
```bash
pytest tests/test_security.py::TestPasswordHashing::test_hash_password_success -v
```

---

## 📊 テストスイート構成

### 作成されたファイル

```
tests/
├── __init__.py                  # テストパッケージ初期化
├── conftest.py                  # フィクスチャと共通設定
├── test_security.py             # セキュリティテスト (50+)
├── test_auth.py                 # 認証テスト (20+)
├── test_models.py               # ORM モデルテスト (30+)
├── test_dal.py                  # DAL テスト (40+)
├── test_integration.py          # 統合テスト (25+)
└── run_tests.py                 # テスト実行ユーティリティ

pytest.ini                        # pytest 設定
```

### テスト数

| ファイル | テスト数 |
|---------|---------|
| test_security.py | 50+ |
| test_auth.py | 20+ |
| test_models.py | 30+ |
| test_dal.py | 40+ |
| test_integration.py | 25+ |
| **合計** | **165+** |

---

## 🧪 テスト実行パターン

### パターン 1: 高速テスト（ユニットテストのみ）
```bash
pytest -m unit -v
# 実行時間: < 5 秒
```

### パターン 2: 完全なテストスイート
```bash
pytest -v
# 実行時間: 15-30 秒
```

### パターン 3: セキュリティ検証
```bash
pytest -m security -v
# XSS、SQL インジェクション等を検証
```

### パターン 4: パフォーマンステスト
```bash
pytest -m performance -v
# 大量データ処理等を検証
```

---

## ✅ テスト成功の確認

テスト実行時に以下のような出力が表示されれば成功です：

```
======================== 165 passed in 20.42s ========================
```

### 各テストファイルの確認

```bash
# セキュリティテスト
pytest tests/test_security.py -q
# → 50+ passed

# 認証テスト
pytest tests/test_auth.py -q
# → 20+ passed

# モデルテスト
pytest tests/test_models.py -q
# → 30+ passed

# DAL テスト
pytest tests/test_dal.py -q
# → 40+ passed

# 統合テスト
pytest tests/test_integration.py -q
# → 25+ passed
```

---

## 🔍 トラブルシューティング

### Issue 1: "No module named 'modules'"
```bash
# 原因: PYTHONPATH が設定されていない
# 解決策:
cd c:\Users\dokechukwu\Documents\aws-skills-web
pytest
```

### Issue 2: "No module named 'pytest'"
```bash
# 原因: pytest がインストールされていない
# 解決策:
pip install -r requirements.txt
```

### Issue 3: "database is locked"
```bash
# 原因: SQLite テンポラリファイルがロック中
# 解決策:
rm -f aws_skills_test.db*
pytest
```

### Issue 4: テストが遅い
```bash
# 解決策: 遅いテストを除外
pytest -m "not slow"

# または 並列実行（別途インストール必要）
pip install pytest-xdist
pytest -n 4  # 4 並列で実行
```

---

## 📈 カバレッジ確認

### ターミナル出力
```bash
pytest --cov=modules --cov-report=term-missing
```

### 出力例
```
modules/security.py       95%      (5 lines)
modules/auth.py           88%      (12 lines)
modules/models.py         90%      (10 lines)
modules/dal.py            92%      (8 lines)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                      90%      (35 lines)
```

### HTML レポート
```bash
pytest --cov=modules --cov=tools --cov-report=html
# htmlcov/index.html をブラウザで開く
```

---

## 📝 テストマーカー

### 利用可能なマーカー

```python
@pytest.mark.unit           # ユニットテスト（高速）
@pytest.mark.integration    # 統合テスト（DB 含む）
@pytest.mark.security       # セキュリティテスト
@pytest.mark.performance    # パフォーマンステスト
@pytest.mark.slow           # 長時間実行テスト
```

### マーカー実行例

```bash
# ユニットテストのみ（高速）
pytest -m unit -v

# セキュリティテストのみ
pytest -m security -v

# 遅いテストを除外
pytest -m "not slow" -v

# 複数マーカー組み合わせ
pytest -m "unit and not slow" -v
```

---

## 🛠️ 連続テスト実行（Watch Mode）

```bash
# ptw がインストールされている場合
pip install pytest-watch
ptw

# ファイル変更時に自動実行
```

---

## 📚 参考資料

- [pytest 公式ドキュメント](https://docs.pytest.org/)
- [Streamlit テスト](https://docs.streamlit.io/library/advanced-features/app-testing)
- [SQLAlchemy テスト](https://docs.sqlalchemy.org/en/14/orm/test.html)

---

## ✨ Phase 4 完了チェックリスト

- ✅ pytest インストール
- ✅ テストファイル作成（165+ テスト）
- ✅ conftest.py 設定完了
- ✅ Security テスト実装
- ✅ Authentication テスト実装
- ✅ ORM Models テスト実装
- ✅ DAL テスト実装
- ✅ Integration テスト実装
- ✅ カバレッジ測定設定完了

---

**最終更新**: 2026-08-19  
**テスト数**: 165+  
**期待カバレッジ**: 90%+
