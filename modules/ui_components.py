"""AWS Skills - UI コンポーネント

画面で使い回す表示部品をまとめる。色は theme.COLORS を参照する。
"""

import html
from datetime import datetime, timedelta

import streamlit as st

from modules.theme import COLORS, DIFFICULTY_COLORS

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _esc(value) -> str:
    """HTML に埋め込む前にエスケープする。"""
    return html.escape(str(value if value is not None else ""))


# --- 基本パーツ -----------------------------------------------------------
def render_section(title: str, subtitle: str = "") -> None:
    """セクション見出し。"""
    sub_html = (
        f"<span class='aws-section-sub'>{_esc(subtitle)}</span>" if subtitle else ""
    )
    st.markdown(
        f"<div class='aws-section'>"
        f"<span class='aws-section-title'>{_esc(title)}</span>{sub_html}</div>",
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, eyebrow: str = "") -> None:
    """ホーム画面のヒーロー領域。"""
    eyebrow_html = (
        f"<div class='aws-hero-eyebrow'>{_esc(eyebrow)}</div>" if eyebrow else ""
    )
    st.markdown(
        f"""
        <div class="aws-hero">
            {eyebrow_html}
            <h1>{_esc(title)}</h1>
            <p>{_esc(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, description: str, icon: str = "📘") -> None:
    """データが無いときの空状態表示。"""
    st.markdown(
        f"""
        <div class="aws-empty">
            <div style="font-size:26px;">{_esc(icon)}</div>
            <div class="aws-empty-title">{_esc(title)}</div>
            <div class="aws-empty-desc">{_esc(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chips(items, style: str = "") -> str:
    """チップ（タグ）の HTML 文字列を生成する。"""
    cls = "aws-chip" + (f" {style}" if style else "")
    return "".join(f"<span class='{cls}'>{_esc(i)}</span>" for i in items)


def progress_bar_html(percentage: float, color: str = None) -> str:
    """プログレスバーの HTML 文字列を生成する。"""
    color = color or COLORS["primary"]
    pct = max(0.0, min(100.0, float(percentage)))
    return (
        f"<div class='aws-bar'><div style='width:{pct:.1f}%;"
        f"background:{color};'></div></div>"
    )


def render_progress_bar(value, max_value=100, color=None, label="") -> None:
    """プログレスバーを描画する。"""
    percentage = (value / max_value * 100) if max_value else 0
    if label:
        st.markdown(
            f"<div style='color:{COLORS['text_secondary']};font-size:.76rem;"
            f"margin-bottom:4px;'>{_esc(label)}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(progress_bar_html(percentage, color), unsafe_allow_html=True)


def render_metric_card(col, title, value, icon="", caption="", color=None) -> None:
    """メトリクスカード。col は st.columns の要素。"""
    color = color or COLORS["primary"]
    icon_html = f"<span>{_esc(icon)}</span>" if icon else ""
    caption_html = (
        f"<div class='aws-metric-caption'>{_esc(caption)}</div>" if caption else ""
    )
    with col:
        st.markdown(
            f"""
            <div class="aws-metric">
                <div class="aws-metric-label">{icon_html}{_esc(title)}</div>
                <div class="aws-metric-value" style="color:{color};">{_esc(value)}</div>
                {caption_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- ダッシュボード向け ---------------------------------------------------
def render_progress_card(exam_code, exam_name, percentage, days_until,
                         next_action, accuracy) -> None:
    """学習進捗カード（試験目標・進捗・残り日数・次の行動）。"""
    days_color = COLORS["danger"] if days_until <= 30 else COLORS["text"]
    days_text = f"{days_until}日" if days_until > 0 else "日程未設定"

    st.markdown(
        f"""
        <div class="aws-card">
            <div style="display:flex;justify-content:space-between;
                        align-items:flex-start;gap:12px;flex-wrap:wrap;">
                <div>
                    <div style="font-size:.72rem;color:{COLORS['text_secondary']};
                                font-weight:600;">学習目標</div>
                    <div style="font-size:1.15rem;font-weight:700;margin-top:2px;">
                        {_esc(exam_code)}
                    </div>
                    <div style="font-size:.78rem;color:{COLORS['text_secondary']};">
                        {_esc(exam_name)}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:.72rem;color:{COLORS['text_secondary']};
                                font-weight:600;">試験日まで</div>
                    <div style="font-size:1.3rem;font-weight:700;color:{days_color};">
                        {_esc(days_text)}
                    </div>
                </div>
            </div>
            <div style="margin-top:16px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:.76rem;margin-bottom:6px;">
                    <span style="color:{COLORS['text_secondary']};">全体の進捗</span>
                    <span style="color:{COLORS['primary']};font-weight:700;">
                        {percentage:.0f}%
                    </span>
                </div>
                {progress_bar_html(percentage)}
                <div style="margin-top:6px;font-size:.72rem;
                            color:{COLORS['text_muted']};">
                    現在の正答率 {accuracy:.1f}%
                </div>
            </div>
            <div style="margin-top:16px;padding:12px 14px;
                        background:rgba(9,114,211,.10);
                        border-left:3px solid {COLORS['secondary']};
                        border-radius:8px;">
                <div style="font-size:.72rem;color:#6BB4F5;font-weight:700;">
                    次のおすすめ
                </div>
                <div style="font-size:.84rem;margin-top:4px;line-height:1.65;">
                    {_esc(next_action)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_week_activity(study_dates, results=None) -> None:
    """直近 7 日間の学習アクティビティ。

    以前のカレンダー表示は表示崩れと表記の誤りがあったため置き換えた。
    """
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    study_dates = study_dates or set()

    # 結果からも学習日を補完する
    result_dates = set()
    for result in results or []:
        try:
            result_dates.add(datetime.fromisoformat(result["timestamp"]).date())
        except (KeyError, ValueError, TypeError):
            continue
    active_dates = set(study_dates) | result_dates

    if not active_dates:
        render_empty_state(
            "まだ学習記録がありません",
            "練習問題または模擬試験を1回解くと、直近7日間の学習状況がここに表示されます。",
            "📅",
        )
        return

    cells = []
    for day in days:
        is_active = day in active_dates
        is_today = day == today
        if is_active:
            bg = COLORS["success"]
            fg = "#0E1A0E"
            border = COLORS["success"]
        else:
            bg = COLORS["card_alt"]
            fg = COLORS["text_muted"]
            border = COLORS["border"]
        if is_today:
            border = COLORS["primary"]
        cells.append(
            f"<div class='aws-week-day'>"
            f"<div class='aws-week-label'>{WEEKDAY_JA[day.weekday()]}</div>"
            f"<div class='aws-week-cell' style='background:{bg};color:{fg};"
            f"border-color:{border};'>{day.day}</div></div>"
        )

    active_count = sum(1 for d in days if d in active_dates)
    st.markdown(
        f"""
        <div class="aws-card">
            <div class="aws-week">{''.join(cells)}</div>
            <div style="margin-top:14px;font-size:.76rem;
                        color:{COLORS['text_secondary']};">
                直近7日間で <span style="color:{COLORS['primary']};font-weight:700;">
                {active_count}日</span> 学習しました
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_weak_categories(weak_cats, limit: int = 5) -> None:
    """苦手分野ランキング。"""
    if not weak_cats:
        render_empty_state(
            "苦手分野の分析データがありません",
            "練習問題や模擬試験を解くと、カテゴリごとの正答率がここに表示されます。",
            "📊",
        )
        return

    rows = []
    for i, (category, accuracy) in enumerate(weak_cats[:limit], 1):
        if accuracy < 50:
            color = COLORS["danger"]
        elif accuracy < 70:
            color = COLORS["warning"]
        else:
            color = COLORS["success"]
        rows.append(
            f"""
            <div style="margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:.82rem;margin-bottom:6px;">
                    <span><span style="color:{COLORS['text_muted']};">{i}.</span>
                        {_esc(category)}</span>
                    <span style="color:{color};font-weight:700;">{accuracy:.1f}%</span>
                </div>
                {progress_bar_html(accuracy, color)}
            </div>
            """
        )

    st.markdown(
        f"<div class='aws-card'>{''.join(rows)}</div>", unsafe_allow_html=True
    )


def render_continue_card(category, question_count, accuracy) -> None:
    """「続きから学習」カードの表示部分。"""
    accuracy_html = (
        f"<span style='color:{COLORS['primary']};font-weight:700;'>"
        f"{accuracy:.0f}%</span>"
        if accuracy is not None else
        f"<span style='color:{COLORS['text_muted']};'>未受験</span>"
    )
    st.markdown(
        f"""
        <div class="aws-card">
            <div style="font-size:.72rem;color:{COLORS['text_secondary']};
                        font-weight:600;">おすすめの学習分野</div>
            <div style="font-size:1.12rem;font-weight:700;margin:4px 0 8px;">
                {_esc(category)}
            </div>
            <div style="font-size:.78rem;color:{COLORS['text_secondary']};
                        line-height:1.7;">
                この分野には {question_count} 問が登録されています。<br>
                現在の正答率: {accuracy_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- 学習パス -------------------------------------------------------------
def render_path_card(path, progress) -> None:
    """学習パスカード。ボタンは呼び出し側でこの下に配置する。"""
    difficulty = path.get("difficulty", "標準")
    diff_color = DIFFICULTY_COLORS.get(difficulty, COLORS["secondary"])

    if progress["total"] > 0:
        progress_line = (
            f"<div style='display:flex;justify-content:space-between;"
            f"font-size:.74rem;margin-bottom:6px;'>"
            f"<span style='color:{COLORS['text_secondary']};'>学習の進捗</span>"
            f"<span style='color:{COLORS['primary']};font-weight:700;'>"
            f"{progress['accuracy']:.0f}%（{progress['correct']}/{progress['total']}問）"
            f"</span></div>{progress_bar_html(progress['accuracy'])}"
        )
    else:
        progress_line = (
            f"<div style='font-size:.74rem;color:{COLORS['text_muted']};'>"
            f"まだ学習記録がありません</div>"
            f"{progress_bar_html(0)}"
        )

    st.markdown(
        f"""
        <div class="aws-card" style="height:100%;">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;gap:8px;">
                <span class="aws-chip" style="background:rgba(9,114,211,.14);
                      color:#6BB4F5;border-color:rgba(9,114,211,.4);">
                    {_esc(path.get('code', ''))}
                </span>
                <span style="font-size:.72rem;font-weight:700;color:{diff_color};">
                    難易度: {_esc(difficulty)}
                </span>
            </div>
            <div style="font-size:1.05rem;font-weight:700;margin:10px 0 6px;">
                {_esc(path['title'])}
            </div>
            <div style="font-size:.79rem;color:{COLORS['text_secondary']};
                        line-height:1.7;min-height:44px;">
                {_esc(path.get('description', ''))}
            </div>
            <div style="margin-top:10px;font-size:.74rem;
                        color:{COLORS['text_secondary']};">
                <div>対象: {_esc(path.get('audience', ''))}</div>
                <div style="margin-top:2px;">目安学習時間: {_esc(path.get('hours', ''))}</div>
            </div>
            <div style="margin-top:10px;">{chips(path.get('services', []))}</div>
            <div style="margin-top:14px;">{progress_line}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- サービス辞典 ---------------------------------------------------------
def render_service_card(service_name, description, icon, cp_points="") -> None:
    """AWS サービスカード。"""
    cp_html = ""
    if cp_points:
        cp_html = (
            f"<div style='margin-top:10px;padding-top:10px;"
            f"border-top:1px solid {COLORS['border']};'>"
            f"<div style='font-size:.68rem;color:{COLORS['text_muted']};"
            f"font-weight:700;margin-bottom:3px;'>試験のポイント</div>"
            f"<div style='color:{COLORS['success']};font-size:.75rem;"
            f"line-height:1.6;'>{_esc(cp_points)}</div></div>"
        )

    st.markdown(
        f"""
        <div class="aws-card" style="margin-bottom:10px;">
            <div style="font-size:1rem;font-weight:700;">
                {_esc(icon)} {_esc(service_name)}
            </div>
            <div style="color:{COLORS['text_secondary']};font-size:.79rem;
                        margin-top:4px;line-height:1.7;">
                {_esc(description)}
            </div>
            {cp_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- 実績 -----------------------------------------------------------------
def render_badge(badge_name, badge_icon, badge_desc, unlocked=False) -> None:
    """実績バッジ。"""
    if unlocked:
        border = COLORS["primary"]
        opacity = "1"
        name_color = COLORS["text"]
        status = "獲得済み"
        status_color = COLORS["primary"]
    else:
        border = COLORS["border"]
        opacity = ".55"
        name_color = COLORS["text_secondary"]
        status = "未獲得"
        status_color = COLORS["text_muted"]

    st.markdown(
        f"""
        <div class="aws-card" style="text-align:center;border-color:{border};
             opacity:{opacity};margin-bottom:10px;">
            <div style="font-size:30px;">{_esc(badge_icon)}</div>
            <div style="font-size:.85rem;font-weight:700;margin-top:8px;
                        color:{name_color};">{_esc(badge_name)}</div>
            <div style="font-size:.7rem;color:{COLORS['text_secondary']};
                        margin-top:4px;line-height:1.6;">{_esc(badge_desc)}</div>
            <div style="font-size:.66rem;margin-top:8px;font-weight:700;
                        color:{status_color};">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- 問題表示 -------------------------------------------------------------
def render_question_header(index, total, category, difficulty, services) -> None:
    """問題のヘッダー（進捗・カテゴリ・難易度・関連サービス）。"""
    diff_color = DIFFICULTY_COLORS.get(difficulty, COLORS["secondary"])
    service_html = (
        f"<div style='margin-top:8px;'>{chips(services, 'aws-chip-plain')}</div>"
        if services else ""
    )
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;
                    align-items:center;gap:10px;flex-wrap:wrap;">
            <div style="font-size:.8rem;color:{COLORS['text_secondary']};
                        font-weight:600;">
                問題 <span style="color:{COLORS['primary']};font-size:1rem;">
                {index}</span> / {total}
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
                <span class="aws-chip aws-chip-blue">{_esc(category)}</span>
                <span class="aws-chip" style="background:transparent;
                      color:{diff_color};border-color:{diff_color};">
                    {_esc(difficulty)}
                </span>
            </div>
        </div>
        {service_html}
        """,
        unsafe_allow_html=True,
    )


def render_question_text(text) -> None:
    """問題文。"""
    st.markdown(
        f"""
        <div class="aws-card" style="margin:12px 0 6px;">
            <div style="font-size:1rem;line-height:1.85;font-weight:600;">
                {_esc(text)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_answer_feedback(is_correct, correct_text, explanation) -> None:
    """回答後のフィードバック（学習モード用）。"""
    if is_correct:
        color = COLORS["success"]
        label = "正解です"
        icon = "✓"
    else:
        color = COLORS["danger"]
        label = "不正解"
        icon = "✗"

    explanation_html = ""
    if explanation:
        explanation_html = (
            f"<div style='margin-top:10px;padding-top:10px;"
            f"border-top:1px solid {COLORS['border']};font-size:.82rem;"
            f"line-height:1.8;color:{COLORS['text_secondary']};'>"
            f"<span style='color:{COLORS['text']};font-weight:700;'>解説</span><br>"
            f"{_esc(explanation)}</div>"
        )

    st.markdown(
        f"""
        <div class="aws-card" style="border-left:4px solid {color};">
            <div style="color:{color};font-weight:700;font-size:.95rem;">
                {icon} {label}
            </div>
            <div style="font-size:.84rem;margin-top:6px;line-height:1.7;">
                正解: {_esc(correct_text)}
            </div>
            {explanation_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_option_breakdown(
    options, correct_indices, selected_indices, option_explanations
) -> None:
    """選択肢ごとの解説（なぜ正解か / なぜ誤りか）を表示する。"""
    if not options or not option_explanations:
        return

    correct_set = set(correct_indices or [])
    selected_set = set(selected_indices or [])

    rows = []
    for i, text in enumerate(options):
        if i in correct_set:
            color = COLORS["success"]
            mark = "✓"
        elif i in selected_set:
            color = COLORS["danger"]
            mark = "✗"
        else:
            color = COLORS["border"]
            mark = "・"

        note = ""
        if i in selected_set:
            note = (
                f"<span style='margin-left:6px;font-size:.7rem;"
                f"color:{COLORS['text_muted']};'>あなたの回答</span>"
            )

        detail = ""
        if i < len(option_explanations) and option_explanations[i]:
            detail = (
                f"<div style='margin-top:4px;font-size:.78rem;line-height:1.7;"
                f"color:{COLORS['text_secondary']};'>"
                f"{_esc(option_explanations[i])}</div>"
            )

        rows.append(
            f"""
            <div style="padding:10px 12px;margin-bottom:8px;
                        border-left:3px solid {color};
                        background:{COLORS['card_alt']};border-radius:6px;">
                <div style="font-size:.82rem;line-height:1.6;">
                    <span style="color:{color};font-weight:700;">{mark}</span>
                    {_esc(text)}{note}
                </div>
                {detail}
            </div>
            """
        )

    st.markdown(
        f"<div class='aws-card'>"
        f"<div style='font-size:.78rem;font-weight:700;margin-bottom:10px;"
        f"color:{COLORS['text']};'>選択肢ごとの解説</div>"
        f"{''.join(rows)}</div>",
        unsafe_allow_html=True,
    )


def render_references(references) -> None:
    """出典（AWS 公式ドキュメントなど）へのリンクを表示する。"""
    if not references:
        return

    links = []
    for r in references:
        title = r.get("title") or r.get("url", "")
        url = r.get("url", "")
        if not url:
            continue
        links.append(
            f"<li style='margin-bottom:6px;line-height:1.6;'>"
            f"<a href='{_esc(url)}' target='_blank' rel='noopener noreferrer' "
            f"style='color:{COLORS['secondary']};text-decoration:none;'>"
            f"{_esc(title)} ↗</a></li>"
        )

    if not links:
        return

    st.markdown(
        f"<div class='aws-card'>"
        f"<div style='font-size:.78rem;font-weight:700;margin-bottom:8px;"
        f"color:{COLORS['text']};'>出典</div>"
        f"<ul style='margin:0;padding-left:18px;font-size:.78rem;'>"
        f"{''.join(links)}</ul></div>",
        unsafe_allow_html=True,
    )


def render_result_summary(correct, total, accuracy, passed) -> None:
    """試験結果のサマリー。"""
    color = COLORS["success"] if passed else COLORS["warning"]
    label = "合格ライン到達" if passed else "合格ラインまであと少し"
    st.markdown(
        f"""
        <div class="aws-card" style="text-align:center;border-color:{color};">
            <div style="font-size:.76rem;color:{COLORS['text_secondary']};
                        font-weight:600;">今回のスコア</div>
            <div style="font-size:2.4rem;font-weight:700;color:{color};
                        margin:6px 0;">{accuracy:.0f}%</div>
            <div style="font-size:.86rem;">{correct} / {total} 問 正解</div>
            <div style="margin-top:10px;font-size:.78rem;color:{color};
                        font-weight:700;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
