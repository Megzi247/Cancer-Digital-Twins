import os
import threading
from clickhouse_driver import Client
from dotenv import load_dotenv

load_dotenv()

_local = threading.local()


def _secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, fall back to env vars."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


def get_client() -> Client:
    if not hasattr(_local, "client"):
        _local.client = Client(
            host=_secret("CLICKHOUSE_HOST", "localhost"),
            port=int(_secret("CLICKHOUSE_PORT", "9000")),
            user=_secret("CLICKHOUSE_USER", "default"),
            password=_secret("CLICKHOUSE_PASSWORD", ""),
            database=_secret("CLICKHOUSE_DATABASE", "cancer_digital_twins"),
            settings={"use_numpy": False},
        )
    return _local.client
