import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from modules.security import validate_json_integrity, validate_json_file_size, check_injection_attempt

# ロギング設定
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# セキュリティ設定
MAX_JSON_FILE_SIZE_MB = 50
ALLOWED_FILENAMES = {
    "questions.json", "user_profile.json", "results.json",
    "config.json", "progress.json", "exam_history.json",
    "study_time.json", "services.json"
}


def _validate_filename(filename: str) -> bool:
    """ファイル名が許可されたものか確認する。"""
    if filename not in ALLOWED_FILENAMES:
        logger.warning(f"不正なファイル名へのアクセス試行: {filename}")
        return False
    return True


def load_json(filename: str, default=None):
    """JSON ファイルを読み込む（セキュリティ検証付き）。
    
    Args:
        filename: ファイル名
        default: 読み込み失敗時のデフォルト値
        
    Returns:
        読み込んだデータ
    """
    # ファイル名検証
    if not _validate_filename(filename):
        logger.error(f"不正なファイル名: {filename}")
        return default if default is not None else {}
    
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return default if default is not None else {}
    
    try:
        # ファイルサイズ検証
        if not validate_json_file_size(file_path, MAX_JSON_FILE_SIZE_MB):
            logger.error(f"ファイルサイズが大きすぎます: {filename}")
            return default if default is not None else {}
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # JSON 整合性検証
        if not validate_json_integrity(data):
            logger.error(f"JSON 整合性チェック失敗: {filename}")
            return default if default is not None else {}
        
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON デコードエラー {filename}: {str(e)}")
        return default if default is not None else {}
    
    except Exception as e:
        logger.error(f"ファイル読み込みエラー {filename}: {str(e)}")
        return default if default is not None else {}


def save_json(filename: str, data):
    """JSON ファイルを保存する（セキュリティ検証付き）。
    
    Args:
        filename: ファイル名
        data: 保存するデータ
        
    Returns:
        成功時 True
    """
    # ファイル名検証
    if not _validate_filename(filename):
        logger.error(f"不正なファイル名: {filename}")
        return False
    
    # データ整合性検証
    if not validate_json_integrity(data):
        logger.error(f"JSON 整合性チェック失敗: {filename}")
        return False
    
    file_path = DATA_DIR / filename
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存後のサイズ検証
        if not validate_json_file_size(file_path, MAX_JSON_FILE_SIZE_MB):
            logger.error(f"保存後のファイルサイズが大きすぎます: {filename}")
            return False
        
        logger.info(f"ファイル保存成功: {filename}")
        return True
    
    except Exception as e:
        logger.error(f"ファイル保存エラー {filename}: {str(e)}")
        return False

def init_data():
    """Initialize data files"""
    # Load or create questions
    questions = load_json("questions.json", [])
    if not questions:
        questions = []
        save_json("questions.json", questions)

    # Load or create user profile
    user_profile = load_json("user_profile.json", {
        "username": "学習者",
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "exam_date": "2026-10-15",
        "badges": [],
        "achievements": []
    })
    save_json("user_profile.json", user_profile)

    # Load or create results
    results = load_json("results.json", [])
    save_json("results.json", results)

    # Load or create config
    config = load_json("config.json", {
        "theme": "dark",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })
    save_json("config.json", config)

    # Load or create progress
    progress = load_json("progress.json", {
        "total_studied": 0,
        "streak": 0,
        "last_study_date": None,
        "achievements": []
    })
    save_json("progress.json", progress)

    # Load or create exam history
    exam_history = load_json("exam_history.json", [])
    save_json("exam_history.json", exam_history)

    # Load or create study times
    study_times = load_json("study_time.json", [])
    save_json("study_time.json", study_times)

    # Load or create services
    services = load_json("services.json", {})
    save_json("services.json", services)

    return {
        "questions": questions,
        "user_profile": user_profile,
        "results": results,
        "config": config,
        "progress": progress,
        "exam_history": exam_history,
        "study_times": study_times,
        "services": services
    }

def get_study_dates():
    """Get set of dates when user studied"""
    study_times = load_json("study_time.json", [])
    study_dates = set()
    for study in study_times:
        try:
            date = datetime.fromisoformat(study["timestamp"]).date()
            study_dates.add(date)
        except:
            pass
    return study_dates

def get_streak():
    """Calculate current learning streak"""
    study_dates = get_study_dates()
    if not study_dates:
        return 0

    today = datetime.now().date()
    streak = 0
    check_date = today

    for _ in range(365):
        if check_date in study_dates:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return streak

def record_exam_result(exam_data):
    """Record exam result"""
    results = load_json("results.json", [])
    results.append(exam_data)
    return save_json("results.json", results)

def add_study_time(duration_seconds, category="general"):
    """Record study time"""
    study_times = load_json("study_time.json", [])
    study_times.append({
        "timestamp": datetime.now().isoformat(),
        "duration": duration_seconds,
        "category": category
    })
    return save_json("study_time.json", study_times)

def update_user_profile(updates: dict):
    """ユーザープロフィールを更新する（入力値検証付き）。
    
    Args:
        updates: 更新するフィールド
        
    Returns:
        成功時 True
    """
    # 入力値検証
    for key, value in updates.items():
        # インジェクション攻撃チェック
        if isinstance(value, str) and check_injection_attempt(value):
            logger.warning(f"インジェクション攻撃の可能性: {key}={value}")
            return False
        
        # username 長さ制限
        if key == "username" and isinstance(value, str):
            if len(value) < 2 or len(value) > 32:
                logger.warning(f"無効なユーザー名長: {value}")
                return False
    
    user_profile = load_json("user_profile.json", {})
    user_profile.update(updates)
    return save_json("user_profile.json", user_profile)

def add_badge(badge_id):
    """Add badge to user"""
    user_profile = load_json("user_profile.json", {})
    badges = user_profile.get("badges", [])
    if badge_id not in badges:
        badges.append(badge_id)
    user_profile["badges"] = badges
    return save_json("user_profile.json", user_profile)

def get_category_stats(results, category):
    """Get stats for a category"""
    cat_results = [r for r in results if r.get("type") == category]
    if not cat_results:
        return {"correct": 0, "total": 0, "accuracy": 0}

    correct = sum(r.get("correct", 0) for r in cat_results)
    total = sum(r.get("total", 0) for r in cat_results)
    accuracy = (correct / total * 100) if total > 0 else 0

    return {"correct": correct, "total": total, "accuracy": accuracy}
