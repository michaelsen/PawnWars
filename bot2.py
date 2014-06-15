import time
import sys
import random
import copy

from base_client import LiacBot

WHITE = 1
BLACK = -1
NONE = 0

MAX = 10000000
MIN = -MAX
NEGAMAX_DEPTH = 2

def negamax_pruning(board, depth, inferior, superior, player):
    moves = board.generate()
    if depth == 0 or moves == None:
        return player * board.heuristic(), None
    best_move = None
    best_score = inferior
    for move in moves:
        updated_board = copy.deepcopy(board)
        updated_board.simulate_move(move[0], move[1])
        score, movement = negamax_pruning(updated_board, depth-1, -superior, -inferior, -player)
        score = -score + random.uniform(-1.0, 1.0)
        if score > best_score:
            best_score = score
            best_move = move
        inferior = max(inferior, score)
        if inferior >= superior:
            break
    return best_score, best_move

# BOT =======================================================
class Bot0xFFCCFF(LiacBot):
    name = 'BotoCorDeRosa'

    def __init__(self):
        super(Bot0xFFCCFF, self).__init__()
        self.last_move = None

    def choose_move(self, board):
        moves = board.generate()
        best_score, best_move = negamax_pruning(board, NEGAMAX_DEPTH, MIN, MAX, board.my_team)
        return  best_move

    def on_move(self, state):
        print 'Generating a move...',
        board = Board(state)

        # if state['bad_move']:
        #     print state['board']
        #     raw_input()

        move = self.choose_move(board)
        self.last_move = move
        print move
        self.send_move(move[0], move[1])

    def on_game_over(self, state):
        print 'Game Over.'
        # sys.exit()

# ========================================================# BOARD ======================================================================
class Board(object):
    def __init__(self, state):
        self.cells = [[None for j in xrange(8)] for i in xrange(8)]
        self.my_pieces = []
        self.enemy_pieces = []
        self.my_team = None

        PIECES = {
            'r': Rook,
            'p': Pawn,
            'b': Bishop,
        }

        self.my_team = state['who_moves']
        c = state['board']
        i = 0

        for row in xrange(7, -1, -1):
            for col in xrange(0, 8):
                if c[i] != '.':
                    cls = PIECES[c[i].lower()]
                    team = BLACK if c[i].lower() == c[i] else WHITE

                    piece = cls(self, team, (row, col))
                    self.cells[row][col] = piece

                    if team == self.my_team:
                        self.my_pieces.append(piece)
                    else:
                        self.enemy_pieces.append(piece)

                i += 1

    def __getitem__(self, pos):
        if not 0 <= pos[0] <= 7 or not 0 <= pos[1] <= 7:
            return None

        return self.cells[pos[0]][pos[1]]

    def __setitem__(self, pos, value):
        self.cells[pos[0]][pos[1]] = value

    def is_empty(self, pos):
        return self[pos] is None

    def generate(self):
        moves = []
        for piece in self.my_pieces:
            ms = piece.generate()
            ms = [(piece.position, m) for m in ms]
            moves.extend(ms)

        return moves

    def simulate_move(self, origin, destination):
        actor = self[origin]
        goal = self[destination]
        # since only valid moves are generated, there's no need for validation

        if goal is not None:
            # capture
            self.enemy_pieces.remove(goal)

        self[destination] = actor
        self[origin] = None
        actor.position = destination

        self.my_team = -self.my_team
        self.my_pieces, self.enemy_pieces = self.enemy_pieces, self.my_pieces

        return

    def pawn_count(self):
        my_count = 0
        enemy_count = 0
        for piece in self.my_pieces:
            if piece == Pawn:
                my_count += 1
        for piece in self.enemy_pieces:
            if piece == Pawn:
                enemy_count += 1
        return my_count, enemy_count

    def pawn_grudge(self):
        # removes points from player depending on how many pawn were lost
        grudge = [-1000, -100, -25, -15, -5, 0, 0, 0, 0]
        my_pawns, enemy_pawns = self.pawn_count()
        return grudge[my_pawns] - grudge[enemy_pawns]

    def heuristic(self):
        score = 0  
        for piece in self.my_pieces:
            score = score + piece.evaluate()
        for piece in self.enemy_pieces:
            score = score - piece.evaluate()
        score += self.pawn_grudge()
        if self.my_team == BLACK:
            score = -score
        return score
		
# ========================================================# PIECES ======================================================================

class Piece(object):
    def __init__(self):
        self.board = None
        self.team = None
        self.position = None
        self.type = None

    def generate(self):
        pass

    def is_opponent(self, piece):
        return piece is not None and piece.team != self.team

class Pawn(Piece):
    def __init__(self, board, team, position):
        self.board = board
        self.team = team
        self.position = position

    def generate(self):
        moves = []
        my_row, my_col = self.position

        d = self.team

        # Movement to 1 forward
        pos = (my_row + d*1, my_col)
        if self.board.is_empty(pos) and pos[0] > -1 and pos[0] < 8:
            moves.append(pos)

        # Normal capture to right
        pos = (my_row + d*1, my_col+1)
        piece = self.board[pos]
        if self.is_opponent(piece):
            moves.append(pos)

        # Normal capture to left
        pos = (my_row + d*1, my_col-1)
        piece = self.board[pos]
        if self.is_opponent(piece):
            moves.append(pos)

        return moves

    def class_evaluate(self):
        return 10

    def evaluate(self):
        return self.class_evaluate()

class Rook(Piece):
    def __init__(self, board, team, position):
        self.board = board
        self.team = team
        self.position = position
        
    def _col(self, dir_):
        my_row, my_col = self.position
        d = -1 if dir_ < 0 else 1
        for col in xrange(1, abs(dir_)):
            yield (my_row, my_col + d*col)

    def _row(self, dir_):
        my_row, my_col = self.position

        d = -1 if dir_ < 0 else 1
        for row in xrange(1, abs(dir_)):
            yield (my_row + d*row, my_col)

    def _gen(self, moves, gen, idx):
        for pos in gen(idx):
            piece = self.board[pos]
            
            if piece is None: 
                moves.append(pos)
                continue
            
            elif piece.team != self.team:
                moves.append(pos)

            break

    def generate(self):
        moves = []

        my_row, my_col = self.position
        self._gen(moves, self._col, 8-my_col) # RIGHT
        self._gen(moves, self._col, -my_col-1) # LEFT
        self._gen(moves, self._row, 8-my_row) # TOP
        self._gen(moves, self._row, -my_row-1) # BOTTOM

        return moves

    def class_evaluate(self):
        return 35

    def evaluate(self):
        return self.class_evaluate()

class Bishop(Piece):
    def __init__(self, board, team, position):
        self.board = board
        self.team = team
        self.position = position

    def _gen(self, moves, row_dir, col_dir):
        my_row, my_col = self.position

        for i in xrange(1, 8):
            row = row_dir*i
            col = col_dir*i
            q_row, q_col = my_row+row, my_col+col

            if not 0 <= q_row <= 7 or not 0 <= q_col <= 7:
                break

            piece = self.board[q_row, q_col]
            if piece is not None:
                if piece.team != self.team:
                    moves.append((q_row, q_col))
                break

            moves.append((q_row, q_col))

    def generate(self):
        moves = []

        self._gen(moves, row_dir=1, col_dir=1) # TOPRIGHT
        self._gen(moves, row_dir=1, col_dir=-1) # TOPLEFT
        self._gen(moves, row_dir=-1, col_dir=-1) # BOTTOMLEFT
        self._gen(moves, row_dir=-1, col_dir=1) # BOTTOMRIGHT

        return moves

    def class_evaluate(self):
        return 21

    def evaluate(self):
        return self.class_evaluate()

# =============================================================================

if __name__ == '__main__':
    color = 0
    port = 50100

    if len(sys.argv) > 1:
        if sys.argv[1] == 'black':
            color = 1
            port = 50200

    bot = Bot0xFFCCFF()
    bot.port = port

    bot.start()






