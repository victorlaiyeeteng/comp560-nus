# TODO: Optimize Ultimate Tic-Tac-Toe AI
# Suggestions:
# 1. Replace naive nested lists with bitboard representation for speed.
# 2. Add transposition table (Zobrist hashing) to cache evaluated positions.
# 3. Implement move ordering: try winning/capturing moves first, use killer moves & history heuristics.
# 4. Consider shallow Monte Carlo Tree Search (MCTS) or hybrid Minimax+MCTS for better play.
# 5. Enhance evaluation:
#    - Add threat stacking: count one-in-a-row, two-in-a-row, and three-in-a-row potentials.
#    - Factor mobility: number of legal moves.
#    - Incorporate strategic patterns: opposite corner responses, edge plays.
# 6. Use Principal Variation Search (NegaScout) to tighten alpha-beta bounds.
# 7. Tune weights with self-play: use reinforcement learning or hill-climbing.

import sys
import time
from typing import List, Tuple, Optional

INF = 10_000_000
MAX_DEPTH = 10  # Depth limit for minimax search (increased for deeper lookahead)

# Player constants
ME: int = 1
OPP: int = -1
EMPTY: int = 0

# -------------------------------------------------------------------
# Utility functions for mapping between global cells and local boards
# -------------------------------------------------------------------


def board_index(row: int, col: int) -> int:
    return (row // 3) * 3 + (col // 3)


def cell_coords(idx: int) -> Tuple[int, int]:
    return (idx // 3, idx % 3)


class State:
    """
    Represents the full Ultimate Tic-Tac-Toe state:
    - 9 local 3×3 boards
    - Each board's winner
    - Global winner
    - Next forced board index for send-control (None means any)
    """

    def __init__(self) -> None:
        self.boards: List[List[List[int]]] = [
            [[EMPTY] * 3 for _ in range(3)] for _ in range(9)
        ]
        self.local_winner: List[int] = [EMPTY] * 9
        self.global_winner: int = EMPTY
        self.next_board: Optional[int] = None

    def clone(self) -> "State":
        st = State()
        st.boards = [[row[:] for row in b] for b in self.boards]
        st.local_winner = self.local_winner[:]
        st.global_winner = self.global_winner
        st.next_board = self.next_board
        return st

    def apply_move(self, move: Tuple[int, int], player: int) -> None:
        r, c = move
        bi = board_index(r, c)
        lr, lc = r % 3, c % 3
        self.boards[bi][lr][lc] = player

        if self.local_winner[bi] == EMPTY:
            w = check_3x3_winner(self.boards[bi])
            self.local_winner[bi] = w

        global_grid = [
            [self.local_winner[i * 3 + j] for j in range(3)] for i in range(3)
        ]
        self.global_winner = check_3x3_winner(global_grid)

        target = board_index(r, c)
        self.next_board = target if self.local_winner[target] == EMPTY else None

    def legal_moves(self) -> List[Tuple[int, int]]:
        moves: List[Tuple[int, int]] = []

        def add_from_board(bi: int) -> None:
            for lr in range(3):
                for lc in range(3):
                    if self.boards[bi][lr][lc] == EMPTY:
                        gr = (bi // 3) * 3 + lr
                        gc = (bi % 3) * 3 + lc
                        moves.append((gr, gc))

        if self.next_board is not None and self.local_winner[self.next_board] == EMPTY:
            add_from_board(self.next_board)
        else:
            for bi in range(9):
                if self.local_winner[bi] == EMPTY:
                    add_from_board(bi)
        return moves


def check_3x3_winner(grid: List[List[int]]) -> int:
    for i in range(3):
        if grid[i][0] != EMPTY and grid[i][0] == grid[i][1] == grid[i][2]:
            return grid[i][0]
        if grid[0][i] != EMPTY and grid[0][i] == grid[1][i] == grid[2][i]:
            return grid[0][i]
    if grid[0][0] != EMPTY and grid[0][0] == grid[1][1] == grid[2][2]:
        return grid[0][0]
    if grid[0][2] != EMPTY and grid[0][2] == grid[1][1] == grid[2][0]:
        return grid[0][2]
    for row in grid:
        if EMPTY in row:
            return EMPTY
    return 2


def count_two_in_rows(grid: List[List[int]], player: int) -> int:
    cnt = 0
    lines = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]
    for line in lines:
        vals = [grid[r][c] for r, c in line]
        if vals.count(player) == 2 and vals.count(EMPTY) == 1:
            cnt += 1
    return cnt


def evaluate(state: State) -> int:
    if state.global_winner == ME:
        return INF
    if state.global_winner == OPP:
        return -INF

    score = 0
    global_grid = [[state.local_winner[i * 3 + j] for j in range(3)] for i in range(3)]
    score += 500 * (
        count_two_in_rows(global_grid, ME) - count_two_in_rows(global_grid, OPP)
    )

    for bi in range(9):
        winner = state.local_winner[bi]
        weight = 3 if bi == 4 else (2 if bi in {0, 2, 6, 8} else 1)

        if winner == ME:
            score += 100 * weight
        elif winner == OPP:
            score -= 100 * weight
        else:
            mini = state.boards[bi]
            score += 10 * (count_two_in_rows(mini, ME) - count_two_in_rows(mini, OPP))
            moves_played = sum(1 for row in mini for cell in row if cell != EMPTY)

            if mini[1][1] == ME and moves_played > 1:
                score += 3
            elif mini[1][1] == OPP and moves_played > 1:
                score -= 3

            for r, c in [(0, 0), (0, 2), (2, 0), (2, 2)]:
                if mini[r][c] == ME:
                    score += 1
                elif mini[r][c] == OPP:
                    score -= 1
    return score


def minimax(state: State, depth: int, maximizing: bool, alpha: int, beta: int) -> int:
    if depth == 0 or state.global_winner != EMPTY:
        return evaluate(state)
    moves = state.legal_moves()
    if not moves:
        return 0
    if maximizing:
        value = -INF
        for mv in moves:
            child = state.clone()
            child.apply_move(mv, ME)
            value = max(value, minimax(child, depth - 1, False, alpha, beta))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = INF
        for mv in moves:
            child = state.clone()
            child.apply_move(mv, OPP)
            value = min(value, minimax(child, depth - 1, True, alpha, beta))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


# —— Main game loop ——
state = State()
is_first_move = True
while True:
    orow, ocol = map(int, sys.stdin.readline().split())
    if orow != -1:
        state.apply_move((orow, ocol), OPP)

    # Determine per-move time limit (slightly under thresholds)
    time_limit = 0.98 if is_first_move else 0.090
    is_first_move = False

    valid_count = int(sys.stdin.readline())
    valid_moves: List[Tuple[int, int]] = [
        tuple(map(int, sys.stdin.readline().split())) for _ in range(valid_count)
    ]

    best_move = valid_moves[0]
    best_val = -INF
    start_time = time.time()
    last_completed_depth = 0

    for depth in range(1, MAX_DEPTH + 1):
        current_best, current_best_val = best_move, best_val

        for mv in valid_moves:
            if time.time() - start_time > time_limit:
                sys.stderr.write(f"Cutoff at depth {depth}\n")
                break

            child = state.clone()
            child.apply_move(mv, ME)
            val = minimax(child, depth - 1, False, -INF, INF)

            if val > current_best_val:
                current_best_val, current_best = val, mv
        else:
            best_move, best_val = current_best, current_best_val
            last_completed_depth = depth
            continue

        break

    if last_completed_depth == MAX_DEPTH:
        sys.stderr.write(f"Completed all depths up to {MAX_DEPTH}\n")

    state.apply_move(best_move, ME)
    print(f"{best_move[0]} {best_move[1]}", flush=True)
