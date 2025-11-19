# services/auth_service.py
from __future__ import annotations
import streamlit as st
import os

try:
    import streamlit_authenticator as stauth
    ST_AUTH_AVAILABLE = True
except Exception:
    ST_AUTH_AVAILABLE = False

from utils.auth import (
    credentials_for_authenticator,
    register as auth_register,
    load_users,
    verify_login,
    migrate_plaintext_passwords,
)


class AuthManager:
    """Adapter that supports cookie auth (streamlit-authenticator) or a fallback session login."""
    def __init__(self):
        self.cookie_name = os.environ.get("COOKIE_NAME", "leetdash_auth")
        self.cookie_key = os.environ.get("COOKIE_KEY", "change-me")
        self.cookie_exp = int(os.environ.get("COOKIE_EXPIRY_DAYS", "14"))
        self.authenticator = None
        if ST_AUTH_AVAILABLE:
            self._build_authenticator()

    def _build_authenticator(self):
        self.authenticator = stauth.Authenticate(
            credentials=credentials_for_authenticator(),
            cookie_name=self.cookie_name,
            key=self.cookie_key,
            cookie_expiry_days=self.cookie_exp,
        )

    @staticmethod
    def login_compat(authenticator):
        try:
            res = authenticator.login(location="main")
            if isinstance(res, tuple) and len(res) == 3:
                return res
            return (None, None, None) if res is None else res
        except TypeError:
            return authenticator.login("Login", "main")

    @staticmethod
    def logout_compat(authenticator, where="sidebar"):
        try:
            authenticator.logout("🚪 Logout", location=where)
        except TypeError:
            authenticator.logout("🚪 Logout", where)

    def render_users_diagnostics(self):
        with st.expander("🧩 Users Diagnostics", expanded=False):
            db = load_users()
            usernames = sorted(db.get("users", {}).keys())
            st.write(f"Found **{len(usernames)}** user(s).")
            if usernames:
                st.write("Usernames:", ", ".join(usernames))
            if st.button("Migrate legacy plaintext passwords ➜ bcrypt"):
                migrated = migrate_plaintext_passwords()
                if migrated > 0:
                    st.success(f"Migrated {migrated} account(s) to bcrypt.")
                    if ST_AUTH_AVAILABLE:
                        self._build_authenticator()
                    st.rerun()
                else:
                    st.info("No legacy plaintext passwords detected.")

    def authenticate(self):
        """
        Returns: (user, is_authenticated: bool).
        Handles both modes (cookie vs fallback).
        """
        if ST_AUTH_AVAILABLE:
            name, status, username = self.login_compat(self.authenticator)
            if status is None:
                st.subheader("🔐 Login")
                self._render_register()
                st.info("Please log in to continue.")
                return None, False
            if status is False:
                st.error("Invalid username or password.")
                return None, False
            st.sidebar.success(f"Logged in as {username}")
            self.logout_compat(self.authenticator, where="sidebar")
            return username, True
        else:
            st.info("Running with basic session login (install `streamlit-authenticator` for persistent cookies).")
            if "user" not in st.session_state:
                st.session_state.user = None
            if st.session_state.user is None:
                st.subheader("🔐 Login")
                c1, c2 = st.columns(2)
                with c1:
                    u = st.text_input("Username")
                with c2:
                    p = st.text_input("Password", type="password")
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🚀 Login"):
                        if verify_login(u, p):
                            st.session_state.user = u
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")
                with b2:
                    if st.button("📝 Register"):
                        if not u or not p:
                            st.warning("Enter username & password.")
                        else:
                            ok = auth_register(u, p, name=u)
                            st.success("Registered. Click Login.") if ok else st.error("Username already exists.")
                return None, False
            else:
                st.sidebar.success(f"Logged in as {st.session_state.user}")
                if st.sidebar.button("🚪 Logout"):
                    st.session_state.user = None
                    st.rerun()
                return st.session_state.user, True

    def _render_register(self):
        with st.expander("📝 New here? Register", expanded=False):
            r1, r2 = st.columns(2)
            with r1:
                reg_user = st.text_input("Choose a username")
                reg_name = st.text_input("Your display name (optional)")
            with r2:
                reg_email = st.text_input("Email (optional)")
                reg_pw = st.text_input("Choose a password", type="password")
            if st.button("Create account", type="primary", key="register_btn_auth"):
                if not reg_user or not reg_pw:
                    st.warning("Please enter username and password.")
                else:
                    ok = auth_register(reg_user, reg_pw, name=reg_name, email=reg_email)
                    if ok and ST_AUTH_AVAILABLE:
                        self._build_authenticator()
                    st.success("Account created. Please log in.") if ok else st.error("Username already exists.")
