from datetime import datetime
from collections import defaultdict

def calculate_pass_probability(results):
    """Calculate probability of passing the exam"""
    if not results:
        return 0.0

    total_correct = sum(r.get("correct", 0) for r in results)
    total_attempts = sum(r.get("total", 0) for r in results)
    accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

    pass_line = 65.0
    if accuracy >= pass_line:
        return min(100, 70 + (accuracy - pass_line) / (100 - pass_line) * 30)
    else:
        return (accuracy / pass_line) * 70

def calculate_overall_accuracy(results):
    """Calculate overall accuracy"""
    if not results:
        return 0.0

    total_correct = sum(r.get("correct", 0) for r in results)
    total_attempts = sum(r.get("total", 0) for r in results)

    return (total_correct / total_attempts * 100) if total_attempts > 0 else 0

def get_category_stats(results):
    """Aggregate correct/total per AWS category.

    Prefers the per-category breakdown stored under the "categories" key.
    Older records without that key are grouped by exam type so that
    previously saved results still contribute to the analysis.
    """
    category_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for result in results or []:
        breakdown = result.get("categories")
        if breakdown:
            for category, stats in breakdown.items():
                category_stats[category]["correct"] += stats.get("correct", 0)
                category_stats[category]["total"] += stats.get("total", 0)
        else:
            exam_type = str(result.get("type", "unknown"))
            category_stats[exam_type]["correct"] += result.get("correct", 0)
            category_stats[exam_type]["total"] += result.get("total", 0)

    return dict(category_stats)


def get_weak_categories(results):
    """Get categories sorted by accuracy (weakest first)"""
    weak = []
    for category, stats in get_category_stats(results).items():
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"] * 100
            weak.append((category, accuracy))

    return sorted(weak, key=lambda x: x[1])


# --- schema_version 2 の内訳を使った詳細な弱点分析 -------------------------
# quiz.py が結果に "domains" / "topics" / "services" / "difficulties" を
# 保存する。これらが無い古い記録は自動的に無視される。

BREAKDOWN_KEYS = ("categories", "domains", "topics", "services", "difficulties")


def get_breakdown_stats(results, key):
    """Aggregate correct/total for one named breakdown across all results."""
    stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for result in results or []:
        breakdown = result.get(key)
        if not isinstance(breakdown, dict):
            continue
        for label, entry in breakdown.items():
            if not isinstance(entry, dict):
                continue
            stats[label]["correct"] += entry.get("correct", 0)
            stats[label]["total"] += entry.get("total", 0)

    return dict(stats)


def get_weak_areas(results, key, min_total=1, limit=None):
    """Return weakest areas as (label, accuracy, correct, total).

    Sorted by accuracy ascending; ties broken by the larger sample first so
    that a 0/4 topic ranks above a 0/1 topic.
    """
    rows = []
    for label, stats in get_breakdown_stats(results, key).items():
        total = stats["total"]
        if total >= min_total:
            accuracy = stats["correct"] / total * 100
            rows.append((label, accuracy, stats["correct"], total))

    rows.sort(key=lambda r: (r[1], -r[3]))
    return rows[:limit] if limit else rows


def has_breakdown(results, key):
    """True if at least one result carries the given breakdown."""
    return any(
        isinstance(r.get(key), dict) and r.get(key)
        for r in (results or [])
    )


def get_focus_recommendations(results, limit=3):
    """Pick the topics most worth reviewing next.

    Falls back to domains, then categories, when finer data is unavailable.
    """
    for key in ("topics", "domains", "categories"):
        rows = get_weak_areas(results, key, min_total=1)
        # 正答率 100% の分野は復習対象にしない
        rows = [r for r in rows if r[1] < 100]
        if rows:
            return key, rows[:limit]
    return "topics", []


def get_overall_progress(results, question_count):
    """Estimate overall study progress as a percentage.

    Combines two signals so the number moves both when the learner covers
    more material and when accuracy improves:
      - coverage: answered questions relative to the question bank size
      - accuracy: overall correct ratio
    Each contributes half of the final value.
    """
    if not results or not question_count:
        return 0.0

    answered = sum(r.get("total", 0) for r in results)
    coverage = min(1.0, answered / question_count) * 100
    accuracy = calculate_overall_accuracy(results)

    return min(100.0, coverage * 0.5 + accuracy * 0.5)

def get_study_metrics(results, study_times):
    """Get study metrics"""
    today = datetime.now().date()

    # Today's study time
    today_minutes = int(sum(
        s.get("duration", 0) / 60 for s in study_times
        if datetime.fromisoformat(s["timestamp"]).date() == today
    ))

    # This week's stats
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())
    week_correct = 0
    week_total = 0
    for result in results:
        if datetime.fromisoformat(result["timestamp"]).date() >= week_start:
            week_correct += result.get("correct", 0)
            week_total += result.get("total", 0)

    week_accuracy = (week_correct / week_total * 100) if week_total > 0 else 0

    return {
        "today_minutes": today_minutes,
        "week_accuracy": week_accuracy,
        "total_questions": sum(r.get("total", 0) for r in results),
        "total_correct": sum(r.get("correct", 0) for r in results),
        "overall_accuracy": calculate_overall_accuracy(results)
    }

def get_days_until_exam(exam_date_str):
    """Get days until exam"""
    try:
        exam_date = datetime.fromisoformat(exam_date_str).date()
        days = (exam_date - datetime.now().date()).days
        return max(0, days)
    except:
        return 0
