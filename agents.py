import random
import chess

# ارزش مهره‌ها با واحد صدم پیاده بیان می‌شود تا با امتیازهای موقعیتی جمع‌پذیر باشند.
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
    """کلاس پایهٔ ایجنت‌ها برای جست‌وجو، ارزیابی و انتخاب حرکت."""

    search_depth = 2  # عمق جست‌وجو شامل حرکت ایجنت و پاسخ حریف است.
    material_scale = 1.0
    center_scale = 1.0
    king_safety_scale = 1.0
    aggression_scale = 1.0

    def __init__(self, name):
        """نام ایجنت و وضعیت انتخاب حرکت آغازین را مقداردهی می‌کند."""
        self.name = name
        self._has_moved = False

    def choose_move(self, board):
        """حرکت نخست را تصادفی و حرکت‌های بعدی را با Minimax انتخاب می‌کند."""
        legal_moves = list(board.legal_moves)
        # اگر حرکت قانونی وجود نداشته باشد، ایجنت حرکتی برنمی‌گرداند.
        if not legal_moves:
            return None

        # نخستین حرکت این ایجنت بدون ارزیابی موقعیت، تصادفی انتخاب می‌شود.
        if not self._has_moved:
            self._has_moved = True
            return random.choice(legal_moves)

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

            # اگر امتیاز بهتر از بهترین مقدار فعلی باشد، بهترین گزینه عوض می‌شود.
            if score > best_score:
                best_score = score
                best_moves = [move]
            # اگر امتیاز برابر باشد، حرکت برای انتخاب تصادفی به فهرست افزوده می‌شود.
            elif score == best_score:
                best_moves.append(move)
            alpha = max(alpha, best_score)

        return random.choice(best_moves)

    def _minimax(self, board, depth, alpha, beta, perspective, ply):
        # مات قطعی از برتری مادی یا موقعیتی مهم‌تر است.
        # اگر وضعیت مات باشد، امتیاز قطعی مات را برمی‌گردانیم.
        """به‌صورت بازگشتی بهترین امتیاز ایجنت یا بهترین پاسخ حریف را محاسبه می‌کند."""
        if board.is_checkmate():
            # این مقدار بر اساس برقرار بودن شرط «board.turn == perspective» انتخاب می‌شود.
            return -MATE_SCORE + ply if board.turn == perspective else MATE_SCORE - ply

        # اگر بازی طبق قواعد کتابخانه مساوی یا تمام شده باشد، امتیاز صفر می‌گیرد.
        if board.is_game_over(claim_draw=True):
            return 0

        # اگر به عمق جست‌وجو رسیده‌ایم، وضعیت را ایستا ارزیابی می‌کنیم.
        if depth <= 0:
            return self._evaluate_position(board, perspective)

        legal_moves = self._ordered_moves(board, list(board.legal_moves))
        maximizing = board.turn == perspective

        # اگر نوبت ایجنت باشد، بیشترین امتیاز را جست‌وجو می‌کنیم.
        if maximizing:
            value = float("-inf")
            for move in legal_moves:
                board.push(move)
                value = max(
                    value,
                    self._minimax(board, depth - 1, alpha, beta, perspective, ply + 1),
                )
                board.pop()
                alpha = max(alpha, value)
                # اگر کران‌ها به هم رسیده‌اند، ادامهٔ شاخه نتیجه را تغییر نمی‌دهد و هرس می‌شود.
                if alpha >= beta:
                    break
            return value

        value = float("inf")
        for move in legal_moves:
            board.push(move)
            value = min(
                value,
                self._minimax(board, depth - 1, alpha, beta, perspective, ply + 1),
            )
            board.pop()
            beta = min(beta, value)
            # اگر کران‌ها به هم رسیده‌اند، ادامهٔ شاخه نتیجه را تغییر نمی‌دهد و هرس می‌شود.
            if alpha >= beta:
                break
        return value

    def _ordered_moves(self, board, moves):
        """حرکت‌های گرفتن مهره و ارتقا را برای جست‌وجوی زودتر مرتب می‌کند."""

        def priority(move):
            """اولویت تقریبی یک حرکت را برای ترتیب جست‌وجو محاسبه می‌کند."""
            score = 0
            # اگر حرکت گرفتن مهره باشد، ارزش مهرهٔ گرفته‌شده در اولویت لحاظ می‌شود.
            if board.is_capture(move):
                # این مقدار بر اساس برقرار بودن شرط «board.is_en_passant(move)» انتخاب می‌شود.
                captured = (
                    chess.PAWN
                    if board.is_en_passant(move)
                    else board.piece_type_at(move.to_square)
                )
                attacker = board.piece_type_at(move.from_square)
                score += 10 * PIECE_VALUES[captured] - PIECE_VALUES[attacker]
            # اگر حرکت ارتقا باشد، امتیاز مهرهٔ جدید به اولویت افزوده می‌شود.
            if move.promotion:
                score += PIECE_VALUES[move.promotion]
            return score

        return sorted(moves, key=priority, reverse=True)

    def _evaluate_position(self, board, perspective):
        """وضعیت مادی و موقعیتی صفحه را از دید ایجنت امتیازدهی می‌کند."""
        score = 0.0
        center_squares = (chess.D4, chess.E4, chess.D5, chess.E5)

        for square, piece in board.piece_map().items():
            # این مقدار بر اساس برقرار بودن شرط «piece.color == chess.WHITE» انتخاب می‌شود.
            sign = 1 if piece.color == chess.WHITE else -1
            value = PIECE_VALUES[piece.piece_type] * self.material_scale
            positional = 0.0

            file_index = chess.square_file(square)
            rank_index = chess.square_rank(square)
            center_distance = abs(file_index - 3.5) + abs(rank_index - 3.5)

            # اگر مهره اسب، فیل یا وزیر باشد، موقعیت مرکزی آن امتیاز می‌گیرد.
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP, chess.QUEEN):
                positional += (7 - center_distance) * 7 * self.center_scale
            # اگر مهره پیاده باشد، پیشروی و استقرار مرکزی آن سنجیده می‌شود.
            elif piece.piece_type == chess.PAWN:
                # این مقدار بر اساس برقرار بودن شرط «piece.color == chess.WHITE» انتخاب می‌شود.
                advance = rank_index if piece.color == chess.WHITE else 7 - rank_index
                positional += advance * 5
                # اگر پیاده در یکی از خانه‌های مرکزی باشد، پاداش مرکزی می‌گیرد.
                if square in center_squares:
                    positional += 8 * self.center_scale

            # مهرهٔ بی‌دفاع جریمه می‌گیرد؛ حرکت آن‌پاسان در شاخه‌های جست‌وجو با صفحهٔ حاصل بررسی می‌شود.
            enemy = not piece.color
            attacked = board.is_attacked_by(enemy, square)
            defended = board.is_attacked_by(piece.color, square)
            # اگر مهره مورد حمله باشد، جریمهٔ آسیب‌پذیری اعمال می‌شود.
            if attacked:
                # این مقدار بر اساس برقرار بودن شرط «defended» انتخاب می‌شود.
                positional -= value * (0.08 if defended else 0.24)

            score += sign * (value + positional)

        # کیش خطر فوری شاه است و وزن آن با سبک ایجنت تغییر می‌کند.
        # اگر شاه نوبت جاری در کیش باشد، نشانگر هشدار را برمی‌گردانیم.
        if board.is_check():
            # این مقدار بر اساس برقرار بودن شرط «board.turn == chess.WHITE» انتخاب می‌شود.
            checked_sign = 1 if board.turn == chess.WHITE else -1
            score -= checked_sign * 45 * self.king_safety_scale
            score -= checked_sign * 18 * self.aggression_scale

        # این مقدار بر اساس برقرار بودن شرط «perspective == chess.WHITE» انتخاب می‌شود.
        return score if perspective == chess.WHITE else -score

class AggressiveAgent(BaseAgent):
    """پروفایل تهاجمی را تعریف می‌کند و فشار اطراف شاه حریف را وزن می‌دهد."""

    aggression_scale = 2.2
    center_scale = 1.25

    def __init__(self):
        """نام ایجنت را ذخیره می‌کند."""
        super().__init__("Aggressive Agent")

    def _evaluate_position(self, board, perspective):
        """وضعیت مادی و موقعیتی صفحه را از دید ایجنت امتیازدهی می‌کند."""
        score = super()._evaluate_position(board, perspective)

        # فشار پیرامون شاه حریف پاداش می‌گیرد و خطر شاه خودی نیز کم می‌شود.
        enemy_pressure = self._king_pressure(board, not perspective)
        own_pressure = self._king_pressure(board, perspective)
        return score + (enemy_pressure - own_pressure) * 16

    @staticmethod
    def _king_pressure(board, king_color):
        """میزان کنترل خانه‌های اطراف شاه را از سوی حریف می‌شمارد."""
        king_square = board.king(king_color)
        # اگر شاه روی صفحه نباشد، فشار یا خطر شاهی صفر است.
        if king_square is None:
            return 0

        king_zone = chess.SquareSet(chess.BB_KING_ATTACKS[king_square])
        king_zone.add(king_square)
        return sum(
            min(2, len(board.attackers(not king_color, square))) for square in king_zone
        )

class DefensiveAgent(BaseAgent):
    """پروفایل دفاعی را تعریف می‌کند و امنیت شاه و مهره‌های خودی را تقویت می‌کند."""

    king_safety_scale = 2.0

    def __init__(self):
        """نام ایجنت را ذخیره می‌کند."""
        super().__init__("Defensive Agent")

    def _evaluate_position(self, board, perspective):
        """وضعیت مادی و موقعیتی صفحه را از دید ایجنت امتیازدهی می‌کند."""
        score = super()._evaluate_position(board, perspective)

        # خطر خانه‌های اطراف شاه خودی بیشتر جریمه می‌شود و سپر پیاده‌ای پاداش می‌گیرد.
        own_danger = self._king_danger(board, perspective)
        enemy_danger = self._king_danger(board, not perspective)
        own_shield = self._pawn_shield(board, perspective)
        enemy_shield = self._pawn_shield(board, not perspective)

        score += (enemy_danger - own_danger) * 20
        score += (own_shield - enemy_shield) * 8

        # حفظ مهره‌های خودی، به‌ویژه مهره‌های باارزش، امتیاز می‌گیرد.
        for square, piece in board.piece_map().items():
            # اگر مهره متعلق به ایجنت نباشد یا شاه باشد، از این جریمه می‌گذریم.
            if piece.color != perspective or piece.piece_type == chess.KING:
                continue
            # اگر شرط «board.is_attacked_by(not perspective, square) and not board.is_attacked_by(perspective, square)» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
            if board.is_attacked_by(
                not perspective, square
            ) and not board.is_attacked_by(perspective, square):
                score -= PIECE_VALUES[piece.piece_type] * 0.18

        return score

    @staticmethod
    def _king_danger(board, color):
        """خطر خانه‌های اطراف شاه را با شمار مهاجمان و مدافعان برآورد می‌کند."""
        king_square = board.king(color)
        # اگر شاه روی صفحه نباشد، فشار یا خطر شاهی صفر است.
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
        """تعداد پیاده‌های محافظ جلوی شاه را می‌شمارد."""
        king_square = board.king(color)
        # اگر شاه روی صفحه نباشد، فشار یا خطر شاهی صفر است.
        if king_square is None:
            return 0

        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        # اگر کارت متعلق به سفید باشد، انتخاب سفید به‌روز می‌شود.
        forward = 1 if color == chess.WHITE else -1
        shield_rank = king_rank + forward
        # اگر رتبهٔ جلوی شاه بیرون صفحه باشد، سپر پیاده‌ای شمرده نمی‌شود.
        if not 0 <= shield_rank < 8:
            return 0

        return sum(
            board.piece_at(chess.square(file_index, shield_rank))
            == chess.Piece(chess.PAWN, color)
            for file_index in range(max(0, king_file - 1), min(7, king_file + 1) + 1)
        )

class MaterialAgent(BaseAgent):
    """پروفایل مهره‌محور را تعریف می‌کند و ارزش مهره‌ها را بیشتر وزن می‌دهد."""

    material_scale = 1.3

    def __init__(self):
        """نام ایجنت را ذخیره می‌کند."""
        super().__init__("Material Agent")

    def _evaluate_position(self, board, perspective):
        """وضعیت مادی و موقعیتی صفحه را از دید ایجنت امتیازدهی می‌کند."""
        score = super()._evaluate_position(board, perspective)

        # از دست دادن مهرهٔ بی‌دفاع برای این سبک هزینهٔ بیشتری دارد.
        for square, piece in board.piece_map().items():
            # اگر مهره متعلق به ایجنت نباشد یا شاه باشد، از این جریمه می‌گذریم.
            if piece.color != perspective or piece.piece_type == chess.KING:
                continue
            # اگر شرط «board.is_attacked_by(not perspective, square) and not board.is_attacked_by(perspective, square)» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
            if board.is_attacked_by(
                not perspective, square
            ) and not board.is_attacked_by(perspective, square):
                score -= PIECE_VALUES[piece.piece_type] * 0.22

        return score

class PositionalAgent(BaseAgent):
    """پروفایل موقعیت‌محور را تعریف می‌کند و کنترل مرکز و فعالیت مهره‌ها را پاداش می‌دهد."""

    center_scale = 2.0

    def __init__(self):
        """نام ایجنت را ذخیره می‌کند."""
        super().__init__("Positional Agent")

    def _evaluate_position(self, board, perspective):
        """وضعیت مادی و موقعیتی صفحه را از دید ایجنت امتیازدهی می‌کند."""
        score = super()._evaluate_position(board, perspective)

        # کنترل و اشغال ناحیهٔ مرکزی ۴×۴ پاداش می‌گیرد، نه فقط نزدیک کردن یک مهره به مرکز.
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

        # خروج اسب و فیل از ردیف آغازین به‌عنوان نشانهٔ فعالیت مهره پاداش می‌گیرد.
        for square, piece in board.piece_map().items():
            # اگر مهره متعلق به ایجنت نباشد، پاداش فعالیت خودی نمی‌گیرد.
            if piece.color != perspective:
                continue
            # اگر مهره اسب یا فیل نباشد، پاداش توسعهٔ مهرهٔ سبک نمی‌گیرد.
            if piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
                continue
            # این مقدار بر اساس برقرار بودن شرط «piece.color == chess.WHITE» انتخاب می‌شود.
            home_rank = 0 if piece.color == chess.WHITE else 7
            # اگر اسب یا فیل از ردیف آغازین خارج شده باشد، فعال محسوب می‌شود.
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
    """کلاس ایجنت را بر اساس نام انتخاب‌شده از رجیستری می‌سازد."""
    agent_class = AGENT_REGISTRY.get(agent_type)
    # اگر نام ایجنت در رجیستری نباشد، خطای نوع ایجنت صادر می‌شود.
    if agent_class is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return agent_class()
