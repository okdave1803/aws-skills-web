# -*- coding: utf-8 -*-
"""問題データ（data/questions.json）の検証スクリプト。

問題を追加・編集したあとに実行してください。
外部ライブラリは不要です。

    python tools/validate_questions.py

参照 URL が実際に到達できるかも確認する場合（ネットワーク接続が必要）:

    python tools/validate_questions.py --check-urls
"""
import io
import json
import os
import re
import sys

# Windows のコンソールでも日本語を出力できるようにする
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):  # pragma: no cover
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(ROOT, "data", "questions.json")

REQUIRED_FIELDS = [
    "schema_version", "id", "category", "domain", "topic", "difficulty",
    "type", "select_count", "services", "exam", "tags",
    "question", "options", "correct", "explanation",
    "option_explanations", "source_title", "source_url", "references",
]

VALID_CATEGORY = {"クラウドの基礎", "AWS サービス", "セキュリティ", "コスト最適化"}
VALID_DOMAIN = {
    # CLF-C02
    "クラウドの概念", "セキュリティとコンプライアンス",
    "クラウドテクノロジーとサービス", "請求、料金、およびサポート",
    # SAA-C03
    "セキュアなアーキテクチャの設計", "弾力性に優れたアーキテクチャの設計",
    "高性能アーキテクチャの設計", "コストを最適化したアーキテクチャの設計",
}
VALID_DIFFICULTY = {"基礎", "標準", "応用", "難関"}
VALID_TYPE = {"single", "multiple"}
VALID_EXAM = {"CLF-C02", "SAA-C03", "SOA-C02", "DVA-C02", "SAP-C02"}

MIN_EXPLANATION = 60
# ハングル（韓国語）の混入検出。
# 文字そのものを書かず、コードポイント範囲から組み立てる。
_HANGUL_RANGES = ((0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F))
HANGUL = re.compile(
    "[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in _HANGUL_RANGES) + "]"
)


def validate(questions):
    errors = []
    warnings = []
    seen_ids = {}

    if not isinstance(questions, list) or not questions:
        return ["questions.json はオブジェクトの配列である必要があります"], []

    for pos, q in enumerate(questions):
        tag = f"[{pos}] id={q.get('id', '?')}"

        if not isinstance(q, dict):
            errors.append(f"{tag}: オブジェクトではありません")
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in q]
        if missing:
            errors.append(f"{tag}: 必須フィールドがありません: {missing}")
            continue

        unknown = [k for k in q if k not in REQUIRED_FIELDS]
        if unknown:
            warnings.append(f"{tag}: 未知のフィールド: {unknown}")

        if q["schema_version"] != 2:
            errors.append(f"{tag}: schema_version は 2 である必要があります")

        # id
        if not isinstance(q["id"], int) or q["id"] < 1:
            errors.append(f"{tag}: id は 1 以上の整数である必要があります")
        elif q["id"] in seen_ids:
            errors.append(f"{tag}: id が重複しています（[{seen_ids[q['id']]}] と同じ）")
        else:
            seen_ids[q["id"]] = pos

        # enums
        for field, valid in (
            ("category", VALID_CATEGORY),
            ("domain", VALID_DOMAIN),
            ("difficulty", VALID_DIFFICULTY),
            ("type", VALID_TYPE),
        ):
            if q[field] not in valid:
                errors.append(f"{tag}: {field} が不正です: {q[field]!r}")

        for code in q["exam"] or []:
            if code not in VALID_EXAM:
                errors.append(f"{tag}: exam の試験コードが不正です: {code!r}")
        if not q["exam"]:
            errors.append(f"{tag}: exam を 1 つ以上指定してください")

        # options / correct
        options = q["options"]
        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"{tag}: options は 2 件以上必要です")
            continue
        if len({str(o) for o in options}) != len(options):
            warnings.append(f"{tag}: options に重複した文言があります")

        correct = q["correct"]
        if not isinstance(correct, list) or not correct:
            errors.append(f"{tag}: correct は空でないリストである必要があります")
        else:
            if len(set(correct)) != len(correct):
                errors.append(f"{tag}: correct にインデックスの重複があります")
            for i in correct:
                if not isinstance(i, int) or not (0 <= i < len(options)):
                    errors.append(f"{tag}: correct のインデックス {i} が範囲外です")
            if q["select_count"] != len(correct):
                errors.append(
                    f"{tag}: select_count ({q['select_count']}) と "
                    f"correct の件数 ({len(correct)}) が一致しません"
                )
            expect = "multiple" if len(correct) > 1 else "single"
            if q["type"] != expect:
                errors.append(f"{tag}: type は {expect} である必要があります")
            if len(correct) >= len(options):
                errors.append(f"{tag}: すべての選択肢が正解になっています")

        # explanations
        if len(q["option_explanations"]) != len(options):
            errors.append(
                f"{tag}: option_explanations の件数 "
                f"({len(q['option_explanations'])}) が options "
                f"({len(options)}) と一致しません"
            )
        else:
            correct_set = set(correct if isinstance(correct, list) else [])
            for j, oe in enumerate(q["option_explanations"]):
                if not str(oe).strip():
                    errors.append(f"{tag}: option_explanations[{j}] が空です")
                marked = str(oe).startswith("正解です")
                if marked and j not in correct_set:
                    errors.append(
                        f"{tag}: option_explanations[{j}] が「正解です」で"
                        f"始まっていますが、correct に含まれていません"
                    )
                if not marked and j in correct_set:
                    warnings.append(
                        f"{tag}: option_explanations[{j}] は正解の選択肢です。"
                        f"「正解です」で始めることを推奨します"
                    )

        if len(q["explanation"]) < MIN_EXPLANATION:
            errors.append(
                f"{tag}: explanation が短すぎます "
                f"({len(q['explanation'])} 文字、{MIN_EXPLANATION} 文字以上必要)"
            )

        # references
        if not q["references"]:
            errors.append(f"{tag}: references を 1 つ以上指定してください")
        for r in q["references"] or []:
            if not isinstance(r, dict) or "title" not in r or "url" not in r:
                errors.append(f"{tag}: references の要素に title と url が必要です")
                continue
            if not str(r["url"]).startswith("https://"):
                errors.append(f"{tag}: references の URL は https:// で始めてください: {r['url']!r}")

        # source_title / source_url（主たる出典）
        if not str(q["source_title"]).strip():
            errors.append(f"{tag}: source_title が空です")
        if not str(q["source_url"]).startswith("https://"):
            errors.append(
                f"{tag}: source_url は https:// で始めてください: {q['source_url']!r}"
            )
        first = (q["references"] or [{}])[0]
        if isinstance(first, dict):
            if first.get("url") != q["source_url"]:
                errors.append(
                    f"{tag}: source_url が references[0].url と一致しません"
                )
            if first.get("title") != q["source_title"]:
                errors.append(
                    f"{tag}: source_title が references[0].title と一致しません"
                )

        # services は data/services.json と表記を合わせることを推奨
        if not isinstance(q["services"], list):
            errors.append(f"{tag}: services はリストである必要があります")

        # 文字化け・他言語の混入チェック
        blob = " ".join([
            q["question"], q["explanation"], q["topic"],
            " ".join(str(o) for o in options),
            " ".join(str(o) for o in q["option_explanations"]),
        ])
        m = HANGUL.search(blob)
        if m:
            errors.append(f"{tag}: 韓国語の文字が含まれています: {m.group()!r}")

    return errors, warnings


def check_urls(questions):
    """参照 URL に実際にアクセスして到達性を確認する。"""
    import urllib.request
    import urllib.error

    urls = sorted({
        r["url"] for q in questions for r in q.get("references", [])
        if isinstance(r, dict) and r.get("url")
    })
    print(f"\n参照 URL の到達性を確認します（{len(urls)} 件）...")
    bad = []
    for url in urls:
        try:
            req = urllib.request.Request(
                url, method="HEAD",
                headers={"User-Agent": "Mozilla/5.0 (aws-skills-validator)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                code = resp.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:  # noqa: BLE001
            code = f"ERROR: {e}"
        ok = code == 200
        if not ok:
            bad.append((url, code))
        print(f"  {'OK ' if ok else 'NG '} {code}  {url}")
    return bad


def main():
    if not os.path.exists(QUESTIONS):
        print(f"見つかりません: {QUESTIONS}")
        return 1

    with io.open(QUESTIONS, encoding="utf-8") as f:
        try:
            questions = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON の解析に失敗しました: {e}")
            return 1

    print(f"{len(questions)} 問を検証します: {QUESTIONS}")
    errors, warnings = validate(questions)

    if warnings:
        print(f"\n警告 ({len(warnings)} 件):")
        for w in warnings:
            print("  -", w)

    if errors:
        print(f"\nエラー ({len(errors)} 件):")
        for e in errors:
            print("  -", e)
        print("\n検証に失敗しました。")
        return 1

    # 統計
    lens = [len(q["explanation"]) for q in questions]
    cats, domains, exams, topics = {}, {}, {}, set()
    multi = 0
    for q in questions:
        cats[q["category"]] = cats.get(q["category"], 0) + 1
        domains[q["domain"]] = domains.get(q["domain"], 0) + 1
        for code in q["exam"]:
            exams[code] = exams.get(code, 0) + 1
        topics.add(q["topic"])
        if q["type"] == "multiple":
            multi += 1

    def show(title, mapping):
        print(f"  {title}")
        for k, v in sorted(mapping.items(), key=lambda kv: -kv[1]):
            print(f"      {k}: {v}")

    print("\n検証に成功しました。")
    print(f"  問題数        : {len(questions)}（複数選択 {multi} 問）")
    print(f"  論点数        : {len(topics)}")
    print(f"  解説の文字数  : 最小 {min(lens)} / 最大 {max(lens)} / "
          f"平均 {sum(lens) // len(lens)}")
    show("試験別内訳（重複あり）:", exams)
    show("カテゴリ内訳:", cats)
    show("出題分野内訳:", domains)
    refs = sum(len(q["references"]) for q in questions)
    urls = {r["url"] for q in questions for r in q["references"]}
    print(f"  出典リンク    : {refs} 件（ユニーク URL {len(urls)} 件）")

    if "--check-urls" in sys.argv:
        bad = check_urls(questions)
        if bad:
            print(f"\n到達できない URL が {len(bad)} 件あります:")
            for url, code in bad:
                print(f"  - {code}  {url}")
            return 1
        print("すべての参照 URL に到達できました。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
