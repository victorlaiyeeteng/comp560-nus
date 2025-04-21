# Ultimate Tic-Tac-Toe game
import sys
import time
from typing import List, Tuple, Optional

INF = 10_000_000
MAX_DEPTH = 3  # Depth limit for minimax search

# Player constants
ME: int = 1
OPP: int = -1
EMPTY: int = 0

# Utility functions for mapping between global cells and local board indices


def board_index(row: int, col: int) -> int:
    """
    Compute the index (0..8) of the 3×3 local board containing global cell (row, col).
    """
    return (row // 3) * 3 + (col // 3)


def cell_coords(idx: int) -> Tuple[int, int]:
    """
    Convert a local-board index (0..8) back to its top-left global row/col in the 3×3 grid of boards.
    """
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
        # 9 local boards, each a 3×3 grid of EMPTY/ME/OPP
        self.boards: List[List[List[int]]] = [
            [[EMPTY] * 3 for _ in range(3)] for _ in range(9)
        ]
        # Winner of each local board (EMPTY, ME, OPP, or 2 for tie)
        self.local_winner: List[int] = [EMPTY] * 9
        # Overall global winner (EMPTY, ME, OPP, or 2 for global tie)
        self.global_winner: int = EMPTY
        # Send-control: index (0..8) of the board the next player must play in; None means free choice
        self.next_board: Optional[int] = None

    def clone(self) -> "State":
        """Return a deep copy of this state, including send-control."""
        st = State()
        st.boards = [[row[:] for row in b] for b in self.boards]
        st.local_winner = self.local_winner[:]
        st.global_winner = self.global_winner
        st.next_board = self.next_board
        return st

    def apply_move(self, move: Tuple[int, int], player: int) -> None:
        """
        Apply a move for `player` at global coordinates (row, col). Updates:
         - the appropriate local board cell
         - local board winner
         - global winner
         - next_board for send-control
        """
        r, c = move
        bi = board_index(r, c)
        lr, lc = r % 3, c % 3
        self.boards[bi][lr][lc] = player

        # 1) Update local board winner if undecided
        if self.local_winner[bi] == EMPTY:
            w = check_3x3_winner(self.boards[bi])
            self.local_winner[bi] = w

        # 2) Update global winner by treating local_winner as 3×3 grid
        global_grid = [
            [self.local_winner[i * 3 + j] for j in range(3)] for i in range(3)
        ]
        self.global_winner = check_3x3_winner(global_grid)

        # 3) Send-control: determine next_board
        # If the target local board is still playable, force it; else free choice
        target = board_index(r, c)
        if self.local_winner[target] == EMPTY:
            self.next_board = target
        else:
            self.next_board = None

    def legal_moves(self) -> List[Tuple[int, int]]:
        """
        Return all legal moves respecting send-control:
        - If next_board is set and unfinished, only cells in that board
        - Otherwise any cell in any unfinished board
        """
        moves: List[Tuple[int, int]] = []

        # Helper to add empties from a specific board
        def add_from_board(bi: int) -> None:
            for lr in range(3):
                for lc in range(3):
                    if self.boards[bi][lr][lc] == EMPTY:
                        gr = (bi // 3) * 3 + lr
                        gc = (bi % 3) * 3 + lc
                        moves.append((gr, gc))

        if self.next_board is not None and self.local_winner[self.next_board] == EMPTY:
            # Forced board
            add_from_board(self.next_board)
        else:
            # Any unfinished board
            for bi in range(9):
                if self.local_winner[bi] == EMPTY:
                    add_from_board(bi)
        return moves


def check_3x3_winner(grid: List[List[int]]) -> int:
    """
    Check a single 3×3 grid for a winner:
     - Returns ME or OPP if three in a row
     - Returns EMPTY if still playable (empty cell exists)
     - Returns 2 for a full tie (no empties, no winner)
    """
    # Rows & columns
    for i in range(3):
        if grid[i][0] != EMPTY and grid[i][0] == grid[i][1] == grid[i][2]:
            return grid[i][0]
        if grid[0][i] != EMPTY and grid[0][i] == grid[1][i] == grid[2][i]:
            return grid[0][i]
    # Diagonals
    if grid[0][0] != EMPTY and grid[0][0] == grid[1][1] == grid[2][2]:
        return grid[0][0]
    if grid[0][2] != EMPTY and grid[0][2] == grid[1][1] == grid[2][0]:
        return grid[0][2]
    # Any empties?
    for row in grid:
        if EMPTY in row:
            return EMPTY
    # Tie
    return 2


def count_two_in_rows(grid: List[List[int]], player: int) -> int:
    """
    Count lines (rows, cols, diags) in `grid` where `player` has exactly two marks and one empty.
    Used for heuristic (threat/opportunity counts).
    """
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
    """
    Heuristic evaluation combining global and local board features:

    1. Terminal: global win/loss → ±INF
    2. Global two-in-a-rows → forks (+) and threats (-)
    3. Local boards:
       • Completed: add/subtract weighted scores by position (center>corners>edges)
       • Unfinished: local two-in-a-rows, center control, corner control
    """
    # 1. Check for global terminal
    if state.global_winner == ME:
        return +INF
    if state.global_winner == OPP:
        return -INF

    score = 0
    # 2. Global two-in-a-rows on the 3×3 of local winners
    global_grid = [[state.local_winner[i * 3 + j] for j in range(3)] for i in range(3)]
    score += 500 * (
        count_two_in_rows(global_grid, ME) - count_two_in_rows(global_grid, OPP)
    )

    # 3. Local boards contribution
    for bi in range(9):
        winner = state.local_winner[bi]
        # Weight by board position: center=3×, corners=2×, edges=1×
        weight = 3 if bi == 4 else (2 if bi in {0, 2, 6, 8} else 1)

        if winner == ME:
            score += 100 * weight
        elif winner == OPP:
            score -= 100 * weight
        else:
            mini = state.boards[bi]
            # a) local two-in-rows
            score += 10 * (count_two_in_rows(mini, ME) - count_two_in_rows(mini, OPP))
            # b) center control
            if mini[1][1] == ME:
                score += 3
            elif mini[1][1] == OPP:
                score -= 3
            # c) corner control
            for r, c in [(0, 0), (0, 2), (2, 0), (2, 2)]:
                if mini[r][c] == ME:
                    score += 1
                elif mini[r][c] == OPP:
                    score -= 1

    return score


def minimax(state: State, depth: int, maximizing: bool, alpha: int, beta: int) -> int:
    """
    Depth-limited minimax with alpha-beta pruning under send-control constraints.
    """
    # Terminal or depth cutoff
    if depth == 0 or state.global_winner != EMPTY:
        return evaluate(state)

    moves = state.legal_moves()
    if not moves:
        # No legal moves → draw
        return 0

    if maximizing:
        value = -INF
        for mv in moves:
            child = state.clone()
            child.apply_move(mv, ME)
            value = max(value, minimax(child, depth - 1, False, alpha, beta))
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # β-cutoff
        return value
    else:
        value = +INF
        for mv in moves:
            child = state.clone()
            child.apply_move(mv, OPP)
            value = min(value, minimax(child, depth - 1, True, alpha, beta))
            beta = min(beta, value)
            if beta <= alpha:
                break  # α-cutoff
        return value


# —— Main game loop ——
state = State()
is_first_move = True

while True:
    # Read opponent move (-1 -1 for first turn)
    orow, ocol = map(int, sys.stdin.readline().split())
    if orow != -1:
        state.apply_move((orow, ocol), OPP)

    # Determine per‐move time limit
    time_limit = 1.0 if is_first_move else 0.1
    is_first_move = False

    # Read valid moves under send-control
    valid_count = int(sys.stdin.readline())
    valid_moves: List[Tuple[int, int]] = [
        tuple(map(int, sys.stdin.readline().split())) for _ in range(valid_count)
    ]

    # Iterative deepening
    best_move = valid_moves[0]
    best_val = -INF
    start_time = time.time()
    last_completed_depth = 0

    for depth in range(1, MAX_DEPTH + 1):
        current_best, current_best_val = best_move, best_val

        for mv in valid_moves:
            # Check time before each new child
            if time.time() - start_time > time_limit:
                # cutoff: report the depth we just *started*
                sys.stderr.write(f"Cutoff at depth {depth}\n")
                break

            child = state.clone()
            child.apply_move(mv, ME)
            # note: we search depth-1 because apply_move used up one ply
            val = minimax(child, depth - 1, False, -INF, INF)

            if val > current_best_val:
                current_best_val, current_best = val, mv

        else:
            # only if inner loop did *not* break
            best_move, best_val = current_best, current_best_val
            last_completed_depth = depth
            continue

        # we broke due to time; stop deepening
        break

    # If we ever finish all depths without a time‐break, report that too
    if last_completed_depth == MAX_DEPTH:
        sys.stderr.write(f"Completed all depths up to {MAX_DEPTH}\n")

    # Apply and output the best move found
    state.apply_move(best_move, ME)
    print(f"{best_move[0]} {best_move[1]}", flush=True)
