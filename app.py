import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="서울시 미세먼지 대시보드", page_icon="😷", layout="wide")
st.title("😷 서울시 구별 (초)미세먼지 시각화 대시보드")

# 2. 데이터 로드 및 전처리 함수 (UI 요소 분리)
@st.cache_data
def load_data():
    file_name = "dustdata.csv"
    
    # [진단 1] 파일 존재 여부 확인
    if not os.path.exists(file_name):
        return {"status": "error", "message": f"❌ 오류: 깃허브 저장소에서 `{file_name}` 파일을 찾을 수 없습니다. 파일명이 정확한지, 확장자(.csv)가 맞는지 확인해주세요."}
        
    # [진단 2] 파일 크기 확인
    if os.path.getsize(file_name) == 0:
        return {"status": "error", "message": f"❌ 오류: 깃허브에 올라간 `{file_name}` 파일의 크기가 0 바이트(공백)입니다. 업로드 중 오류가 났을 수 있으니 다시 확인해주세요."}

    # [진단 3] 한글 인코딩 시도
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
    df = None
    
    for enc in encodings:
        try:
            df = pd.read_csv(file_name, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            return {"status": "error", "message": f"❌ 오류: `{file_name}` 파일이 비어있거나 파이썬이 읽을 수 없는 형식입니다."}
        except Exception as e:
            return {"status": "error", "message": f"❌ 파일 읽기 중 오류 발생: {e}"}
            
    if df is None:
        return {"status": "error", "message": f"❌ 오류: `{file_name}` 파일의 한글 형식을 분석할 수 없습니다. (UTF-8 또는 CP949 형식이어야 합니다.)"}
        
    # [진단 4] 필수 컬럼 확인
    required_cols = ['일시', '구분', '미세먼지(PM10)', '초미세먼지(PM25)']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return {"status": "error", "message": f"❌ 오류: CSV 파일 안에 필수 항목이 없습니다. (누락된 항목: {missing_cols}) \n현재 파일의 항목들: {list(df.columns)}"}

    try:
        # 날짜 데이터 변환 및 결측치 제거
        df['일시'] = pd.to_datetime(df['일시'])
        df = df.dropna(subset=['미세먼지(PM10)', '초미세먼지(PM25)'])
        return {"status": "success", "data": df}
    except Exception as e:
        return {"status": "error", "message": f"❌ 오류: 데이터 날짜/숫자 변환 중 문제가 발생했습니다: {e}"}

# 데이터 로드 실행 및 진단 결과 처리
result = load_data()

if result["status"] == "error":
    st.error(result["message"])
else:
    df = result["data"]

    # 3. 사이드바 설정 (검색 및 필터링 기능)
    st.sidebar.header("🔍 검색 조건 설정")

    # 자치구 다중 선택 기능
    gu_list = sorted(df['구분'].unique().tolist())
    default_gu = ['평균', '강남구'] if '평균' in gu_list else [gu_list[0]]
    selected_gu = st.sidebar.multiselect("확인할 자치구를 선택하세요:", gu_list, default=default_gu)

    # 조회할 날짜 범위 선택 기능
    min_date = df['일시'].min().date()
    max_date = df['일시'].max().date()

    selected_date = st.sidebar.date_input(
        "조회할 기간을 선택하세요:",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # 4. 데이터 필터링 및 시각화 (날짜 선택 예외 처리 강화)
    if isinstance(selected_date, (list, tuple)) and len(selected_date) == 2:
        start_date, end_date = selected_date
        
        filtered_df = df[
            (df['구분'].isin(selected_gu)) &
            (df['일시'].dt.date >= start_date) &
            (df['일시'].dt.date <= end_date)
        ]
        
        if filtered_df.empty:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        else:
            # 미세먼지(PM10) 그래프
            st.subheader("📊 미세먼지 (PM10) 시간별 추이")
            fig_pm10 = px.line(filtered_df, x='일시', y='미세먼지(PM10)', color='구분', 
                               markers=True, template="plotly_white")
            st.plotly_chart(fig_pm10, use_container_width=True)

            # 초미세먼지(PM25) 그래프
            st.subheader("📉 초미세먼지 (PM25) 시간별 추이")
            fig_pm25 = px.line(filtered_df, x='일시', y='초미세먼지(PM25)', color='구분', 
                               markers=True, template="plotly_white")
            st.plotly_chart(fig_pm25, use_container_width=True)
            
            # 원본 데이터 확인 탭
            with st.expander("원본 데이터 테이블 보기"):
                st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
    else:
        st.info("👆 사이드바 달력에서 **시작일과 종료일(두 날짜)**을 모두 클릭해 주세요.")
