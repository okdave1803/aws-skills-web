"""AWS Skills - 学習コンテンツ定義

学習パス、今日の学習プラン、問題メタデータの導出をまとめる。
questions.json / services.json の既存構造はそのまま利用する。
"""

from datetime import datetime

# --- 学習パス定義 ---------------------------------------------------------
# categories は questions.json の "category" 値に対応させる。
LEARNING_PATHS = [
    {
        "id": "clf",
        "title": "AWS Cloud Practitioner",
        "code": "CLF-C02",
        "audience": "AWS をこれから学ぶ方・非エンジニアの方",
        "difficulty": "基礎",
        "hours": "20〜30時間",
        "description": "クラウドの基本概念、AWS の主要サービス、料金とサポート体制を体系的に理解します。",
        "services": ["EC2", "S3", "IAM", "VPC", "CloudWatch"],
        "categories": ["クラウドの基礎", "AWS サービス", "セキュリティ", "コスト最適化"],
    },
    {
        "id": "saa",
        "title": "Solutions Architect Associate",
        "code": "SAA-C03",
        "audience": "可用性と拡張性を考慮した設計を担当する方",
        "difficulty": "標準",
        "hours": "60〜80時間",
        "description": "高可用性・耐障害性・コスト最適化を満たすアーキテクチャの設計方針を学びます。",
        "services": ["EC2", "S3", "VPC", "RDS", "Route 53", "CloudFront"],
        "categories": ["AWS サービス", "セキュリティ", "コスト最適化"],
    },
    {
        "id": "soa",
        "title": "SysOps Administrator Associate",
        "code": "SOA-C02",
        "audience": "AWS 環境の運用・監視を担当する方",
        "difficulty": "標準",
        "hours": "60〜80時間",
        "description": "監視、ログ運用、バックアップ、自動化など日常運用に必要な知識を習得します。",
        "services": ["CloudWatch", "EC2", "IAM", "CloudFormation", "Systems Manager"],
        "categories": ["AWS サービス", "セキュリティ"],
    },
    {
        "id": "dva",
        "title": "Developer Associate",
        "code": "DVA-C02",
        "audience": "AWS 上でアプリケーションを開発する方",
        "difficulty": "標準",
        "hours": "50〜70時間",
        "description": "サーバーレス開発、API 連携、CI/CD を中心に開発者向けの実装知識を学びます。",
        "services": ["Lambda", "DynamoDB", "API Gateway", "S3", "IAM"],
        "categories": ["AWS サービス", "セキュリティ"],
    },
    {
        "id": "sap",
        "title": "Solutions Architect Professional",
        "code": "SAP-C02",
        "audience": "大規模・複数アカウント環境を設計する方",
        "difficulty": "難関",
        "hours": "100時間以上",
        "description": "マルチアカウント戦略、移行計画、複雑な要件を満たす設計判断を扱う最上位レベルです。",
        "services": ["Organizations", "VPC", "Direct Connect", "CloudFormation", "KMS"],
        "categories": ["AWS サービス", "セキュリティ", "コスト最適化"],
    },
]

# --- 難易度の目安 ---------------------------------------------------------
# questions.json に difficulty フィールドが無いため、カテゴリから目安を導出する。
# 問題データ側に "difficulty" を追加した場合はそちらを優先する。
CATEGORY_DIFFICULTY = {
    "クラウドの基礎": "基礎",
    "AWS サービス": "標準",
    "セキュリティ": "標準",
    "コスト最適化": "応用",
}

# 問題文から関連サービスを抽出するための名称一覧。
# 長い名称を先に並べ、部分一致の誤検出を避ける。
SERVICE_KEYWORDS = [
    "Elastic Beanstalk", "CloudFormation", "CloudFront", "CloudWatch", "CloudTrail",
    "API Gateway", "Secrets Manager", "Systems Manager", "Direct Connect",
    "Organizations", "DynamoDB", "Route 53", "AppSync", "Lambda", "Aurora",
    "Athena", "Backup", "Config", "EMR", "Glacier", "Redshift", "SageMaker",
    "Shield", "Snowball", "Trusted Advisor", "WAF", "Cost Explorer",
    "Auto Scaling", "EC2", "ECS", "EKS", "EBS", "EFS", "ELB", "RDS", "S3",
    "SNS", "SQS", "SSM", "VPC", "IAM", "KMS",
]


def get_difficulty(question: dict) -> str:
    """問題の難易度ラベルを返す。

    データに difficulty があればそれを使い、無ければカテゴリから目安を返す。
    """
    explicit = question.get("difficulty")
    if explicit:
        return str(explicit)
    return CATEGORY_DIFFICULTY.get(question.get("category", ""), "標準")


def get_related_services(question: dict, limit: int = 4) -> list:
    """問題文・選択肢・解説から関連 AWS サービス名を抽出する。"""
    explicit = question.get("services")
    if explicit:
        return list(explicit)[:limit]

    blob = " ".join([
        str(question.get("question", "")),
        " ".join(str(o) for o in question.get("options", [])),
        str(question.get("explanation", "")),
    ])

    found = []
    for name in SERVICE_KEYWORDS:
        if name in blob and name not in found:
            # 既に検出した長い名称の一部であれば除外する
            if any(name != other and name in other for other in found):
                continue
            found.append(name)
        if len(found) >= limit:
            break
    return found


def get_categories(questions: list) -> list:
    """出題カテゴリの一覧を返す（出現順）。"""
    seen = []
    for q in questions:
        cat = q.get("category")
        if cat and cat not in seen:
            seen.append(cat)
    return seen


def _daily_seed(offset: int = 0) -> int:
    """日付ベースの安定したシード値。同じ日は同じ結果になる。"""
    today = datetime.now().date()
    return (today.toordinal() + offset)


def get_daily_plan(questions: list, services: dict, weak_categories=None) -> dict:
    """今日の学習プランを組み立てる。

    苦手カテゴリがあればそれを優先し、無ければ日替わりで選ぶ。
    同じ日のあいだは再実行しても内容が変わらない。
    """
    categories = get_categories(questions)
    weak_categories = weak_categories or []

    # 重点カテゴリ: 苦手分野を最優先、無ければ日替わり
    focus_category = None
    for cat, _acc in weak_categories:
        if cat in categories:
            focus_category = cat
            break
    if not focus_category and categories:
        focus_category = categories[_daily_seed() % len(categories)]

    focus_questions = [q for q in questions if q.get("category") == focus_category]

    # 今日のおすすめサービス
    flat_services = []
    for cat, items in (services or {}).items():
        for item in items:
            flat_services.append((cat, item))
    recommended_service = None
    if flat_services:
        recommended_service = flat_services[_daily_seed(3) % len(flat_services)]

    target_count = 10 if len(focus_questions) >= 10 else max(1, len(focus_questions))

    checklist = [
        f"{focus_category} の練習問題を {target_count} 問解く" if focus_category
        else "練習問題を 10 問解く",
        "間違えた問題の解説を読み直す",
        (f"AWS サービス辞典で {recommended_service[1].get('name')} を確認する"
         if recommended_service else "AWS サービス辞典を確認する"),
        "学習時間を記録する",
    ]

    return {
        "focus_category": focus_category,
        "focus_questions": focus_questions,
        "target_count": target_count,
        "target_minutes": 20,
        "recommended_service": recommended_service,
        "checklist": checklist,
    }


def get_path_progress(path: dict, results: list) -> dict:
    """学習パスの進捗目安を算出する。

    results に category 別内訳（categories キー）があればそれを使う。
    無い場合は 0% を返し、UI 側で「データなし」として扱う。
    """
    correct = 0
    total = 0
    for result in results or []:
        breakdown = result.get("categories") or {}
        for cat, stats in breakdown.items():
            if cat in path["categories"]:
                correct += stats.get("correct", 0)
                total += stats.get("total", 0)

    accuracy = (correct / total * 100) if total > 0 else 0.0
    return {"correct": correct, "total": total, "accuracy": accuracy}


# --- 実績バッジ -----------------------------------------------------------
BADGE_DEFS = {
    "first_step": {"name": "第一歩", "icon": "🎓", "desc": "最初の問題に正解する"},
    "hundred": {"name": "百問チャレンジ", "icon": "🎯", "desc": "累計100問を解く"},
    "streak_7": {"name": "7日連続", "icon": "🔥", "desc": "7日連続で学習する"},
    "accuracy_80": {"name": "正答率80%", "icon": "📈", "desc": "累計正答率80%以上"},
    "perfect_20": {"name": "完全正解", "icon": "💯", "desc": "20問以上を全問正解する"},
}


def evaluate_badges(results: list, streak: int) -> list:
    """獲得条件を満たしたバッジ ID の一覧を返す。"""
    earned = []
    if not results:
        return earned

    total_correct = sum(r.get("correct", 0) for r in results)
    total_questions = sum(r.get("total", 0) for r in results)
    accuracy = (total_correct / total_questions * 100) if total_questions else 0

    if total_correct >= 1:
        earned.append("first_step")
    if total_questions >= 100:
        earned.append("hundred")
    if streak >= 7:
        earned.append("streak_7")
    # 少ない母数で達成扱いにならないよう10問以上を条件に加える
    if total_questions >= 10 and accuracy >= 80:
        earned.append("accuracy_80")
    if any(r.get("total", 0) >= 20 and r.get("correct", 0) == r.get("total", 0)
           for r in results):
        earned.append("perfect_20")

    return earned


def calculate_level(total_xp: int) -> dict:
    """累計 XP からレベルと次のレベルまでの進捗を求める。"""
    level = 1
    remaining = max(0, int(total_xp))
    need = 100
    while remaining >= need:
        remaining -= need
        level += 1
        need = 100 + (level - 1) * 50
    return {
        "level": level,
        "current_xp": remaining,
        "next_xp": need,
        "percentage": (remaining / need * 100) if need else 0,
    }


def get_next_action(metrics: dict, results: list, weak_categories=None) -> str:
    """学習状況に応じた次のおすすめ行動を日本語で返す。"""
    if not results:
        return "まずは練習問題を 10 問解いて、現在の実力を確認しましょう。"

    weak_categories = weak_categories or []
    if weak_categories:
        cat, acc = weak_categories[0]
        if acc < 60:
            return f"「{cat}」の正答率が {acc:.0f}% です。この分野を重点的に復習しましょう。"

    accuracy = metrics.get("overall_accuracy", 0)
    if accuracy < 65:
        return "全体の正答率が合格ラインを下回っています。解説を確認しながら学習モードで進めましょう。"
    if metrics.get("today_minutes", 0) == 0:
        return "本日はまだ学習記録がありません。今日の学習から始めましょう。"
    if accuracy >= 80:
        return "十分な正答率です。模擬試験で本番形式の時間配分を確認しましょう。"
    return "順調に進んでいます。模擬試験で実力を確認してみましょう。"
