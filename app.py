import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="리더십 영향력 진단", layout="wide")

# 2. 데이터 로드 함수
@st.cache_data
def load_data():
    file_name = "data.xlsx"
    df = pd.DataFrame()
    
    # [읽기] 엑셀, CSV 등 가능한 모든 방법 시도
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
        # 가장 긴 글자가 있는 컬럼을 질문으로 선택
        target_col = None
        max_len = 0
        for col in df.columns:
            avg_len = df[col].astype(str).str.len().mean()
            if avg_len > max_len:
                max_len = avg_len
                target_col = col
        
        if target_col is not None:
            df = df[[target_col]]
        else:
            df = df.iloc[:, [0]] 

        df.columns = ["question"]
        
        # [필터] 껍데기 제거 (글자 수 5자 미만인 'None', '질문' 등 삭제)
        df = df[df["question"].astype(str).str.len() > 5]

        # [수정됨] 번호표를 1번부터 시작하게 변경
        df = df.reset_index(drop=True)
        df.index = df.index + 1 # 0,1,2... -> 1,2,3... 으로 변경
        
        # 44개 부족하면 채우기
        if len(df) < 44:
            needed = 44 - len(df)
            dummy = pd.DataFrame({"question": [f"(부족한 문항 채움 {i+1})"] * needed})
            dummy.index = range(len(df)+1, 45) # 인덱스 이어붙이기
            df = pd.concat([df, dummy])
        
        # 44개만 자르기
        df = df.iloc[:44]
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

# --- [수정됨] 데이터 전체 확인 (스크롤 가능!) ---
if not df_questions.empty:
    with st.expander(f"✅ 문항 리스트 확인 (총 {len(df_questions)}개 - 클릭해서 펼쳐보세요)", expanded=True):
        st.write("이제 번호가 1번부터 시작하며, 스크롤을 내려서 44번까지 확인할 수 있습니다.")
        # height=400을 주어서 스크롤이 생기게 함
        st.dataframe(df_questions, height=400, use_container_width=True)
# ---------------------------------------------

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
                    # 질문 텍스트 출력 (인덱스가 1부터 시작하므로 i 그대로 사용)
                    scores[i] = st.slider(f"{i}. {row['question']}", 1, 5, 3, key=i)
        
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
            st.plotly_chart(fig2, use_container_width=
