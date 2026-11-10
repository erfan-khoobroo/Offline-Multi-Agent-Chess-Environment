import chess

LONE_KING_DRAW_PLIES = 16

class ChessEngine:
    """وضعیت شطرنج را نگه می‌دارد و عملیات اصلی بازی را در اختیار رابط می‌گذارد."""

    def __init__(self):
        """صفحهٔ آغازین و شمارندهٔ قانون سفارشی را مقداردهی می‌کند."""
        self.board = chess.Board()
        self._lone_king_side = self._find_lone_king_side()
        self._lone_king_plies = 0

    # صفحه را به وضعیت آغازین بازمی‌گرداند.
    def reset(self):
        """صفحه و شمارنده‌های بازی را به وضعیت آغازین بازمی‌گرداند."""
        self.board.reset()
        self._lone_king_side = self._find_lone_king_side()
        self._lone_king_plies = 0

    def _find_lone_king_side(self):
        """رنگ طرفی را که تنها شاه دارد پیدا می‌کند؛ اگر هر دو فقط شاه داشته باشند، None می‌دهد."""
        lone_sides = []
        for color in (chess.WHITE, chess.BLACK):
            # اگر شاه این رنگ موجود نباشد، بررسی مهره‌هایش ادامه پیدا نمی‌کند.
            if self.board.king(color) is None:
                continue
            piece_count = sum(
                len(self.board.pieces(piece_type, color))
                for piece_type in chess.PIECE_TYPES
            )
            # اگر تنها مهرهٔ این رنگ شاه باشد، طرف به‌عنوان شاه تنها ثبت می‌شود.
            if piece_count == 1:
                lone_sides.append(color)
        # این مقدار بر اساس برقرار بودن شرط «len(lone_sides) == 1» انتخاب می‌شود.
        return lone_sides[0] if len(lone_sides) == 1 else None

    # کپی صفحه را همراه با تاریخچهٔ حرکت‌ها برمی‌گرداند.
    def get_board_copy(self):
        """کپی صفحه را همراه با تاریخچهٔ حرکت‌ها برمی‌گرداند."""
        return self.board.copy(stack=True)

    # مهرهٔ خانهٔ مشخص‌شده را برمی‌گرداند.
    def piece_at(self, square):
        """مهرهٔ خانهٔ داده‌شده را برمی‌گرداند."""
        return self.board.piece_at(square)

    # حرکت‌های قانونی آغازشونده از خانهٔ مشخص‌شده را برمی‌گرداند.
    def legal_moves_from(self, square):
        """حرکت‌های قانونی آغازشونده از خانهٔ داده‌شده را برمی‌گرداند."""
        return [move for move in self.board.legal_moves if move.from_square == square]

    # حرکت قانونی را اجرا می‌کند.
    def make_move(self, move):
        # اگر حرکت در میان حرکت‌های قانونی نباشد، اجرا را رد می‌کنیم.
        """قانونی بودن حرکت را بررسی و سپس آن را اجرا می‌کند و شمارندهٔ شاه تنها را به‌روز می‌کند."""
        if move not in self.board.legal_moves:
            raise ValueError("Illegal move!")
        self.board.push(move)

        lone_king_side = self._find_lone_king_side()
        # اگر هیچ طرف یکتایی شاه تنها نداشته باشد، شمارندهٔ سفارشی پاک می‌شود.
        if lone_king_side is None:
            self._lone_king_side = None
            self._lone_king_plies = 0
        # اگر وضعیت شاه تنها تازه آغاز یا عوض شده باشد، شمارنده از صفر شروع می‌شود.
        elif lone_king_side != self._lone_king_side:
            self._lone_king_side = lone_king_side
            self._lone_king_plies = 0
        # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.
        else:
            self._lone_king_plies += 1

    # پایان بازی را بررسی می‌کند.
    def is_game_over(self):
        """پایان استاندارد بازی یا پایان قانون سفارشی را بررسی می‌کند."""
        return (
            self.board.is_game_over() or self._lone_king_plies >= LONE_KING_DRAW_PLIES
        )

    # نتیجهٔ بازی را برمی‌گرداند.
    def outcome(self):
        """نتیجهٔ استاندارد یا مساوی ناشی از قانون سفارشی را برمی‌گرداند."""
        outcome = self.board.outcome()
        # اگر کتابخانه نتیجهٔ استانداردی داده باشد، همان نتیجه برگردانده می‌شود.
        if outcome is not None:
            return outcome
        # اگر شمارنده به حد سفارشی برسد، مساوی اعلام می‌شود.
        if self._lone_king_plies >= LONE_KING_DRAW_PLIES:
            return chess.Outcome(chess.Termination.VARIANT_DRAW, None)
        return None
