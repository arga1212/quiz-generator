import streamlit as st
import google.generativeai as genai
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # Updated to stable model
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 2000
    }
)

# Streamlit UI
st.set_page_config(page_title="AI Quiz Generator", page_icon="🧠")
st.title("Quiz Generator")
st.write("Paste materi Anda, generate kuis otomatis!")

# Input User
user_material = st.text_area("**Materi:**", height=200, placeholder="Paste teks materi di sini...")
difficulty = st.selectbox("**Tingkat Kesulitan:**", ["Easy", "Medium", "Hard"])
num_questions = st.slider("**Jumlah Soal:**", 1, 10, 5)

if st.button("Generate Quiz") and user_material:
    with st.spinner("Membuat kuis..."):
        # Improved prompt with better JSON structure
        prompt = f"""
        Buat {num_questions} soal kuis pilihan ganda berdasarkan teks berikut:
        ---
        {user_material}
        ---
        **Format Output (HARUS JSON):**
        {{
            "quiz": [
                {{
                    "question": "pertanyaan",
                    "options": {{
                        "a": "teks opsi a",
                        "b": "teks opsi b", 
                        "c": "teks opsi c",
                        "d": "teks opsi d"
                    }},
                    "correct_answer": "a",  # HURUF KECIL (a/b/c/d)
                    "correct_text": "teks opsi a",  # TEKS JAWABAN BENAR
                    "explanation": "penjelasan"
                }}
            ]
        }}
        **Aturan:**
        1. Tingkat kesulitan: {difficulty}
        2. Pastikan 'correct_text' sama persis dengan salah satu opsi
        3. Hanya kembalikan JSON, tanpa komentar lain
        """
        
        try:
            response = model.generate_content(prompt)
            # Improved JSON extraction
            json_str = re.search(r'\{[\s\S]*\}', response.text).group()
            quiz_data = json.loads(json_str)
            
            # Validation
            for question in quiz_data["quiz"]:
                if question["correct_answer"] not in question["options"]:
                    raise ValueError("Jawaban benar tidak sesuai dengan opsi")
                if question["correct_text"] != question["options"][question["correct_answer"]]:
                    raise ValueError("Teks jawaban benar tidak match")
            
            st.session_state.quiz = quiz_data
            st.success("Kuis berhasil dibuat!")
            
        except Exception as e:
            st.error(f"Error: {str(e)}\n\nCoba generate lagi atau perbaiki prompt.")

# Display quiz
if "quiz" in st.session_state:
    st.divider()
    st.header("📝 Soal")
    user_answers = {}
    
    for i, q in enumerate(st.session_state.quiz["quiz"]):
        st.subheader(f"Soal {i+1}: {q['question']}")
        options = list(q["options"].values())
        user_answers[i] = st.radio(
            "Pilih jawaban:",
            options,
            key=f"q{i}",
            index=None
        )
        st.write("---")
    
    # Check answers
    if st.button("Periksa Jawaban"):
        st.divider()
        st.header("📊 Hasil")
        score = 0
        
        for i, q in enumerate(st.session_state.quiz["quiz"]):
            user_answer = user_answers[i]
            correct_key = q["correct_answer"]
            correct_text = q["correct_text"]
            
            st.subheader(f"Soal {i+1}")
            st.write(f"**Pertanyaan:** {q['question']}")
            
            if user_answer == correct_text:
                st.success(f"✅ Jawaban Anda: {user_answer} (Benar)")
                score += 1
            else:
                st.error(f"❌ Jawaban Anda: {user_answer}")
                st.info(f"Jawaban benar: {correct_text} ({correct_key})")
            
            st.write(f"💡 Penjelasan: {q.get('explanation', 'Tidak ada penjelasan')}")
            st.write("---")
        
        st.success(f"🎉 Skor Anda: {score}/{len(st.session_state.quiz['quiz'])}")

# Initial message
elif not user_material:
    st.info("💡 Paste materi Anda di atas, lalu klik **Generate Quiz**.")