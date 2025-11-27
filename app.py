import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="리더십 영향력 진단", layout="wide")

# 2. 데이터 로드 함수 (스마트 필터링 기능 추가)
@st.cache_data
def load_data():
    file_name = "data.xlsx"
    df = pd.DataFrame()
    
    # [1단계] 파일 읽기 (엑셀, CSV, 한글 등 모든 경우의 수 시도)
    try:
        df = pd.read_excel(file_name, engine='openpyxl', header=None)
    except:
        try:
            df = pd.read_csv(file_name, header=None, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(file_name, header=None, encoding='cp949')
            except:
                return pd.DataFrame()

    if not df.empty:
        # [2단계] 가장 '질문스러운' 긴 글자가 있는 컬럼 찾기
        target_col = None
        max_len = 0
        for col in df.columns:
            # 모든 값을 문자로 바꾸고 평균 길이를 잽니다.
            avg_len = df[col].astype(str).str.len().mean()
            if avg_len > max_len:
                max_len = avg_len
                target_col = col
        
        # 질문 컬럼 선택
        if target_col is not None:
            df = df[[target_col]]
        else:
            df = df.iloc[:, [0]] 

        df.columns = ["question"]
        
        # -----------------------------------------------------------
        # [핵심 수정] 껍데기(제목, 빈칸) 제거하는 필터
        # 1. 내용이 없는(NaN) 줄 제거
        df = df.dropna()
        # 2. "질문", "문항", "번호" 같은 제목 줄 제거 (글자 수가 5자 미만인 것은 질문이 아니라고 판단)
        df = df[df["question"].astype(str).str.len() > 5]
        # -----------------------------------------------------------

        # 번호표 다시 매기기 (0번부터 깔끔하게)
        df = df.reset_index(drop=True)
        
        # 만약 44개보다 모자라면 채우기 (에러 방지용)
        if len(df) < 44:
            needed = 44 - len(df)
            dummy = pd.DataFrame({"question": [f"(누락된 문항 {i+1})"] * needed})
            df = pd.concat([df, dummy], ignore_index=True)
        
        # 정확히 44개만 자르기
        df = df.head(44)
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

# --- 데이터 확인용 (이제 '질문'이나 'None'이 없어야 합니다) ---
if not df_questions.empty:
    with st.expander(f"✅ 데이터 로드 성공 (총 {len(df_questions)}문항)", expanded=True):
        st.write("아래 1번 문항이 'None'이나 '질문'이 아니라, **진짜 첫 번째 질문**이어야 합니다.")
        st.dataframe(df_questions.head(3)) # 맨 위 3개만 보여줍니다
# -------------------------------------------------------

if len(df_questions) < 44:
    st.error("❌ 유효한 질문을 찾지 못했습니다.")
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
