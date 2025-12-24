import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import io

st.set_page_config(page_title="극지식물 최적 EC 농도 연구", layout="wide")

# 한글 폰트 CSS
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

# ----------------- 파일 탐색 (NFC/NFD 완전 대응) -----------------
def find_file(target_name):
    target_nfc = unicodedata.normalize("NFC", target_name)
    target_nfd = unicodedata.normalize("NFD", target_name)

    for p in DATA_DIR.iterdir():
        name_nfc = unicodedata.normalize("NFC", p.name)
        name_nfd = unicodedata.normalize("NFD", p.name)
        if name_nfc == target_nfc or name_nfd == target_nfd:
            return p
    return None

# ----------------- 데이터 로딩 -----------------
@st.cache_data
def load_env_data():
    env_files = []
    for p in DATA_DIR.iterdir():
        if p.suffix.lower() == ".csv":
            env_files.append(p)

    if not env_files:
        return None

    data = {}
    for f in env_files:
        school = f.stem.replace("_환경데이터", "")
        data[school] = pd.read_csv(f)
    return data


@st.cache_data
def load_growth_data():
    xlsx = None
    for p in DATA_DIR.iterdir():
        if p.suffix.lower() == ".xlsx":
            xlsx = p
            break

    if xlsx is None:
        return None

    sheets = pd.read_excel(xlsx, sheet_name=None)
    return sheets


with st.spinner("데이터 로딩 중..."):
    env_data = load_env_data()
    growth_data = load_growth_data()

if env_data is None or growth_data is None:
    st.error("❌ data 폴더에 CSV 또는 XLSX 파일이 없습니다.")
    st.stop()

EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0
}

st.title("🌱 극지식물 최적 EC 농도 연구")

school_list = ["전체"] + list(env_data.keys())
selected_school = st.sidebar.selectbox("학교 선택", school_list)

# ----------------- Tab -----------------
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ================= Tab1 =================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.write("극지식물의 생육에 최적인 EC 농도를 도출하기 위한 다학교 비교 실험")

    summary = []
    for s, df in growth_data.items():
        summary.append([s, EC_MAP.get(s, "-"), len(df)])

    summary_df = pd.DataFrame(summary, columns=["학교", "EC 목표", "개체수"])
    st.table(summary_df)

    total_cnt = sum(summary_df["개체수"])
    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    growth_avg = {
        s: df["생중량(g)"].mean() for s, df in growth_data.items()
    }
    best_school = max(growth_avg, key=growth_avg.get)
    best_ec = EC_MAP.get(best_school)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", f"{total_cnt}개")
    c2.metric("평균 온도", f"{avg_temp:.2f}℃")
    c3.metric("평균 습도", f"{avg_hum:.2f}%")
    c4.metric("최적 EC", f"{best_ec} ({best_school})")

# ================= Tab2 =================
with tab2:
    avg_df = []
    for s, df in env_data.items():
        avg_df.append([
            s,
            df["temperature"].mean(),
            df["humidity"].mean(),
            df["ph"].mean(),
            df["ec"].mean()
        ])
    avg_df = pd.DataFrame(avg_df, columns=["학교", "온도", "습도", "pH", "EC"])

    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"])

    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["온도"]), row=1, col=1)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["습도"]), row=1, col=2)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["pH"]), row=2, col=1)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["EC"], name="실측 EC"), row=2, col=2)
    fig.add_trace(go.Bar(x=list(EC_MAP.keys()), y=list(EC_MAP.values()), name="목표 EC"), row=2, col=2)

    fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        df = env_data[selected_school]
        fig2 = px.line(df, x="time", y=["temperature", "humidity", "ec"])
        fig2.add_hline(y=EC_MAP[selected_school], line_dash="dash")
        fig2.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
        st.plotly_chart(fig2, use_container_width=True)

        with st.expander("환경 데이터 원본"):
            st.dataframe(df)
            buffer = io.BytesIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button("CSV 다운로드", buffer, f"{selected_school}_환경데이터.csv", "text/csv")

# ================= Tab3 =================
with tab3:
    avg_weight = {s: df["생중량(g)"].mean() for s, df in growth_data.items()}
    best = max(avg_weight, key=avg_weight.get)

    cols = st.columns(len(avg_weight))
    for i, (s, v) in enumerate(avg_weight.items()):
        cols[i].metric(s, f"{v:.2f} g", "⭐ 최적" if s == best else "")

    fig3 = px.bar(x=list(avg_weight.keys()), y=list(avg_weight.values()), title="EC별 평균 생중량")
    fig3.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("생육 데이터 원본 다운로드"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for s, df in growth_data.items():
                df.to_excel(writer, sheet_name=s, index=False)
        buffer.seek(0)
        st.download_button("XLSX 다운로드", buffer, "생육결과.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
