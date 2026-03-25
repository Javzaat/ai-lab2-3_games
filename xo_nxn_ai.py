# xo_nxn_ai.py
# ============================================================
# XO (Tic-Tac-Toe) NxN — Streamlit Click UI + AI Opponent
# ------------------------------------------------------------
# Энэ програм нь:
#   1) N×N хэмжээтэй XO тоглоом (3x3, 5x5, 7x7 ... хүртэл)
#   2) Ялах нөхцөл K (дараалсан тэмдэг) тохируулгатай
#   3) 2 горимтой:
#        - Human vs Human (2 хүн ээлжилж тоглоно)
#        - Human vs AI (нэг хүн AI-тай тоглоно)
#   4) AI нь 3 түвшинтэй:
#        - Easy   : санамсаргүй нүүдэл
#        - Medium : heuristic (оноо тооцоолол) ашиглан хамгийн ашигтай нүүдэл
#        - Hard   : 2 алхмын урьдчилсан харалт (2-ply lookahead)
#
# Хэрхэн ажиллуулах вэ?
#   source .venv/bin/activate
#   python -m streamlit run xo_nxn_ai.py
# ============================================================

import streamlit as st
import random

# ============================================================
# 1) Туслах функцууд (Core helpers)
# ============================================================

def create_board(n):
    """
    n хэмжээтэй хоосон board үүсгэнэ.
    Board нь 2 хэмжээст массив (list of lists) байна.
    Нүд бүр эхлээд "" (хоосон) гэж хадгалагдана.
    """
    return [["" for _ in range(n)] for _ in range(n)]

def in_bounds(n, r, c):
    """
    (r, c) координат board-ийн хүрээнд багтаж байгаа эсэхийг шалгана.
    """
    return 0 <= r < n and 0 <= c < n

def is_full(board):
    """
    Board бүрэн дүүрсэн эсэх.
    Нэг ч хоосон "" нүд байхгүй бол True.
    """
    n = len(board)
    return all(board[r][c] != "" for r in range(n) for c in range(n))

def empty_cells(board):
    """
    Одоогоор хоосон байгаа бүх нүдийг (r,c) хэлбэрээр жагсааж буцаана.
    AI болон хүн нүүдэл хийхэд ашиглана.
    """
    n = len(board)
    return [(r, c) for r in range(n) for c in range(n) if board[r][c] == ""]

# ============================================================
# 2) Хожлын шалгалт (Winner detection)
# ============================================================

def find_winning_cells(board, player, k):
    """
    Тухайн player ("X" эсвэл "O") нь K дараалсан тэмдэг тавьж чадсан эсэхийг шалгана.
    Хэрвээ олдвол яг тэр K дараалсан нүднүүдийн координатыг буцаана.

    Дараах 4 чиглэлээр шалгана:
      (0,1)   = хэвтээ (→)
      (1,0)   = босоо (↓)
      (1,1)   = диагональ (↘)
      (1,-1)  = эсрэг диагональ (↙)
    """
    n = len(board)
    dirs = [(0,1), (1,0), (1,1), (1,-1)]

    for r in range(n):
        for c in range(n):
            if board[r][c] != player:
                continue

            for dr, dc in dirs:
                cells = [(r, c)]
                rr, cc = r + dr, c + dc

                while in_bounds(n, rr, cc) and board[rr][cc] == player:
                    cells.append((rr, cc))
                    if len(cells) == k:
                        return cells
                    rr += dr
                    cc += dc

    return None

def winner_of(board, k):
    """
    Board дээр хэн нэг нь хожсон эсэхийг шалгана.
    Буцаах утга:
      ("X", winning_cells) эсвэл ("O", winning_cells) эсвэл (None, None)
    """
    wX = find_winning_cells(board, "X", k)
    if wX:
        return "X", wX
    wO = find_winning_cells(board, "O", k)
    if wO:
        return "O", wO
    return None, None

# ============================================================
# 3) Heuristic scoring (AI-д оноо тооцоолох хэсэг)
# ============================================================

def lines_through_cell(n, r, c):
    """
    (r,c) нүдээр дайрч өнгөрөх бүх боломжит мөр/багана/диагональ шугамуудыг үүсгэнэ.
    Энэ нь heuristic_move_score дээр ашиглагдаж,
    тухайн нүүдэл нь хэдэн "боломжит ялалтын шугам" нээж байгааг тооцоолно.

    4 чиглэлээр бүрэн line үүсгэнэ:
      - хэвтээ
      - босоо
      - диагональ
      - эсрэг диагональ
    """
    dirs = [(0,1), (1,0), (1,1), (1,-1)]
    for dr, dc in dirs:
        # line-ийн эхлэл рүү ухрана
        rr, cc = r, c
        while in_bounds(n, rr - dr, cc - dc):
            rr -= dr
            cc -= dc

        # одоо урагш бүх line-г цуглуулна
        line = []
        while in_bounds(n, rr, cc):
            line.append((rr, cc))
            rr += dr
            cc += dc

        yield line

def heuristic_move_score(board, k, player, move):
    """
    Medium/Hard AI-д ашиглах "оноо тооцоолох" функц.

    Санаа:
      1) Төв рүү ойрхон нүүдэл -> илүү сайн (center_bonus)
      2) Ялах боломжтой "цонх" (k урттай хэсэг) олон нээж байгаа нүүдэл -> илүү сайн
         - Opponent тэмдэг орсон цонх бол хэрэггүй (blocked)
         - Өөрийн тэмдэг олон байх тусам сайн
    """
    n = len(board)
    r, c = move
    opp = "O" if player == "X" else "X"

    # --- төв рүү ойртох бонус ---
    center_r = (n - 1) / 2
    center_c = (n - 1) / 2
    # төвөөс холдох тусам оноо буурна (тэгэхээр сөрөг тоо нэмэгдэнэ)
    center_bonus = - (abs(r - center_r) + abs(c - center_c))

    # --- боломжит ялалтын шугамын оноо ---
    pot = 0
    for line in lines_through_cell(n, r, c):
        L = len(line)
        for i in range(0, L - k + 1):
            window = line[i:i+k]
            vals = [board[rr][cc] for rr, cc in window]

            # opponent тэмдэг байгаа бол энэ window ашиггүй
            if opp in vals:
                continue

            # тухайн window дотор өөрийн тэмдэг хэд байна?
            ours = vals.count(player)
            empties = vals.count("")

            # энэ window бидний тавих (r,c)-г агуулж байвал л тооцно
            if (r, c) not in window:
                continue

            # Өөрийн тэмдэг олон байх тусам +10-оор өсгөнө
            # empties нэмснээр нээлттэй window-г бас дэмжиж өгнө
            pot += (ours + 1) * 10 + empties

    return pot + center_bonus

# ============================================================
# 4) AI нүүдэл сонгох (Easy/Medium/Hard)
# ============================================================

def choose_ai_move(board, k, difficulty, ai_player):
    """
    AI нүүдлийг difficulty-гээс хамаарч сонгоно.

    Easy:
      - Санамсаргүй хоосон нүд сонгоно.

    Medium:
      - (1) шууд хожих нүүдэл байвал тэрийг хийнэ
      - (2) өрсөлдөгч шууд хожих гэж байвал хаана
      - (3) heuristic_move_score хамгийн өндөр нүүдлийг сонгоно

    Hard:
      - Medium-ийн 1,2-г эхлээд хийж үзнэ
      - Дараа нь 2 алхам урьдчилж харна:
        AI нүүдэл хийсний дараа opponent хамгийн сайн хариу нүүдэл хийнэ гэж үзээд
        AI өөрийн ашиг (heuristic) - opponent ашиг гэсэн үнэлгээг хамгийн их болгоно.
    """
    n = len(board)
    opp = "O" if ai_player == "X" else "X"
    empties = empty_cells(board)
    if not empties:
        return None

    # --- EASY: random ---
    if difficulty == "Easy":
        return random.choice(empties)

    # helper: шууд хожих нүүдэл хайх
    def find_immediate_win(p):
        for (r, c) in empties:
            board[r][c] = p
            w, _ = winner_of(board, k)
            board[r][c] = ""
            if w == p:
                return (r, c)
        return None

    # 1) AI шууд хожих боломжтой юу?
    win_now = find_immediate_win(ai_player)
    if win_now:
        return win_now

    # 2) Өрсөлдөгч шууд хожих гэж байна уу? тэгвэл блоклоно
    block = find_immediate_win(opp)
    if block:
        return block

    # --- MEDIUM: heuristic хамгийн өндөр оноотой нүүдэл ---
    if difficulty == "Medium":
        best = None
        best_score = -10**18
        for m in empties:
            s = heuristic_move_score(board, k, ai_player, m)
            if s > best_score:
                best_score = s
                best = m
        return best if best else random.choice(empties)

    # --- HARD: 2-ply lookahead ---
    best = None
    best_value = -10**18

    candidates = empties
    # Хэрвээ хоосон нүд их байвал гацахаас сэргийлж candidate-ийг багасгана
    if len(candidates) > 60:
        scored = sorted(candidates, key=lambda m: heuristic_move_score(board, k, ai_player, m), reverse=True)
        candidates = scored[:40]

    for m in candidates:
        r, c = m
        board[r][c] = ai_player

        # гэнэт хожих нөхцөл болсон байж болно
        w, _ = winner_of(board, k)
        if w == ai_player:
            board[r][c] = ""
            return m

        opp_empties = empty_cells(board)
        if not opp_empties:
            value = 0
        else:
            # opponent шууд хожих боломжтой юу?
            opp_win = None
            for om in opp_empties:
                rr, cc = om
                board[rr][cc] = opp
                ww, _ = winner_of(board, k)
                board[rr][cc] = ""
                if ww == opp:
                    opp_win = om
                    break

            if opp_win:
                value = -10**9  # AI-д маш муу (opponent win)
            else:
                # opponent heuristic хамгийн өндөр нүүдлээ сонгоно гэж үзнэ
                opp_best = max(opp_empties, key=lambda om: heuristic_move_score(board, k, opp, om))
                value = heuristic_move_score(board, k, ai_player, m) - heuristic_move_score(board, k, opp, opp_best)

        board[r][c] = ""

        if value > best_value:
            best_value = value
            best = m

    return best if best else random.choice(empties)

# ============================================================
# 5) Streamlit UI хэсэг
# ============================================================

st.set_page_config(page_title="XO (NxN) + AI", layout="centered")
st.title("XO (NxN) — Click UI + AI Opponent")

# ---------------- Sidebar: тохиргоо ----------------
with st.sidebar:
    st.header("Тохиргоо")

    # N = board-ийн хэмжээ
    n = st.number_input("Хүснэгтийн хэмжээ N", min_value=3, max_value=15, value=5, step=1)
    # K = дараалсан тэмдэг (ялалтын нөхцөл)
    k = st.number_input("Ялах дарааллын урт K", min_value=3, max_value=int(n), value=4, step=1)

    mode = st.selectbox("Тоглох горим", ["Human vs Human", "Human vs AI"])
    difficulty = st.selectbox("AI хэцүү түвшин", ["Easy", "Medium", "Hard"]) if mode == "Human vs AI" else "—"
    human_mark = st.selectbox("Хүн аль нь вэ?", ["X (Эхэлнэ)", "O (Хоёр дахь)"]) if mode == "Human vs AI" else "—"

    # session_state-д тохиргооны хуучин утга хадгалах
    if "n" not in st.session_state:
        st.session_state.n = int(n)
        st.session_state.k = int(k)

    # Хэрвээ N/K өөрчлөгдвөл тоглоомыг reset хийнэ
    if int(n) != st.session_state.n or int(k) != st.session_state.k:
        st.session_state.n = int(n)
        st.session_state.k = int(k)
        st.session_state.board = create_board(st.session_state.n)
        st.session_state.current = "X"
        st.session_state.game_over = False
        st.session_state.win = []
        st.session_state.msg = ""

# ---------------- session defaults ----------------
if "scores" not in st.session_state:
    st.session_state.scores = {"X": 0, "O": 0, "D": 0}  # D = draw
if "board" not in st.session_state:
    st.session_state.board = create_board(st.session_state.n)
if "current" not in st.session_state:
    st.session_state.current = "X"
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "win" not in st.session_state:
    st.session_state.win = []
if "msg" not in st.session_state:
    st.session_state.msg = ""

def reset_round():
    """
    Нэг тоглолтыг шинээр эхлүүлэх (score хэвээр үлдэнэ).
    """
    st.session_state.board = create_board(st.session_state.n)
    st.session_state.current = "X"
    st.session_state.game_over = False
    st.session_state.win = []
    st.session_state.msg = ""

# ---------------- scoreboard ----------------
c1, c2, c3 = st.columns(3)
c1.metric("X", st.session_state.scores["X"])
c2.metric("O", st.session_state.scores["O"])
c3.metric("Тэнцээ", st.session_state.scores["D"])

# ---------------- controls ----------------
b1, b2 = st.columns(2)
if b1.button("Шинээр эхлэх"):
    reset_round()
if b2.button("Score reset"):
    st.session_state.scores = {"X": 0, "O": 0, "D": 0}
    reset_round()

# ---------------- mode: human/AI тэмдэг сонгох ----------------
if mode == "Human vs AI":
    human = "X" if human_mark.startswith("X") else "O"
    ai = "O" if human == "X" else "X"
else:
    human = None
    ai = None

st.write(f"**N={st.session_state.n}**, **K={st.session_state.k}**   |   **Одоо тоглох:** `{st.session_state.current}`")
if mode == "Human vs AI":
    st.caption(f"Горим: Human vs AI  |  Хүн = {human}, AI = {ai}  |  Түвшин = {difficulty}")

win_set = set(st.session_state.win)

def finish_game(msg):
    """
    Тоглоом дуусах үед game_over=True болгож, дэлгэцэнд харуулах мессеж хадгална.
    """
    st.session_state.game_over = True
    st.session_state.msg = msg

def apply_move(r, c, player):
    """
    Нэг нүүдэл хийх:
      - board[r][c] = player
      - winner эсэх шалгах
      - draw эсэх шалгах
      - үргэлжилбэл current-ийг сольж өгнө
    """
    st.session_state.board[r][c] = player

    w, cells = winner_of(st.session_state.board, st.session_state.k)
    if w:
        st.session_state.win = cells
        st.session_state.scores[w] += 1
        finish_game(f"🏆 {w} хожлоо!")
        return

    if is_full(st.session_state.board):
        st.session_state.scores["D"] += 1
        finish_game("🤝 Тэнцлээ!")
        return

    st.session_state.current = "O" if st.session_state.current == "X" else "X"

def maybe_ai_move():
    """
    Хэрвээ AI-ийн ээлж бол AI нүүдэл хийлгэнэ.
    """
    if mode != "Human vs AI":
        return
    if st.session_state.game_over:
        return
    if st.session_state.current != ai:
        return

    move = choose_ai_move(st.session_state.board, st.session_state.k, difficulty, ai)
    if move is None:
        return
    r, c = move
    apply_move(r, c, ai)

# ---------------- AI starts case (human=O) ----------------
# Хэрвээ хүн O сонгосон бол AI эхэлнэ → эхний нүүдлийг автоматаар хийнэ
if mode == "Human vs AI" and not st.session_state.game_over and st.session_state.current == ai:
    # board хоосон үед л эхний AI move хийнэ
    if all(st.session_state.board[r][c] == "" for r in range(st.session_state.n) for c in range(st.session_state.n)):
        maybe_ai_move()
        st.rerun()

# ============================================================
# 6) Board-г render хийх (Click UI)
# ============================================================
for r in range(st.session_state.n):
    cols = st.columns(st.session_state.n)
    for c in range(st.session_state.n):
        # Нүд дээр харагдах тэмдэг
        label = st.session_state.board[r][c] if st.session_state.board[r][c] else " "

        # Хожлын мөрөнд багтсан бол ✅ нэмээд тодруулна
        if (r, c) in win_set and label.strip():
            label = f"✅ {label}"

        # Нүд дүүрсэн эсвэл тоглоом дууссан бол дарж болохгүй
        disabled = st.session_state.game_over or st.session_state.board[r][c] != ""

        # Human vs AI үед AI-ийн ээлж бол хүнийг даруулахгүй
        if mode == "Human vs AI" and st.session_state.current == ai:
            disabled = True

        # Click event
        if cols[c].button(label, key=f"cell_{r}_{c}", disabled=disabled):
            if mode == "Human vs AI":
                # Хүний нүүдэл
                if st.session_state.current != human:
                    st.warning("Одоогоор AI-ийн ээлж байна.")
                else:
                    apply_move(r, c, human)
                    # хүний дараа тоглоом дуусаагүй бол AI хөдөлнө
                    if not st.session_state.game_over:
                        maybe_ai_move()
                    st.rerun()
            else:
                # Human vs Human үед current-ээр нүүдэл хийнэ
                apply_move(r, c, st.session_state.current)
                st.rerun()

# Эцсийн мессеж
if st.session_state.msg:
    st.success(st.session_state.msg)