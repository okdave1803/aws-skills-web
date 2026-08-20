"""AWS Skills - デザインシステム

AWS コンソール / Skill Builder 風のカラートークンとグローバル CSS を提供する。
色や余白の定義はこのファイルに集約し、他モジュールは COLORS を参照する。
"""

import streamlit as st
import streamlit.components.v1 as components

APP_NAME = "AWS Skills"
APP_SUBTITLE = "AWS認定試験 学習アプリ"
APP_VERSION = "v2.1 - Skill Builder Edition"

# --- カラートークン -------------------------------------------------------
# 既存モジュールとの互換のため、従来のキー（primary/accent/success/danger/
# bg/card/text）は必ず維持する。
COLORS = {
    # 背景
    "bg": "#16191F",
    "sidebar": "#1B222C",
    "card": "#232F3E",
    "card_alt": "#1F2937",
    "surface": "#1E2530",
    # アクセント
    "primary": "#FF9900",
    "primary_hover": "#FFB143",
    "secondary": "#0972D3",
    "accent": "#0972D3",
    "secondary_hover": "#2B8FE8",
    # ステータス
    "success": "#2BB534",
    "warning": "#F2C037",
    "danger": "#FF5D5D",
    # テキスト
    "text": "#F2F3F3",
    "text_secondary": "#AAB7B8",
    "text_muted": "#7D8998",
    # 罫線
    "border": "#2E3B4E",
    "border_soft": "#252F3E",
}

# 難易度ごとの表示色
DIFFICULTY_COLORS = {
    "基礎": COLORS["success"],
    "標準": COLORS["secondary"],
    "応用": COLORS["primary"],
    "難関": COLORS["danger"],
}


def _css() -> str:
    c = COLORS
    return f"""
<style>
/* ===== ベース ===== */
.stApp, [data-testid="stAppViewContainer"] {{
    background-color: {c['bg']};
    color: {c['text']};
}}
[data-testid="stMainBlockContainer"] {{
    padding-top: 2.2rem;
    padding-bottom: 4rem;
    max-width: 1180px;
}}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}

html, body, [data-testid="stAppViewContainer"] {{
    overflow-x: hidden;
    -webkit-text-size-adjust: 100%;
}}

/* ===== サイドバー ===== */
[data-testid="stSidebar"] {{
    background-color: {c['sidebar']};
    border-right: 1px solid {c['border_soft']};
}}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding-top: 1.2rem;
}}

/* ===== 見出し（過大な余白を避ける） ===== */
h1, h2, h3, h4 {{
    color: {c['text']};
    letter-spacing: .01em;
}}
h1 {{ font-size: 1.65rem !important; margin-bottom: .35rem !important; }}
h2 {{ font-size: 1.28rem !important; margin: .2rem 0 .3rem !important; }}
h3 {{ font-size: 1.06rem !important; margin: .2rem 0 .3rem !important; }}
hr {{ border-color: {c['border_soft']}; margin: 1.1rem 0; }}

/* ===== 共通カード ===== */
.aws-card {{
    background: {c['card']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 18px 20px;
    transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease;
}}
.aws-card:hover {{
    border-color: {c['primary']};
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,.35);
}}

/* セクション見出し */
.aws-section {{
    display: flex; align-items: baseline; gap: 10px;
    margin: 4px 0 12px;
}}
.aws-section-title {{ font-size: 1.05rem; font-weight: 700; color: {c['text']}; }}
.aws-section-sub {{ font-size: .78rem; color: {c['text_secondary']}; }}

/* ヒーロー */
.aws-hero {{
    background: linear-gradient(135deg, #232F3E 0%, #1B2532 55%, #16191F 100%);
    border: 1px solid {c['border']};
    border-left: 4px solid {c['primary']};
    border-radius: 14px;
    padding: 26px 28px;
    margin-bottom: 18px;
}}
.aws-hero h1 {{ font-size: 1.55rem !important; margin: 0 0 8px !important; }}
.aws-hero p {{ color: {c['text_secondary']}; font-size: .92rem; margin: 0; line-height: 1.7; }}
.aws-hero-eyebrow {{
    display: inline-block; font-size: .7rem; font-weight: 700; letter-spacing: .12em;
    color: {c['primary']}; margin-bottom: 10px;
}}

/* メトリクスカード */
.aws-metric {{
    background: {c['card']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
    transition: border-color .18s ease, transform .18s ease;
}}
.aws-metric:hover {{ border-color: {c['primary']}; transform: translateY(-2px); }}
.aws-metric-label {{
    color: {c['text_secondary']}; font-size: .76rem; font-weight: 600;
    display: flex; align-items: center; gap: 6px;
}}
.aws-metric-value {{
    font-size: 1.7rem; font-weight: 700; margin-top: 6px; line-height: 1.15;
}}
.aws-metric-caption {{ color: {c['text_muted']}; font-size: .7rem; margin-top: 4px; }}

/* バッジ・チップ */
.aws-chip {{
    display: inline-block;
    background: rgba(255,153,0,.12);
    color: {c['primary']};
    border: 1px solid rgba(255,153,0,.35);
    border-radius: 999px;
    padding: 3px 10px;
    font-size: .72rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
}}
.aws-chip-blue {{
    background: rgba(9,114,211,.14); color: #6BB4F5; border-color: rgba(9,114,211,.4);
}}
.aws-chip-plain {{
    background: rgba(170,183,184,.1); color: {c['text_secondary']};
    border-color: {c['border']};
}}

/* プログレスバー */
.aws-bar {{
    background: {c['border_soft']};
    border-radius: 999px;
    overflow: hidden;
    height: 8px;
    width: 100%;
}}
.aws-bar > div {{ height: 100%; border-radius: 999px; transition: width .4s ease; }}

/* 空状態 */
.aws-empty {{
    background: {c['card_alt']};
    border: 1px dashed {c['border']};
    border-radius: 12px;
    padding: 26px 20px;
    text-align: center;
}}
.aws-empty-title {{ color: {c['text']}; font-weight: 600; font-size: .95rem; }}
.aws-empty-desc {{ color: {c['text_secondary']}; font-size: .8rem; margin-top: 6px; line-height: 1.7; }}

/* 週間アクティビティ */
.aws-week {{ display: flex; gap: 8px; justify-content: space-between; }}
.aws-week-day {{ flex: 1; text-align: center; }}
.aws-week-label {{ font-size: .68rem; color: {c['text_secondary']}; margin-bottom: 6px; }}
.aws-week-cell {{
    height: 38px; border-radius: 8px; display: flex; align-items: center;
    justify-content: center; font-size: .72rem; font-weight: 700;
    border: 1px solid {c['border']};
}}

/* ===== Streamlit ウィジェット調整 ===== */
.stButton > button {{
    border-radius: 10px;
    font-weight: 600;
    min-height: 44px;           /* タッチ操作に十分な高さ */
    border: 1px solid {c['border']};
    background-color: {c['card']};
    color: {c['text']};
    transition: all .16s ease;
    width: 100%;
}}
.stButton > button:hover {{
    border-color: {c['primary']};
    color: {c['primary']};
    background-color: #26344A;
}}
.stButton > button[kind="primary"] {{
    background-color: {c['primary']};
    border-color: {c['primary']};
    color: #16191F;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: {c['primary_hover']};
    border-color: {c['primary_hover']};
    color: #16191F;
}}

div[data-testid="stExpander"] details {{
    background: {c['card']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
div[data-testid="stExpander"] summary:hover {{ color: {c['primary']}; }}

div[data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {c['border_soft']}; }}
button[data-baseweb="tab"] {{ font-weight: 600; }}

[data-testid="stMetricValue"] {{ font-size: 1.5rem; }}

/* ラジオ（選択肢）をカード風に */
[data-testid="stRadio"] label {{
    padding: 6px 2px;
    font-size: .93rem;
    line-height: 1.6;
}}

/* ===== モバイル最適化（768px 未満） ===== */
@media (max-width: 768px) {{
    [data-testid="stMainBlockContainer"] {{
        padding-top: 1rem;
        padding-left: .85rem;
        padding-right: .85rem;
    }}
    /* カラムを 1 列に */
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: .6rem !important; }}
    [data-testid="stColumn"] {{
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }}
    .aws-hero {{ padding: 20px 18px; }}
    .aws-hero h1 {{ font-size: 1.28rem !important; }}
    .aws-hero p {{ font-size: .86rem; }}
    h1 {{ font-size: 1.32rem !important; }}
    .aws-metric-value {{ font-size: 1.5rem; }}
    .stButton > button {{ min-height: 48px; font-size: .95rem; }}
    /* 本文の可読性 */
    .aws-card {{ padding: 16px; }}
    .aws-week-cell {{ height: 32px; font-size: .66rem; }}
    /* モバイルではサイドバーを広く取りすぎない */
    [data-testid="stSidebar"] {{ min-width: 17rem !important; }}
}}

/* モバイル用クイックナビ（PC では非表示） */
.st-key-mobile_nav {{ display: none; }}
@media (max-width: 768px) {{
    .st-key-mobile_nav {{
        display: block;
        background: {c['card_alt']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        padding: 10px 10px 4px;
        margin-bottom: 14px;
    }}
    .st-key-mobile_nav [data-testid="stColumn"] {{
        min-width: 33% !important;
        flex: 1 1 33% !important;
    }}
    .st-key-mobile_nav .stButton > button {{
        min-height: 42px; font-size: .78rem; padding: 4px 2px;
    }}
}}

/* 横スクロール防止 */
[data-testid="stMainBlockContainer"] * {{ max-width: 100%; }}
</style>
"""


def inject_css() -> None:
    """グローバル CSS を適用する。"""
    st.markdown(_css(), unsafe_allow_html=True)


_PWA_SCRIPT = """
<script>
(function () {
  try {
    /* st.html はページ内に、components.html は iframe 内に展開されるため
       どちらでも親ドキュメントを取得できるようにする */
    var d = (window.parent && window.parent.document) || document;
    if (!d || d.getElementById("aws-skills-pwa")) return;
    var marker = d.createElement("meta");
    marker.id = "aws-skills-pwa";
    d.head.appendChild(marker);

    function meta(attr, key, val) {
      var el = d.querySelector("meta[" + attr + '="' + key + '"]');
      if (!el) {
        el = d.createElement("meta");
        el.setAttribute(attr, key);
        d.head.appendChild(el);
      }
      el.setAttribute("content", val);
    }
    meta("name", "viewport",
         "width=device-width, initial-scale=1, viewport-fit=cover");
    meta("name", "apple-mobile-web-app-capable", "yes");
    meta("name", "mobile-web-app-capable", "yes");
    meta("name", "apple-mobile-web-app-status-bar-style", "black-translucent");
    meta("name", "apple-mobile-web-app-title", "AWS Skills");
    meta("name", "theme-color", "#16191F");
  } catch (e) {
    /* クロスオリジン等で失敗しても無視する */
  }
})();
</script>
"""


def inject_pwa_head() -> None:
    """iPhone の Safari「ホーム画面に追加」向けの head メタタグを注入する。

    Streamlit は st.markdown 内の <script> をサニタイズするため、
    JavaScript を実行できる API 経由で head を更新する。
    失敗しても表示や機能には影響しない（ベストエフォート）。
    """
    try:
        # Streamlit 1.49 以降の推奨 API
        st.html(_PWA_SCRIPT, unsafe_allow_javascript=True)
    except TypeError:
        # 旧バージョン向けのフォールバック
        components.html(_PWA_SCRIPT, height=0)


def setup() -> None:
    """ページ全体のテーマ設定をまとめて適用する。"""
    inject_css()
    inject_pwa_head()
