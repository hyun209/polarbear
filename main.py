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

# ----------------- 데이터 로딩 -----------------
@st.cache_data
def load_env_data():
    env = {}
    for p in DATA_DIR.iterdir():
        if p.suffix.lower() == ".csv":
            name = p.stem.replace("_환경데이터", "")
            env[name] = pd.read_csv(p)
    return env if env else None

@st.cache_data
def load_growth_data():
    xlsx = None
    for p in DATA_DIR.iterdir():
        if p.suffix.lower() == ".xlsx":
            xlsx = p
            break
    if xlsx is None:
        return None
    return pd.read_excel(xlsx, sheet_name=None)

with st.spinner("데이터 불러오는 중..."):
    env_data = load_env_data()
    growth_data = load_growth_data()

if env_data is None or growth_data is None:
    st.error("❌ data 폴더에 CSV 또는 XLSX 파일이 없습니다.")
    st.stop()

EC_MAP = {"송도고":2.0, "하늘고":4.0, "아라고":8.0, "동산고":1.0}

st.title("🌿 나도수영의 환경분석")

school = st.sidebar.selectbox("학교 선택", ["전체"] + list(env_data.keys()))

tab1, tab2, tab3 = st.tabs([
    "📈 생중량-환경 상관관계",
    "🌡️ 온도와 생중량",
    "⭐ 나도수영 최적 생장 조건"
])

# ================== Tab1 ==================
with tab1:
    rows = []
    for s in env_data:
        e = env_data[s]
        g = growth_data[s]
        rows.append({
            "학교":s,
            "온도":e["temperature"].mean(),
            "습도":e["humidity"].mean(),
            "pH":e["ph"].mean(),
            "EC":e["ec"].mean(),
            "생중량":g["생중량(g)"].mean()
        })
    df = pd.DataFrame(rows)

    fig = make_subplots(rows=2, cols=2,
        subplot_titles=["온도-생중량","습도-생중량","pH-생중량","EC-생중량"])

    vars = ["온도","습도","pH","EC"]
    for i,v in enumerate(vars):
        r,c = divmod(i,2)
        fig.add_trace(go.Scatter(x=df[v], y=df["생중량"], mode="markers+text", text=df["학교"]),
                      row=r+1, col=c+1)

    fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

# ================== Tab2 ==================
with tab2:
    if school != "전체":
        e = env_data[school]
        g = growth_data[school]
        fig = px.scatter(x=[e["temperature"].mean()]*len(g),
                         y=g["생중량(g)"],
                         labels={"x":"평균 온도","y":"생중량(g)"},
                         title=f"{school} 평균 온도와 생중량 관계")
        fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
        st.plotly_chart(fig, use_container_width=True)

# ================== Tab3 ==================
with tab3:
    avg_weight = {s:df["생중량(g)"].mean() for s,df in growth_data.items()}
    best = max(avg_weight, key=avg_weight.get)

    for s,v in avg_weight.items():
        st.metric(s, f"{v:.2f} g", "⭐ 최적" if s==best else "")

    st.write(f"➡ 현재 데이터 기준 **나도수영 최적 생장 EC는 {EC_MAP[best]} ({best})** 로 분석됩니다.")

    with st.expander("생육 데이터 XLSX 다운로드"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for s,df in growth_data.items():
                df.to_excel(writer, sheet_name=s, index=False)
        buffer.seek(0)
        st.download_button("다운로드", buffer, "나도수영_생육결과.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


