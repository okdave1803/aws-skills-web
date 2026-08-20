"""AWS Skills - 出題エンジン

練習問題と模擬試験で共通利用する。
学習モードは回答直後に解説を表示し、試験モードは最後にまとめて表示する。
"""

from datetime import datetime

import streamlit as st

from modules import content, data_manager, ui_components
from modules.theme import COLORS

PASS_LINE = 65.0
MODE_STUDY = "study"
MODE_EXAM = "exam"


def start_quiz(questions, mode=MODE_STUDY, source="practice", title="練習問題"):
    """出題セッションを開始する。"""
    st.session_state.quiz = {
        "questions": list(questions),
        "mode": mode,
        "source": source,
        "title": title,
        "answers": [],
        "index": 0,
        "revealed": False,
        "start_time": datetime.now().isoformat(),
        "saved": False,
    }
    # 前回の選択状態が残らないようにする
    for key in [k for k in st.session_state.keys() if str(k).startswith("opt_")]:
        del st.session_state[key]


def is_active() -> bool:
    return bool(st.session_state.get("quiz"))


def clear_quiz() -> None:
    st.session_state.quiz = None


def get_correct_indices(question):
    """正解インデックスをリストで返す。

    schema_version 2 は correct をリストで保持する。
    旧形式（整数）のデータもそのまま扱えるようにしている。
    """
    correct = question.get("correct", 0)
    if isinstance(correct, list):
        return sorted(int(i) for i in correct)
    return [int(correct)]


def get_select_count(question):
    """選ぶべき選択肢の数。"""
    count = question.get("select_count")
    if isinstance(count, int) and count > 0:
        return count
    return len(get_correct_indices(question))


def is_multiple(question) -> bool:
    """複数選択問題かどうか。"""
    if question.get("type") == "multiple":
        return True
    if question.get("type") == "single":
        return False
    return len(get_correct_indices(question)) > 1


def _record_answer(quiz, question, selected):
    """回答を記録する。selected は選択インデックスのリスト（未回答は None）。"""
    correct_indices = get_correct_indices(question)

    if selected is None:
        selected_indices = None
        is_correct = False
    else:
        selected_indices = sorted(set(selected))
        # 単一選択・複数選択のいずれも集合一致で採点する
        is_correct = selected_indices == correct_indices

    quiz["answers"].append({
        "id": question.get("id"),
        "category": question.get("category", "未分類"),
        "domain": question.get("domain", ""),
        "topic": question.get("topic", ""),
        "difficulty": content.get_difficulty(question),
        "services": list(question.get("services") or []),
        "question": question.get("question", ""),
        "options": question.get("options", []),
        "selected": selected_indices,
        "correct": correct_indices,
        "is_correct": is_correct,
        "explanation": question.get("explanation", ""),
        "option_explanations": list(question.get("option_explanations") or []),
        "references": list(question.get("references") or []),
        "skipped": selected_indices is None,
    })
    return is_correct


def _build_breakdown(answers, field, default="未分類"):
    """指定フィールド単位で正答数と出題数を集計する。"""
    breakdown = {}
    for answer in answers:
        label = answer.get(field) or default
        stats = breakdown.setdefault(label, {"correct": 0, "total": 0})
        stats["total"] += 1
        if answer["is_correct"]:
            stats["correct"] += 1
    return breakdown


def _build_service_breakdown(answers):
    """関連サービス単位で集計する（1 問が複数サービスに紐づく）。"""
    breakdown = {}
    for answer in answers:
        for service in answer.get("services") or []:
            stats = breakdown.setdefault(service, {"correct": 0, "total": 0})
            stats["total"] += 1
            if answer["is_correct"]:
                stats["correct"] += 1
    return breakdown


def _build_category_breakdown(answers):
    """カテゴリ別の集計（既存の結果フォーマットと互換）。"""
    return _build_breakdown(answers, "category")


def _save_result(quiz):
    """結果と学習時間を保存し、バッジと XP を更新する。"""
    if quiz.get("saved"):
        return
    quiz["saved"] = True

    answers = quiz["answers"]
    if not answers:
        return

    correct_count = sum(1 for a in answers if a["is_correct"])
    total_count = len(answers)
    accuracy = correct_count / total_count * 100

    try:
        started = datetime.fromisoformat(quiz["start_time"])
        elapsed = max(0, int((datetime.now() - started).total_seconds()))
    except (ValueError, KeyError):
        elapsed = 0

    # 既存の結果フォーマットを維持し、分析用の内訳を追加する
    data_manager.record_exam_result({
        "timestamp": datetime.now().isoformat(),
        "correct": correct_count,
        "total": total_count,
        "accuracy": accuracy,
        "type": quiz.get("source", "practice"),
        "mode": quiz.get("mode", MODE_STUDY),
        "categories": _build_category_breakdown(answers),
        "domains": _build_breakdown(answers, "domain", "未設定"),
        "topics": _build_breakdown(answers, "topic", "未設定"),
        "services": _build_service_breakdown(answers),
        "difficulties": _build_breakdown(answers, "difficulty", "標準"),
    })

    # 学習時間の記録（学習カレンダーと分析で使用する）
    data_manager.add_study_time(elapsed, quiz.get("source", "practice"))

    # XP とレベルの更新
    profile = data_manager.load_json("user_profile.json", {})
    gained = correct_count * 10 + total_count * 2
    total_xp = int(profile.get("total_xp", 0)) + gained
    level_info = content.calculate_level(total_xp)
    data_manager.update_user_profile({
        "total_xp": total_xp,
        "xp": level_info["current_xp"],
        "level": level_info["level"],
    })
    quiz["gained_xp"] = gained

    # バッジ判定
    results = data_manager.load_json("results.json", [])
    streak = data_manager.get_streak()
    for badge_id in content.evaluate_badges(results, streak):
        data_manager.add_badge(badge_id)


def render_quiz(on_finish=None):
    """出題セッションを描画する。終了時は結果画面を表示する。"""
    quiz = st.session_state.get("quiz")
    if not quiz:
        return

    questions = quiz["questions"]
    if not questions:
        ui_components.render_empty_state(
            "出題できる問題がありません",
            "問題データを確認してください。",
            "⚠️",
        )
        if st.button("戻る", key="quiz_empty_back"):
            clear_quiz()
            st.rerun()
        return

    if quiz["index"] >= len(questions):
        _render_result(quiz, on_finish)
        return

    _render_question(quiz)


def _render_question(quiz):
    questions = quiz["questions"]
    index = quiz["index"]
    question = questions[index]
    mode = quiz["mode"]

    mode_label = "学習モード" if mode == MODE_STUDY else "試験モード"
    st.markdown(
        f"<div style='font-size:.76rem;color:{COLORS['text_secondary']};"
        f"margin-bottom:8px;'>{quiz['title']}・{mode_label}</div>",
        unsafe_allow_html=True,
    )

    st.progress(index / len(questions))
    ui_components.render_question_header(
        index + 1,
        len(questions),
        question.get("category", "未分類"),
        content.get_difficulty(question),
        content.get_related_services(question),
    )
    ui_components.render_question_text(question.get("question", ""))

    options = question.get("options", [])
    multiple = is_multiple(question)
    need = get_select_count(question)
    base_key = f"opt_{index}_{question.get('id', index)}"

    if multiple:
        st.markdown(
            f"<div style='font-size:.8rem;color:{COLORS['primary']};"
            f"font-weight:700;margin-bottom:4px;'>"
            f"正しいものを {need} つ選んでください</div>",
            unsafe_allow_html=True,
        )
        selected = []
        for i, text in enumerate(options):
            if st.checkbox(
                text, key=f"{base_key}_{i}", disabled=quiz["revealed"]
            ):
                selected.append(i)
    else:
        picked = st.radio(
            "選択肢を1つ選んでください",
            options=list(range(len(options))),
            format_func=lambda i: options[i],
            key=base_key,
            index=None,
            disabled=quiz["revealed"],
        )
        selected = [] if picked is None else [picked]

    # --- 学習モード: 回答後に解説を表示 ---
    if quiz["revealed"]:
        answer = quiz["answers"][-1]
        correct_text = "／".join(
            options[i] for i in answer["correct"] if i < len(options)
        )
        ui_components.render_answer_feedback(
            answer["is_correct"],
            correct_text,
            answer["explanation"],
        )
        ui_components.render_option_breakdown(
            options,
            answer["correct"],
            answer["selected"],
            answer.get("option_explanations"),
        )
        ui_components.render_references(answer.get("references"))
        is_last = index + 1 >= len(questions)
        label = "結果を見る" if is_last else "次の問題へ"
        if st.button(label, type="primary", key=f"next_{index}"):
            quiz["index"] += 1
            quiz["revealed"] = False
            st.rerun()
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("回答する", type="primary", key=f"answer_{index}"):
            if not selected:
                if multiple:
                    st.warning(f"選択肢を {need} つ選んでください。")
                else:
                    st.warning("選択肢を1つ選んでください。")
            elif multiple and len(selected) != need:
                st.warning(
                    f"{need} つ選んでください（現在 {len(selected)} つ選択中）。"
                )
            else:
                _record_answer(quiz, question, selected)
                if quiz["mode"] == MODE_STUDY:
                    quiz["revealed"] = True
                else:
                    quiz["index"] += 1
                st.rerun()

    with col2:
        if st.button("スキップ", key=f"skip_{index}"):
            _record_answer(quiz, question, None)
            quiz["index"] += 1
            quiz["revealed"] = False
            st.rerun()


def _render_result(quiz, on_finish=None):
    _save_result(quiz)

    answers = quiz["answers"]
    if not answers:
        ui_components.render_empty_state(
            "回答がありません",
            "問題に回答すると結果が表示されます。",
            "📝",
        )
        if st.button("戻る", key="result_empty_back"):
            clear_quiz()
            st.rerun()
        return

    correct_count = sum(1 for a in answers if a["is_correct"])
    total_count = len(answers)
    accuracy = correct_count / total_count * 100
    passed = accuracy >= PASS_LINE

    st.markdown("## 学習結果")
    ui_components.render_result_summary(correct_count, total_count, accuracy, passed)

    gained = quiz.get("gained_xp", 0)
    if gained:
        st.markdown(
            f"<div style='text-align:center;margin-top:10px;font-size:.82rem;"
            f"color:{COLORS['primary']};font-weight:700;'>+{gained} XP を獲得しました"
            f"</div>",
            unsafe_allow_html=True,
        )

    # カテゴリ別の内訳
    breakdown = _build_category_breakdown(answers)
    if len(breakdown) > 1:
        st.markdown("")
        ui_components.render_section("カテゴリ別の正答率")
        rows = sorted(
            ((c, s["correct"] / s["total"] * 100, s) for c, s in breakdown.items()),
            key=lambda x: x[1],
        )
        weak = [(c, acc) for c, acc, _s in rows]
        ui_components.render_weak_categories(weak, limit=len(weak))

    st.markdown("")
    ui_components.render_section(
        "問題の振り返り", "すべての問題の解説を確認できます"
    )

    for i, answer in enumerate(answers, 1):
        if answer["skipped"]:
            status = "⏭ スキップ"
        elif answer["is_correct"]:
            status = "✓ 正解"
        else:
            status = "✗ 不正解"

        with st.expander(f"{i}. {status}　{answer['question'][:42]}"):
            options = answer.get("options", [])
            correct_indices = answer.get("correct") or []
            selected_indices = answer.get("selected")

            correct_text = "／".join(
                options[j] for j in correct_indices if j < len(options)
            )
            if selected_indices and options:
                your_text = "／".join(
                    options[j] for j in selected_indices if j < len(options)
                )
            else:
                your_text = "未回答"

            st.markdown(f"**あなたの回答:** {your_text}")
            st.markdown(f"**正解:** {correct_text}")
            if answer["explanation"]:
                st.markdown(f"**解説:** {answer['explanation']}")

            ui_components.render_option_breakdown(
                options,
                correct_indices,
                selected_indices,
                answer.get("option_explanations"),
            )
            ui_components.render_references(answer.get("references"))

    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("もう一度挑戦する", type="primary", key="result_retry"):
            start_quiz(
                quiz["questions"], quiz["mode"], quiz["source"], quiz["title"]
            )
            st.rerun()
    with col2:
        if st.button("ホームに戻る", key="result_home"):
            clear_quiz()
            if on_finish:
                on_finish()
            st.rerun()
