import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 페이지 기본 설정
st.set_page_config(page_title="서울시 공영주차장 안내", page_icon="🚗", layout="wide")

st.title("🚗 서울시 공영주차장 안내 및 최저가 검색 앱")
st.markdown("주소를 기반으로 한 지도 시각화, 요금 정보, 그리고 선택한 자치구 내 가장 저렴한 주차장을 찾아줍니다.")

# 1. 파일 업로드 기능
uploaded_file = st.file_uploader("주차장 데이터 CSV 파일을 업로드해주세요", type=['csv'])

if uploaded_file:
    # 2. 데이터 로드 및 전처리
    @st.cache_data
    def load_data(file):
        # 1. 파일 인코딩 오류 방지를 위한 예외 처리 추가
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0) # 파일을 다시 처음부터 읽기 위해 포인터 초기화
            df = pd.read_csv(file, encoding='cp949') # 한국어 윈도우/엑셀 기본 인코딩으로 재시도
            
        # '주소' 컬럼의 첫 번째 단어를 '자치구'로 추출 (예: '강북구 미아동...' -> '강북구')
        df['자치구'] = df['주소'].apply(lambda x: str(x).split()[0] if pd.notnull(x) else "알수없음")
        
        # 위도, 경도 숫자형으로 변환 (오류 발생 시 NaN 처리 후 제거)
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        # 정확한 요금 비교를 위한 '1분당 요금' 계산 로직 추가
        def calc_per_min(row):
            try:
                fee = float(row['기본 주차 요금'])
                time = float(row['기본 주차 시간(분 단위)'])
                return fee / time if time > 0 else float('inf')
            except:
                return float('inf')
                
        df['분당요금'] = df.apply(calc_per_min, axis=1)
        return df
        # '주소' 컬럼의 첫 번째 단어를 '자치구'로 추출 (예: '강북구 미아동...' -> '강북구')
        df['자치구'] = df['주소'].apply(lambda x: str(x).split()[0] if pd.notnull(x) else "알수없음")
        
        # 위도, 경도 숫자형으로 변환 (오류 발생 시 NaN 처리 후 제거)
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        # 정확한 요금 비교를 위한 '1분당 요금' 계산 로직 추가
        def calc_per_min(row):
            try:
                fee = float(row['기본 주차 요금'])
                time = float(row['기본 주차 시간(분 단위)'])
                return fee / time if time > 0 else float('inf')
            except:
                return float('inf')
                
        df['분당요금'] = df.apply(calc_per_min, axis=1)
        return df

    df = load_data(uploaded_file)

    # 3. 사이드바 - 검색 필터 (자치구 선택 등)
    st.sidebar.header("🔍 검색 필터")
    districts = sorted([d for d in df['자치구'].unique() if d.endswith('구')])
    selected_district = st.sidebar.selectbox("자치구 선택", ["서울 전체"] + districts)
    
    # 데이터 필터링
    filtered_df = df if selected_district == "서울 전체" else df[df['자치구'] == selected_district]

    # 4. 가장 저렴한 주차장 추천 (핵심 기능)
    st.subheader(f"💡 {selected_district} 추천 공영주차장 (가장 저렴한 곳)")
    if not filtered_df.empty:
        # 유료 주차장 중에서 분당 요금이 가장 싼 곳 찾기
        paid_df = filtered_df[filtered_df['유무료구분명'] == '유료']
        
        if not paid_df.empty:
            cheapest = paid_df.sort_values(by='분당요금').iloc[0]
            st.success(f"🏆 가장 저렴한 유료 주차장: **{cheapest['주차장명']}**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**📍 주소:** {cheapest['주소']}")
                st.write(f"**💰 기본요금:** {cheapest['기본 주차 시간(분 단위)']}분 당 {cheapest['기본 주차 요금']}원")
            with col2:
                st.write(f"**🌙 야간 무료개방:** {cheapest['야간무료개방여부명']}")
                st.write(f"**🗓️ 주말운영시간:** {cheapest['주말 운영 시작시각(HHMM)']} ~ {cheapest['주말 운영 종료시각(HHMM)']}")
        else:
            st.info("선택하신 지역에는 유료 주차장 정보가 없습니다.")
    else:
        st.warning("데이터가 없습니다.")

    # 5. 지도 시각화 (Folium)
    st.subheader("🗺️ 주차장 위치 지도")
    st.markdown("마커에 마우스를 올리면 주차장 이름이, 클릭하면 상세 정보가 나타납니다. (🟢 무료 / 🔵 유료)")
    
    if not filtered_df.empty:
        # 지도의 중심을 필터링된 데이터의 평균 위경도로 설정
        center_lat = filtered_df['위도'].mean()
        center_lon = filtered_df['경도'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        for idx, row in filtered_df.iterrows():
            # 유무료 여부에 따른 마커 색상 변경 (추가 추천 기능)
            marker_color = 'green' if row['유무료구분명'] == '무료' else 'blue'
            
            # 마커 클릭 시 보여줄 상세 팝업 HTML (원하시는 모든 정보 포함)
            popup_html = f"""
            <div style="width:250px;">
                <h4 style="margin-top:0px;">{row['주차장명']}</h4>
                <b>주소:</b> {row['주소']}<br>
                <b>구분:</b> {row['유무료구분명']}<br>
                <b>요금:</b> 기본 {row['기본 주차 시간(분 단위)']}분 / {row['기본 주차 요금']}원<br>
                <b>야간 무료 여부:</b> {row['야간무료개방여부명']}<br>
                <b>주말 운영:</b> {row['주말 운영 시작시각(HHMM)']} ~ {row['주말 운영 종료시각(HHMM)']}<br>
            </div>
            """
            
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=row['주차장명'], # 마우스를 올렸을 때 나타나는 툴팁
                icon=folium.Icon(color=marker_color, icon='info-sign')
            ).add_to(m)

        # 스트림릿에 지도 출력
        st_folium(m, width=1000, height=600)

    # 6. 추가 기능: 전체 데이터 표기 및 검색
    with st.expander("📊 상세 데이터 표 보기 (이름으로 검색)"):
        search_query = st.text_input("주차장 이름 검색")
        if search_query:
            display_df = filtered_df[filtered_df['주차장명'].str.contains(search_query, na=False)]
        else:
            display_df = filtered_df
            
        st.dataframe(display_df[['주차장명', '주소', '유무료구분명', '기본 주차 요금', '기본 주차 시간(분 단위)', '야간무료개방여부명']])

else:
    st.info("👆 데이터를 분석하고 지도를 생성하려면 상단의 버튼을 눌러 CSV 파일을 업로드해주세요.")
