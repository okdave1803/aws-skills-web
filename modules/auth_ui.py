"""AWS Skills - 認証 UI コンポーネント

ログイン画面、登録画面などの UI を提供する。
"""

import streamlit as st

from modules.auth import auth_manager
from modules.theme import COLORS
from modules.security import sanitize_html


def render_login_form() -> None:
    """ログイン画面を表示する。"""
    st.markdown(
        f"""
        <div style="max-width:400px; margin:40px auto;">
            <div style="background:{COLORS['card']}; border-radius:12px; padding:30px; 
                        border:1px solid {COLORS['border']};">
                <h2 style="text-align:center; color:{COLORS['primary']}; margin-bottom:30px;">
                    🔐 ログイン
                </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # タブセレクション
        tab1, tab2 = st.tabs(["ログイン", "新規登録"])
        
        with tab1:
            st.markdown("#### ログイン")
            
            username = st.text_input(
                "ユーザー名",
                key="login_username",
                help="2〜32文字の英数字、アンダースコア、ハイフンのみ"
            )
            
            password = st.text_input(
                "パスワード",
                type="password",
                key="login_password",
            )
            
            if st.button("🔓 ログイン", use_container_width=True):
                if not username or not password:
                    st.error("ユーザー名とパスワードを入力してください")
                else:
                    success, message = auth_manager.login(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        with tab2:
            st.markdown("#### 新規登録")
            
            new_username = st.text_input(
                "ユーザー名",
                key="register_username",
                help="2〜32文字の英数字、アンダースコア、ハイフンのみ"
            )
            
            new_email = st.text_input(
                "メールアドレス（オプション）",
                key="register_email",
                help="メールアドレスは必須ではありません"
            )
            
            new_password = st.text_input(
                "パスワード",
                type="password",
                key="register_password",
                help="8文字以上で、大文字・小文字・数字を含める必要があります"
            )
            
            new_password_confirm = st.text_input(
                "パスワード（確認）",
                type="password",
                key="register_password_confirm",
            )
            
            if st.button("📝 登録", use_container_width=True):
                if not new_username or not new_password:
                    st.error("ユーザー名とパスワードは必須です")
                elif new_password != new_password_confirm:
                    st.error("パスワードが一致しません")
                else:
                    success, message = auth_manager.register_user(
                        new_username,
                        new_password,
                        new_email if new_email else None
                    )
                    if success:
                        st.success(message)
                        st.info("ログイン画面に切り替わります。ユーザー名とパスワードでログインしてください。")
                    else:
                        st.error(message)


def render_user_menu() -> None:
    """認証済みユーザーのメニュー。"""
    user = auth_manager.get_current_user()
    
    if user:
        with st.sidebar:
            st.markdown("---")
            
            st.markdown(
                f"""
                <div style="background:{COLORS['card_alt']}; border-radius:8px; padding:12px; 
                            border:1px solid {COLORS['border_soft']};">
                    <div style="color:{COLORS['text']}; font-weight:700; font-size:0.9rem;">
                        👤 {sanitize_html(user.get('username', 'ユーザー'))}
                    </div>
                    <div style="color:{COLORS['text_secondary']}; font-size:0.75rem; margin-top:4px;">
                        Level {user.get('level', 1)} • {user.get('total_xp', 0)} XP
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⚙️ 設定", use_container_width=True):
                    # Phase 2 で実装
                    st.info("設定画面は準備中です")
            
            with col2:
                if st.button("🚪 ログアウト", use_container_width=True):
                    auth_manager.logout()
                    st.success("ログアウトしました")
                    st.rerun()


def render_auth_status() -> None:
    """認証ステータスを表示する。"""
    if auth_manager.is_authenticated():
        user = auth_manager.get_current_user()
        st.success(f"✅ ログイン済み: {user.get('username', 'ユーザー')}")
    else:
        st.warning("⚠️ ログインしてください")


def require_authentication(page_name: str = "このページ") -> bool:
    """認証が必要なページを保護する。
    
    未認証ユーザーがアクセスした場合、ログイン画面を表示してから False を返す。
    
    Args:
        page_name: ページ名（エラーメッセージで使用）
        
    Returns:
        認証済みなら True、未認証なら False
    """
    if not auth_manager.is_authenticated():
        st.warning(f"🔐 {page_name}にアクセスするにはログインが必要です")
        st.divider()
        render_login_form()
        return False
    
    return True
