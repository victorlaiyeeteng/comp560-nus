import sys
import math
import time
import random
import copy


# ----------------------------------------------------------------------
# Game State for Ultimate Tic‑Tac‑Toe
# ----------------------------------------------------------------------
class State:
    def __init__(self):
        # 9×9 board: 0=empty, 1=player1, -1=player2
        self.board = [[0] * 9 for _ in range(9)]
        # local board winners: 0=ongoing, 1 or -1 = won by
        self.local_winner = [[0] * 3 for _ in range(3)]
        # who plays next: 1 (us) or -1 (opp)
        self.next_player = 1
        # last move (r,c) or None
        self.last_move = None

    def copy(self):
        st = State()
        st.board = [row[:] for row in self.board]
        st.local_winner = [row[:] for row in self.local_winner]
        st.next_player = self.next_player
        st.last_move = self.last_move
        return st

    def get_valid_moves(self):
        if self.last_move is None:
            return [(r, c) for r in range(9) for c in range(9) if self.board[r][c] == 0]
        lr, lc = self.last_move
        br, bc = lr % 3, lc % 3
        if self.local_winner[br][bc] != 0 or all(
            self.board[3 * br + i][3 * bc + j] != 0 for i in range(3) for j in range(3)
        ):
            return [(r, c) for r in range(9) for c in range(9) if self.board[r][c] == 0]
        else:
            moves = []
            for i in range(3):
                for j in range(3):
                    r, c = 3 * br + i, 3 * bc + j
                    if self.board[r][c] == 0:
                        moves.append((r, c))
            return moves

    def apply_move(self, move):
        r, c = move
        p = self.next_player
        self.board[r][c] = p
        self.last_move = (r, c)
        br, bc = r // 3, c // 3
        if self.local_winner[br][bc] == 0:
            cells = [
                self.board[3 * br + i][3 * bc + j] for i in range(3) for j in range(3)
            ]
            for line in [
                (0, 1, 2),
                (3, 4, 5),
                (6, 7, 8),
                (0, 3, 6),
                (1, 4, 7),
                (2, 5, 8),
                (0, 4, 8),
                (2, 4, 6),
            ]:
                if cells[line[0]] == cells[line[1]] == cells[line[2]] != 0:
                    self.local_winner[br][bc] = p
                    break
        self.next_player = -p

    def is_terminal(self):
        lw = self.local_winner
        for line in [
            (0, 0, 0, 1, 0, 2),
            (1, 0, 1, 1, 1, 2),
            (2, 0, 2, 1, 2, 2),
            (0, 0, 1, 0, 2, 0),
            (0, 1, 1, 1, 2, 1),
            (0, 2, 1, 2, 2, 2),
            (0, 0, 1, 1, 2, 2),
            (0, 2, 1, 1, 2, 0),
        ]:
            a = lw[line[0]][line[1]]
            b = lw[line[2]][line[3]]
            c = lw[line[4]][line[5]]
            if a == b == c != 0:
                return True
        if all(
            lw[i][j] != 0
            or all(
                self.board[3 * i + ii][3 * j + jj] != 0
                for ii in range(3)
                for jj in range(3)
            )
            for i in range(3)
            for j in range(3)
        ):
            return True
        return False

    def get_winner(self):
        lw = self.local_winner
        for line in [
            (0, 0, 0, 1, 0, 2),
            (1, 0, 1, 1, 1, 2),
            (2, 0, 2, 1, 2, 2),
            (0, 0, 1, 0, 2, 0),
            (0, 1, 1, 1, 2, 1),
            (0, 2, 1, 2, 2, 2),
            (0, 0, 1, 1, 2, 2),
            (0, 2, 1, 1, 2, 0),
        ]:
            a = lw[line[0]][line[1]]
            b = lw[line[2]][line[3]]
            c = lw[line[4]][line[5]]
            if a == b == c != 0:
                return a
        if all(
            lw[i][j] != 0
            or all(
                self.board[3 * i + ii][3 * j + jj] != 0
                for ii in range(3)
                for jj in range(3)
            )
            for i in range(3)
            for j in range(3)
        ):
            return 0
        return None


class Node:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.wins = 0
        self.visits = 0
        self.children = []
        self.untried_moves = state.get_valid_moves()

    def uct_select(self):
        log_parent = math.log(self.visits)
        return max(
            self.children,
            key=lambda c: (c.wins / c.visits) + math.sqrt(2 * log_parent / c.visits),
        )

    def expand(self):
        m = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
        next_state = self.state.copy()
        next_state.apply_move(m)
        child = Node(next_state, parent=self, move=m)
        self.children.append(child)
        return child

    def simulate(self):
        st = self.state.copy()
        while not st.is_terminal():
            moves = st.get_valid_moves()
            st.apply_move(random.choice(moves))
        return st.get_winner()

    def backpropagate(self, result):
        self.visits += 1
        if self.parent and result == self.parent.state.next_player:
            self.wins += 1
        if self.parent:
            self.parent.backpropagate(result)

    def mcts_iteration(self):
        node = self
        while node.untried_moves == [] and node.children:
            node = node.uct_select()
        if node.untried_moves:
            node = node.expand()
        result = node.simulate()
        node.backpropagate(result)


# ----------------------------------------------------------------------
# Main loop with timing & send-control
# ----------------------------------------------------------------------
state = State()
first_move = True

while True:
    opponent_row, opponent_col = [int(i) for i in input().split()]
    valid_action_count = int(input())
    valid_moves = []
    for _ in range(valid_action_count):
        r, c = [int(j) for j in input().split()]
        valid_moves.append((r, c))

    if opponent_row != -1:
        state.apply_move((opponent_row, opponent_col))

    time_limit = 1.0 if first_move else 0.1
    first_move = False

    root = Node(state.copy())
    start = time.time()
    while time.time() - start < time_limit:
        root.mcts_iteration()

    best_child = max(root.children, key=lambda c: c.visits)
    best_move = best_child.move
    # send-control: if our MCTS suggestion is invalid, pick a random valid move
    if best_move not in valid_moves:
        best_move = random.choice(valid_moves)

    print(f"{best_move[0]} {best_move[1]}", flush=True)
    state.apply_move(best_move)
