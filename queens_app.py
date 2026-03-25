# queens_app.py
# ============================================================
# 8 Queens — Chess UI + Fundamental filter + Orbit horizontal scroll (carousel-like)
# ------------------------------------------------------------
# Энэ програм нь "8 бэрсийн бодлого"-ын бүх шийдлийг олж,
# дараа нь Streamlit ашиглан "жинхэнэ шатрын хөлөг" мэт UI-тайгаар
# үзүүлж харуулдаг.
#
# Гол боломжууд:
#   1) 8×8 хөлөг дээр 8 бэрс (♛)-ийг
#      - нэг мөрөнд 1,
#      - нэг баганад 1,
#      - диагоналиар давхцахгүй
#      байдлаар байрлуулах бүх шийдлийг олно.
#
#   2) 2 янзаар үзэж болно:
#      - All solutions (92): Давхардаагүй 92 шийдэл
#      - Fundamental solutions (12): Симметрээр (эргүүлэх/тольдох) адил
#        шийдлүүдийг 1 бүлэг болгож "үндсэн" 12 төлөөлөгч шийдэл
#
#   3) Fundamental горимд:
#      - Orbit (симметр хувилбарууд)-ыг carousel шиг хэвтээ scroll-оор харуулна.
#
# Хэрхэн ажиллуулах вэ?
#   source .venv/bin/activate
#   python -m streamlit run queens_app.py
# ============================================================

import streamlit as st

# ============================================================
# 1) Шийдэл олох хэсэг (Solver)
# ============================================================
def solve_n_queens(n=8):
    """
    N-Queens бодлогын бүх шийдлийг backtracking аргаар олно.

    pos[row] = col гэсэн хэлбэрээр хадгална:
      - row мөрөнд байрласан бэрс нь col баганад байна гэсэн үг.

    Хурд/хязгаарлалтууд:
      - cols  : аль баганууд дээр аль хэдийн бэрс байгаа эсэх
      - diag1 : (row - col) диагональ давхцаж байгаа эсэх
      - diag2 : (row + col) диагональ давхцаж байгаа эсэх

    Буцаах: solutions
      solutions = [pos1, pos2, ...]
      pos нь урт n list байна.
    """
    solutions = []
    cols, diag1, diag2 = set(), set(), set()
    pos = [-1] * n

    def backtrack(row):
        # бүх мөрөнд бэрс тавьсан бол 1 шийдэл олдлоо гэсэн үг
        if row == n:
            solutions.append(pos.copy())
            return

        # тухайн мөрөнд (row) боломжит бүх баганад тавьж үзнэ
        for col in range(n):
            # 1) багана давхцаж болохгүй
            # 2) diag1 (row-col) давхцахгүй
            # 3) diag2 (row+col) давхцахгүй
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue

            # тавина
            pos[row] = col
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)

            # дараагийн мөр
            backtrack(row + 1)

            # буцааж авна (backtrack)
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)
            pos[row] = -1

    backtrack(0)
    return solutions

# ============================================================
# 2) Шатрын координатын тэмдэглэгээ (Notation)
# ============================================================
def pos_to_notation(pos):
    """
    pos (list) -> ["A1", "E2", ...] гэх мэт шатрын координатын жагсаалт болгоно.

    Анхаарах зүйл:
      - col 0..7 -> A..H
      - row 0..7 -> 1..8
    """
    out = []
    for row, col in enumerate(pos):
        file_ = chr(ord("A") + col)  # багана: A..H
        rank = row + 1               # мөр: 1..8
        out.append(f"{file_}{rank}")
    return out

# ============================================================
# 3) Симметр (D4 group) — эргүүлэх/тольдох хувиргалтууд
# ============================================================
# 8×8 шатрын хөлөг дээр "адил" гэж үзэх симметрүүд байдаг:
#   - 90°, 180°, 270° эргүүлэх (rotation)
#   - босоо/хэвтээ тольдох (reflection)
#   - гол диагональ / эсрэг диагональ тольдох
#
# Эдгээрийг нийлүүлбэл нийт 8 төрлийн хувиргалт байдаг (D4 group).

def pos_to_coords(pos):
    """
    pos[row]=col -> [(row,col), ...] координат руу хувиргана.
    """
    return [(r, c) for r, c in enumerate(pos)]

def coords_to_pos(coords, n):
    """
    [(row,col), ...] -> pos[row]=col хэлбэрт буцаана.
    """
    pos = [-1] * n
    for r, c in coords:
        pos[r] = c
    return pos

def transform_coord(r, c, n, t):
    """
    Нэг координатыг (r,c) симметрээр хувиргана.
    t = 0..7 байх ба 8 төрлийн хувиргалтыг илэрхийлнэ.

    t-ийн тайлбар:
      0: өөрчлөхгүй
      1: 90° эргүүлэх
      2: 180° эргүүлэх
      3: 270° эргүүлэх
      4: босоо тольдох
      5: хэвтээ тольдох
      6: гол диагональ тольдох
      7: эсрэг диагональ тольдох
    """
    if t == 0:  return (r, c)
    if t == 1:  return (c, n - 1 - r)          # rot90
    if t == 2:  return (n - 1 - r, n - 1 - c)  # rot180
    if t == 3:  return (n - 1 - c, r)          # rot270
    if t == 4:  return (r, n - 1 - c)          # reflect vertical
    if t == 5:  return (n - 1 - r, c)          # reflect horizontal
    if t == 6:  return (c, r)                  # reflect main diagonal
    if t == 7:  return (n - 1 - c, n - 1 - r)  # reflect anti diagonal
    raise ValueError("Invalid transform")

def transform_pos(pos, n, t):
    """
    Нэг бүтэн шийдэл (pos)-ийг симметрээр хувиргаад
    шинэ pos хэлбэрээр буцаана.
    """
    coords = pos_to_coords(pos)
    new_coords = [transform_coord(r, c, n, t) for (r, c) in coords]

    # coords_to_pos хийхэд row-ийн дарааллаар байлгах хэрэгтэй
    new_coords.sort(key=lambda x: x[0])
    return coords_to_pos(new_coords, n)

def canonical_key(pos, n):
    """
    Шийдлийг "каноник төлөөлөл" болгож өгнө.
    Өөрөөр хэлбэл:
      - тухайн шийдлийн 8 симметр хувилбар дундаас
      - хамгийн "жижиг" (lexicographically min) хувилбарыг түлхүүр болгоно.

    Ингэснээр симметрээр адил шийдлүүд нэг ижил canonical_key-тэй болно.
    """
    variants = [tuple(transform_pos(pos, n, t)) for t in range(8)]
    return min(variants)

def orbit_variants(pos, n):
    """
    Нэг төлөөлөгч шийдлийн бүх өвөрмөц симметр хувилбаруудыг (orbit) олно.
    Зарим шийдэл өөртөө симметртэй байж болох тул orbit_size 8 биш 4 болж болно.
    """
    vars_set = set(tuple(transform_pos(pos, n, t)) for t in range(8))
    return [list(v) for v in sorted(vars_set)]

def fundamental_solutions(all_solutions, n):
    """
    All solutions (92)-ийг симметрээр бүлэглээд Fundamental solutions (12) болгоно.

    groups:
      key = canonical_key
      value = тэр түлхүүрт хамаарах бүх шийдэл

    fundamentals:
      - rep: бүлгийн төлөөлөгч (canonical)
      - orbit: симметрийн бүх өвөрмөц хувилбарууд
      - orbit_size: orbit-ийн хэмжээ (ихэвчлэн 8, заримдаа 4)
      - count_in_all: энэ бүлэгт all_solutions-оос хэд таарч байгааг тоолно
    """
    groups = {}
    for sol in all_solutions:
        key = canonical_key(sol, n)
        groups.setdefault(key, []).append(sol)

    fundamentals = []
    for key, members in groups.items():
        rep = list(key)
        orbit = orbit_variants(rep, n)
        fundamentals.append({
            "rep": rep,
            "orbit": orbit,
            "orbit_size": len(orbit),
            "count_in_all": len(members)
        })

    # special (orbit_size=4) эхэнд, дараа нь бусад
    fundamentals.sort(key=lambda d: (d["orbit_size"], d["rep"]))
    return fundamentals

# ============================================================
# 4) Chessboard HTML — шатрын хөлөг шиг дүрслэх (A..H, 1..8)
# ============================================================
def chessboard_html(pos, n=8, cell=46):
    """
    pos[row]=col хэлбэрийн шийдлийг HTML/CSS-аар шатрын хөлөг шиг зурна.
    - Ногоон/шаргал (green/beige) өнгөтэй
    - ♛ тэмдэгээр бэрсийг харуулна
    - Дээд/доод талд A..H, хоёр талд 1..8 дугаарлалтай
    """
    files = [chr(ord('A') + i) for i in range(n)]
    rows = []

    # HTML дээр уламжлалт шатар шиг харагдуулахын тулд
    # r=7..0 гэж уруудаж явна (8-р мөр дээрээс харагдана)
    for r in range(n - 1, -1, -1):
        cells = []
        for c in range(n):
            is_dark = (r + c) % 2 == 1
            bg = "#769656" if is_dark else "#eeeed2"
            piece = "♛" if pos[r] == c else ""

            cells.append(
                f"""
                <div class="cell" style="background:{bg}; width:{cell}px; height:{cell}px;">
                    <span class="piece">{piece}</span>
                </div>
                """
            )

        rows.append(
            f"""
            <div class="row">
              <div class="rank">{r+1}</div>
              {''.join(cells)}
              <div class="rank right">{r+1}</div>
            </div>
            """
        )

    file_labels = "".join([f'<div class="file">{f}</div>' for f in files])

    html = f"""
    <style>
      .board-wrap {{
        display: inline-block;
        padding: 10px;
        border-radius: 14px;
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.12);
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
      }}
      .files {{
        display: grid;
        grid-template-columns: 24px repeat({n}, {cell}px) 24px;
        align-items: center;
        justify-items: center;
        margin-bottom: 6px;
        font-weight: 700;
        color: #333;
      }}
      .file {{ width:{cell}px; text-align:center; }}
      .rows {{ display:flex; flex-direction:column; }}
      .row {{
        display: grid;
        grid-template-columns: 24px repeat({n}, {cell}px) 24px;
        align-items: center;
      }}
      .rank {{
        width: 24px;
        text-align:center;
        font-weight: 700;
        color: #333;
      }}
      .rank.right {{ opacity: 0.55; }}
      .cell {{
        display:flex;
        align-items:center;
        justify-content:center;
        user-select:none;
        border-radius: 2px;
      }}
      .piece {{
        font-size: {int(cell*0.70)}px;
        line-height: 1;
        color: #111;
      }}
      .footer-files {{
        display: grid;
        grid-template-columns: 24px repeat({n}, {cell}px) 24px;
        align-items: center;
        justify-items: center;
        margin-top: 6px;
        font-weight: 700;
        color: #333;
      }}
    </style>

    <div class="board-wrap">
      <div class="files">
        <div></div>
        {file_labels}
        <div></div>
      </div>
      <div class="rows">
        {''.join(rows)}
      </div>
      <div class="footer-files">
        <div></div>
        {file_labels}
        <div></div>
      </div>
    </div>
    """
    return html

def board_height(n=8, cell=46):
    """
    Streamlit дээр components.v1.html-ийн height-ийг тааруулах туслах.
    (Хөлгийн cell хэмжээ өөрчлөгдвөл height өсөх/буурах ёстой)
    """
    return int(20 + 56 + (cell * n) + 40)

# ============================================================
# 5) Orbit horizontal scroll HTML — олон хувилбарыг carousel шиг харуулах
# ============================================================
def orbit_scroll_html(variants, n=8, cell=30):
    """
    Orbit дахь олон хувилбарыг нэг мөрөнд байрлуулж,
    хэвтээ scroll (horizontal scroll)-оор гүйлгэж харуулна.

    card бүр:
      - Variant i гарчиг
      - жижиг хөлөг (cell жижиг)
      - координатын тайлбар
    """
    cards = []
    for i, v in enumerate(variants, 1):
        board = chessboard_html(v, n, cell=cell)
        coords = ", ".join(pos_to_notation(v))
        cards.append(f"""
        <div class="card">
          <div class="card-title">Variant {i}</div>
          {board}
          <div class="card-coords">{coords}</div>
        </div>
        """)

    html = f"""
    <style>
      .orbit-scroll {{
        overflow-x: auto;
        overflow-y: hidden;
        white-space: nowrap;
        padding: 10px 8px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.03);
      }}
      .card {{
        display: inline-block;
        vertical-align: top;
        white-space: normal;
        width: 360px;
        margin-right: 14px;
      }}
      .card-title {{
        font-weight: 800;
        margin: 0 0 10px 0;
        font-size: 16px;
      }}
      .card-coords {{
        margin-top: 10px;
        font-size: 12px;
        opacity: 0.92;
        line-height: 1.35;
        word-break: break-word;
      }}
    </style>

    <div class="orbit-scroll">
      {''.join(cards)}
    </div>
    """
    return html

# ============================================================
# 6) Streamlit App — UI хэсэг
# ============================================================
st.set_page_config(page_title="8 Queens — Chess UI", layout="wide")
st.title("8 бэрс (8 Queens) — Chess UI (Fundamental + Orbit scroll)")

# cache_data:
# - solve_n_queens(8) зэрэг хүнд тооцооллыг дахин дахин хийлгэхгүйн тулд
# - Streamlit дахин rerun хийх үед өмнөх үр дүнг санаж ашиглана.
@st.cache_data
def get_data():
    all_solutions = solve_n_queens(8)                     # нийт 92 шийдэл
    fundamentals = fundamental_solutions(all_solutions, 8)  # үндсэн 12 төлөөлөгч
    return all_solutions, fundamentals

all_solutions, fundamentals = get_data()

# ---------------- Sidebar controls ----------------
with st.sidebar:
    st.header("Тохиргоо")

    # Харах горим: 92 эсвэл 12
    view_mode = st.radio("Харах төрөл", ["All solutions (92)", "Fundamental solutions (12)"])

    # Fundamental дээр "fundamental гэж юу вэ?" гэсэн тайлбар харуулах эсэх
    show_explain = st.checkbox("Тайлбар харуулах", value=True)

    # Fundamental дээр тусгай filter: зөвхөн orbit_size=4-ийг харуулах
    # (8 queens дээр ганц special fundamental байдаг)
    only_special = False
    if view_mode == "Fundamental solutions (12)":
        only_special = st.checkbox("Зөвхөн orbit_size=4 (special) харуулах", value=False)

    # Fundamental дээр orbit (симметр хувилбарууд)-ыг доор нь харуулах эсэх
    show_orbit = st.checkbox(
        "Orbit (симметр хувилбар) харуулах",
        value=True if view_mode == "Fundamental solutions (12)" else False
    )

    # Orbit жижиг хөлгийн cell хэмжээ
    orbit_cell = st.slider("Orbit-ийн cell хэмжээ", min_value=24, max_value=36, value=30, step=1)

# ---------------- Data selection based on view_mode ----------------
if view_mode == "All solutions (92)":
    # Энэ горимд data зөвхөн "rep" (нэг нэг шийдэл)
    data = [{"rep": s} for s in all_solutions]
else:
    # Энэ горимд data нь fundamentals list (rep + orbit гэх мэт)
    data = fundamentals
    if only_special:
        data = [d for d in data if d["orbit_size"] == 4]

total = len(data)
if total == 0:
    st.error("Filter-ийн үр дүн 0 боллоо.")
    st.stop()

# ---------------- Session index (navigator) ----------------
if "idx" not in st.session_state:
    st.session_state.idx = 0
if st.session_state.idx >= total:
    st.session_state.idx = 0

# ---------------- KPI row ----------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("All solutions", len(all_solutions))
k2.metric("Fundamental", len(fundamentals))
k3.metric("Board", "8×8")
k4.metric("Symmetry", "D4 (8 transforms)")

# ---------------- Navigator UI ----------------
nav1, nav2, nav3, nav4 = st.columns([1, 2, 1, 1])

with nav1:
    if st.button("⬅️ Prev", use_container_width=True):
        st.session_state.idx = (st.session_state.idx - 1) % total

with nav3:
    if st.button("Next ➡️", use_container_width=True):
        st.session_state.idx = (st.session_state.idx + 1) % total

with nav2:
    chosen = st.selectbox("Index", options=list(range(1, total + 1)), index=st.session_state.idx)
    st.session_state.idx = chosen - 1

with nav4:
    st.write(f"**{st.session_state.idx+1} / {total}**")

# ---------------- Current selected item ----------------
item = data[st.session_state.idx]
sol = item["rep"]

# ---------------- Main layout columns ----------------
left, right = st.columns([1.05, 1.0], gap="large")

# ============================================================
# 7) Зүүн тал — гол шийдлийг шатрын хөлөг дээр харуулах
# ============================================================
with left:
    # гарчиг
    title = f"Solution #{st.session_state.idx+1}" if view_mode == "All solutions (92)" else f"Fundamental #{st.session_state.idx+1}"
    st.subheader(title)

    # гол хөлгийн хэмжээ том байг
    main_cell = 52

    # components.v1.html ашиглан шатрын хөлөг html-ээ render хийнэ
    st.components.v1.html(chessboard_html(sol, 8, cell=main_cell), height=board_height(8, main_cell))

    # координат
    st.write("**Q байрлал (A1..H8):** " + ", ".join(pos_to_notation(sol)))

# ============================================================
# 8) Баруун тал — Fundamental дээр нэмэлт мэдээлэл + Orbit carousel
# ============================================================
with right:
    if view_mode == "Fundamental solutions (12)":
        st.subheader("Summary")

        # orbit_size: тухайн fundamental шийдэл хэдэн өвөрмөц симметр хувилбартай вэ?
        st.write(f"- **orbit_size:** `{item['orbit_size']}`")

        # count_in_all: энэ бүлэг нийт 92 дотор хэдэн шийдэлтэй тэнцүү вэ?
        st.write(f"- **class_count_in_all:** `{item['count_in_all']}`")

        # Тайбар хэсэг (хэрэглэгч сонгосон бол)
        if show_explain:
            st.info(
                "Fundamental solutions гэдэг нь симметр (эргүүлэх/тольдох)-ээр адил шийдлүүдийг нэг бүлэгт нэгтгэсэн хэлбэр.\n\n"
                "8 queens дээр:\n"
                "- ихэнх fundamental нь orbit_size=8\n"
                "- нэг special fundamental нь orbit_size=4\n\n"
                "Тиймээс 12×8=96 биш: **11×8 + 1×4 = 92**"
            )

        # Orbit харуулах (хэвтээ scroll)
        if show_orbit:
            st.markdown("## Orbit (симметр хувилбарууд)")
            st.caption(f"Нийт өвөрмөц хувилбар: {item['orbit_size']} — доорх хэсэг хэвтээ scroll-той.")

            variants = item["orbit"]

            # card-ууд багтахуйц height
            orbit_height = 620

            st.components.v1.html(
                orbit_scroll_html(variants, n=8, cell=orbit_cell),
                height=orbit_height,
                scrolling=False
            )

    else:
        st.subheader("Info")
        st.write("Энэ горимд 92 distinct шийдлийг тус бүрээр нь харуулж байна.")