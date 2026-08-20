# AWS Skills - AWS認定試験 学習アプリ

**v2.1 - Skill Builder Edition**

AWS 認定試験の学習を支援する Web アプリです。
ブラウザから利用でき、iPhone・Android・PC すべてに対応しています。

## 🎯 画面構成

| 画面 | 内容 |
| --- | --- |
| 🏠 ホーム | 学習進捗、主要指標、続きから学習、週間アクティビティ |
| 🧭 学習パス | 認定資格別の学習コースと目標設定 |
| 📅 今日の学習 | 今日の目標、おすすめサービス、チェックリスト |
| ✏️ 練習問題 | 学習モード / 試験モード、カテゴリ・問題数の選択 |
| 📋 模擬試験 | 本番形式・短時間・全問演習、受験履歴 |
| 📖 AWSサービス辞典 | 主要サービスの検索と試験ポイント |
| 📊 分析 | 正答率の推移、分野別正答率、学習時間 |
| 🏆 実績 | レベル・XP・バッジ |
| ⚙️ 設定 | プロフィール、目標試験、CSV出力、データ初期化 |

### 主な機能

- 🎓 **学習モード / 試験モード** - 解説を即時表示、または試験後にまとめて確認
- 📝 **選択肢ごとの解説** - 正解の理由だけでなく、誤答がなぜ誤りかも表示
- 🔗 **出典リンク** - 各問題に AWS 公式ドキュメントへのリンクを収録
- ☑️ **複数選択問題に対応** - 集合一致で採点（部分点なし）
- 📈 **弱点分析** - 論点 / 出題分野 / AWS サービス / カテゴリの4つの単位で正答率を集計
- 🔥 **連続学習ストリーク** と週間アクティビティ
- ⭐ **レベルと XP、実績バッジ** による学習の継続支援
- 💾 **データエクスポート** - CSV 形式

## 📚 問題データについて

問題は `data/questions.json` に保存されています（schema_version 2）。
1 問ごとに次の情報を持ちます。

| 項目 | 内容 |
| --- | --- |
| `domain` / `topic` | 出題分野と論点。弱点分析の集計単位 |
| `difficulty` | 基礎 / 標準 / 応用 / 難関 |
| `type` / `select_count` / `correct` | 単一選択・複数選択と正解（インデックスの配列） |
| `services` | 関連 AWS サービス（サービス辞典と相互参照） |
| `exam` | 対象試験コード（CLF-C02、SAA-C03 など） |
| `explanation` | 全体解説（3〜5 文） |
| `option_explanations` | 選択肢ごとの解説（誤答の理由を含む） |
| `references` | 出典 URL |

- 形式の定義: `data/questions.schema.json`
- 追加・編集のしかた: [`docs/questions.md`](docs/questions.md)
- 検証: `python tools/validate_questions.py`
  （`--check-urls` を付けると出典 URL の到達性も確認します）

> 問題文は AWS 公式ドキュメントと試験ガイドの出題範囲をもとにした
> オリジナルの内容です。有料教材や公式模擬試験からの転載は含みません。

## 📱 対応デバイス

- ✅ iPhone / iPad
- ✅ Android
- ✅ PC / Mac
- ✅ タブレット

## 🚀 クイックスタート

### 1. インストール

```bash
# リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/aws-skills-web.git
cd aws-skills-web

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. ローカルで実行

```bash
streamlit run streamlit_app.py
```

ブラウザが自動で開きます。通常 `http://localhost:8501` でアクセス可能です。

### 3. データの準備

既存のデスクトップ版データを使用できます：

```
aws-skills-web/
└── data/
    ├── questions.json (問題データ)
    ├── user_profile.json (ユーザー情報)
    ├── results.json (試験結果)
    ├── study_time.json (学習時間)
    ├── services.json (AWSサービス)
    └── config.json (設定)
```

初回実行時に自動作成されます。

## 🌐 Streamlit Community Cloud へ無料公開

### ステップ1: GitHub へアップロード

```bash
# Git初期化
git init
git add .
git commit -m "Initial commit: AWS Skills Web App"

# GitHubにプッシュ
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/aws-skills-web.git
git push -u origin main
```

### ステップ2: Community Cloud で公開

1. [Streamlit Community Cloud](https://streamlit.io/cloud) にアクセス
2. GitHub アカウントで連携
3. "New app" をクリック
4. リポジトリを選択: `aws-skills-web`
5. ブランチ: `main`
6. ファイル: `streamlit_app.py`

**ポイント:**
- 無料で公開可能
- カスタムドメイン設定可
- HTTPS対応

公開URLは以下の形式になります：
```
https://YOUR_USERNAME-aws-skills-web.streamlit.app
```

## 📱 スマートフォンから使う方法

### iPhoneの場合

1. Safari で上記のURLにアクセス
2. 下部の共有ボタン → "ホーム画面に追加"
3. アイコンをタップしてアプリとして利用可能（PWA）

### Androidの場合

1. Chrome で上記のURLにアクセス
2. メニュー → "アプリをインストール"
3. またはホーム画面に追加

## 🔐 環境変数（オプション）

`.streamlit/secrets.toml` にシークレット情報を保存できます：

```toml
[database]
username = "user"
password = "password"

[email]
api_key = "sk_xxx"
```

## 📊 ファイル構成

```
aws-skills-web/
├── streamlit_app.py          # メインアプリケーション
├── requirements.txt          # Python依存関係
├── README.md                 # このファイル
├── .gitignore               # Git除外設定
├── .streamlit/
│   └── config.toml          # Streamlit設定
├── modules/
│   ├── __init__.py
│   ├── theme.py             # カラートークンとグローバルCSS
│   ├── content.py           # 学習パス・今日の学習・バッジ定義
│   ├── quiz.py              # 出題エンジン（学習/試験モード）
│   ├── ui_components.py     # UIコンポーネント
│   ├── data_manager.py      # データ管理
│   ├── calculator.py        # 計算ロジック
│   └── analytics.py         # 分析機能
├── tools/
│   └── validate_questions.py # 問題データの検証スクリプト
├── docs/
│   └── questions.md          # 問題の追加・編集ガイド
├── data/                     # データファイル
│   ├── questions.json
│   ├── questions.schema.json # 問題データの形式定義
│   ├── user_profile.json
│   ├── results.json
│   ├── study_time.json
│   ├── services.json
│   ├── config.json
│   └── exam_history.json
└── static/                   # 静的ファイル
```

## 🔄 既存データとの互換性

デスクトップ版（Tkinter）と同じJSONファイル形式を使用しています：

- ✅ `questions.json` - 100%互換
- ✅ `user_profile.json` - 100%互換
- ✅ `results.json` - 100%互換
- ✅ `study_time.json` - 100%互換
- ✅ `services.json` - 100%互換
- ✅ `config.json` - 100%互換

どちらのバージョンでも同じデータが使用できます。

## 🎨 デザイン

AWS Management Console / Skill Builder 風のダークテーマです。
色の定義は `modules/theme.py` の `COLORS` に集約しています。

| 用途 | 値 |
| --- | --- |
| 背景 | `#16191F` |
| サイドバー | `#1B222C` |
| カード | `#232F3E` |
| プライマリ（AWS Orange） | `#FF9900` |
| セカンダリ（AWS Blue） | `#0972D3` |
| テキスト | `#F2F3F3` |
| サブテキスト | `#AAB7B8` |

### レスポンシブ対応

- 768px 未満ではカードを1列表示に切り替え
- ボタンの最小高さを 44px 以上に設定（タッチ操作向け）
- スマートフォンではサイドバーを自動的に折りたたみ、上部にクイックナビを表示
- 横スクロールが発生しないように調整

## 🐛 トラブルシューティング

### Streamlitが起動しない

```bash
# 環境を確認
python -m streamlit hello

# キャッシュをクリア
rm -rf ~/.streamlit/cache/
```

### データが保存されない

- `data/` ディレクトリの書き込み権限を確認
- ファイルパーミッション: `chmod 755 data/`

### Community Cloud でエラー

- `requirements.txt` に全依存関係があるか確認
- ログを確認: Community Cloud の "Manage app" → "View logs"

## 📞 サポート

問題が発生した場合：

1. [Issues](https://github.com/YOUR_USERNAME/aws-skills-web/issues) で報告
2. ログを添付してください
3. 環境情報：Python版、OS、ブラウザ

## 📄 ライセンス

MIT License

## 🙏 謝辞

- Streamlit コミュニティ
- AWS Community

## 📝 更新履歴

### 学習コンテンツの強化（問題データ schema_version 2）

アプリのバージョン表記は v2.1 のままです（画面構成の変更はありません）。

- 問題データを schema_version 2 に移行（`data/questions.schema.json` を追加）
- 全 50 問に出題分野・論点・難易度・関連サービス・対象試験・タグを付与
- 全 50 問の解説を 3〜5 文に強化（平均 61 文字 → 239 文字）
- 全 200 件の選択肢に個別解説を追加（誤答がなぜ誤りかを明示）
- 全 50 問に AWS 公式ドキュメントへの出典リンクを追加（到達性を検証済み）
- 複数選択問題に対応（チェックボックス表示・集合一致による採点）
- 弱点分析を論点 / 出題分野 / AWS サービス単位に拡張し、復習すべき論点を提示
- 問題データの検証スクリプト `tools/validate_questions.py` を追加
- 問題追加ガイド `docs/questions.md` を追加
- 解説内の文字化け（CodePipeline の問題）を修正

### v2.1 (Skill Builder Edition)
- 画面構成を9ページに再編（ホーム / 学習パス / 今日の学習 / 練習問題 ほか）
- AWS コンソール風のデザインに刷新（`modules/theme.py`）
- 学習モードと試験モードを分離した出題エンジンを追加
- カテゴリ別の正答率を記録し、弱点分析を分野単位で表示
- 学習時間・XP・バッジを自動記録
- 週間学習アクティビティを追加（従来のカレンダー表示を置き換え）
- スマートフォン向けのレイアウトとクイックナビを追加
- 表記の誤り（韓国語の混入、中国語表現、カタカナの誤記）を修正

### v2.0 (Web Edition)
- Streamlit での実装
- モバイル完全対応
- GitHub風学習カレンダー
- リアルタイムグラフ
- データエクスポート

### v1.0 (Desktop Edition)
- CustomTkinter による実装
- ゲーミフィケーション機能
- 詳細分析

---

**Happy Learning! 🎓**
