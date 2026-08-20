"""AWS Skills - データマネージャー（ハイブリッド: JSON + DB対応）

FEATURE_DATABASE フラグに応じて JSON または DB から読み込む。
段階的なマイグレーションをサポートする。
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from modules.config import settings
from modules.security import validate_json_integrity, validate_json_file_size, check_injection_attempt
from modules.models import init_db, User
from modules.dal import UserDAL, QuizResultDAL, StudyLogDAL, ProgressDAL

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

# グローバルデータベースセッション
_db_session: Session = None


def init_db_session():
    """データベースセッションを初期化する（初回呼び出し時）。"""
    global _db_session
    
    if _db_session is not None:
        return
    
    if not settings.FEATURE_DATABASE:
        logger.info("データベース機能は無効です（JSON モード）")
        return
    
    try:
        db_url = settings.get_database_url()
        engine, _db_session = init_db(db_url)
        logger.info(f"データベースセッション初期化: {db_url}")
    
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
        _db_session = None


def get_db_session() -> Session:
    """現在のデータベースセッションを取得する。
    
    Returns:
        セッション、または DB 無効時は None
    """
    init_db_session()
    return _db_session


# ===== JSON モード用の関数 =============================================


def _validate_filename(filename: str) -> bool:
    """ファイル名が許可されたものか確認する。"""
    if filename not in ALLOWED_FILENAMES:
        logger.warning(f"不正なファイル名へのアクセス試行: {filename}")
        return False
    return True


def _load_json(filename: str, default=None):
    """JSON ファイルを読み込む（セキュリティ検証付き）。"""
    if not _validate_filename(filename):
        logger.error(f"不正なファイル名: {filename}")
        return default if default is not None else {}
    
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return default if default is not None else {}
    
    try:
        if not validate_json_file_size(file_path, MAX_JSON_FILE_SIZE_MB):
            logger.error(f"ファイルサイズが大きすぎます: {filename}")
            return default if default is not None else {}
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
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


def _save_json(filename: str, data):
    """JSON ファイルを保存する（セキュリティ検証付き）。"""
    if not _validate_filename(filename):
        logger.error(f"不正なファイル名: {filename}")
        return False
    
    if not validate_json_integrity(data):
        logger.error(f"JSON 整合性チェック失敗: {filename}")
        return False
    
    file_path = DATA_DIR / filename
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if not validate_json_file_size(file_path, MAX_JSON_FILE_SIZE_MB):
            logger.error(f"保存後のファイルサイズが大きすぎます: {filename}")
            return False
        
        logger.info(f"ファイル保存成功: {filename}")
        return True
    
    except Exception as e:
        logger.error(f"ファイル保存エラー {filename}: {str(e)}")
        return False


# ===== パブリック API（DB/JSON 両対応）==================================


def init_data():
    """データを初期化する。
    
    DB 有効時は DB から、無効時は JSON から初期データを取得する。
    """
    if settings.FEATURE_DATABASE:
        init_db_session()
        
        if _db_session:
            # DB からのデータ読み込み
            user_dal = UserDAL(_db_session)
            
            # デフォルトユーザーがなければ作成
            user = user_dal.get_user_by_username("demo_user")
            if not user:
                user = user_dal.create_user(
                    username="demo_user",
                    password="DemoPassword123"
                )
            
            return {
                "questions": _load_json("questions.json", []),
                "user_profile": {
                    "username": user.username if user else "学習者",
                    "level": user.level if user else 1,
                    "xp": user.xp if user else 0,
                    "total_xp": user.total_xp if user else 0,
                    "exam_date": user.exam_date if user else "2026-10-15",
                    "badges": user.badges if user else [],
                    "achievements": user.achievements if user else [],
                },
                "results": [],  # DB から取得する場合は QueryResult のリストになる
                "config": _load_json("config.json", {"theme": "dark", "version": "2.1"}),
                "progress": {},  # DB から取得
                "exam_history": [],  # DB から取得
                "study_times": [],  # DB から取得
                "services": _load_json("services.json", {}),
            }
    
    # JSON モード（デフォルト）
    questions = _load_json("questions.json", [])
    user_profile = _load_json("user_profile.json", {
        "username": "学習者",
        "level": 1,
        "xp": 0,
        "total_xp": 0,
        "exam_date": "2026-10-15",
        "badges": [],
        "achievements": []
    })
    _save_json("user_profile.json", user_profile)
    
    results = _load_json("results.json", [])
    _save_json("results.json", results)
    
    config = _load_json("config.json", {
        "theme": "dark",
        "version": "2.1",
        "timestamp": datetime.now().isoformat()
    })
    _save_json("config.json", config)
    
    progress = _load_json("progress.json", {
        "total_studied": 0,
        "streak": 0,
        "last_study_date": None,
        "achievements": []
    })
    _save_json("progress.json", progress)
    
    exam_history = _load_json("exam_history.json", [])
    _save_json("exam_history.json", exam_history)
    
    study_times = _load_json("study_time.json", [])
    _save_json("study_time.json", study_times)
    
    services = _load_json("services.json", {})
    _save_json("services.json", services)
    
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
    """学習日の set を取得する。"""
    if settings.FEATURE_DATABASE and _db_session:
        session = get_db_session()
        if session:
            study_dal = StudyLogDAL(session)
            return study_dal.get_study_dates(user_id=1)  # demo_user
    
    # JSON モード
    study_times = _load_json("study_time.json", [])
    study_dates = set()
    for study in study_times:
        try:
            date = datetime.fromisoformat(study["timestamp"]).date()
            study_dates.add(date)
        except:
            pass
    
    return study_dates


def get_streak():
    """連続学習日数を計算する。"""
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
    """試験結果を記録する。"""
    if settings.FEATURE_DATABASE and _db_session:
        session = get_db_session()
        if session:
            quiz_dal = QuizResultDAL(session)
            quiz_dal.create_result(user_id=1, **exam_data)
            return True
    
    # JSON モード
    results = _load_json("results.json", [])
    results.append(exam_data)
    return _save_json("results.json", results)


def add_study_time(duration_seconds, category="general"):
    """学習時間を記録する。"""
    if settings.FEATURE_DATABASE and _db_session:
        session = get_db_session()
        if session:
            study_dal = StudyLogDAL(session)
            study_dal.create_log(user_id=1, duration_seconds=duration_seconds, category=category)
            return True
    
    # JSON モード
    study_times = _load_json("study_time.json", [])
    study_times.append({
        "timestamp": datetime.now().isoformat(),
        "duration": duration_seconds,
        "category": category
    })
    return _save_json("study_time.json", study_times)


def update_user_profile(updates: dict):
    """ユーザープロフィールを更新する。"""
    # 入力値検証
    for key, value in updates.items():
        if isinstance(value, str) and check_injection_attempt(value):
            logger.warning(f"インジェクション攻撃の可能性: {key}={value}")
            return False
        
        if key == "username" and isinstance(value, str):
            if len(value) < 2 or len(value) > 32:
                logger.warning(f"無効なユーザー名長: {value}")
                return False
    
    if settings.FEATURE_DATABASE and _db_session:
        session = get_db_session()
        if session:
            user_dal = UserDAL(session)
            user = user_dal.get_user_by_id(1)  # demo_user
            if user:
                return user_dal.update_user(user, **updates)
    
    # JSON モード
    user_profile = _load_json("user_profile.json", {})
    user_profile.update(updates)
    return _save_json("user_profile.json", user_profile)


def add_badge(badge_id):
    """バッジを追加する。"""
    if settings.FEATURE_DATABASE and _db_session:
        session = get_db_session()
        if session:
            user_dal = UserDAL(session)
            user = user_dal.get_user_by_id(1)
            if user and badge_id not in user.badges:
                return user_dal.update_user(user, badges=user.badges + [badge_id])
            return True
    
    # JSON モード
    user_profile = _load_json("user_profile.json", {})
    badges = user_profile.get("badges", [])
    if badge_id not in badges:
        badges.append(badge_id)
    user_profile["badges"] = badges
    return _save_json("user_profile.json", user_profile)


def get_category_stats(results, category):
    """カテゴリ統計を取得する。"""
    if isinstance(results, dict):
        # DB mode で QueryResult に変換された場合
        cat_results = [r for r in results if hasattr(r, 'category') and r.category == category]
    else:
        cat_results = [r for r in results if r.get("type") == category]
    
    if not cat_results:
        return {"correct": 0, "total": 0, "accuracy": 0}
    
    correct = sum(1 if (hasattr(r, 'is_correct') and r.is_correct) else (r.get("correct", 0)) for r in cat_results)
    total = len(cat_results)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    return {"correct": correct, "total": total, "accuracy": accuracy}
