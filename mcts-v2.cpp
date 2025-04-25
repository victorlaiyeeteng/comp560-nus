#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <iostream>
#include <limits>
#include <random>
#include <utility>
#include <vector>

using namespace std;

// ----------------------------------------------------------------------
// Bitboard Constants
// ----------------------------------------------------------------------
static const int FILLED_MASK = 0x1FF; // lower 9 bits set
static const array<int, 8> WIN_LINES = {
    0x7,   // row 0:   000000111
    0x38,  // row 1:   000111000
    0x1C0, // row 2:   111000000
    0x49,  // col 0:   001001001
    0x92,  // col 1:   010010010
    0x124, // col 2:   100100100
    0x111, // diag 1:  100010001
    0x54   // diag 2:  001010100
};

// ----------------------------------------------------------------------
// Game State with Bit Encoding
// ----------------------------------------------------------------------
struct State {
  // Each sub-board: lower 9 bits for X, next 9 bits for O
  array<int, 9> sub;
  int sub_idx; // which sub-board to play (0–8), or 9 = any
  bool turnX;  // true = X to play, false = O

  // Meta boards: bitmask of won (or drawn) sub-boards
  int metaX, metaO, metaD;
  int winner; // 0 = ongoing, 1=X wins, -1=O wins, 2=draw

  State()
      : sub{}, sub_idx(9), turnX(true), metaX(0), metaO(0), metaD(0),
        winner(0) {}
  State copy() const { return *this; }

  // Check if bitmask m has any winning line
  static bool isWin(int m) {
    for (int w : WIN_LINES)
      if ((m & w) == w)
        return true;
    return false;
  }

  // Generate all valid moves respecting the last sub_idx (const-safe)
  vector<pair<int, int>> get_valid_moves() const {
    vector<pair<int, int>> moves;
    auto add_moves = [&](int s) {
      int xb = sub[s] & FILLED_MASK;
      int ob = (sub[s] >> 9) & FILLED_MASK;
      int filled = xb | ob;
      for (int i = 0; i < 9; ++i) {
        if (!(filled & (1 << i))) {
          int r = (s / 3) * 3 + i / 3;
          int c = (s % 3) * 3 + i % 3;
          moves.emplace_back(r, c);
        }
      }
    };

    int targetIndex = sub_idx;
    if (targetIndex < 9) {
      bool closed = ((metaX | metaO | metaD) >> targetIndex) & 1;
      int xb = sub[targetIndex] & FILLED_MASK;
      int ob = (sub[targetIndex] >> 9) & FILLED_MASK;
      bool full = ((xb | ob) == FILLED_MASK);
      if (closed || full)
        targetIndex = 9;
    }
    if (targetIndex == 9) {
      for (int s = 0; s < 9; ++s) {
        if (((metaX | metaO | metaD) >> s) & 1)
          continue;
        add_moves(s);
      }
    } else {
      add_moves(targetIndex);
    }
    return moves;
  }

  // Apply a move and update sub/meta boards and next player
  void apply_move(const pair<int, int> &mv) {
    auto [r, c] = mv;
    int s = (r / 3) * 3 + (c / 3);
    int pos = (r % 3) * 3 + (c % 3);
    if (turnX)
      sub[s] |= 1 << pos;
    else
      sub[s] |= 1 << (pos + 9);

    // Update sub-board status
    int xb = sub[s] & FILLED_MASK;
    int ob = (sub[s] >> 9) & FILLED_MASK;
    if (!((metaX | metaO | metaD) & (1 << s))) {
      if (isWin(xb))
        metaX |= 1 << s;
      else if (isWin(ob))
        metaO |= 1 << s;
      else if ((xb | ob) == FILLED_MASK)
        metaD |= 1 << s;
    }

    // Determine overall winner or draw
    if (isWin(metaX))
      winner = 1;
    else if (isWin(metaO))
      winner = -1;
    else if (((metaX | metaO | metaD) == ((1 << 9) - 1))) {
      // No player has 3 aligned, check who won more small boards
      int x_count = __builtin_popcount(metaX);
      int o_count = __builtin_popcount(metaO);
      if (x_count > o_count)
        winner = 1;
      else if (o_count > x_count)
        winner = -1;
      else
        winner = 2; // draw
    }

    // Next sub_idx: target sub-board or any if closed/drawn
    int target = pos;
    if (((metaX | metaO | metaD) >> target) & 1)
      sub_idx = 9;
    else
      sub_idx = target;

    turnX = !turnX;
  }

  bool is_terminal() const { return winner != 0; }

  int get_winner() const {
    if (winner == 1)
      return 1;
    if (winner == -1)
      return -1;
    if (winner == 2)
      return 0;                        // draw
    return numeric_limits<int>::min(); // ongoing
  }
};

// ----------------------------------------------------------------------
// MCTS Node
// ----------------------------------------------------------------------
struct Node {
  State state;
  Node *parent;
  pair<int, int> move;
  double wins;
  int visits;
  vector<Node *> children;
  vector<pair<int, int>> untried_moves;

  Node(const State &st, Node *par = nullptr, pair<int, int> mv = {-1, -1})
      : state(st), parent(par), move(mv), wins(0), visits(0) {
    untried_moves = state.get_valid_moves();
  }

  ~Node() {
    for (auto c : children)
      delete c;
  }

  Node *uct_select() {
    double log_parent = log(visits);
    return *max_element(
        children.begin(), children.end(), [&](Node *a, Node *b) {
          double ua = a->wins / a->visits + sqrt(2 * log_parent / a->visits);
          double ub = b->wins / b->visits + sqrt(2 * log_parent / b->visits);
          return ua < ub;
        });
  }

  Node *expand(mt19937 &rng) {
    uniform_int_distribution<size_t> dist(0, untried_moves.size() - 1);
    size_t idx = dist(rng);
    auto mv = untried_moves[idx];
    untried_moves.erase(untried_moves.begin() + idx);
    State next_st = state.copy();
    next_st.apply_move(mv);
    Node *child = new Node(next_st, this, mv);
    children.push_back(child);
    return child;
  }

  int simulate(mt19937 &rng) {
    State st = state.copy();
    while (!st.is_terminal()) {
      auto moves = st.get_valid_moves();
      uniform_int_distribution<size_t> dist(0, moves.size() - 1);
      st.apply_move(moves[dist(rng)]);
    }
    return st.get_winner();
  }

  void backpropagate(int result) {
    visits++;
    if (parent) {
      int mover = parent->state.turnX ? 1 : -1;
      if (result == mover)
        wins++;
      parent->backpropagate(result);
    }
  }

  void mcts_iteration(mt19937 &rng) {
    Node *node = this;
    // selection
    while (node->untried_moves.empty() && !node->children.empty()) {
      node = node->uct_select();
    }
    // expansion
    if (!node->untried_moves.empty()) {
      node = node->expand(rng);
    }
    // simulation
    int result = node->simulate(rng);
    // backpropagation
    node->backpropagate(result);
  }
};

int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);

  State state;
  bool first_move = true;
  mt19937 rng(static_cast<unsigned>(
      chrono::system_clock::now().time_since_epoch().count()));

  while (true) {
    int opp_r, opp_c;
    cin >> opp_r >> opp_c;
    int valid_count;
    cin >> valid_count;
    vector<pair<int, int>> valid_moves(valid_count);
    for (int i = 0; i < valid_count; ++i)
      cin >> valid_moves[i].first >> valid_moves[i].second;

    if (opp_r != -1) {
      state.apply_move({opp_r, opp_c});
    }

    double time_limit = first_move ? 1.0 : 0.1;
    first_move = false;

    Node *root = new Node(state.copy());
    auto start = chrono::high_resolution_clock::now();
    int iterations = 0;
    while (true) {
      auto now = chrono::high_resolution_clock::now();
      chrono::duration<double> elapsed = now - start;
      if (elapsed.count() >= time_limit)
        break;
      root->mcts_iteration(rng);
      ++iterations;
    }
    cerr << "MCTS iterations run: " << iterations << endl;

    // choose best
    Node *best = nullptr;
    int best_visits = -1;
    for (auto c : root->children) {
      if (c->visits > best_visits) {
        best_visits = c->visits;
        best = c;
      }
    }
    pair<int, int> best_move =
        best ? best->move : valid_moves[rng() % valid_moves.size()];

    cout << best_move.first << " " << best_move.second << endl;
    state.apply_move(best_move);
    delete root;
  }
  return 0;
}
