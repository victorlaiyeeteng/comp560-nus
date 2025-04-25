#include <iostream>
#include <vector>
#include <array>
#include <utility>
#include <limits>
#include <random>
#include <algorithm>
#include <cmath>
#include <chrono>

using namespace std;

// ----------------------------------------------------------------------
// Game State for Ultimate Tic-Tac-Toe
// ----------------------------------------------------------------------
struct State {
    array<array<int,9>,9> board;            // 9x9 board: 0=empty, 1=player1, -1=player2
    array<array<int,3>,3> local_winner;      // 3x3 local board winners: 0=ongoing, 1/-1=won
    int next_player;                         // who plays next: 1 (us) or -1 (opp)
    pair<int,int> last_move;                 // last move (r,c), (-1,-1) if none

    State() {
        for(auto &row: board) row.fill(0);
        for(auto &row: local_winner) row.fill(0);
        next_player = 1;
        last_move = {-1,-1};
    }

    State copy() const {
        State st;
        st.board = board;
        st.local_winner = local_winner;
        st.next_player = next_player;
        st.last_move = last_move;
        return st;
    }

    vector<pair<int,int>> get_valid_moves() const {
        vector<pair<int,int>> moves;
        if (last_move.first == -1) {
            for(int r=0; r<9; ++r)
                for(int c=0; c<9; ++c)
                    if(board[r][c] == 0) moves.emplace_back(r,c);
            return moves;
        }
        int lr = last_move.first, lc = last_move.second;
        int br = lr % 3, bc = lc % 3;
        bool block_full = true;
        for(int i=0;i<3;++i) for(int j=0;j<3;++j)
            if(board[3*br+i][3*bc+j] == 0) block_full = false;
        if(local_winner[br][bc] != 0 || block_full) {
            for(int r=0; r<9; ++r)
                for(int c=0; c<9; ++c)
                    if(board[r][c] == 0) moves.emplace_back(r,c);
        } else {
            for(int i=0;i<3;++i)
                for(int j=0;j<3;++j) {
                    int r = 3*br+i, c = 3*bc+j;
                    if(board[r][c] == 0) moves.emplace_back(r,c);
                }
        }
        return moves;
    }

    void apply_move(const pair<int,int>& mv) {
        int r = mv.first, c = mv.second;
        int p = next_player;
        board[r][c] = p;
        last_move = mv;
        int br = r/3, bc = c/3;
        if(local_winner[br][bc] == 0) {
            vector<int> cells;
            for(int i=0;i<3;++i)
                for(int j=0;j<3;++j)
                    cells.push_back(board[3*br+i][3*bc+j]);
            static const vector<array<int,3>> lines = {{0,1,2},{3,4,5},{6,7,8},
                                                      {0,3,6},{1,4,7},{2,5,8},
                                                      {0,4,8},{2,4,6}};
            for(auto &ln: lines) {
                if(cells[ln[0]] == p && cells[ln[1]] == p && cells[ln[2]] == p) {
                    local_winner[br][bc] = p;
                    break;
                }
            }
        }
        next_player = -p;
    }

    bool is_terminal() const {
        static const vector<array<int,6>> lines = {{0,0,0,1,0,2},{1,0,1,1,1,2},{2,0,2,1,2,2},
                                                    {0,0,1,0,2,0},{0,1,1,1,2,1},{0,2,1,2,2,2},
                                                    {0,0,1,1,2,2},{0,2,1,1,2,0}};
        for(auto &ln: lines) {
            int a = local_winner[ln[0]][ln[1]];
            int b = local_winner[ln[2]][ln[3]];
            int c = local_winner[ln[4]][ln[5]];
            if(a!=0 && a==b && b==c) return true;
        }
        for(int i=0;i<3;++i) for(int j=0;j<3;++j)
            if(local_winner[i][j] == 0) {
                bool full = true;
                for(int ii=0;ii<3;++ii)
                    for(int jj=0;jj<3;++jj)
                        if(board[3*i+ii][3*j+jj] == 0) full = false;
                if(!full) return false;
            }
        return true;
    }

    int get_winner() const {
        static const vector<array<int,6>> lines = {{0,0,0,1,0,2},{1,0,1,1,1,2},{2,0,2,1,2,2},
                                                    {0,0,1,0,2,0},{0,1,1,1,2,1},{0,2,1,2,2,2},
                                                    {0,0,1,1,2,2},{0,2,1,1,2,0}};
        for(auto &ln: lines) {
            int a = local_winner[ln[0]][ln[1]];
            int b = local_winner[ln[2]][ln[3]];
            int c = local_winner[ln[4]][ln[5]];
            if(a!=0 && a==b && b==c) return a;
        }
        // draw
        for(int i=0;i<3;++i) for(int j=0;j<3;++j) {
            bool full = true;
            for(int ii=0;ii<3;++ii)
                for(int jj=0;jj<3;++jj)
                    if(board[3*i+ii][3*j+jj] == 0) full = false;
            if(local_winner[i][j] == 0 && !full) return numeric_limits<int>::min();
        }
        return 0;
    }
};

// ----------------------------------------------------------------------
// MCTS Node
// ----------------------------------------------------------------------
struct Node {
    State state;
    Node* parent;
    pair<int,int> move;
    double wins;
    int visits;
    vector<Node*> children;
    vector<pair<int,int>> untried_moves;

    Node(const State& st, Node* par=nullptr, pair<int,int> mv={-1,-1})
        : state(st), parent(par), move(mv), wins(0), visits(0) {
        untried_moves = state.get_valid_moves();
    }

    ~Node() {
        for(auto c: children) delete c;
    }

    Node* uct_select() {
        double log_parent = log(visits);
        return *max_element(children.begin(), children.end(), [&](Node* a, Node* b) {
            double ua = a->wins/a->visits + sqrt(2 * log_parent / a->visits);
            double ub = b->wins/b->visits + sqrt(2 * log_parent / b->visits);
            return ua < ub;
        });
    }

    Node* expand(mt19937 &rng) {
        uniform_int_distribution<size_t> dist(0, untried_moves.size()-1);
        size_t idx = dist(rng);
        auto mv = untried_moves[idx];
        untried_moves.erase(untried_moves.begin()+idx);
        State next_st = state.copy();
        next_st.apply_move(mv);
        Node* child = new Node(next_st, this, mv);
        children.push_back(child);
        return child;
    }

    int simulate(mt19937 &rng) {
        State st = state.copy();
        while(!st.is_terminal()) {
            auto moves = st.get_valid_moves();
            uniform_int_distribution<size_t> dist(0, moves.size()-1);
            st.apply_move(moves[dist(rng)]);
        }
        return st.get_winner();
    }

    void backpropagate(int result) {
        visits++;
        if(parent && result == parent->state.next_player) wins++;
        if(parent) parent->backpropagate(result);
    }

    void mcts_iteration(mt19937 &rng) {
        Node* node = this;
        // selection
        while(node->untried_moves.empty() && !node->children.empty()) {
            node = node->uct_select();
        }
        // expansion
        if(!node->untried_moves.empty()) {
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
    mt19937 rng(static_cast<unsigned>(chrono::system_clock::now().time_since_epoch().count()));

    while(true) {
        int opp_r, opp_c;
        cin >> opp_r >> opp_c;
        int valid_count;
        cin >> valid_count;
        vector<pair<int,int>> valid_moves(valid_count);
        for(int i=0;i<valid_count;++i) cin >> valid_moves[i].first >> valid_moves[i].second;

        if(opp_r != -1) {
            state.apply_move({opp_r, opp_c});
        }

        double time_limit = first_move ? 1.0 : 0.1;
        first_move = false;

        Node* root = new Node(state.copy());
        auto start = chrono::high_resolution_clock::now();
        int iterations = 0;
        while(true) {
            auto now = chrono::high_resolution_clock::now();
            chrono::duration<double> elapsed = now - start;
            if(elapsed.count() >= time_limit) break;
            root->mcts_iteration(rng);
            ++iterations;
        }
        cerr << "MCTS iterations run: " << iterations << endl;

        // choose best
        Node* best = nullptr;
        int best_visits = -1;
        for(auto c: root->children) {
            if(c->visits > best_visits) {
                best_visits = c->visits;
                best = c;
            }
        }
        pair<int,int> best_move = best ? best->move : valid_moves[rng()%valid_moves.size()];
        // ensure move valid
        if(find(valid_moves.begin(), valid_moves.end(), best_move) == valid_moves.end()) {
            best_move = valid_moves[rng()%valid_moves.size()];
        }

        cout << best_move.first << " " << best_move.second << endl;
        state.apply_move(best_move);
        
        // clean up
        delete root;
    }
    return 0;
}
