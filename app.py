import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="리더십 영향력 진단", layout="wide")

# 2. 데이터 로드 함수 (부족하면 채워넣는 기능 추가)
@st.cache_data
def load_data():
    file_name = "data.xlsx"
    df = pd.DataFrame()
    
    # [읽기] 엑셀 파일 읽기 (헤더 없이 통째로 읽어봅니다)
    try:
        df = pd.read_excel(file_name, engine='openpyxl', header=None)
    except:
        try:
            df = pd.read_csv(file_name, header=None, encoding='utf-8-sig')
        except:
            return pd.DataFrame()

    if not df.empty:
        # 가장 글자가 많은 컬럼을 질문 컬럼으로 추측해서 선택
        # (엑셀에 잡다한 숫자가 있어도 긴 문장을 질문으로 인식함)
        target_col = None
        max_len = 0
        for col in df.columns:
            # 문자열로 변환해서 길이 측정
            avg_len = df[col].astype(str).str.len().mean()
            if avg_len > max_len:
                max_len = avg_len
                target_col = col
        
        if target_col is not None:
            df = df[[target_col]] # 그 컬럼만 남김
        else:
            df = df.iloc[:, [0]] # 못 찾으면 무조건 첫 번째 컬럼

        df.columns = ["question"]
        
        # 빈 값 제거하지 않음! (부족하면 채울 것이므로)
        # 대신, 너무 짧은(1글자 이하) 노이즈만 제거
        df = df[df["question"].astype(str).str.len() > 1]
        df = df.reset_index(drop=True)
        
        # [핵심] 44개보다 모자라면? -> "빈 질문"으로 채워서 에러 방지
        current_len = len(df)
        if current_len < 44:
            needed = 44 - current_len
            dummy_data = pd.DataFrame({"question": [f"(데이터 부족으로 생성된 빈 질문 {i+1})"] * needed})
            df = pd.concat([df, dummy_data], ignore_index=True)
        
        # 44개만 딱 자르기
        df = df.head(44)
        return df
    else:
        # 파일이 아예 없으면 전부 가짜 데이터로 채움
        return pd.DataFrame({"question": [f"질문 파일을 읽지 못해 생성된 임시 문항 {i+1}"] * 44})

df_questions = load_data()

# 3. 로직 구조
structure = {
    "합리적 파워": ["합리적 설득", "이해관계 설명", "교환"],
    "친화적 파워": ["영감에 대한 호소", "협의", "호의 얻기", "개인적 호소", "협력"],
    "강압적 파워": ["합법화", "압력", "연합"]
}

# 4. 앱 화면 구성
st.title("📊 리더십 영향력 스타일 진단")

# --- 데이터 확인용 박스 ---
with st.expander("🔍 내 엑셀 파일이 어떻게 읽혔는지 확인하기 (클릭)", expanded=True):
    st.write("아래 표에 질문이 보여야 합니다. 이상한 글씨(제목 등)가 섞여 있어도 슬라이더는 작동합니다.")
    st.dataframe(df_questions, height=200)
# -----------------------

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
    if len(df_questions) == 44: # 위에서 강제로 44개를 맞췄으므로 무조건 실행됨
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
