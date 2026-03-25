# puzzle_app.py
# ============================================================
# 8-Puzzle (3x3) + Agent (A*) — Chess-style UI (beige/green) + Solution carousel
# ------------------------------------------------------------
# Энэ програм нь 3×3 хэмжээтэй "8-Puzzle" тоглоомыг Streamlit дээр ажиллуулна.
#
# Тоглоомын зорилго:
#   - 1..8 тоонууд болон 0 (хоосон нүд)-ийг зөв байрлалд хүргэх.
#   - 0 (хоосон нүд)-тэй зэргэлдээ байгаа тоон дээр дарж солих замаар хөдөлнө.
#
# Гол боломжууд:
#   1) Tile дээр дараад хөдөлгөх (arrow товч хэрэггүй).
#   2) Scramble: solvable төлөв үүсгэж хутгах.
#   3) Agent: A* search + Manhattan heuristic ашиглаж автоматаар шийдэх.
#   4) Playback: Start / Next / Auto / Stop.
#   5) Solution path carousel: олсон бүх төлвүүдийг хэвтээ scroll-оор харуулах.
#
# Хэрхэн ажиллуулах вэ?
#   source .venv/bin/activate
#   python -m streamlit run puzzle_app.py
# ============================================================

import streamlit as st          # Streamlit UI framework (вэб интерфэйс хийх)
import random                   # санамсаргүй сонголт/хутгалт хийх
import time                     # auto-play үед жижиг delay хийх
import heapq                    # A* priority queue (min-heap) хэрэглэх

# ============================================================
# 1) Puzzle-ийн суурь тогтмолууд (constants)
# ============================================================

N = 3
# N=3 гэдэг нь 3×3 хүснэгт гэсэн үг. 8-puzzle стандарт хэмжээ нь энэ.

GOAL = (1, 2, 3,
        4, 5, 6,
        7, 8, 0)
# GOAL = зорилтот төлөв.
# 0 нь хоосон нүд (blank) гэсэн тэмдэглэгээ.

# ============================================================
# 2) Puzzle-ийн туслах функцууд (helpers)
# ============================================================

def to_grid(state):
    """
    1 хэмжээст tuple/list state-ийг 2 хэмжээст хүснэгт (grid) болгоно.
    Жишээ:
      state = (1,2,3,4,5,6,7,8,0)
      -> [[1,2,3],[4,5,6],[7,8,0]]
    """
    return [list(state[i * N:(i + 1) * N]) for i in range(N)]

def find_zero(state):
    """
    state доторх 0 (хоосон нүд)-ийн байрлалыг (row, col) хэлбэрээр олно.
    """
    i = state.index(0)       # 0-ийн index
    return i // N, i % N     # index-ийг мөр/багана руу хувиргана

def adjacent(a, b):
    """
    Хоёр координат (r,c) зэргэлдээ эсэхийг шалгана.
    Зэргэлдээ = Манхэттэн зай 1 (дээш/доош/зүүн/баруун).
    """
    (r1, c1), (r2, c2) = a, b
    return abs(r1 - r2) + abs(c1 - c2) == 1

def swap_positions(state, r1, c1, r2, c2):
    """
    state дээрх (r1,c1) ба (r2,c2) хоёр нүдний утгыг сольж шинэ state буцаана.
    Энэ нь 'нүүдэл хийх' үндсэн үйлдэл юм.
    """
    lst = list(state)                  # tuple-г list болгож өөрчлөх боломжтой болгоно
    i1, i2 = r1 * N + c1, r2 * N + c2  # 2 хэмжээст координатыг 1 хэмжээст index болгоно
    lst[i1], lst[i2] = lst[i2], lst[i1]
    return tuple(lst)                  # буцаад tuple болгоно (hashable байх давуу талтай)

def neighbors(state):
    """
    Тухайн state-ээс нэг алхамд хүрч болох бүх хөрш төлвүүдийг олно.
    Үндсэн санаа:
      - зөвхөн 0 (хоосон нүд) хөдөлнө гэж үзнэ
      - 0 нь дээш/доош/зүүн/баруун тийш шилжиж болно (хэрвээ хүрээнээс гарахгүй)
    Буцаах хэлбэр:
      [(next_state, "U/D/L/R"), ...]
      action нь 0 (blank) хэрхэн хөдөлснийг тэмдэглэнэ.
    """
    r, c = find_zero(state)
    out = []

    # 0 дээш шилжих боломжтой юу? (r>0)
    if r > 0:
        out.append((swap_positions(state, r, c, r - 1, c), "U"))
    # 0 доош шилжих боломжтой юу? (r < N-1)
    if r < N - 1:
        out.append((swap_positions(state, r, c, r + 1, c), "D"))
    # 0 зүүн тийш шилжих боломжтой юу? (c>0)
    if c > 0:
        out.append((swap_positions(state, r, c, r, c - 1), "L"))
    # 0 баруун тийш шилжих боломжтой юу? (c < N-1)
    if c < N - 1:
        out.append((swap_positions(state, r, c, r, c + 1), "R"))

    return out

def manhattan(state):
    """
    Manhattan heuristic:
      - 1..8 тоо бүр зорилтот байрлалаасаа хэдэн алхам хол байгааг тооцоод нийлбэрлэнэ.
      - 0 (blank)-ийг тооцохгүй.
    Энэ heuristic нь A* дээр түгээмэл бөгөөд "ихэнхдээ богино зам" олдог.
    """
    dist = 0
    for idx, tile in enumerate(state):
        if tile == 0:
            continue  # blank тооцохгүй
        goal_idx = tile - 1           # tile=1 бол goal index=0 гэх мэт
        r1, c1 = idx // N, idx % N    # одоогийн байрлал
        r2, c2 = goal_idx // N, goal_idx % N  # зорилтот байрлал
        dist += abs(r1 - r2) + abs(c1 - c2)
    return dist

def is_solvable(state):
    """
    8-puzzle solvable эсэхийг inversion parity-гаар шалгана (3×3 дээр).
    0-г хассан дараалалд:
      - inversion тоо тэгш байвал solvable
      - inversion тоо сондгой байвал unsolvable
    """
    arr = [x for x in state if x != 0]
    inv = 0
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                inv += 1
    return inv % 2 == 0

def random_solvable(scramble_moves=25):
    """
    Solvable төлөв үүсгэх хамгийн найдвартай арга:
      - GOAL-оос эхлээд санамсаргүй зөв хөдөлгөөнөөр N алхам хутгана.
      - Ингэснээр 100% solvable хэвээр байна (учир нь буцааж л хөдөлсөн гэсэн үг).
    prev ашигласнаар:
      - яг өмнөх төлөв рүү шууд буцаад явах (undo) магадлалыг багасгана.
    """
    s = GOAL
    prev = None

    for _ in range(scramble_moves):
        nxts = neighbors(s)

        # шууд буцах хөдөлгөөнийг багасгах (боломжтой бол)
        if prev is not None:
            nxts2 = [x for x in nxts if x[0] != prev]
            if nxts2:
                nxts = nxts2

        ns, _ = random.choice(nxts)
        prev, s = s, ns

    return s

def apply_tile_click(state, r, c):
    """
    Хэрэглэгч нэг тоон дээр дарсан үед:
      - хэрвээ тэр тоо 0 (blank)-тэй зэргэлдээ байвал:
          -> swap хийж шинэ state буцаана (ok=True)
      - үгүй бол:
          -> өөрчлөхгүй (ok=False)
    """
    zr, zc = find_zero(state)
    if not adjacent((r, c), (zr, zc)):
        return state, False
    return swap_positions(state, r, c, zr, zc), True

# ============================================================
# 3) Agent — A* Search алгоритм
# ============================================================

def astar(start, max_expand=200000):
    """
    A* search:
      f(n) = g(n) + h(n)
        - g(n) = эхлэлээс одоогийн төлөв хүртэлх алхмын тоо
        - h(n) = heuristic (энд Manhattan)
    Priority queue (heapq) ашиглаж хамгийн бага f-тэй төлвийг түрүүлж задлана.

    max_expand:
      - хэт хүнд асуудал дээр гацахаас сэргийлэх хамгаалалт.
      - expanded > max_expand бол зогсооно.

    Буцаах:
      states, actions, stats
        - states: [start, ..., goal] төлвүүдийн жагсаалт
        - actions: ["U","L",...] алхамын жагсаалт
        - stats: expanded тоо, цаг, solution_len
    """
    t0 = time.time()

    # эхлэл нь аль хэдийн GOAL бол шууд буцаана
    if start == GOAL:
        return [start], [], {"expanded": 0, "time_sec": 0.0, "solution_len": 0}

    # pq item: (f, g, state)
    pq = []
    g_cost = {start: 0}            # state -> хамгийн бага g
    parent = {start: None}         # state -> өмнөх state
    parent_action = {start: None}  # state -> түүнийг үүсгэсэн action

    heapq.heappush(pq, (manhattan(start), 0, start))
    expanded = 0

    while pq:
        f, g, s = heapq.heappop(pq)

        # stale entry хамгаалалт:
        # pq-д нэг state олон удаа орж магадгүй, хамгийн сайн g бишийг алгасна
        if g != g_cost.get(s, None):
            continue

        # зорилтод хүрсэн бол path сэргээнэ
        if s == GOAL:
            states, actions = [], []
            cur = s
            while cur is not None:
                states.append(cur)
                act = parent_action[cur]
                if act is not None:
                    actions.append(act)
                cur = parent[cur]
            states.reverse()
            actions.reverse()
            return states, actions, {
                "expanded": expanded,
                "time_sec": round(time.time() - t0, 4),
                "solution_len": len(actions),
            }

        expanded += 1
        if expanded > max_expand:
            break

        # хөршүүдийг задлана
        for ns, act in neighbors(s):
            ng = g + 1
            # хэрвээ шинэ зам (ng) өмнөхөөсөө сайн (бага) бол шинэчилнэ
            if ng < g_cost.get(ns, 10**18):
                g_cost[ns] = ng
                parent[ns] = s
                parent_action[ns] = act
                heapq.heappush(pq, (ng + manhattan(ns), ng, ns))

    # хүрч чадаагүй (эсвэл limit хүрсэн)
    return None, None, {
        "expanded": expanded,
        "time_sec": round(time.time() - t0, 4),
        "solution_len": None
    }

# ============================================================
# 4) UI — Гол board-ыг beige/green болгох CSS (Streamlit button styling)
# ============================================================

def inject_tile_css(cell=96):
    """
    Streamlit-ийн button-ууд default theme-ээс (заримдаа хар) хамаараад
    хүссэн өнгө гарахгүй байх асуудлыг CSS-ээр хүчээр засна.

    - Тайлтай нүдүүдийг beige (#eeeed2) болгоно
    - Хоосон tile (disabled) нүдийг green (#769656) болгоно
    """
    st.markdown(
        f"""
        <style>
        /* Main puzzle buttons (tile buttons) */
        div[data-testid="column"] button[kind="secondary"] {{
            height: {cell}px !important;
            width: {cell}px !important;
            border-radius: 10px !important;
            font-weight: 900 !important;
            font-size: {int(cell*0.35)}px !important;
            line-height: 1 !important;
            padding: 0 !important;

            background: #eeeed2 !important; /* beige */
            color: #111111 !important;

            border: 1px solid rgba(0,0,0,0.15) !important;
            box-shadow: 0 6px 18px rgba(0,0,0,0.12) !important;
        }}

        /* Hover үед бага зэрэг өөр өнгө */
        div[data-testid="column"] button[kind="secondary"]:hover {{
            background: #dfe6c3 !important;
            border-color: rgba(0,0,0,0.22) !important;
        }}

        /* Button доторх padding-ийг 0 болгоно */
        div[data-testid="column"] button[kind="secondary"] > div {{
            padding: 0 !important;
        }}

        /* Blank tile (disabled) -> green */
        div[data-testid="column"] button[kind="secondary"]:disabled {{
            background: #769656 !important; /* green */
            color: rgba(0,0,0,0.0) !important; /* текст нуух */
            border-color: rgba(0,0,0,0.15) !important;
            box-shadow: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# 5) Solution carousel — жижиг mini board-уудыг HTML/CSS-ээр зурна
# ============================================================

def state_mini_html(state, cell=26):
    """
    Нэг төлвийг жижиг 3×3 mini-board болгож HTML буцаана.
    - light/dark өнгө: beige/green
    - 0 бол хоосон
    """
    grid = to_grid(state)
    parts = []
    for r in range(N):
        for c in range(N):
            v = grid[r][c]
            txt = "" if v == 0 else str(v)
            cls = "dark" if (r + c) % 2 == 1 else "light"
            parts.append(f"""
              <div class="mcell {cls}" style="width:{cell}px; height:{cell}px;">
                <div class="mtile">{txt}</div>
              </div>
            """)
    return f"""
    <div class="mini-board-wrap">
      <div class="mgrid">{''.join(parts)}</div>
    </div>
    """

def path_carousel_html(states, current_idx, cell=26):
    """
    Agent олсон states жагсаалтыг card хэлбэрээр нэг мөрөнд байрлуулж,
    horizontal scroll (carousel) болгох HTML буцаана.

    current_idx:
      - аль алхам дээр явж байгааг highlight хийхэд ашиглана.
    """
    cards = []
    for i, s in enumerate(states):
        active = "active" if i == current_idx else ""
        cards.append(f"""
        <div class="pcard {active}">
          <div class="ptitle">#{i}</div>
          {state_mini_html(s, cell=cell)}
        </div>
        """)

    return f"""
    <style>
      .pscroll {{
        overflow-x: auto;
        overflow-y: hidden;
        white-space: nowrap;
        padding: 10px 8px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.03);
      }}

      .pcard {{
        display:inline-block;
        vertical-align:top;
        white-space: normal;
        width: 170px;
        margin-right: 14px;
      }}

      .ptitle {{
        font-weight: 800 !important;
        margin: 0 0 8px 0 !important;
        font-size: 13px !important;
        color: rgba(255,255,255,0.92) !important;
      }}

      /* mini board цагаан хайрцаг */
      .mini-board-wrap {{
        display: inline-block;
        padding: 10px;
        border-radius: 14px;
        background: #ffffff !important;
        border: 1px solid rgba(0,0,0,0.12) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12) !important;
      }}

      .mgrid {{
        display: grid;
        grid-template-columns: repeat(3, {cell}px);
        gap: 0px;
      }}

      .mcell {{
        display: flex;
        align-items: center;
        justify-content: center;
        user-select: none;
      }}

      /* force chess colors */
      .mcell.light {{ background: #eeeed2 !important; }}
      .mcell.dark  {{ background: #769656 !important; }}

      .mtile {{
        font-size: {int(cell*0.62)}px !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        color: #111111 !important;
      }}

      /* одоогийн алхам дээр outline тавьж тодруулна */
      .pcard.active .mini-board-wrap {{
        outline: 3px solid rgba(255,255,255,0.65);
        outline-offset: 2px;
      }}
    </style>

    <div class="pscroll">
      {''.join(cards)}
    </div>
    """

# ============================================================
# 6) Streamlit App — үндсэн UI болон session_state
# ============================================================

st.set_page_config(page_title="8-Puzzle + Agent", layout="wide")
st.title("Puzzle тоглоом (8-Puzzle) — Агент (A*) + Same UI")

# -------------------- Session init --------------------
# Streamlit нь UI interaction болгонд скриптийг дээрээс нь дахин ажиллуулдаг.
# Тиймээс тоглоомын төлөвийг st.session_state-д хадгалж "санах" хэрэгтэй.

if "state" not in st.session_state:
    st.session_state.state = random_solvable(25)   # эхний тоглолтын төлөв
if "solution_states" not in st.session_state:
    st.session_state.solution_states = []          # agent олсон states list
if "solution_actions" not in st.session_state:
    st.session_state.solution_actions = []         # agent олсон actions list
if "step_i" not in st.session_state:
    st.session_state.step_i = 0                    # playback дээрх одоогийн алхам
if "stats" not in st.session_state:
    st.session_state.stats = {}                    # expanded/time/len гэх мэт статистик
if "auto" not in st.session_state:
    st.session_state.auto = False                  # auto-play асаалттай эсэх

# ============================================================
# 7) Sidebar — тохиргоо, scramble, solve, auto-speed
# ============================================================

with st.sidebar:
    st.header("Тохиргоо")

    # scramble хэр их хутгах вэ (GOAL-оос хэд алхам санамсаргүй хөдөлгөх)
    scramble_k = st.slider("Scramble хэмжээ (move)", 5, 60, 25, 1)

    # UI дээрх нэг tile-ийн хэмжээ (button size)
    cell_size = st.slider("Хөлгийн хэмжээ (UI)", 70, 120, 96, 2)

    st.divider()
    st.subheader("Үйлдэл")

    # шинэ тоглоом: solvable scramble
    if st.button("🔀 Scramble (шинэ тоглоом)", use_container_width=True):
        st.session_state.state = random_solvable(scramble_k)
        st.session_state.solution_states = []
        st.session_state.solution_actions = []
        st.session_state.step_i = 0
        st.session_state.stats = {}
        st.session_state.auto = False
        st.rerun()

    # зорилтот төлөв рүү шууд тавих (test хийхэд хэрэгтэй)
    if st.button("🎯 Goal state (дууссан төлөв)", use_container_width=True):
        st.session_state.state = GOAL
        st.session_state.solution_states = []
        st.session_state.solution_actions = []
        st.session_state.step_i = 0
        st.session_state.stats = {}
        st.session_state.auto = False
        st.rerun()

    st.divider()
    st.subheader("Agent (A*)")

    # A* доторх expanded node-ийн limit
    max_expand = st.number_input(
        "Max expanded (хязгаар)",
        min_value=1000,
        max_value=500000,
        value=200000,
        step=1000
    )

    # solve товч: A* ажиллуулж solution гаргана
    if st.button("🤖 Solve with A*", use_container_width=True):
        start = st.session_state.state
        states, actions, stats = astar(start, max_expand=max_expand)
        st.session_state.stats = stats

        # шийдэл олдоогүй бол list-үүдийг цэвэрлэнэ
        if states is None:
            st.session_state.solution_states = []
            st.session_state.solution_actions = []
            st.session_state.step_i = 0
            st.session_state.auto = False
            st.error("Шийдэл олдсонгүй (хязгаар хүрсэн байж магадгүй).")
        else:
            st.session_state.solution_states = states
            st.session_state.solution_actions = actions
            st.session_state.step_i = 0
            st.session_state.auto = False
            st.success(f"Шийдэл олдлоо! Алхам: {stats['solution_len']}")

        st.rerun()

    # auto-play үед алхам хоорондын delay
    auto_speed = st.slider("Auto-play хурд (сек/алхам)", 0.05, 1.0, 0.25, 0.05)

# CSS-г одоогийн cell_size-д тааруулж шахна
inject_tile_css(cell=cell_size)

# ============================================================
# 8) Main layout — 2 багана (left=board, right=agent info)
# ============================================================

left, right = st.columns([1.05, 1.0], gap="large")

# ============================================================
# 9) Зүүн тал — Puzzle board (tile дээр дарж хөдөлгөнө)
# ============================================================

with left:
    st.subheader("Хөлөг (Tile дээр дарж хөдөлгөнө)")

    # Board-ийг white box болгож (Queens шиг) гоё харагдуулах
    st.markdown(
        """
        <div style="
            display:inline-block;
            padding:12px;
            border-radius:14px;
            background:#ffffff;
            border:1px solid rgba(0,0,0,0.12);
            box-shadow:0 6px 18px rgba(0,0,0,0.12);
        ">
        """,
        unsafe_allow_html=True
    )

    # state-ийг 2D grid болгож харуулна
    grid = to_grid(st.session_state.state)

    # 3×3-г Streamlit button-уудаар зурна
    for r in range(N):
        cols = st.columns(N, gap="small")
        for c in range(N):
            v = grid[r][c]
            label = "" if v == 0 else str(v)  # 0 бол хоосон
            disabled = (v == 0)              # 0 tile дээр дарж болохгүй

            # Хэрэглэгч тоон дээр дарвал:
            if cols[c].button(label if label else " ", key=f"tile_{r}_{c}", use_container_width=True, disabled=disabled):
                # зөвхөн blank-тэй зэргэлдээ бол swap хийнэ
                ns, ok = apply_tile_click(st.session_state.state, r, c)
                if ok:
                    st.session_state.state = ns

                    # Хэрэглэгч гараар хөдөлгөсөн тул өмнөх agent solution хүчингүй
                    st.session_state.solution_states = []
                    st.session_state.solution_actions = []
                    st.session_state.step_i = 0
                    st.session_state.auto = False

                    st.rerun()
                else:
                    st.warning("❌ Зөвхөн 0 (хоосон) нүдтэй зэргэлдээ тоо хөдөлнө.")

    # white box хаах
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Дүрэм: зөвхөн 0 (хоосон) нүдтэй зэргэлдээ байгаа тоог дарж сольж хөдөлгөнө.")

# ============================================================
# 10) Баруун тал — Agent мэдээлэл + playback + carousel
# ============================================================

with right:
    st.subheader("Summary / Agent playback")

    # KPI: heuristic, solvable, goal?
    k1, k2, k3 = st.columns(3)
    k1.metric("Heuristic (Manhattan)", manhattan(st.session_state.state))
    k2.metric("Solvable?", "Yes" if is_solvable(st.session_state.state) else "No")
    k3.metric("Is goal?", "Yes" if st.session_state.state == GOAL else "No")

    st.divider()

    # Хэрвээ agent шийдэл олсон бол playback/control гаргана
    if st.session_state.solution_states:
        stats = st.session_state.stats or {}

        st.markdown("### Agent result (A*)")

        # статистик
        c1, c2, c3 = st.columns(3)
        c1.metric("Solution length", stats.get("solution_len", "?"))
        c2.metric("Expanded nodes", stats.get("expanded", "?"))
        c3.metric("Time (sec)", stats.get("time_sec", "?"))

        st.markdown("### Playback controls")

        # playback товчнууд
        p1, p2, p3, p4 = st.columns(4)

        # эхлэл рүү буцаах
        if p1.button("⏮ Start", use_container_width=True):
            st.session_state.step_i = 0
            st.session_state.state = st.session_state.solution_states[0]
            st.session_state.auto = False
            st.rerun()

        # дараагийн алхам
        if p2.button("▶️ Next", use_container_width=True):
            i = st.session_state.step_i
            if i < len(st.session_state.solution_states) - 1:
                st.session_state.step_i += 1
                st.session_state.state = st.session_state.solution_states[st.session_state.step_i]
                st.session_state.auto = False
                st.rerun()

        # auto-play зогсоох
        if p3.button("⏸ Stop", use_container_width=True):
            st.session_state.auto = False
            st.rerun()

        # auto-play эхлүүлэх
        if p4.button("▶️ Auto", use_container_width=True):
            st.session_state.auto = True
            st.rerun()

        # одоогийн алхам/дараагийн үйлдлийг мэдээлэх
        i = st.session_state.step_i
        if i < len(st.session_state.solution_actions):
            st.info(f"Алхам: {i}/{len(st.session_state.solution_actions)} | Дараагийн үйлдэл: **{st.session_state.solution_actions[i]}**")
        else:
            st.success("Шийдэл дууссан (Goal reached) ✅")

        # Carousel: solution path
        st.markdown("### Solution path (carousel)")
        st.caption("Доорх нь Agent олсон төлвүүдийг chess-style box-оор (horizontal scroll) харуулна.")

        st.components.v1.html(
            path_carousel_html(st.session_state.solution_states, st.session_state.step_i, cell=26),
            height=240,
            scrolling=False
        )

        # Auto-play логик:
        # Streamlit дахин rerun хийх замаар алхам алхмаар урагшлуулна
        if st.session_state.auto:
            if st.session_state.step_i < len(st.session_state.solution_states) - 1:
                time.sleep(auto_speed)
                st.session_state.step_i += 1
                st.session_state.state = st.session_state.solution_states[st.session_state.step_i]
                st.rerun()
            else:
                st.session_state.auto = False
                st.rerun()

        # actions list-ийг дэлгэх боломж
        with st.expander("Алхамуудын жагсаалт (actions)"):
            st.write(" ".join(st.session_state.solution_actions))

    else:
        # agent solution байхгүй үед
        st.write("🤖 Agent шийдэл хараахан алга. Sidebar дээр **Solve with A\\*** дарж шийдүүлээрэй.")
        st.caption("Зөвлөмж: scramble их байх тусам шийдэх алхам урт болно. Max expanded-ийг өсгөж болно.")

# ============================================================
# 11) Доод тайлбар
# ============================================================

st.divider()
st.caption(
    "Agent тайлбар: Энэ puzzle дээр агент нь goal-based planning хийж, "
    "A* хайлтаар (Manhattan heuristic ашиглан) ихэнхдээ хамгийн богино замыг олдог."
)