import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 페이지 설정 ---
st.set_page_config(page_title="내 주변 맛집 탐지기", page_icon="🍔", layout="centered")
st.title("🍔 내 주변 1km 맛집 탐지기")
st.write("주소를 입력하면 가장 평점이 높은 맛집들을 찾아드립니다!")

# --- API 키 설정 (Streamlit Cloud Secrets 사용) ---
# 로컬 테스트 시에는 st.secrets 대신 문자열로 직접 입력해도 되지만, 클라우드 배포 시에는 반드시 Secrets를 사용하세요.
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Google API Key가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 설정해주세요.")
    st.stop()

# --- 함수 정의 ---
def get_coordinates(address, api_key):
    """주소를 위도/경도로 변환"""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}&language=ko"
    response = requests.get(url).json()
    if response['status'] == 'OK':
        location = response['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None

def get_nearby_restaurants(lat, lng, api_key, open_now=False):
    """주변 1km 식당 검색 및 정렬"""
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&type=restaurant&key={api_key}&language=ko"
    if open_now:
        url += "&opennow=true"
        
    response = requests.get(url).json()
    restaurants = []
    
    if response['status'] == 'OK':
        for place in response['results']:
            # 평점이 있는 곳만 필터링
            if 'rating' in place:
                restaurants.append({
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'rating': place.get('rating', 0),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'address': place.get('vicinity', ''),
                    'price_level': place.get('price_level', 0)
                })
                
        # 별점 높은 순으로 정렬, 평점이 같으면 리뷰 수 많은 순
        restaurants.sort(key=lambda x: (x['rating'], x['user_ratings_total']), reverse=True)
        return restaurants[:10] # 상위 10개만 반환
    return []

def get_place_details(place_id, api_key):
    """특정 식당의 상세 정보 (리뷰, URL 등) 가져오기"""
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,reviews,url,formatted_phone_number&key={api_key}&language=ko"
    response = requests.get(url).json()
    if response['status'] == 'OK':
        return response['result']
    return {}

# --- UI 및 로직 ---
address_input = st.text_input("📍 기준이 될 주소를 입력하세요 (예: 서울특별시 강남구 테헤란로 152)", placeholder="주소를 입력해주세요...")

col1, col2 = st.columns([1, 1])
with col1:
    open_now_filter = st.checkbox("🟢 현재 영업 중인 곳만 보기")

if st.button("맛집 찾기", type="primary"):
    if address_input:
        with st.spinner("주변 맛집을 탐색 중입니다... 🕵️‍♂️"):
            lat, lng = get_coordinates(address_input, GOOGLE_API_KEY)
            
            if lat and lng:
                restaurants = get_nearby_restaurants(lat, lng, GOOGLE_API_KEY, open_now_filter)
                
                if not restaurants:
                    st.warning("주변에 조건에 맞는 식당을 찾지 못했습니다.")
                else:
                    st.success(f"검색 성공! 주변 상위 맛집 {len(restaurants)}곳을 찾았습니다.")
                    
                    # 1. 지도 시각화
                    st.subheader("🗺️ 맛집 지도")
                    m = folium.Map(location=[lat, lng], zoom_start=15)
                    # 내 위치 마커
                    folium.Marker([lat, lng], popup="내 위치", icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
                    
                    for idx, rest in enumerate(restaurants):
                        folium.Marker(
                            [rest['lat'], rest['lng']], 
                            popup=f"{idx+1}. {rest['name']} (⭐{rest['rating']})",
                            icon=folium.Icon(color="blue", icon="cutlery")
                        ).add_to(m)
                    
                    st_folium(m, width=700, height=400)
                    
                    # 2. 식당 상세 정보 표시
                    st.subheader("🏆 별점 순 맛집 리스트")
                    for idx, rest in enumerate(restaurants):
                        details = get_place_details(rest['place_id'], GOOGLE_API_KEY)
                        price_display = "💰" * rest['price_level'] if rest['price_level'] > 0 else "가격 정보 없음"
                        
                        with st.expander(f"**{idx+1}. {rest['name']}** (⭐ {rest['rating']} / 리뷰 {rest['user_ratings_total']}개)"):
                            st.write(f"**주소:** {rest['address']}")
                            st.write(f"**가격대:** {price_display}")
                            if 'formatted_phone_number' in details:
                                st.write(f"**전화번호:** {details['formatted_phone_number']}")
                            if 'url' in details:
                                st.markdown(f"[🗺️ 구글 맵에서 보기]({details['url']})")
                            
                            # 리뷰 표시
                            if 'reviews' in details:
                                st.markdown("---")
                                st.markdown("##### 💬 최신 리뷰")
                                for review in details['reviews'][:3]: # 리뷰 3개만 표시
                                    st.info(f"**{review.get('author_name', '익명')}** (⭐ {review.get('rating', 0)})\n\n{review.get('text', '리뷰 내용이 없습니다.')}")
            else:
                st.error("주소를 인식할 수 없습니다. 더 정확한 주소를 입력해주세요.")
    else:
        st.warning("주소를 먼저 입력해주세요!")
