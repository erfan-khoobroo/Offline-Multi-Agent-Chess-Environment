import chess


LONE_KING_DRAW_PLIES = 16


class ChessEngine:
    def __init__(self):
        self.board = chess.Board()
        self._lone_king_side = self._find_lone_king_side()
        self._lone_king_plies = 0

    # Reset the game
    def reset(self):
        self.board.reset()
        self._lone_king_side = self._find_lone_king_side()
        self._lone_king_plies = 0

    def _find_lone_king_side(self):
        """Return the color with only a king, unless both sides have only kings."""
        lone_sides = []
        for color in (chess.WHITE, chess.BLACK):
            if self.board.king(color) is None:
                continue
            piece_count = sum(
                len(self.board.pieces(piece_type, color))
                for piece_type in chess.PIECE_TYPES
            )
            if piece_count == 1:
                lone_sides.append(color)
        return lone_sides[0] if len(lone_sides) == 1 else None

    # Get a copy of the current board
    def get_board_copy(self):
        return self.board.copy(stack=True)

    # Get the piece at a specific square
    def piece_at(self, square):
        return self.board.piece_at(square)

    # Get legal moves from a specific square
    def legal_moves_from(self, square):
        return [ move for move in self.board.legal_moves if move.from_square == square ]

    # Execute a move
    def make_move(self, move):
        if move not in self.board.legal_moves:
            raise ValueError("Illegal move!")
        self.board.push(move)

        lone_king_side = self._find_lone_king_side()
        if lone_king_side is None:
            self._lone_king_side = None
            self._lone_king_plies = 0
        elif lone_king_side != self._lone_king_side:
            self._lone_king_side = lone_king_side
            self._lone_king_plies = 0
        else:
            self._lone_king_plies += 1

    # Check if the game is over
    def is_game_over(self):
        return (
            self.board.is_game_over()
            or self._lone_king_plies >= LONE_KING_DRAW_PLIES
        )

    # Get the game result
    def outcome(self):
        outcome = self.board.outcome()
        if outcome is not None:
            return outcome
        if self._lone_king_plies >= LONE_KING_DRAW_PLIES:
            return chess.Outcome(chess.Termination.VARIANT_DRAW, None)
        return None

