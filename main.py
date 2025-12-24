import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

st.set_page_config(page_title="나도수영의 환경분석", layout="wide")

# ----------------- 한글 폰트 -----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# ----------------- NFC / NFD 파일 인식 -----------------
def find_file(target_name):
    t_nfc = unicodedata.normalize("NFC", target_name)
    t_nfd = unicodedata.normalize("NFD", target_name)
    for p in DATA_DIR.iterdir():
        p_nfc = unicodedata.normalize("NFC", p.name)
        p_nfd = unicodedata.normalize("NFD", p.name)
        if p_nfc == t_nfc or p_nfd == t_nfd:
            return p
    return None

# ----------------- 데이터 로딩 ------------

