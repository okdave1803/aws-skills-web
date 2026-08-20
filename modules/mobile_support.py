"""
AWS Skills - モバイル対応ユーティリティ

デバイス検出、レスポンシブ UI、モバイル固有の機能を提供する。
"""

import streamlit as st
from modules.theme import COLORS


def is_mobile_device() -> bool:
    """モバイルデバイスで実行中かを判定"""
    try:
        # Streamlit の session_state でデバイス情報を確認
        if 'device_type' not in st.session_state:
            # User-Agent を確認（クライアント側で設定される）
            st.session_state.device_type = 'desktop'
        return st.session_state.device_type == 'mobile'
    except:
        return False


def get_layout_columns() -> tuple:
    """デバイスに応じた列数を取得
    
    Returns:
        (main_cols, sidebar_space): メイン列数、サイドバースペース
    """
    if is_mobile_device():
        return 1, 0  # モバイルは 1 列
    return 3, 1  # デスクトップは 3 列


def render_mobile_navbar() -> None:
    """モバイル用ナビゲーションバー（トップに配置）"""
    if not is_mobile_device():
        return
    
    st.markdown("""
    <style>
    .mobile-navbar {
        position: sticky;
        top: 0;
        background: #232F3E;
        border-bottom: 1px solid #2E3B4E;
        padding: 0.5rem;
        z-index: 999;
        display: flex;
        gap: 0.5rem;
        overflow-x: auto;
    }
    .mobile-navbar-item {
        flex: 0 0 auto;
        padding: 0.4rem 0.8rem;
        background: #1B222C;
        border: 1px solid #2E3B4E;
        border-radius: 8px;
        font-size: 0.8rem;
        cursor: pointer;
        white-space: nowrap;
    }
    .mobile-navbar-item:hover {
        background: #26344A;
        border-color: #FF9900;
    }
    </style>
    """, unsafe_allow_html=True)


def render_responsive_metric(label: str, value: str, icon: str = "") -> None:
    """レスポンシブなメトリクス表示
    
    Args:
        label: ラベルテキスト
        value: 値（大きく表示）
        icon: 絵文字またはアイコン
    """
    if is_mobile_device():
        # モバイル: 小さく表示
        st.markdown(f"""
        <div style="
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            margin: 4px 0;
        ">
            <div style="font-size: 0.75rem; color: {COLORS['text_secondary']};">
                {icon} {label}
            </div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {COLORS['text']}; margin-top: 4px;">
                {value}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # デスクトップ: 通常表示
        st.metric(label, value)


def render_responsive_columns(items: list, cols: int = 3) -> None:
    """レスポンシブなカラムレイアウト
    
    Args:
        items: 表示するアイテムのリスト
        cols: デスクトップの列数（デフォルト 3）
    """
    if is_mobile_device():
        # モバイル: 1 列
        for item in items:
            if callable(item):
                item()  # コールバック関数を実行
            else:
                st.write(item)
    else:
        # デスクトップ: 指定列数
        columns = st.columns(cols)
        for i, item in enumerate(items):
            col = columns[i % cols]
            with col:
                if callable(item):
                    item()
                else:
                    st.write(item)


def render_button_group(buttons: dict, full_width: bool = True) -> str:
    """ボタングループ（モバイル対応）
    
    Args:
        buttons: {"label": "key"} の辞書
        full_width: フルサイズボタンか
        
    Returns:
        クリックされたボタンのキー
    """
    cols = st.columns(len(buttons))
    for col, (label, key) in zip(cols, buttons.items()):
        with col:
            if st.button(label, key=key, use_container_width=True):
                return key
    return None


def render_mobile_friendly_tabs(tabs_dict: dict) -> str:
    """モバイル対応タブ
    
    Args:
        tabs_dict: {"タブ名": content_function} の辞書
        
    Returns:
        選択されたタブ名
    """
    if is_mobile_device():
        # モバイル: セレクトボックスで表示
        selected = st.selectbox(
            "メニュー",
            list(tabs_dict.keys()),
            label_visibility="collapsed"
        )
        return selected
    else:
        # デスクトップ: タブで表示
        selected = st.tabs(list(tabs_dict.keys()))
        for i, (tab_name, content_func) in enumerate(tabs_dict.items()):
            with selected[i]:
                if callable(content_func):
                    content_func()
                else:
                    st.write(content_func)
        return list(tabs_dict.keys())[0]


def render_mobile_friendly_form(form_fields: dict) -> dict:
    """モバイル対応フォーム
    
    Args:
        form_fields: {
            "field_name": {
                "type": "text|number|select|...",
                "label": "ラベル",
                "options": [...],  # select の場合
                "value": "デフォルト値"
            }
        }
        
    Returns:
        {field_name: value} の辞書
    """
    results = {}
    
    with st.form("mobile_form", clear_on_submit=False):
        for field_name, field_config in form_fields.items():
            field_type = field_config.get("type", "text")
            label = field_config.get("label", field_name)
            value = field_config.get("value", "")
            
            if field_type == "text":
                results[field_name] = st.text_input(
                    label,
                    value=value,
                    key=field_name
                )
            elif field_type == "number":
                results[field_name] = st.number_input(
                    label,
                    value=float(value) if value else 0.0,
                    key=field_name
                )
            elif field_type == "select":
                options = field_config.get("options", [])
                results[field_name] = st.selectbox(
                    label,
                    options,
                    key=field_name
                )
            elif field_type == "password":
                results[field_name] = st.text_input(
                    label,
                    type="password",
                    key=field_name
                )
            elif field_type == "checkbox":
                results[field_name] = st.checkbox(
                    label,
                    value=bool(value),
                    key=field_name
                )
        
        submitted = st.form_submit_button(
            "送信",
            use_container_width=True
        )
    
    return results if submitted else None


def render_touch_friendly_list(items: list, on_click=None) -> None:
    """タッチフレンドリーなリスト表示
    
    Args:
        items: {
            "title": "タイトル",
            "subtitle": "サブタイトル",
            "icon": "🎯",
            "id": "unique_id"
        } のリスト
        on_click: アイテムクリック時のコールバック
    """
    for item in items:
        st.markdown(f"""
        <div style="
            background: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.2s ease;
        " class="touch-item">
            <div style="font-size: 1.1rem; font-weight: 600; color: {COLORS['text']};">
                {item.get('icon', '')} {item.get('title', '')}
            </div>
            <div style="font-size: 0.85rem; color: {COLORS['text_secondary']}; margin-top: 4px;">
                {item.get('subtitle', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # クリック検出用の隠しボタン
        if st.button(
            f"Select {item.get('id')}",
            key=f"btn_{item.get('id')}",
            label_visibility="collapsed"
        ):
            if on_click:
                on_click(item)


def init_mobile_session() -> None:
    """モバイルセッション初期化"""
    if 'mobile_initialized' not in st.session_state:
        # デバイス検出スクリプトを挿入
        st.markdown("""
        <script>
        function detectDevice() {
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            // Streamlit にデバイス情報を送信
            window.streamlitDeviceType = isMobile ? 'mobile' : 'desktop';
        }
        detectDevice();
        </script>
        """, unsafe_allow_html=True)
        st.session_state.mobile_initialized = True


def inject_mobile_styles() -> None:
    """モバイル用 CSS を注入"""
    st.markdown("""
    <style>
    /* モバイル・タッチ最適化 */
    @media (max-width: 640px) {
        /* ボタンの最小サイズを 48px に（タッチ操作が容易） */
        button {
            min-height: 48px !important;
            min-width: 48px !important;
            font-size: 1rem !important;
        }
        
        /* 入力フィールド */
        input, textarea, select {
            min-height: 44px !important;
            font-size: 16px !important;  /* iOS での自動ズーム防止 */
        }
        
        /* パディング調整 */
        [data-testid="stMainBlockContainer"] {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* ナビゲーション */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        /* リンク・タップ対象 */
        a {
            min-height: 44px !important;
            display: inline-block;
            padding: 8px !important;
        }
    }
    
    /* iPhone Safe Area 対応 */
    @supports (padding: max(0px)) {
        body {
            padding-left: max(12px, env(safe-area-inset-left)) !important;
            padding-right: max(12px, env(safe-area-inset-right)) !important;
        }
    }
    
    /* ダークモード対応（自動） */
    @media (prefers-color-scheme: dark) {
        body { color-scheme: dark; }
    }
    </style>
    """, unsafe_allow_html=True)
