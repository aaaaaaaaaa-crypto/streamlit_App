import streamlit as st
import random

# ==========================================
# 1. 한글 초성 자동 추출 함수 (유니코드 계산)
# ==========================================
def get_initial_consonants(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    result = []
    for char in text:
        if '가' <= char <= '힣':
            char_code = ord(char) - 0xAC00
            chosung_index = char_code // 588
            result.append(CHOSUNG_LIST[chosung_index])
        else:
            result.append(char)
    return "".join(result)

# ==========================================
# 2. 기본 데이터셋 정의
# ==========================================
DEFAULT_DATABASE = {
    "🎬 영화 & 드라마": ["기생충", "오징어게임", "범죄도시", "아바타", "한산"],
    "🍕 음식": ["떡볶이", "마라탕", "삼겹살", "짜장면", "후라이드치킨"],
    "💻 IT & 개발": ["파이썬", "스트림릿", "인공지능", "데이터베이스", "알고리즘"],
    "🐶 동물": ["호랑이", "판다", "돌고래", "수달", "앵무새"]
}

# 페이지 설정
st.set_page_config(page_title="초성퀴즈 마스터", page_icon="🧩", layout="centered")

# ==========================================
# 3. Session State 초기화
# ==========================================
if "db" not in st.session_state:
    st.session_state.db = DEFAULT_DATABASE
if "score" not in st.session_state:
    st.session_state.score = 0
if "combo" not in st.session_state:
    st.session_state.combo = 0
if "show_hint" not in st.session_state:
    st.session_state.show_hint = False
if "current_word" not in st.session_state:
    st.session_state.current_category = "🍕 음식"
    st.session_state.current_word = random.choice(st.session_state.db["🍕 음식"])

# 새로운 단어 세팅 함수
def set_new_quiz():
    category = st.session_state.current_category
    word_list = st.session_state.db[category]
    st.session_state.current_word = random.choice(word_list)
    st.session_state.show_hint = False

# ==========================================
# 4. 사이드바 (점수판 및 단어 추가)
# ==========================================
st.sidebar.title("🎮 게임 현황 & 설정")
st.sidebar.metric(label="현재 점수", value=f"{st.session_state.score} 점")
st.sidebar.metric(label="연속 정답 콤보", value=f"🔥 {st.session_state.combo} Combo")

st.sidebar.markdown("---")
st.sidebar.subheader("➕ 나만의 단어 추가하기")
new_cat = st.sidebar.selectbox("카테고리 선택", list(st.session_state.db.keys()))
new_word = st.sidebar.text_input("추가할 단어 (한글만):")

if st.sidebar.button("단어 등록"):
    clean_word = new_word.strip()
    if clean_word:
        st.session_state.db[new_cat].append(clean_word)
        st.sidebar.success(f"'{clean_word}' 단어가 추가되었습니다!")
    else:
        st.sidebar.warning("단어를 입력해주세요.")

# ==========================================
# 5. 메인 화면 UI
# ==========================================
st.title("🧩 자동 초성퀴즈 마스터")
st.caption("API 없이 동작하는 스마트한 초성 맞추기 게임!")

# 카테고리 선택
selected_category = st.selectbox(
    "카테고리를 선택하세요:",
    list(st.session_state.db.keys()),
    index=list(st.session_state.db.keys()).index(st.session_state.current_category)
)

# 카테고리가 변경되면 문제 새로 세팅
if selected_category != st.session_state.current_category:
    st.session_state.current_category = selected_category
    set_new_quiz()
    st.rerun()

# 현재 단어 정보
target_word = st.session_state.current_word
initials = get_initial_consonants(target_word)

st.markdown("---")

# 문제 표시 영역
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"### 문제: :blue[{initials}]")
    st.caption(f"글자 수: {len(target_word)}글자")
with col2:
    if st.button("💡 첫 글자 힌트"):
        st.session_state.show_hint = True

# 힌트 출력
if st.session_state.show_hint:
    st.info(f"첫 번째 글자는 **'{target_word[0]}'** 입니다! (정답 시 5점 감점)")

# 정답 제출 폼
with st.form(key="answer_form", clear_on_submit=True):
    user_input = st.text_input("정답을 입력하세요:")
    submit = st.form_submit_button("정답 제출 🚀")

if submit:
    if user_input.strip() == target_word:
        # 점수 계산
        st.session_state.combo += 1
        gained_score = 10 + (st.session_state.combo * 2) # 콤보 보너스
        if st.session_state.show_hint:
            gained_score = max(1, gained_score - 5) # 힌트 감점
        
        st.session_state.score += gained_score
        st.balloons()
        st.success(f"🎉 **정답입니다!** (+{gained_score}점 획득)")
        
        # 다음 문제로
        set_new_quiz()
        st.button("다음 문제 풀기 ➡️")
    else:
        st.session_state.combo = 0 # 오답 시 콤보 리셋
        st.error("❌ 틀렸습니다! 다시 생각해보세요. (콤보가 리셋되었습니다)")

# 패스 버튼
if st.button("다음 문제로 패스 ⏭️"):
    st.session_state.combo = 0
    set_new_quiz()
    st.rerun()
