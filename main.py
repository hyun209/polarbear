import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io
import re

st.set_page_config(page_title="나도수영의 환경분석", layout="wide")

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

def clean(x):
    return re.sub(r"[^가-힣]", "", unicodedata.normalize("NFC", str(x))).strip()

@st.cache_data
def load_env():
    env={}
    for p in DATA_DIR.iterdir():
        if p.suffix.lower()==".csv":
            env[clean(p.stem)] = pd.read_csv(p)
    return env if env else None

@st.cache_data
def load_growth():
    xlsx=None
    for p in DATA_DIR.iterdir():
        if p.suffix.lower()==".xlsx":
            xlsx=p; break
    if xlsx is None: return None
    sheets=pd.read_excel(xlsx, sheet_name=None)
    return {clean(k):v for k,v in sheets.items()}

with st.spinner("데이터 로딩중..."):
    env=load_env()
    growth=load_growth()

if env is None or growth is None:
    st.error("❌ data 폴더에 CSV 또는 XLSX 파일이 없습니다.")
    st.stop()

# ---------- 매칭 검증 ----------
matched = set(env) & set(growth)
if not matched:
    st.error("❌ CSV 학교명과 XLSX 시트명이 하나도 매칭되지 않았습니다.")
    st.write("CSV:", list(env.keys()))
    st.write("XLSX:", list(growth.keys()))
    st.stop()

EC_MAP={"송도고":2.0,"하늘고":4.0,"아라고":8.0,"동산고":1.0}

st.title("🌿 나도수영의 환경분석")
school=st.sidebar.selectbox("학교 선택",["전체"]+sorted(matched))

tab1,tab2,tab3=st.tabs(["📈 생중량-환경 상관관계","🌡️ 온도-생중량","⭐ 최적 생장 조건"])

with tab1:
    rows=[]
    for s in matched:
        e=env[s]; g=growth[s]
        rows.append({
            "학교":s,
            "온도":e["temperature"].mean(),
            "습도":e["humidity"].mean(),
            "pH":e["ph"].mean(),
            "EC":e["ec"].mean(),
            "생중량":g["생중량(g)"].mean()
        })
    df=pd.DataFrame(rows)

    fig=make_subplots(rows=2,cols=2,
        subplot_titles=["온도-생중량","습도-생중량","pH-생중량","EC-생중량"])
    vars=["온도","습도","pH","EC"]
    for i,v in enumerate(vars):
        r,c=divmod(i,2)
        fig.add_trace(go.Scatter(x=df[v],y=df["생중량"],
                                 mode="markers+text",text=df["학교"]),
                      row=r+1,col=c+1)

    fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
    st.plotly_chart(fig,use_container_width=True)
