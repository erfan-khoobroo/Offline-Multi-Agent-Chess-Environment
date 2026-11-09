import random
import chess


# Piece values are expressed in centipawns so positional terms can be combined
# with material in a predictable way.
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}
MATE_SCORE = 100_000


class BaseAgent:
    """A small alpha-beta chess player with a style-specific evaluation."""

    search_depth = 2  # Our move plus the opponent's reply.
    material_scale = 1.0
    center_scale = 1.0
    king_safety_scale = 1.0
    aggression_scale = 1.0

    def __init__(self, name):
        self.name = name

    def choose_move(self, board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        perspective = board.turn
        best_score = float("-inf")
        best_moves = []
        alpha, beta = float("-inf"), float("inf")

        for move in self._ordered_moves(board, legal_moves):
            board.push(move)
            score = self._minimax(
                board,
                self.search_depth - 1,
                alpha,
                beta,
                perspective,
                ply=1,
            )
            board.pop()

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
            alpha = max(alpha, best_score)

        return random.choice(best_moves)

    def _minimax(self, board, depth, alpha, beta, perspective, ply):
        # A forced mate is always more important than material or position.
        if board.is_checkmate():
            return (-MATE_SCORE + ply if board.turn == perspective
                    else MATE_SCORE - ply)

        if board.is_game_over(claim_draw=True):
            return 0

        if depth <= 0:
            return self._evaluate_position(board, perspective)

        legal_moves = self._ordered_moves(board, list(board.legal_moves))
        maximizing = board.turn == perspective

        if maximizing:
            value = float("-inf")
            for move in legal_moves:
                board.push(move)
                value = max(
                    value,
                    self._minimax(board, depth - 1, alpha, beta,
                                  perspective, ply + 1),
                )
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        value = float("inf")
        for move in legal_moves:
            board.push(move)
            value = min(
                value,
                self._minimax(board, depth - 1, alpha, beta,
                              perspective, ply + 1),
            )
            board.pop()
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    def _ordered_moves(self, board, moves):
        """Try forcing and material-winning moves first to improve pruning."""
        def priority(move):
            score = 0
            if board.is_capture(move):
                captured = (chess.PAWN if board.is_en_passant(move)
                            else board.piece_type_at(move.to_square))
                attacker = board.piece_type_at(move.from_square)
                score += 10 * PIECE_VALUES[captured] - PIECE_VALUES[attacker]
            if move.promotion:
                score += PIECE_VALUES[move.promotion]
            return score

        return sorted(moves, key=priority, reverse=True)

    def _evaluate_position(self, board, perspective):
        """Return a white-relative static score, then orient it to the agent."""
        score = 0.0
        center_squares = (chess.D4, chess.E4, chess.D5, chess.E5)

        for square, piece in board.piece_map().items():
            sign = 1 if piece.color == chess.WHITE else -1
            value = PIECE_VALUES[piece.piece_type] * self.material_scale
            positional = 0.0

            file_index = chess.square_file(square)
            rank_index = chess.square_rank(square)
            center_distance = abs(file_index - 3.5) + abs(rank_index - 3.5)

            if piece.piece_type in (chess.KNIGHT, chess.BISHOP, chess.QUEEN):
                positional += (7 - center_distance) * 7 * self.center_scale
            elif piece.piece_type == chess.PAWN:
                advance = rank_index if piece.color == chess.WHITE else 7 - rank_index
                positional += advance * 5
                if square in center_squares:
                    positional += 8 * self.center_scale

            # Discourage leaving a piece hanging. En passant is handled by the
            # board's attack map on the resulting positions in the search.
            enemy = not piece.color
            attacked = board.is_attacked_by(enemy, square)
            defended = board.is_attacked_by(piece.color, square)
            if attacked:
                positional -= value * (0.08 if defended else 0.24)

            score += sign * (value + positional)

        # A checked king is in immediate danger; style affects the weight.
        if board.is_check():
            checked_sign = 1 if board.turn == chess.WHITE else -1
            score -= checked_sign * 45 * self.king_safety_scale
            score -= checked_sign * 18 * self.aggression_scale

        return score if perspective == chess.WHITE else -score


class AggressiveAgent(BaseAgent):
    aggression_scale = 2.2
    center_scale = 1.25

    def __init__(self):
        super().__init__("Aggressive Agent")

    def _evaluate_position(self, board, perspective):
        score = super()._evaluate_position(board, perspective)

        # Reward sustained attacks around the opposing king, while still
        # accounting for pressure on our own king.
        enemy_pressure = self._king_pressure(board, not perspective)
        own_pressure = self._king_pressure(board, perspective)
        return score + (enemy_pressure - own_pressure) * 16

    @staticmethod
    def _king_pressure(board, king_color):
        king_square = board.king(king_color)
        if king_square is None:
            return 0

        king_zone = chess.SquareSet(chess.BB_KING_ATTACKS[king_square])
        king_zone.add(king_square)
        return sum(
            min(2, len(board.attackers(not king_color, square)))
            for square in king_zone
        )


class DefensiveAgent(BaseAgent):
    king_safety_scale = 2.0

    def __init__(self):
        super().__init__("Defensive Agent")

    def _evaluate_position(self, board, perspective):
        score = super()._evaluate_position(board, perspective)

        # Penalize attacked squares around our king more heavily than the
        # shared evaluation does, and reward a small pawn shield.
        own_danger = self._king_danger(board, perspective)
        enemy_danger = self._king_danger(board, not perspective)
        own_shield = self._pawn_shield(board, perspective)
        enemy_shield = self._pawn_shield(board, not perspective)

        score += (enemy_danger - own_danger) * 20
        score += (own_shield - enemy_shield) * 8

        # Value keeping our own pieces safe, especially the more valuable ones.
        for square, piece in board.piece_map().items():
            if piece.color != perspective or piece.piece_type == chess.KING:
                continue
            if (board.is_attacked_by(not perspective, square)
                    and not board.is_attacked_by(perspective, square)):
                score -= PIECE_VALUES[piece.piece_type] * 0.18

        return score

    @staticmethod
    def _king_danger(board, color):
        king_square = board.king(color)
        if king_square is None:
            return 0

        king_zone = chess.SquareSet(chess.BB_KING_ATTACKS[king_square])
        king_zone.add(king_square)
        danger = 0
        for square in king_zone:
            enemy_attackers = len(board.attackers(not color, square))
            friendly_defenders = len(board.attackers(color, square))
            danger += max(0, enemy_attackers - friendly_defenders)
        return danger

    @staticmethod
    def _pawn_shield(board, color):
        king_square = board.king(color)
        if king_square is None:
            return 0

        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        forward = 1 if color == chess.WHITE else -1
        shield_rank = king_rank + forward
        if not 0 <= shield_rank < 8:
            return 0

        return sum(
            board.piece_at(chess.square(file_index, shield_rank)) ==
            chess.Piece(chess.PAWN, color)
            for file_index in range(max(0, king_file - 1), min(7, king_file + 1) + 1)
        )


class MaterialAgent(BaseAgent):
    material_scale = 1.3

    def __init__(self):
        super().__init__("Material Agent")

    def _evaluate_position(self, board, perspective):
        score = super()._evaluate_position(board, perspective)

        # Make hanging material especially costly for this style of player.
        for square, piece in board.piece_map().items():
            if piece.color != perspective or piece.piece_type == chess.KING:
                continue
            if (board.is_attacked_by(not perspective, square)
                    and not board.is_attacked_by(perspective, square)):
                score -= PIECE_VALUES[piece.piece_type] * 0.22

        return score


class PositionalAgent(BaseAgent):
    center_scale = 2.0

    def __init__(self):
        super().__init__("Positional Agent")

    def _evaluate_position(self, board, perspective):
        score = super()._evaluate_position(board, perspective)

        # Reward control and occupation of the central 4x4 area, rather than
        # just moving one piece toward the middle.
        central_squares = [
            chess.square(file_index, rank_index)
            for file_index in range(2, 6)
            for rank_index in range(2, 6)
        ]
        central_control = sum(
            board.is_attacked_by(perspective, square)
            - board.is_attacked_by(not perspective, square)
            for square in central_squares
        )
        score += central_control * 7

        # In the opening and middlegame, encourage knights and bishops to
        # leave their starting ranks and become active.
        for square, piece in board.piece_map().items():
            if piece.color != perspective:
                continue
            if piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
                continue
            home_rank = 0 if piece.color == chess.WHITE else 7
            if chess.square_rank(square) != home_rank:
                score += 9

        return score


AGENT_REGISTRY = {
    "Aggressive": AggressiveAgent,
    "Defensive": DefensiveAgent,
    "Material": MaterialAgent,
    "Positional": PositionalAgent,
}


def create_agent(agent_type):
    agent_class = AGENT_REGISTRY.get(agent_type)
    if agent_class is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return agent_class()
