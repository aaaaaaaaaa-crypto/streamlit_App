import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from googleapiclient.discovery import build
from wordcloud import WordCloud
from collections import Counter
import matplotlib.font_manager as fm
import os
import urllib.request  # 👈 인터넷에서 폰트를 다운로드하기 위해 추가

# --- 설정 부분 ---
st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="📊", layout="wide")

FONT_PATH = "NanumGothic.ttf" 

# 🔥 [핵심 수정] 폰트 파일이 없으면 구글 폰트 공식 저장소에서 자동으로 다운로드합니다.
if not os.path.exists(FONT_PATH):
    with st.spinner("🎯 한글 폰트(나눔고딕)를 서버에 설치하는 중입니다..."):
        try:
            font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(font_url, FONT_PATH)
            # 맷플롯립 캐시 재설정
            fm.fontManager.addfont(FONT_PATH)
        except Exception as e:
            st.error(f"폰트 다운로드 중 오류가 발생했습니다: {e}")

# 유튜브 API 키 설정 (Streamlit Secrets에서 가져옴)
try:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
except KeyError:
    st.error("⚠️ Streamlit Secrets에 'YOUTUBE_API_KEY'가 설정되지 않았습니다.")
    st.stop()

# --- 헬퍼 함수 ---
def get_video_id(url):
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if video_id_match:
        return video_id_match.group(1)
    return None

@st.cache_data(show_spinner=False)
def fetch_youtube_comments(video_id, max_results):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    comments = []
    next_page_token = None
    
    while len(comments) < max_results:
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'text': comment['textDisplay'],
                    'published_at': comment['publishedAt'],
                    'like_count': comment['likeCount']
                })
                
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        except Exception as e:
            st.error(f"댓글 수집 중 오류가 발생했습니다: {e}")
            break
            
    return pd.DataFrame(comments)

def analyze_sentiment(text):
    positive_words = ['좋', '최고', '감사', '재밌', '응원', '짱', '완벽', '기대', '사랑', '멋지']
    negative_words = ['별로', '노잼', '최악', '짜증', '아쉽', '실망', '지루', '쓰레기', '나쁜']
    
    pos_score = sum(1 for word in positive_words if word in text)
    neg_score = sum(1 for word in negative_words if word in text)
    
    if pos_score > neg_score: return '긍정'
    elif neg_score > pos_score: return '부정'
    else: return '중립'

# --- 메인 UI ---
st.title("📺 유튜브 댓글 분석기")
st.markdown("유튜브 영상 링크를 입력하면 댓글을 수집하여 시간대별 추이, 반응도, 워드클라우드를 분석합니다.")

with st.container():
    url = st.text_input("유튜브 영상 링크를 입력하세요:", placeholder="https://www.youtube.com/watch?v=...")
    max_comments = st.slider("수집할 최대 댓글 개수", min_value=50, max_value=1000, value=200, step=50)
    analyze_btn = st.button("분석 시작", type="primary")

if analyze_btn and url:
    video_id = get_video_id(url)
    
    if not video_id:
        st.warning("유효한 유튜브 링크가 아닙니다. 다시 확인해주세요.")
    else:
        st.video(url)
        
        with st.spinner("댓글을 수집하고 분석하는 중입니다..."):
            df = fetch_youtube_comments(video_id, max_comments)
            
            if df.empty:
                st.error("해당 영상에 댓글이 없거나 댓글이 비활성화되어 있습니다.")
            else:
                st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다!")
                
                df['published_at'] = pd.to_datetime(df['published_at'])
                df['sentiment'] = df['text'].apply(analyze_sentiment)
                
                col1, col2 = st.columns(2)
                
                # 1. 시간대별 추이
                with col1:
                    st.subheader("📈 시간대별 댓글 작성 추이")
                    trend_df = df.groupby(df['published_at'].dt.date).size().reset_index(name='count')
                    trend_df = trend_df.set_index('published_at')
                    st.line_chart(trend_df)
                
                # 2. 댓글 반응도
                with col2:
                    st.subheader("🎭 댓글 반응도 (긍/부정)")
                    sentiment_counts = df['sentiment'].value_counts()
                    
                    fig, ax = plt.subplots(figsize=(6, 4))
                    if os.path.exists(FONT_PATH):
                        prop = fm.FontProperties(fname=FONT_PATH)
                        plt.rc('font', family=prop.get_name())
                    
                    colors = ['#ff9999','#66b3ff','#99ff99']
                    ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', 
                           startangle=90, colors=colors, textprops={'fontsize': 12})
                    ax.axis('equal')  
                    st.pyplot(fig)

                # 3. 한글 워드클라우드 (Java/KoNLPy 없이 실행)
                st.subheader("☁️ 워드클라우드")
                
                all_text = " ".join(df['text'].tolist())
                # 정규식을 이용해 한글 단어(공백 분리)만 추출
                words = re.findall(r'[가-힣]+', all_text)
                
                # 의미 없는 조사나 짧은 단어 방지를 위해 2글자 이상 단어만 필터링
                # 추가로 분석에 제외하고 싶은 단어가 있다면 아래 리스트에 추가 가능
                stop_words = ['영상', '진짜', '너무', '정말', '이거', '보고', '완전', '그냥', '요즘']
                meaningful_words = [w for w in words if len(w) >= 2 and w not in stop_words]
                
                counts = Counter(meaningful_words)
                
                if not os.path.exists(FONT_PATH):
                    st.error(f"⚠️ 폰트 파일을 찾을 수 없습니다: `{FONT_PATH}`. 깃허브에 파일이 있는지 확인하세요.")
                elif len(counts) > 0:
                    wc = WordCloud(
                        font_path=FONT_PATH,
                        width=800,
                        height=400,
                        background_color='white',
                        colormap='viridis'
                    ).generate_from_frequencies(counts)
                    
                    fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
                    ax_wc.imshow(wc, interpolation='bilinear')
                    ax_wc.axis('off')
                    st.pyplot(fig_wc)
                else:
                    st.info("워드클라우드를 생성할 유의미한 단어가 부족합니다.")
