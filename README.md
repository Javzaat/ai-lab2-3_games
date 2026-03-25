# AI Lab 2 — Games (Streamlit)

Энэ репо нь **Хиймэл оюун ухаан — Лаб 2**-ын 3 даалгаврыг Streamlit UI-тайгаар хийсэн хувилбарууд.

##  Даалгаврууд
1) **XO (NxN) + AI** — NxN хэмжээтэй XO тоглоом, AI opponent (Easy/Medium/Hard)  
2) **8 Queens** — 8 бэрс бодлого (92 шийдэл), fundamental (12) + orbit (симметр) UI  
3) **8-Puzzle + Agent (A\*)** — Tile дээр дарж хөдөлдөг puzzle + A* agent + solution carousel

---

  1) XO (NxN) + AI
 Run
```bash
source .venv/bin/activate
python -m streamlit run xo_nxn_ai.py

2) 8 Queens (Chess UI)

Run
source .venv/bin/activate
python -m streamlit run queens_app.py


3) 8-Puzzle + Agent (A*)
Runsource .venv/bin/activate
python -m streamlit run puzzle_app.py

Setup (анх удаа ажиллуулах)

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install streamlit