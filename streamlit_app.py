"""AWS Skills - AWS認定試験 学習アプリ

Streamlit で動作する学習プラットフォーム。
画面構成は modules 配下のコンポーネントを組み合わせて構築する。

セキュリティ: Phase 1 で XSS 対策、入力値検証を実装
"""

import logging
import random
from datetime import datetime

import pandas as pd
import streamlit as st

from modules import (
    analytics,
    calculator,
    content,
    data_manager,
    quiz,
    theme,
    ui_components,
)
from modules.auth import auth_manager
from modules.auth_ui import render_login_form, render_user_menu, require_authentication
from modules.config import settings
from modules.mobile_support import (
    init_mobile_session,
    inject_mobile_styles,
    is_mobile_device,
    render_mobile_navbar,
)
from modules.security import sanitize_html
from modules.theme import APP_NAME, APP_SUBTITLE, APP_VERSION, COLORS

# --- ロギング初期化 -------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 設定の検証
config_errors = settings.validate()
if config_errors:
    logger.warning(f"設定上の問題: {', '.join(config_errors)}")

st.set_page_config(
    page_title=f"{APP_NAME} | {APP_SUBTITLE}",
    page_icon="🚀",
    layout="wide",
    # モバイル対応: 初期状態でサイドバーを自動で折りたたむ
    initial_sidebar_state="auto",
    menu_items={
        "Get Help": "https://docs.streamlit.io",
        "Report a bug": None,
        "About": f"{APP_NAME} - AWS認定試験 学習アプリ\n{APP_VERSION}"
    }
)

# ページ定義: (キー, ラベル, アイコン)
PAGES = [
    ("home", "ホーム", "🏠"),
    ("paths", "学習パス", "🧭"),
    ("today", "今日の学習", "📅"),
    ("practice", "練習問題", "✏️"),
    ("exam", "模擬試験", "📋"),
    ("services", "AWSサービス辞典", "📖"),
    ("analysis", "分析", "📊"),
    ("achievements", "実績", "🏆"),
    ("settings", "設定", "⚙️"),
]

# モバイルのクイックナビに表示するページ
MOBILE_PAGES = ["home", "today", "practice", "exam", "analysis", "settings"]

DEFAULT_TARGET = "SAA-C03"


# --- 状態管理 -------------------------------------------------------------
def init_session():
    """セッション状態を初期化する。"""
    if "data" not in st.session_state:
        st.session_state.data = data_manager.init_data()
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "quiz" not in st.session_state:
        st.session_state.quiz = None


def refresh_data():
    """データファイルを読み直す。"""
    st.session_state.data = data_manager.init_data()


def goto(page_key):
    """ページを切り替える。"""
    st.session_state.page = page_key


def get_target_path(profile):
    """学習目標に対応する学習パス定義を返す。"""
    target = profile.get("target_exam", DEFAULT_TARGET)
    for path in content.LEARNING_PATHS:
        if path["code"] == target:
            return path
    return content.LEARNING_PATHS[1]


def start_practice(questions, mode, title, source="practice"):
    """出題を開始して練習問題ページへ移動する。"""
    quiz.start_quiz(questions, mode=mode, source=source, title=title)
    goto("practice")


# --- サイドバー -----------------------------------------------------------
def render_sidebar():
    """学習プラットフォーム風のサイドバー。"""
    profile = st.session_state.data["user_profile"]

    st.sidebar.markdown(
        f"""
        <div style="padding:4px 2px 14px;">
            <div style="font-size:1.15rem;font-weight:700;color:{COLORS['text']};">
                🚀 {APP_NAME}
            </div>
            <div style="font-size:.74rem;color:{COLORS['text_secondary']};
                        margin-top:2px;">{APP_SUBTITLE}</div>
            <div style="font-size:.66rem;color:{COLORS['text_muted']};
                        margin-top:6px;">{APP_VERSION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current = st.session_state.page
    for key, label, icon in PAGES:
        if st.sidebar.button(
            f"{icon}　{label}",
            key=f"nav_{key}",
            type="primary" if key == current else "secondary",
        ):
            goto(key)
            st.rerun()

    # 学習者プロフィール
    st.sidebar.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    level_info = content.calculate_level(profile.get("total_xp", 0))
    target_path = get_target_path(profile)

    st.sidebar.markdown(
        f"""
        <div style="background:{COLORS['card']};border:1px solid {COLORS['border']};
                    border-radius:12px;padding:14px;">
            <div style="font-size:.9rem;font-weight:700;">
                {profile.get('username', '学習者')}
            </div>
            <div style="font-size:.7rem;color:{COLORS['text_secondary']};
                        margin-top:2px;">目標: {target_path['code']}</div>
            <div style="display:flex;justify-content:space-between;
                        font-size:.72rem;margin:10px 0 5px;">
                <span style="color:{COLORS['primary']};font-weight:700;">
                    LV.{level_info['level']}
                </span>
                <span style="color:{COLORS['text_secondary']};">
                    {level_info['current_xp']} / {level_info['next_xp']} XP
                </span>
            </div>
            {ui_components.progress_bar_html(level_info['percentage'])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mobile_nav():
    """スマートフォン向けのコンパクトなナビゲーション。

    PC では CSS で非表示にしている。
    """
    labels = {key: (label, icon) for key, label, icon in PAGES}
    with st.container(key="mobile_nav"):
        for row_start in (0, 3):
            cols = st.columns(3)
            for offset, page_key in enumerate(MOBILE_PAGES[row_start:row_start + 3]):
                label, icon = labels[page_key]
                with cols[offset]:
                    if st.button(
                        f"{icon}\n{label}",
                        key=f"mnav_{page_key}",
                        type="primary" if st.session_state.page == page_key
                        else "secondary",
                    ):
                        goto(page_key)
                        st.rerun()


# --- ホーム ---------------------------------------------------------------
def show_home():
    data = st.session_state.data
    profile = data["user_profile"]
    results = data["results"]
    questions = data["questions"]

    metrics = calculator.get_study_metrics(results, data["study_times"])
    days_until = calculator.get_days_until_exam(profile.get("exam_date", ""))
    pass_prob = calculator.calculate_pass_probability(results)
    weak_cats = calculator.get_weak_categories(results)
    progress_pct = calculator.get_overall_progress(results, len(questions))
    target_path = get_target_path(profile)

    ui_components.render_hero(
        "AWS認定試験の学習を始めましょう",
        "今日の学習、練習問題、模擬試験を通じて合格力を高めます。",
        f"{APP_NAME}　{APP_SUBTITLE}",
    )

    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        if st.button("今日の学習を開始", type="primary", key="hero_today"):
            goto("today")
            st.rerun()
    with col2:
        if st.button("模擬試験を受ける", key="hero_exam"):
            goto("exam")
            st.rerun()

    st.markdown("")

    # 学習進捗
    ui_components.render_section("学習の進捗", "目標とする試験に対する現在の到達度")
    ui_components.render_progress_card(
        target_path["code"],
        target_path["title"],
        progress_pct,
        days_until,
        content.get_next_action(metrics, results, weak_cats),
        metrics["overall_accuracy"],
    )

    st.markdown("")

    # 主要指標
    ui_components.render_section("学習サマリー")
    cols = st.columns(4)
    ui_components.render_metric_card(
        cols[0], "正答率", f"{metrics['overall_accuracy']:.1f}%", "🎯",
        "累計の正解割合",
    )
    ui_components.render_metric_card(
        cols[1], "本日の学習時間", f"{metrics['today_minutes']}分", "⏱️",
        "今日の合計", COLORS["secondary"],
    )
    ui_components.render_metric_card(
        cols[2], "解いた問題数", f"{metrics['total_questions']}問", "📝",
        f"正解 {metrics['total_correct']}問", COLORS["text"],
    )
    ui_components.render_metric_card(
        cols[3], "合格可能性", f"{pass_prob:.0f}%", "📈",
        f"合格ライン {quiz.PASS_LINE:.0f}%",
        COLORS["success"] if pass_prob >= 70 else COLORS["warning"],
    )

    st.markdown("")

    # 続きから学習
    col_left, col_right = st.columns([1, 1])

    with col_left:
        ui_components.render_section("続きから学習")
        plan = content.get_daily_plan(questions, data["services"], weak_cats)
        focus = plan["focus_category"]
        focus_questions = plan["focus_questions"]
        accuracy = None
        for cat, acc in weak_cats:
            if cat == focus:
                accuracy = acc
                break

        if focus:
            ui_components.render_continue_card(
                focus, len(focus_questions), accuracy
            )
            if st.button("続きから学習", type="primary", key="home_continue"):
                start_practice(
                    focus_questions[:10], quiz.MODE_STUDY, f"{focus} の練習"
                )
                st.rerun()
        else:
            ui_components.render_empty_state(
                "問題データがありません",
                "data/questions.json に問題を追加すると学習を開始できます。",
                "📭",
            )

    with col_right:
        ui_components.render_section("今週の学習状況")
        ui_components.render_week_activity(
            data_manager.get_study_dates(), results
        )

    st.markdown("")
    ui_components.render_section("苦手分野", "正答率の低い順に表示します")
    ui_components.render_weak_categories(weak_cats)


# --- 学習パス -------------------------------------------------------------
def show_paths():
    data = st.session_state.data
    profile = data["user_profile"]
    results = data["results"]
    current_target = profile.get("target_exam", DEFAULT_TARGET)

    st.markdown("## 学習パス")
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:.86rem;"
        f"margin-bottom:16px;line-height:1.7;'>"
        f"目標とする認定資格を選ぶと、ホーム画面の進捗と推奨学習がその試験に合わせて"
        f"表示されます。現在の目標は <span style='color:{COLORS['primary']};"
        f"font-weight:700;'>{current_target}</span> です。</div>",
        unsafe_allow_html=True,
    )

    paths = content.LEARNING_PATHS
    for row_start in range(0, len(paths), 2):
        cols = st.columns(2)
        for offset, path in enumerate(paths[row_start:row_start + 2]):
            with cols[offset]:
                progress = content.get_path_progress(path, results)
                ui_components.render_path_card(path, progress)

                is_current = path["code"] == current_target
                label = "学習中の目標です" if is_current else "この学習パスを開始"
                if st.button(
                    label,
                    key=f"path_{path['id']}",
                    type="primary" if is_current else "secondary",
                    disabled=is_current,
                ):
                    data_manager.update_user_profile({"target_exam": path["code"]})
                    refresh_data()
                    goto("today")
                    st.rerun()
                st.markdown("<div style='height:8px;'></div>",
                            unsafe_allow_html=True)


# --- 今日の学習 -----------------------------------------------------------
def show_today():
    data = st.session_state.data
    questions = data["questions"]
    results = data["results"]
    metrics = calculator.get_study_metrics(results, data["study_times"])
    weak_cats = calculator.get_weak_categories(results)
    plan = content.get_daily_plan(questions, data["services"], weak_cats)

    today_str = datetime.now().strftime("%Y年%m月%d日")
    ui_components.render_hero(
        "今日の学習",
        "短時間でも毎日続けることが合格への近道です。今日の目標を1つずつ進めましょう。",
        today_str,
    )

    if not questions:
        ui_components.render_empty_state(
            "問題データがありません",
            "data/questions.json に問題を追加すると、今日の学習プランが表示されます。",
            "📭",
        )
        return

    col1, col2 = st.columns([1, 1])

    # 今日の目標
    with col1:
        ui_components.render_section("今日の目標")
        achieved_minutes = metrics["today_minutes"]
        minutes_pct = min(100, achieved_minutes / plan["target_minutes"] * 100)
        st.markdown(
            f"""
            <div class="aws-card">
                <div style="font-size:.78rem;color:{COLORS['text_secondary']};">
                    重点分野
                </div>
                <div style="font-size:1.1rem;font-weight:700;margin:4px 0 12px;">
                    {plan['focus_category']}
                </div>
                <div style="display:flex;justify-content:space-between;
                            font-size:.76rem;margin-bottom:6px;">
                    <span style="color:{COLORS['text_secondary']};">
                        学習時間 {achieved_minutes} / {plan['target_minutes']}分
                    </span>
                    <span style="color:{COLORS['primary']};font-weight:700;">
                        {minutes_pct:.0f}%
                    </span>
                </div>
                {ui_components.progress_bar_html(minutes_pct)}
                <div style="margin-top:12px;font-size:.8rem;
                            color:{COLORS['text_secondary']};line-height:1.7;">
                    目標問題数: <span style="color:{COLORS['text']};font-weight:700;">
                    {plan['target_count']}問</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("練習問題を始める", type="primary", key="today_start"):
            selected = plan["focus_questions"][:plan["target_count"]]
            start_practice(
                selected, quiz.MODE_STUDY, f"{plan['focus_category']} の練習"
            )
            st.rerun()

    # 今日のおすすめサービス
    with col2:
        ui_components.render_section("今日のおすすめサービス")
        recommended = plan["recommended_service"]
        if recommended:
            category, service = recommended
            ui_components.render_service_card(
                service.get("name", ""),
                service.get("description", ""),
                service.get("icon", ""),
                service.get("cp_points", ""),
            )
            if st.button("サービス辞典を開く", key="today_services"):
                goto("services")
                st.rerun()
        else:
            ui_components.render_empty_state(
                "サービス情報がありません",
                "data/services.json にサービスを追加すると表示されます。",
                "📖",
            )

    st.markdown("")
    ui_components.render_section("今日のチェックリスト", "上から順に進めましょう")

    checklist_items = "".join(
        f"<div style='display:flex;gap:10px;align-items:flex-start;"
        f"padding:9px 0;border-bottom:1px solid {COLORS['border_soft']};'>"
        f"<span style='color:{COLORS['primary']};font-weight:700;'>{i}</span>"
        f"<span style='font-size:.85rem;line-height:1.6;'>{item}</span></div>"
        for i, item in enumerate(plan["checklist"], 1)
    )
    st.markdown(
        f"<div class='aws-card'>{checklist_items}</div>", unsafe_allow_html=True
    )


# --- 練習問題 -------------------------------------------------------------
def show_practice():
    data = st.session_state.data
    questions = data["questions"]

    if quiz.is_active():
        quiz.render_quiz(on_finish=lambda: goto("home"))
        return

    st.markdown("## 練習問題")
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:.86rem;"
        f"margin-bottom:16px;line-height:1.7;'>"
        f"学習モードでは回答するたびに解説を表示します。"
        f"試験モードでは解説を最後にまとめて確認します。</div>",
        unsafe_allow_html=True,
    )

    if not questions:
        ui_components.render_empty_state(
            "問題データがありません",
            "data/questions.json に問題を追加すると練習問題を開始できます。",
            "📭",
        )
        return

    mode_label = st.segmented_control(
        "出題モード",
        options=["学習モード", "試験モード"],
        default="学習モード",
        key="practice_mode",
    )
    mode = quiz.MODE_STUDY if mode_label != "試験モード" else quiz.MODE_EXAM

    st.markdown(
        f"<div style='font-size:.78rem;color:{COLORS['text_secondary']};"
        f"margin:-6px 0 14px;line-height:1.7;'>"
        + ("回答するとすぐに正誤と解説が表示されます。じっくり理解したいときに適しています。"
           if mode == quiz.MODE_STUDY else
           "本番と同じように解説を伏せて出題します。最後にまとめて振り返ります。")
        + "</div>",
        unsafe_allow_html=True,
    )

    categories = content.get_categories(questions)
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_categories = st.multiselect(
            "出題カテゴリ（未選択の場合はすべて）",
            options=categories,
            key="practice_categories",
        )
    with col2:
        count = st.slider("出題数", min_value=5, max_value=min(30, len(questions)),
                          value=min(10, len(questions)), step=5,
                          key="practice_count")

    pool = [
        q for q in questions
        if not selected_categories or q.get("category") in selected_categories
    ]

    st.markdown(
        f"<div style='font-size:.78rem;color:{COLORS['text_muted']};"
        f"margin-bottom:10px;'>対象問題数: {len(pool)}問</div>",
        unsafe_allow_html=True,
    )

    if not pool:
        ui_components.render_empty_state(
            "条件に合う問題がありません",
            "カテゴリの選択を見直してください。",
            "🔍",
        )
        return

    if st.button("練習を開始する", type="primary", key="practice_start"):
        selected = random.sample(pool, min(count, len(pool)))
        title = "練習問題"
        if selected_categories:
            title = "・".join(selected_categories) + " の練習"
        quiz.start_quiz(selected, mode=mode, source="practice", title=title)
        st.rerun()

    # カテゴリ別の状況
    st.markdown("")
    ui_components.render_section("カテゴリ別の問題数")
    cat_rows = []
    for category in categories:
        num = sum(1 for q in questions if q.get("category") == category)
        cat_rows.append(
            f"<div style='display:flex;justify-content:space-between;"
            f"padding:8px 0;border-bottom:1px solid {COLORS['border_soft']};"
            f"font-size:.84rem;'><span>{category}</span>"
            f"<span style='color:{COLORS['text_secondary']};'>{num}問</span></div>"
        )
    st.markdown(
        f"<div class='aws-card'>{''.join(cat_rows)}</div>", unsafe_allow_html=True
    )


# --- 模擬試験 -------------------------------------------------------------
def show_exam():
    data = st.session_state.data
    questions = data["questions"]

    if quiz.is_active():
        quiz.render_quiz(on_finish=lambda: goto("home"))
        return

    st.markdown("## 模擬試験")
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:.86rem;"
        f"margin-bottom:16px;line-height:1.7;'>"
        f"本番と同じ形式で出題します。解説は試験終了後にまとめて確認できます。"
        f"合格ラインは {quiz.PASS_LINE:.0f}% です。</div>",
        unsafe_allow_html=True,
    )

    if not questions:
        ui_components.render_empty_state(
            "問題データがありません",
            "data/questions.json に問題を追加すると模擬試験を受けられます。",
            "📭",
        )
        return

    presets = [
        ("本番形式", 20, "本番に近い問題数で実力を確認します", "mock"),
        ("短時間", 10, "10問だけ解いて手軽に確認します", "random"),
        ("全問演習", len(questions), "登録されているすべての問題を解きます", "all"),
    ]

    cols = st.columns(3)
    for col, (name, num, desc, exam_type) in zip(cols, presets):
        actual = min(num, len(questions))
        with col:
            st.markdown(
                f"""
                <div class="aws-card" style="height:100%;">
                    <div style="font-size:1rem;font-weight:700;">{name}</div>
                    <div style="font-size:1.6rem;font-weight:700;
                                color:{COLORS['primary']};margin:6px 0;">
                        {actual}問
                    </div>
                    <div style="font-size:.78rem;color:{COLORS['text_secondary']};
                                line-height:1.7;min-height:42px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("開始する", key=f"exam_{exam_type}", type="primary"):
                selected = random.sample(questions, actual)
                quiz.start_quiz(
                    selected, mode=quiz.MODE_EXAM, source=exam_type,
                    title=f"模擬試験（{name}）",
                )
                st.rerun()

    # 受験履歴
    st.markdown("")
    ui_components.render_section("受験履歴", "直近の結果を表示します")
    results = [r for r in data["results"] if r.get("mode") != quiz.MODE_STUDY]
    if not results:
        ui_components.render_empty_state(
            "受験履歴がありません",
            "模擬試験を受けると、ここに結果の履歴が表示されます。",
            "📋",
        )
        return

    rows = []
    for result in list(reversed(results))[:8]:
        try:
            stamp = datetime.fromisoformat(result["timestamp"]).strftime("%m/%d %H:%M")
        except (KeyError, ValueError):
            stamp = "-"
        accuracy = result.get("accuracy", 0)
        color = COLORS["success"] if accuracy >= quiz.PASS_LINE else COLORS["warning"]
        rows.append(
            f"<div style='display:flex;justify-content:space-between;"
            f"padding:9px 0;border-bottom:1px solid {COLORS['border_soft']};"
            f"font-size:.82rem;'>"
            f"<span style='color:{COLORS['text_secondary']};'>{stamp}</span>"
            f"<span>{result.get('correct', 0)}/{result.get('total', 0)}問</span>"
            f"<span style='color:{color};font-weight:700;'>{accuracy:.0f}%</span>"
            f"</div>"
        )
    st.markdown(
        f"<div class='aws-card'>{''.join(rows)}</div>", unsafe_allow_html=True
    )


# --- AWSサービス辞典 ------------------------------------------------------
def show_services():
    data = st.session_state.data
    services = data["services"]

    st.markdown("## AWSサービス辞典")
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:.86rem;"
        f"margin-bottom:16px;line-height:1.7;'>"
        f"試験で問われる主要サービスを分野ごとにまとめています。</div>",
        unsafe_allow_html=True,
    )

    if not services:
        ui_components.render_empty_state(
            "サービス情報がありません",
            "data/services.json にサービスを追加すると一覧が表示されます。",
            "📖",
        )
        return

    search_term = st.text_input(
        "サービスを検索", placeholder="例: EC2、ストレージ、監視",
        key="service_search",
    )
    term = (search_term or "").strip().lower()

    total_hits = 0
    for category, service_list in services.items():
        matched = [
            s for s in service_list
            if not term
            or term in s.get("name", "").lower()
            or term in s.get("description", "").lower()
            or term in s.get("cp_points", "").lower()
        ]
        if not matched:
            continue
        total_hits += len(matched)

        with st.expander(f"{category}（{len(matched)}件）", expanded=bool(term)):
            for service in matched:
                ui_components.render_service_card(
                    service.get("name", ""),
                    service.get("description", ""),
                    service.get("icon", ""),
                    service.get("cp_points", ""),
                )

    if term and total_hits == 0:
        ui_components.render_empty_state(
            "該当するサービスが見つかりません",
            "別のキーワードで検索してください。",
            "🔍",
        )


# --- 分析 -----------------------------------------------------------------
ANALYSIS_DIMENSIONS = [
    ("論点", "topics", "試験ガイドの論点ごとの正答率です。最も細かい単位で弱点を確認できます。"),
    ("出題分野", "domains", "認定試験の出題分野ごとの正答率です。"),
    ("AWS サービス", "services", "問題に関連する AWS サービスごとの正答率です。"),
    ("カテゴリ", "categories", "アプリ内のカテゴリごとの正答率です。"),
]


def render_focus_recommendation(results):
    """次に復習すべき論点を提示する。"""
    key, rows = calculator.get_focus_recommendations(results, limit=3)
    if not rows:
        st.markdown(
            f"<div class='aws-card' style='border-left:4px solid "
            f"{COLORS['success']};'>"
            f"<div style='font-size:.8rem;font-weight:700;margin-bottom:4px;'>"
            f"苦手分野は見つかりませんでした</div>"
            f"<div style='font-size:.8rem;color:{COLORS['text_secondary']};"
            f"line-height:1.7;'>現在の記録では、すべての分野で正答できています。"
            f"新しいカテゴリの問題や模擬試験に挑戦して、"
            f"出題範囲を広げてみましょう。</div></div>",
            unsafe_allow_html=True,
        )
        return

    label_map = {d[1]: d[0] for d in ANALYSIS_DIMENSIONS}
    unit = label_map.get(key, "分野")

    items = []
    for label, accuracy, correct, total in rows:
        items.append(
            f"<li style='margin-bottom:6px;line-height:1.7;'>"
            f"<span style='color:{COLORS['text']};font-weight:600;'>{label}</span>"
            f"<span style='color:{COLORS['text_muted']};font-size:.76rem;'>"
            f"　{correct}/{total} 問正解・{accuracy:.0f}%</span></li>"
        )

    st.markdown(
        f"<div class='aws-card' style='border-left:4px solid {COLORS['primary']};'>"
        f"<div style='font-size:.8rem;font-weight:700;margin-bottom:8px;'>"
        f"次に復習したい{unit}</div>"
        f"<ul style='margin:0;padding-left:18px;font-size:.82rem;'>"
        f"{''.join(items)}</ul></div>",
        unsafe_allow_html=True,
    )


def render_weak_area_analysis(results):
    """分野・論点・サービス単位の弱点分析。"""
    render_focus_recommendation(results)
    st.markdown("")

    available = [
        (label, key, desc) for label, key, desc in ANALYSIS_DIMENSIONS
        if calculator.has_breakdown(results, key)
    ]

    if not available:
        ui_components.render_empty_state(
            "詳細な分野データがありません",
            "練習問題または模擬試験をもう一度解くと、論点・出題分野・"
            "AWS サービスごとの正答率が表示されます。",
            "📊",
        )
        return

    labels = [a[0] for a in available]
    try:
        picked = st.segmented_control(
            "集計単位",
            labels,
            default=labels[0],
            key="analysis_dimension",
            label_visibility="collapsed",
        )
    except AttributeError:
        picked = st.radio(
            "集計単位", labels, horizontal=True,
            key="analysis_dimension", label_visibility="collapsed",
        )
    if not picked:
        picked = labels[0]

    label, key, desc = next(a for a in available if a[0] == picked)

    st.markdown(
        f"<div style='font-size:.78rem;color:{COLORS['text_secondary']};"
        f"margin:4px 0 10px;line-height:1.6;'>{desc}</div>",
        unsafe_allow_html=True,
    )

    rows = calculator.get_weak_areas(results, key, min_total=1)
    weak = [
        (f"{name}（{correct}/{total} 問）", accuracy)
        for name, accuracy, correct, total in rows
    ]
    ui_components.render_weak_categories(weak, limit=15)


def show_analysis():
    data = st.session_state.data
    results = data["results"]
    study_times = data["study_times"]

    st.markdown("## 分析")
    st.markdown(
        f"<div style='color:{COLORS['text_secondary']};font-size:.86rem;"
        f"margin-bottom:16px;line-height:1.7;'>"
        f"学習の推移と分野ごとの正答率を確認できます。</div>",
        unsafe_allow_html=True,
    )

    if not results:
        ui_components.render_empty_state(
            "分析できるデータがありません",
            "練習問題または模擬試験を1回解くと、正答率の推移や分野別の分析が表示されます。",
            "📊",
        )
        if st.button("練習問題を始める", type="primary", key="analysis_start"):
            goto("practice")
            st.rerun()
        return

    metrics = calculator.get_study_metrics(results, study_times)
    cols = st.columns(3)
    ui_components.render_metric_card(
        cols[0], "累計正答率", f"{metrics['overall_accuracy']:.1f}%", "🎯")
    ui_components.render_metric_card(
        cols[1], "今週の正答率", f"{metrics['week_accuracy']:.1f}%", "📅",
        color=COLORS["secondary"])
    ui_components.render_metric_card(
        cols[2], "連続学習日数", f"{data_manager.get_streak()}日", "🔥",
        color=COLORS["success"])

    st.markdown("")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["正答率の推移", "分野別の正答率", "学習時間", "受験タイプ別"]
    )

    with tab1:
        fig = analytics.create_accuracy_trend_chart(results)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        render_weak_area_analysis(results)

    with tab3:
        fig = analytics.create_study_time_chart(study_times)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            ui_components.render_empty_state(
                "学習時間の記録がありません",
                "練習問題や模擬試験を解くと、学習時間が自動的に記録されます。",
                "⏱️",
            )

    with tab4:
        fig = analytics.create_exam_type_chart(results)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


# --- 実績 -----------------------------------------------------------------
def show_achievements():
    data = st.session_state.data
    profile = data["user_profile"]
    badges = profile.get("badges", [])
    level_info = content.calculate_level(profile.get("total_xp", 0))

    st.markdown("## 実績")

    st.markdown(
        f"""
        <div class="aws-card" style="margin-bottom:18px;">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;gap:12px;flex-wrap:wrap;">
                <div>
                    <div style="font-size:.74rem;color:{COLORS['text_secondary']};">
                        現在のレベル
                    </div>
                    <div style="font-size:1.5rem;font-weight:700;
                                color:{COLORS['primary']};">
                        LV.{level_info['level']}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:.74rem;color:{COLORS['text_secondary']};">
                        累計XP
                    </div>
                    <div style="font-size:1.5rem;font-weight:700;">
                        {profile.get('total_xp', 0)}
                    </div>
                </div>
            </div>
            <div style="margin-top:14px;">
                <div style="font-size:.72rem;color:{COLORS['text_secondary']};
                            margin-bottom:6px;">
                    次のレベルまで {level_info['next_xp'] - level_info['current_xp']} XP
                </div>
                {ui_components.progress_bar_html(level_info['percentage'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ui_components.render_section(
        "獲得バッジ", f"{len(badges)} / {len(content.BADGE_DEFS)} 個を獲得"
    )

    badge_items = list(content.BADGE_DEFS.items())
    for row_start in range(0, len(badge_items), 4):
        cols = st.columns(4)
        for offset, (badge_key, info) in enumerate(
                badge_items[row_start:row_start + 4]):
            with cols[offset]:
                ui_components.render_badge(
                    info["name"], info["icon"], info["desc"],
                    badge_key in badges,
                )


# --- 設定 -----------------------------------------------------------------
def show_settings():
    data = st.session_state.data
    profile = data["user_profile"]

    st.markdown("## 設定")

    col1, col2 = st.columns(2)

    with col1:
        ui_components.render_section("プロフィール")
        username = st.text_input(
            "ユーザー名", profile.get("username", "学習者"), key="set_username"
        )

        codes = [p["code"] for p in content.LEARNING_PATHS]
        current_code = profile.get("target_exam", DEFAULT_TARGET)
        index = codes.index(current_code) if current_code in codes else 1
        target = st.selectbox(
            "目標とする試験",
            options=codes,
            index=index,
            format_func=lambda c: next(
                (f"{p['code']}　{p['title']}" for p in content.LEARNING_PATHS
                 if p["code"] == c), c
            ),
            key="set_target",
        )

        try:
            current_date = datetime.fromisoformat(
                profile.get("exam_date", "2026-10-15")
            )
        except ValueError:
            current_date = datetime(2026, 10, 15)

        exam_date = st.date_input(
            "試験予定日", value=current_date, key="set_exam_date"
        )

        if st.button("保存する", type="primary", key="set_save"):
            data_manager.update_user_profile({
                "username": username,
                "target_exam": target,
                "exam_date": str(exam_date),
            })
            refresh_data()
            st.success("保存しました。")

    with col2:
        ui_components.render_section("学習データ")
        metrics = calculator.get_study_metrics(data["results"], data["study_times"])
        st.markdown(
            f"""
            <div class="aws-card">
                <div style="display:flex;justify-content:space-between;
                            padding:6px 0;font-size:.84rem;">
                    <span style="color:{COLORS['text_secondary']};">総問題数</span>
                    <span style="font-weight:700;">{metrics['total_questions']}問</span>
                </div>
                <div style="display:flex;justify-content:space-between;
                            padding:6px 0;font-size:.84rem;">
                    <span style="color:{COLORS['text_secondary']};">総正解数</span>
                    <span style="font-weight:700;">{metrics['total_correct']}問</span>
                </div>
                <div style="display:flex;justify-content:space-between;
                            padding:6px 0;font-size:.84rem;">
                    <span style="color:{COLORS['text_secondary']};">全体正答率</span>
                    <span style="font-weight:700;color:{COLORS['primary']};">
                        {metrics['overall_accuracy']:.1f}%
                    </span>
                </div>
                <div style="display:flex;justify-content:space-between;
                            padding:6px 0;font-size:.84rem;">
                    <span style="color:{COLORS['text_secondary']};">受験回数</span>
                    <span style="font-weight:700;">{len(data['results'])}回</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        results_df = pd.DataFrame(data["results"])
        if not results_df.empty:
            st.download_button(
                "学習結果をCSVでダウンロード",
                data=results_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="aws_skills_results.csv",
                mime="text/csv",
                key="set_csv",
            )
        else:
            st.markdown(
                f"<div style='font-size:.78rem;color:{COLORS['text_muted']};"
                f"margin-top:8px;'>学習結果が記録されるとCSVを出力できます。</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    ui_components.render_section("データの初期化", "この操作は取り消せません")
    confirm = st.checkbox(
        "学習履歴・学習時間・受験履歴をすべて削除することに同意します",
        key="set_reset_confirm",
    )
    if st.button("すべての学習データを削除する", disabled=not confirm,
                 key="set_reset"):
        data_manager.save_json("results.json", [])
        data_manager.save_json("study_time.json", [])
        data_manager.save_json("exam_history.json", [])
        data_manager.update_user_profile({
            "badges": [], "total_xp": 0, "xp": 0, "level": 1,
        })
        refresh_data()
        st.success("学習データを削除しました。")

    st.markdown(
        f"<div style='margin-top:26px;font-size:.72rem;"
        f"color:{COLORS['text_muted']};'>{APP_NAME}　{APP_VERSION}</div>",
        unsafe_allow_html=True,
    )


# --- ルーティング ---------------------------------------------------------
ROUTES = {
    "home": show_home,
    "paths": show_paths,
    "today": show_today,
    "practice": show_practice,
    "exam": show_exam,
    "services": show_services,
    "analysis": show_analysis,
    "achievements": show_achievements,
    "settings": show_settings,
}


def render_mobile_nav():
    """モバイル用ナビゲーション（サイドバーがない場合）。"""
    if not is_mobile_device():
        return
    
    # モバイルでは、メインコンテンツの上部にナビゲーションバーを表示
    render_mobile_navbar()


# --- メイン ---------------------------------------------------------------
def main():
    """メインアプリケーション実行関数。
    
    認証機能が有効な場合は、ユーザーのログイン状態をチェックして
    ログイン画面または通常 UI を表示する。
    """
    # モバイル対応初期化
    init_mobile_session()
    inject_mobile_styles()
    
    init_session()
    theme.setup()
    
    # 認証機能が有効な場合のチェック
    if settings.FEATURE_AUTHENTICATION:
        if not auth_manager.is_authenticated():
            # 未認証ユーザー向けのログイン画面
            st.markdown(
                f"<h1 style='text-align:center; color:{COLORS['primary']};'>"
                f"🚀 {APP_NAME}</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='text-align:center; color:{COLORS['text_secondary']};'>"
                f"{APP_SUBTITLE}</p>",
                unsafe_allow_html=True,
            )
            st.divider()
            render_login_form()
            logger.info("ユーザーをログイン画面にリダイレクト")
            return
        else:
            # 認証済みユーザー向けのメニュー
            render_user_menu()
    
    # 通常の UI 表示
    render_sidebar()
    render_mobile_nav()

    page = st.session_state.get("page", "home")
    ROUTES.get(page, show_home)()


if __name__ == "__main__":
    main()
