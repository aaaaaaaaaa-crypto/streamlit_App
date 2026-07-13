import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Study Mate", page_icon="📚")

st.title("📚 Study Mate")
st.write("오늘의 공부 계획을 관리해보세요!")

quotes = [
    "오늘 한 공부가 내일의 실력이다.",
    "천재는 노력하는 사람을 이길 수 없다.",
    "포기하지 않으면 반드시 성장한다.",
    "작은 습관이 큰 변화를 만든다.",
    "오늘의 1시간이 미래를 바꾼다."
]

st.subheader("✨ 오늘의 명언")
st.info(random.choice(quotes))

st.subheader("📝 공부 계획")

subjects = ["국어", "수학", "영어", "탐구", "기타"]

data = []

for subject in subjects:
    hour = st.slider(f"{subject} 공부 시간(시간)", 0, 10, 2)
    data.append({"과목": subject, "시간": hour})

df = pd.DataFrame(data)

st.subheader("📊 공부 시간")

st.bar_chart(df.set_index("과목"))

total = df["시간"].sum()

st.metric("총 공부 시간", f"{total}시간")

goal = st.number_input("오늘 목표 공부 시간", 1, 20, 10)

progress = min(total / goal, 1.0)

st.progress(progress)

if total >= goal:
    st.success("🎉 목표 달성!")
else:
    st.warning(f"목표까지 {goal-total}시간 남았습니다.")

st.subheader("🎲 랜덤 공부 추천")

if st.button("추천 받기"):
    st.success(random.choice(subjects))
