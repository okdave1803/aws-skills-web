# 問題データの追加・編集ガイド

問題データは `data/questions.json` に JSON 配列として保存されています。
形式は `data/questions.schema.json`（JSON Schema）で定義されており、
`tools/validate_questions.py` で検証できます。

## 1. 追加のしかた

`data/questions.json` の配列の末尾に、オブジェクトを 1 つ追加します。
ファイルは **UTF-8（BOM なし）** で保存してください。

```json
{
  "schema_version": 2,
  "id": 51,
  "category": "AWS サービス",
  "domain": "クラウドテクノロジーとサービス",
  "topic": "コンテナオーケストレーション",
  "difficulty": "標準",
  "type": "single",
  "select_count": 1,
  "services": ["ECS", "EKS"],
  "exam": ["CLF-C02", "SAA-C03"],
  "tags": ["コンテナ", "オーケストレーション"],
  "question": "Amazon ECS の役割として正しいものはどれですか？",
  "options": [
    "リレーショナルデータベースを提供する",
    "コンテナ化されたアプリケーションを実行・管理する",
    "DNS の名前解決を行う",
    "静的サイトを配信する"
  ],
  "correct": [1],
  "explanation": "Amazon ECS は……（3〜5 文で、なぜ正解が正解なのかを説明します）",
  "option_explanations": [
    "誤りです。リレーショナルデータベースは RDS が提供します。",
    "正解です。コンテナの実行とスケジューリングを担うサービスです。",
    "誤りです。DNS は Route 53 が担当します。",
    "誤りです。静的サイトの配信は S3 と CloudFront の役割です。"
  ],
  "references": [
    {
      "title": "Amazon ECS とは（AWS 公式ドキュメント）",
      "url": "https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/Welcome.html"
    }
  ]
}
```

追加したら必ず検証します。

```bash
python tools/validate_questions.py
```

参照 URL が実際に到達できるかも確認する場合（ネットワーク接続が必要）:

```bash
python tools/validate_questions.py --check-urls
```

## 2. フィールドの意味

| フィールド | 必須 | 説明 |
| --- | --- | --- |
| `schema_version` | ✅ | 現行は `2` 固定 |
| `id` | ✅ | 一意な整数。**一度採番したら変更しない**（学習履歴と対応するため） |
| `category` | ✅ | アプリ内の大分類。練習問題のカテゴリ選択に表示される |
| `domain` | ✅ | 認定試験の出題分野。弱点分析の集計単位 |
| `topic` | ✅ | 具体的な学習トピック。弱点分析の最小単位 |
| `difficulty` | ✅ | `基礎` / `標準` / `応用` / `難関` |
| `type` | ✅ | `single`（単一選択）または `multiple`（複数選択） |
| `select_count` | ✅ | 選ぶべき数。`correct` の件数と一致させる |
| `services` | ✅ | 関連 AWS サービス。`data/services.json` の `name` と表記を合わせる |
| `exam` | ✅ | 対象試験コード。1 つ以上 |
| `tags` | ✅ | 自由キーワード（空配列でも可） |
| `question` | ✅ | 設問文 |
| `options` | ✅ | 選択肢（2〜6 件） |
| `correct` | ✅ | 正解インデックスの**配列**（0 始まり）。単一選択でも `[1]` と書く |
| `explanation` | ✅ | 全体解説。60 文字以上、3〜5 文を推奨 |
| `option_explanations` | ✅ | 選択肢ごとの解説。`options` と同じ件数・同じ順序 |
| `references` | ✅ | 出典。1 件以上、`https://` で始める |

### 使用できる値

- `category`: `クラウドの基礎` / `AWS サービス` / `セキュリティ` / `コスト最適化`
- `domain`: `クラウドの概念` / `セキュリティとコンプライアンス` /
  `クラウドテクノロジーとサービス` / `請求、料金、およびサポート`
- `difficulty`: `基礎` / `標準` / `応用` / `難関`
- `exam`: `CLF-C02` / `SAA-C03` / `SOA-C02` / `DVA-C02` / `SAP-C02`

新しい値を増やす場合は、`data/questions.schema.json` と
`tools/validate_questions.py` の定数の両方を更新してください。

## 3. 複数選択問題の書き方

`type` を `multiple` にし、`correct` に複数のインデックスを、
`select_count` にその件数を指定します。

```json
"type": "multiple",
"select_count": 2,
"correct": [1, 3],
```

- UI はラジオボタンではなくチェックボックスで表示されます
- 「正しいものを 2 つ選んでください」という案内が自動で表示されます
- 指定した数と違う数を選んだ状態で回答しようとすると警告が出ます
- 採点は**集合一致**です。部分点はありません

## 4. 解説の書き方

`explanation` は「なぜその答えになるのか」を説明します。
選択肢の言い換えではなく、判断の根拠を書いてください。

- 3〜5 文、60 文字以上
- 正解の理由 → 補足となる仕組み → 実務上の使い分け、の順が読みやすい
- 関連サービスとの違い（例: CloudWatch と CloudTrail）に触れると定着しやすい

`option_explanations` は選択肢ごとに、
**正解には「正解です。」から始める文**、
**誤答には「誤りです。」から始めて、なぜ誤りかを書いた文**を入れます。
検証スクリプトはこの書き出しと `correct` の対応をチェックします。

## 5. 出典（references）について

- AWS 公式ドキュメント（`https://docs.aws.amazon.com/ja_jp/...`）を第一候補にします
- 製品ページ（`https://aws.amazon.com/jp/...`）は補助的な出典として使えます
- リンクを追加したら `--check-urls` で到達性を確認してください

## 6. 著作権に関する注意

- **有料教材や公式模擬試験の問題文を転載しないでください。**
- 問題は AWS 公式ドキュメントと試験ガイドの出題範囲をもとに、
  自分の言葉で作成したオリジナルの内容にしてください。
- 出典として URL を示すことは問題ありませんが、本文の引き写しは避けてください。

## 7. 旧形式との互換性

`schema_version` が無く `correct` が整数だった旧形式のデータも、
アプリ側（`modules/quiz.py` の `get_correct_indices`）で読み込めます。
ただし新規に追加する問題は schema_version 2 で記述してください。

同様に、`domains` / `topics` / `services` の内訳を持たない過去の学習履歴も
そのまま集計に使われます（その場合、分析画面では該当の集計単位が
選択肢に表示されません）。
