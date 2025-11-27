import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="리더십 영향력 진단", layout="wide")

# 2. 데이터 로드 함수 (디버깅 모드)
@st.cache_data
def load_data():
    file_name = "data.xlsx"
    df = pd.DataFrame()
    
    # [1단계] 엑셀로 시도
    try:
        df = pd.read_excel(file_name, engine='openpyxl')
    except:
        # [2단계] CSV (UTF-8 with BOM - 엑셀 저장 기본값)
        try:
            df = pd.read_csv(file_name, encoding='utf-8-sig')
        except:
            # [3단계] CSV (한글 EUC-KR - 구버전 엑셀)
            try:
                df = pd.read_csv(file_name, encoding='euc-kr')
            except:
                # [4단계] CSV (CP949 - 확장 한글)
                try:
                    df = pd.read_csv(file_name, encoding='cp949')
                except Exception as e:
                    return pd.DataFrame()

    if not df.empty:
        # 데이터 정리
        df = df.reset_index(drop=True)
        df = df.head(44)
        # 첫 번째 컬럼을 강제로 질문 컬럼으로 지정
        df.columns.values[0] = "question"
        return df
    else:
        return pd.DataFrame()

df_questions = load_data()

# 3. 앱 화면 구성
st.title("📊 리더십 영향력 스타일 진단")

# --- [진단용] 데이터가 어떻게 읽혔는지 화면에 보여줍니다 (문제 해결 후 지우면 됨) ---
if not df_questions.empty:
    with st.expander("🔍 데이터 확인하기 (문제가 보이면 여기를 클릭하세요)", expanded=True):
        st.write("컴퓨터가 읽은 데이터의 앞부분입니다. 'question' 열에 한글이 잘 보이나요?")
        st.dataframe(df_questions.head())
# -------------------------------------------------------------------------

if df_questions.empty:
    st.error("❌ 데이터를 읽을 수 없습니다. 깃허브의 파일 이름이 'data.xlsx'인지 확인해주세요.")
else:
    with st.sidebar:
        st.header("진단자 정보")
        name = st.text_input("이름", "Guest")
    
    with st.form("my_form"):
        # 로직 구조
        structure = {
            "합리적 파워": ["합리적 설득", "이해관계 설명", "교환"],
            "친화적 파워": ["영감에 대한 호소", "협의", "호의 얻기", "개인적 호소", "협력"],
            "강압적 파워": ["합법화", "압력", "연합"]
        }
        
        # 매핑
        sub_categories = []
        for main, subs in structure.items():
            for sub in subs:
                sub_categories.append((main, sub))
        
        mappings = []
        for main, sub in sub_categories:
            mappings.extend([(main, sub)] * 4)
            
        if len(df_questions) == len(mappings):
            df_questions['main_cat'] = [m[0] for m in mappings]
            df_questions['sub_cat'] = [m[1] for m in mappings]

        scores = {}
        tabs = st.tabs(["1. 합리적 파워", "2. 친화적 파워", "3. 강압적 파워"])
        
        category_groups = df_questions.groupby('main_cat', sort=False)
        
        for idx, (main_cat, group) in enumerate(category_groups):
            with tabs[idx]:
                st.subheader(main_cat)
                for i, row in group.iterrows():
                    # 질문 텍스트가 비어있으면 대체 텍스트 표시
                    q_text = row['question']
                    if pd.isna(q_text) or str(q_text).strip() == "":
                        q_text = "(질문 내용을 불러오지 못했습니다. 위 '데이터 확인하기'를 봐주세요)"
                    
                    scores[i] = st.slider(f"{i+1}. {q_text}", 1, 5, 3, key=i)
        
        submitted = st.form_submit_button("결과 확인")

    if submitted:
        df_questions['score'] = pd.Series(scores)
        sub_result = df_questions.groupby('sub_cat', sort=False)['score'].mean().reset_index()
        main_result = df_questions.groupby('main_cat', sort=False)['score'].mean().reset_index()

        st.divider()
        st.header(f"📢 {name}님의 결과")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("세부 전술 프로파일")
            fig = px.line_polar(sub_result, r='score', theta='sub_cat', line_close=True, range_r=[0, 5])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("3대 파워 요약")
            fig2 = px.bar(main_result, x='main_cat', y='score', color='main_cat', range_y=[0, 5])
            st.plotly_chart(fig2, use_container_width=True)
