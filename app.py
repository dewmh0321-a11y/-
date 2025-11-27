import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="리더십 영향력 진단", layout="wide")

# 2. 데이터 로드 함수 (빈 줄 제거 + 44개 추출 강화)
@st.cache_data
def load_data():
    file_name = "data.xlsx"
    df = pd.DataFrame()
    
    # [읽기 시도 1] 엑셀
    try:
        df = pd.read_excel(file_name, engine='openpyxl')
    except:
        # [읽기 시도 2] CSV (다양한 인코딩)
        try:
            df = pd.read_csv(file_name, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(file_name, encoding='cp949')
            except:
                return pd.DataFrame()

    if not df.empty:
        # [데이터 청소] 빈 칸이 있는 행은 날려버립니다.
        df = df.dropna()
        # 번호표(인덱스)를 0부터 다시 매깁니다.
        df = df.reset_index(drop=True)
        
        # [핵심] 정확히 44개만 자릅니다. (더 많아도, 적어도 문제 안 생기게)
        df = df.iloc[:44]
        
        # 첫 번째 컬럼을 질문으로 설정
        df.columns.values[0] = "question"
        return df
    else:
        return pd.DataFrame()

df_questions = load_data()

# 3. 로직 구조
structure = {
    "합리적 파워": ["합리적 설득", "이해관계 설명", "교환"],
    "친화적 파워": ["영감에 대한 호소", "협의", "호의 얻기", "개인적 호소", "협력"],
    "강압적 파워": ["합법화", "압력", "연합"]
}

# 4. 앱 화면 구성
st.title("📊 리더십 영향력 스타일 진단")

# --- [수정됨] 데이터 전체 확인하기 (이제 44개가 다 보입니다) ---
if not df_questions.empty:
    with st.expander(f"🔍 데이터 확인하기 (총 {len(df_questions)}개 문항 로드됨)", expanded=True):
        st.write("스크롤을 내리면 44개 문항이 다 보여야 정상입니다.")
        # .head()를 지워서 전체 데이터를 보여줍니다.
        st.dataframe(df_questions, height=300) 
# -----------------------------------------------------------

if len(df_questions) < 44:
    st.error(f"❌ 데이터가 부족합니다! (현재 {len(df_questions)}개)")
    st.info("엑셀 파일 안에 빈 줄이 있거나, 문항 수가 44개보다 적은지 확인해주세요.")
else:
    with st.sidebar:
        st.header("진단자 정보")
        name = st.text_input("이름", "Guest")
    
    with st.form("my_form"):
        # 매핑
        sub_categories = []
        for main, subs in structure.items():
            for sub in subs:
                sub_categories.append((main, sub))
        
        mappings = []
        for main, sub in sub_categories:
            mappings.extend([(main, sub)] * 4)
            
        # 데이터프레임에 카테고리 입히기
        df_questions['main_cat'] = [m[0] for m in mappings]
        df_questions['sub_cat'] = [m[1] for m in mappings]

        scores = {}
        tabs = st.tabs(["1. 합리적 파워", "2. 친화적 파워", "3. 강압적 파워"])
        
        category_groups = df_questions.groupby('main_cat', sort=False)
        
        for idx, (main_cat, group) in enumerate(category_groups):
            with tabs[idx]:
                st.subheader(main_cat)
                for i, row in group.iterrows():
                    # 질문 텍스트 출력
                    scores[i] = st.slider(f"{i+1}. {row['question']}", 1, 5, 3, key=i)
        
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
