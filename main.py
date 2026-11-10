import pygame
import chess
import math
import random
from pathlib import Path
from functools import lru_cache

import arabic_reshaper
from bidi.algorithm import get_display

from chess_engine import ChessEngine
from agents import create_agent

# تنظیمات و ثابت‌های برنامه

BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8

PANEL_WIDTH = 260
WINDOW_WIDTH = BOARD_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = 700
BOARD_TOP = 0
UI_SCALE = 1.0
PANEL_CONTENT_WIDTH = PANEL_WIDTH
AGENT_MOVE_MIN_MS = 2000
AGENT_MOVE_MAX_MS = 4000

def next_agent_move_delay():
    """مدت مکث تصادفی میان حرکت‌های خودکار را برمی‌گرداند."""
    return random.randint(AGENT_MOVE_MIN_MS, AGENT_MOVE_MAX_MS)

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

BACKGROUND = (30, 32, 40)
PANEL_COLOR = (43, 46, 56)
BUTTON_COLOR = (65, 72, 88)
ACCENT_COLOR = (70, 145, 110)

ASSETS_DIR = Path(__file__).parent / "assets"

PLAYER_OPTIONS = ["Human", "Aggressive", "Defensive", "Material", "Positional"]

AGENT_DESCRIPTIONS = {
    "Human": (
        "بازیکن انسانی\n" "تمام تصمیمات و انتخاب حرکت‌ها توسط خود شما انجام می‌شود."
    ),
    "Aggressive": (
        "ایجنت تهاجمی\n"
        "تمرکز بر حمله، گرفتن مهره‌های حریف و ایجاد تهدید.\n"
        "ریسک‌پذیر است و به بازی فعال علاقه دارد."
    ),
    "Defensive": (
        "ایجنت دفاعی\n"
        "تمرکز بر امنیت شاه، محافظت از مهره‌ها و کاهش خطر.\n"
        "اولویت اصلی آن حفظ موقعیت و جلوگیری از ضرر است."
    ),
    "Material": (
        "ایجنت مهره‌محور\n"
        "ارزش مهره‌ها را بررسی می‌کند و به دنبال برتری مادی است.\n"
        "گرفتن مهره‌های باارزش و حفظ مهره‌های خود اهمیت دارد."
    ),
    "Positional": (
        "ایجنت موقعیت‌محور\n"
        "به کنترل مرکز، فعالیت مهره‌ها و جای‌گیری مناسب توجه می‌کند.\n"
        "هدف آن ساختن یک موقعیت مناسب روی صفحه است."
    ),
}

PIECE_NAMES = {
    chess.PAWN: "pawn",
    chess.ROOK: "rook",
    chess.KNIGHT: "knight",
    chess.BISHOP: "bishop",
    chess.QUEEN: "queen",
    chess.KING: "king",
}

PIECE_IMAGES = {}

# قلم‌ها و متن فارسی

def draw_persian_text(screen, text, font, color, center):
    """متن فارسی را شکل‌دهی می‌کند و آن را در نقطهٔ مرکزی داده‌شده می‌کشد."""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)

    text_surface = font.render(bidi_text, True, color)

    text_rect = text_surface.get_rect(center=center)

    screen.blit(text_surface, text_rect)

@lru_cache(maxsize=32)
def get_font(size, bold=False):
    """قلم موردنیاز رابط را با اندازهٔ درخواستی می‌سازد یا از حافظهٔ موقت برمی‌گرداند."""
    font_path = "fonts/Vazirmatn-Regular.ttf"

    return pygame.font.Font(font_path, size)

# رسم متن

def draw_text(screen, text, font, color, x, y):
    """متن ساده را در مختصات داده‌شده روی صفحه رسم می‌کند."""
    image = font.render(text, True, color)

    screen.blit(image, (x, y))

# رسم دکمه

def draw_button(screen, rect, text, font, color=BUTTON_COLOR):
    """دکمه‌ای با متن، اندازه و رنگ مشخص رسم می‌کند."""
    pygame.draw.rect(screen, color, rect, border_radius=10)

    image = font.render(text, True, (255, 255, 255))

    screen.blit(image, image.get_rect(center=rect.center))

# بارگذاری تصاویر مهره‌ها

def load_piece_images():
    """تصویر مهره‌های موجود را بارگذاری و متناسب با اندازهٔ خانه‌ها کوچک یا بزرگ می‌کند."""
    for color, color_name in [(chess.WHITE, "white"), (chess.BLACK, "black")]:

        for piece_type, piece_name in PIECE_NAMES.items():

            path = ASSETS_DIR / f"{color_name}_{piece_name}.png"

            # اگر فایل تصویر وجود نداشته باشد، از بارگذاری آن صرف‌نظر می‌شود.
            if not path.exists():
                continue

            image = pygame.image.load(str(path)).convert_alpha()

            width, height = image.get_size()

            scale = min(SQUARE_SIZE * 0.82 / width, SQUARE_SIZE * 0.82 / height)

            image = pygame.transform.smoothscale(
                image, (int(width * scale), int(height * scale))
            )

            PIECE_IMAGES[(color, piece_type)] = image

# منوی آغازین
def draw_agent_description(screen, font, player_type, x, y, width):
    """توضیح فارسی سبک انتخاب‌شدهٔ ایجنت را در کارت منو نمایش می‌دهد."""
    description = AGENT_DESCRIPTIONS[player_type]

    lines = description.split("\n")

    line_height = 27

    for index, line in enumerate(lines):
        # این مقدار بر اساس برقرار بودن شرط «index == 0» انتخاب می‌شود.
        color = (255, 215, 120) if index == 0 else (210, 210, 210)

        text_surface = font.render(line, True, color)

        text_rect = text_surface.get_rect(
            center=(x + width // 2, y + index * line_height)
        )

        screen.blit(text_surface, text_rect)

def prepare_menu_art(image, size):
    """تصویر منو را برای ستون کناری اندازه‌بندی و قاب‌بندی می‌کند."""
    panel = pygame.Surface(size).convert()
    panel.fill((10, 18, 42))

    # اگر تصویر بارگذاری شده باشد، آن را در قاب منو قرار می‌دهیم.
    if image is not None:
        image_width, image_height = image.get_size()
        scale = max(size[0] / image_width, size[1] / image_height)
        scaled_size = (int(image_width * scale), int(image_height * scale))
        scaled_image = pygame.transform.smoothscale(image, scaled_size)
        crop_x = max(0, (scaled_size[0] - size[0]) // 2)
        crop_y = max(0, (scaled_size[1] - size[1]) // 2)
        panel.blit(
            scaled_image,
            (0, 0),
            pygame.Rect(crop_x, crop_y, size[0], size[1]),
        )

        shade = pygame.Surface(size, pygame.SRCALPHA)
        shade.fill((8, 17, 48, 65))
        panel.blit(shade, (0, 0))

    pygame.draw.line(panel, (79, 174, 220), (0, 0), (0, size[1]), 3)
    caption_font = get_font(17)
    caption = caption_font.render("STRATEGY  •  THINK  •  PLAY", True, (235, 245, 255))
    caption_rect = caption.get_rect(center=(size[0] // 2, size[1] - 34))
    panel.blit(caption, caption_rect)
    return panel

def run_menu(screen, clock):
    """منوی آغازین را نمایش می‌دهد و انتخاب بازیکنان سفید و سیاه را دریافت می‌کند."""
    screen_width, screen_height = screen.get_size()
    art_width = min(500, max(300, int(screen_width * 0.36)))
    content_width = screen_width - art_width
    art_rect = pygame.Rect(content_width, 0, art_width, screen_height)

    image_path = (
        Path(__file__).parent / "Offline Multi-Agent Chess Environment-image.jpg"
    )
    try:
        menu_image = pygame.image.load(str(image_path)).convert()
    except (pygame.error, OSError):
        menu_image = None
    menu_art = prepare_menu_art(menu_image, art_rect.size)

    white_player = "Human"
    black_player = "Aggressive"

    title_font = get_font(38, True)
    subtitle_font = get_font(16)
    font = get_font(20)
    description_font = get_font(13)
    hint_font = get_font(15)

    padding = max(20, int(content_width * 0.045))
    card_width = content_width - 2 * padding
    card_height = max(150, min(180, int(screen_height * 0.25)))
    card_gap = max(14, int(screen_height * 0.025))
    first_card_y = int(screen_height * 0.22)
    cards = {
        chess.WHITE: pygame.Rect(padding, first_card_y, card_width, card_height),
        chess.BLACK: pygame.Rect(
            padding,
            first_card_y + card_height + card_gap,
            card_width,
            card_height,
        ),
    }
    start_button = pygame.Rect(
        max(12, (content_width - 300) // 2),
        screen_height - 82,
        min(300, content_width - 24),
        58,
    )

    while True:
        screen.fill(BACKGROUND)
        screen.blit(menu_art, art_rect.topleft)

        title = title_font.render("CHESS ARENA", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(content_width // 2, 58)))

        subtitle = subtitle_font.render(
            "OFFLINE MULTI-AGENT CHESS", True, (170, 190, 215)
        )
        screen.blit(subtitle, subtitle.get_rect(center=(content_width // 2, 100)))

        for color, label in (
            (chess.WHITE, "WHITE PLAYER"),
            (chess.BLACK, "BLACK PLAYER"),
        ):
            card = cards[color]
            pygame.draw.rect(screen, PANEL_COLOR, card, border_radius=15)
            pygame.draw.rect(screen, (67, 77, 98), card, 1, border_radius=15)

            draw_text(screen, label, font, (240, 240, 245), card.x + 20, card.y + 14)

            # اگر کارت متعلق به سفید باشد، انتخاب سفید به‌روز می‌شود.
            selected = white_player if color == chess.WHITE else black_player
            arrow_y = card.y + 48
            left_button = pygame.Rect(card.x + 18, arrow_y, 44, 38)
            right_button = pygame.Rect(card.right - 62, arrow_y, 44, 38)
            option_rect = pygame.Rect(
                left_button.right + 10,
                arrow_y,
                max(80, right_button.x - left_button.right - 20),
                38,
            )
            draw_button(screen, left_button, "<", font)
            draw_button(screen, right_button, ">", font)
            pygame.draw.rect(screen, (55, 62, 75), option_rect, border_radius=8)
            selected_image = font.render(selected, True, (255, 255, 255))
            screen.blit(
                selected_image, selected_image.get_rect(center=option_rect.center)
            )

            description_lines = AGENT_DESCRIPTIONS[selected].split("\n")
            description_y = card.y + 99
            line_height = 19
            for index, line in enumerate(description_lines[:3]):
                draw_persian_text(
                    screen,
                    line,
                    description_font,
                    (205, 215, 228),
                    (card.centerx, description_y + index * line_height),
                )

        draw_text(
            screen,
            "Choose players",
            hint_font,
            (170, 180, 195),
            padding + 4,
            cards[chess.BLACK].bottom + 8,
        )
        draw_button(screen, start_button, "START GAME", title_font, ACCENT_COLOR)

        pygame.display.flip()

        for event in pygame.event.get():
            # اگر کاربر پنجره را ببندد، منو پایان می‌یابد.
            if event.type == pygame.QUIT:
                return None

            # اگر رویداد کلیک چپ نباشد، آن را نادیده می‌گیریم.
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            position = event.pos
            for color, card in cards.items():
                left_button = pygame.Rect(card.x + 18, card.y + 48, 44, 38)
                right_button = pygame.Rect(card.right - 62, card.y + 48, 44, 38)
                # اگر کارت متعلق به سفید باشد، انتخاب سفید به‌روز می‌شود.
                current = white_player if color == chess.WHITE else black_player
                index = PLAYER_OPTIONS.index(current)

                # اگر پیکان چپ فشرده شده باشد، گزینهٔ قبلی انتخاب می‌شود.
                if left_button.collidepoint(position):
                    index = (index - 1) % len(PLAYER_OPTIONS)
                # اگر پیکان راست فشرده شده باشد، گزینهٔ بعدی انتخاب می‌شود.
                elif right_button.collidepoint(position):
                    index = (index + 1) % len(PLAYER_OPTIONS)
                # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.
                else:
                    continue

                # اگر کارت متعلق به سفید باشد، انتخاب سفید به‌روز می‌شود.
                if color == chess.WHITE:
                    white_player = PLAYER_OPTIONS[index]
                # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.
                else:
                    black_player = PLAYER_OPTIONS[index]

            # اگر دکمهٔ شروع فشرده شود، انتخاب بازیکنان به بازی برگردانده می‌شود.
            if start_button.collidepoint(position):
                return {
                    chess.WHITE: white_player,
                    chess.BLACK: black_player,
                }

        clock.tick(60)

# رسم مهره
# ──────────────────────────────────────────

def draw_piece(screen, piece, rect, font):

    # اگر خانه خالی باشد، رسم مهره لازم نیست.
    """مهره را با تصویر آن یا با نماد متنی جایگزین روی خانه رسم می‌کند."""
    if piece is None:
        return

    key = (piece.color, piece.piece_type)

    # اگر تصویر مهره موجود باشد، همان تصویر رسم می‌شود.
    if key in PIECE_IMAGES:

        image = PIECE_IMAGES[key]

        screen.blit(image, image.get_rect(center=rect.center))

    # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.

    else:

        # این مقدار بر اساس برقرار بودن شرط «piece.color == chess.WHITE» انتخاب می‌شود.
        fill = (245, 245, 240) if piece.color == chess.WHITE else (40, 40, 45)

        # این مقدار بر اساس برقرار بودن شرط «piece.color == chess.WHITE» انتخاب می‌شود.
        text_color = (35, 35, 35) if piece.color == chess.WHITE else (245, 245, 245)

        pygame.draw.circle(screen, fill, rect.center, 27)

        pygame.draw.circle(screen, text_color, rect.center, 27, 2)

        image = font.render(piece.symbol().upper(), True, text_color)

        screen.blit(image, image.get_rect(center=rect.center))

# رسم صفحهٔ شطرنج

def draw_board(screen, engine, selected, font, last_move=None):
    """خانه‌ها، مقصدهای قانونی، مهره‌ها و حرکت آخر را روی صفحه رسم می‌کند."""
    board = engine.board

    legal_targets = []

    # اگر خانه‌ای انتخاب شده باشد، مقصدهای قانونی آن را پیدا می‌کنیم.
    if selected is not None:

        legal_targets = [move.to_square for move in engine.legal_moves_from(selected)]

    for row in range(8):

        for col in range(8):

            square = chess.square(col, 7 - row)

            rect = pygame.Rect(
                col * SQUARE_SIZE,
                BOARD_TOP + row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            )

            # این مقدار بر اساس برقرار بودن شرط «(row + col) % 2 == 0» انتخاب می‌شود.
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

            pygame.draw.rect(screen, color, rect)

            # اگر شرط «last_move is not None and square in ( last_move.from_square, last_move.to_square )» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
            if last_move is not None and square in (
                last_move.from_square,
                last_move.to_square,
            ):
                pygame.draw.rect(screen, (205, 190, 75), rect, 5)

            # اگر این خانه انتخاب‌شده باشد، کادر انتخاب را رسم می‌کنیم.
            if square == selected:

                pygame.draw.rect(screen, (255, 220, 0), rect, 4)

            # اگر خانه مقصد قانونی باشد، نشانگر مقصد را رسم می‌کنیم.
            if square in legal_targets:

                # اگر مقصد خالی باشد، نقطهٔ کوچک نشان داده می‌شود.
                if board.piece_at(square) is None:

                    pygame.draw.circle(screen, (40, 100, 40), rect.center, 10)

                # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.

                else:

                    pygame.draw.circle(screen, (40, 100, 40), rect.center, 35, 4)

    # مهره‌ها را پس از خانه‌ها و نشانگرهای صفحه رسم می‌کنیم.
    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            rect = pygame.Rect(
                col * SQUARE_SIZE,
                BOARD_TOP + row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            )
            draw_piece(screen, engine.piece_at(square), rect, font)

    # اگر حرکت قبلی وجود داشته باشد، مسیر آن را با فلش نشان می‌دهیم.
    if last_move is not None:
        draw_move_arrow(screen, last_move)

def draw_move_arrow(screen, move):
    """فلش نیمه‌شفاف مسیر حرکت را از خانهٔ مبدأ تا مقصد می‌کشد."""
    start = (
        chess.square_file(move.from_square) * SQUARE_SIZE + SQUARE_SIZE // 2,
        (7 - chess.square_rank(move.from_square)) * SQUARE_SIZE + SQUARE_SIZE // 2,
    )
    target = (
        chess.square_file(move.to_square) * SQUARE_SIZE + SQUARE_SIZE // 2,
        (7 - chess.square_rank(move.to_square)) * SQUARE_SIZE + SQUARE_SIZE // 2,
    )
    dx = target[0] - start[0]
    dy = target[1] - start[1]
    distance = math.hypot(dx, dy)
    # اگر طول حرکت صفر باشد، رسم فلش ممکن نیست و برمی‌گردیم.
    if distance == 0:
        return

    direction = (dx / distance, dy / distance)
    tip = (
        target[0] - direction[0] * 25 * UI_SCALE,
        target[1] - direction[1] * 25 * UI_SCALE,
    )
    base = (
        tip[0] - direction[0] * 18 * UI_SCALE,
        tip[1] - direction[1] * 18 * UI_SCALE,
    )
    perpendicular = (-direction[1], direction[0])
    wing = 12 * UI_SCALE
    arrowhead = [
        (round(tip[0]), round(tip[1])),
        (
            round(base[0] + perpendicular[0] * wing),
            round(base[1] + perpendicular[1] * wing),
        ),
        (
            round(base[0] - perpendicular[0] * wing),
            round(base[1] - perpendicular[1] * wing),
        ),
    ]

    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    pygame.draw.line(
        overlay, (10, 35, 48, 175), start, tip, max(5, round(13 * UI_SCALE))
    )
    pygame.draw.polygon(overlay, (10, 35, 48, 175), arrowhead)
    pygame.draw.line(
        overlay, (55, 225, 190, 200), start, tip, max(3, round(7 * UI_SCALE))
    )
    pygame.draw.polygon(overlay, (55, 225, 190, 220), arrowhead)
    screen.blit(overlay, (0, BOARD_TOP))

# وضعیت بازی

def get_status_info(engine):
    """نوع وضعیت بازی، عنوان، توضیح کوتاه و رنگ نشانگر آن را برمی‌گرداند."""
    board = engine.board

    # اگر بازی تمام شده باشد، نتیجهٔ آن را برای نمایش آماده می‌کنیم.
    if engine.is_game_over():
        outcome = engine.outcome()
        # اگر برنده مشخص باشد، وضعیت برد را نمایش می‌دهیم.
        if outcome.winner is not None:
            # این مقدار بر اساس برقرار بودن شرط «outcome.winner == chess.WHITE» انتخاب می‌شود.
            winner = "WHITE" if outcome.winner == chess.WHITE else "BLACK"
            # اگر پایان با مات باشد، نشانگر قرمز انتخاب می‌شود.
            if outcome.termination == chess.Termination.CHECKMATE:
                return "mate", f"{winner} WINS", "Checkmate", (235, 80, 80)
            return "win", f"{winner} WINS", "Game complete", (83, 190, 135)

        # این مقدار بر اساس برقرار بودن شرط «outcome» انتخاب می‌شود.
        termination = outcome.termination.name if outcome else "DRAW"
        draw_labels = {
            "STALEMATE": ("STALEMATE", "No legal moves"),
            "INSUFFICIENT_MATERIAL": ("DRAW", "Insufficient material"),
            "FIFTY_MOVES": ("DRAW", "50-move rule"),
            "SEVENTYFIVE_MOVES": ("DRAW", "75-move rule"),
            "THREEFOLD_REPETITION": ("DRAW", "Position repeated"),
            "FIVEFOLD_REPETITION": ("DRAW", "Position repeated"),
            "VARIANT_DRAW": ("DRAW", "Lone-king limit"),
        }
        title, detail = draw_labels.get(termination, ("DRAW", "Game drawn"))
        return "draw", title, detail, (225, 184, 83)

    # این مقدار بر اساس برقرار بودن شرط «board.turn == chess.WHITE» انتخاب می‌شود.
    side = "WHITE" if board.turn == chess.WHITE else "BLACK"
    # اگر شاه نوبت جاری در کیش باشد، نشانگر هشدار را برمی‌گردانیم.
    if board.is_check():
        return "check", "CHECK!", f"{side.title()} king is attacked", (238, 195, 66)

    return "turn", f"{side} TO MOVE", "Game in progress", (60, 205, 115)

def draw_status_indicator(screen, center, color):
    """چراغ رنگی وضعیت بازی را در مرکز داده‌شده رسم می‌کند."""
    x, y = center
    radius = max(10, round(14 * UI_SCALE))
    pygame.draw.circle(screen, tuple(channel // 3 for channel in color), center, radius)
    pygame.draw.circle(screen, color, center, max(6, round(9 * UI_SCALE)))
    pygame.draw.circle(
        screen,
        (245, 248, 250),
        (x - max(1, round(2 * UI_SCALE)), y - max(1, round(3 * UI_SCALE))),
        max(1, round(2 * UI_SCALE)),
    )

def draw_status_card(screen, rect, engine, font):
    """کارت وضعیت را با چراغ، عنوان و توضیح بازی نمایش می‌دهد."""
    kind, title, detail, accent = get_status_info(engine)
    pygame.draw.rect(screen, (53, 59, 72), rect, border_radius=12)
    pygame.draw.rect(screen, accent, rect, width=2, border_radius=12)

    icon_center = (rect.x + round(28 * UI_SCALE), rect.centery)
    draw_status_indicator(screen, icon_center, accent)

    title_font = get_font(max(12, round(14 * UI_SCALE)), True)
    detail_font = get_font(max(10, round(12 * UI_SCALE)))
    text_x = rect.x + round(55 * UI_SCALE)
    draw_text(
        screen,
        title,
        title_font,
        (248, 248, 250),
        text_x,
        rect.y + round(22 * UI_SCALE),
    )
    draw_text(
        screen,
        detail,
        detail_font,
        (194, 201, 212),
        text_x,
        rect.y + round(47 * UI_SCALE),
    )

# رسم پنل اطلاعات بازی

def draw_game_panel(screen, player_types, engine, font):
    """پنل اطلاعات بازی را متناسب با اندازهٔ صفحه رسم می‌کند."""
    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        pygame.Rect(BOARD_SIZE, 0, PANEL_WIDTH, WINDOW_HEIGHT),
    )

    scale = UI_SCALE
    panel_x = BOARD_SIZE + (PANEL_WIDTH - PANEL_CONTENT_WIDTH) // 2
    panel_right = panel_x + PANEL_CONTENT_WIDTH

    def px(value):
        """مقدار طراحی پایه را با مقیاس رابط کاربری تنظیم می‌کند."""
        return round(value * scale)

    draw_text(screen, "GAME INFO", font, (255, 255, 255), panel_x + px(25), px(35))
    draw_text(screen, "WHITE", font, (230, 230, 230), panel_x + px(25), px(105))
    draw_text(
        screen,
        player_types[chess.WHITE],
        font,
        (120, 210, 160),
        panel_x + px(25),
        px(140),
    )
    draw_text(screen, "BLACK", font, (230, 230, 230), panel_x + px(25), px(205))
    draw_text(
        screen,
        player_types[chess.BLACK],
        font,
        (120, 210, 160),
        panel_x + px(25),
        px(240),
    )

    pygame.draw.line(
        screen,
        (90, 95, 110),
        (panel_x + px(20), px(300)),
        (panel_right - px(20), px(300)),
        max(1, px(2)),
    )

    status_header_font = get_font(max(15, px(19)), True)
    draw_text(
        screen,
        "TURN STATUS",
        status_header_font,
        (15, 19, 27),
        panel_x + px(27),
        px(338),
    )
    draw_text(
        screen,
        "TURN STATUS",
        status_header_font,
        (255, 255, 255),
        panel_x + px(25),
        px(335),
    )

    card_padding = px(15)
    draw_status_card(
        screen,
        pygame.Rect(
            panel_x + card_padding,
            px(370),
            max(180, PANEL_CONTENT_WIDTH - 2 * card_padding),
            px(82),
        ),
        engine,
        font,
    )

    draw_text(screen, "R : Restart", font, (190, 190, 200), panel_x + px(25), px(480))
    draw_text(screen, "M : Main Menu", font, (190, 190, 200), panel_x + px(25), px(520))
    draw_text(screen, "ESC : Exit", font, (190, 190, 200), panel_x + px(25), px(560))

# حلقهٔ بازی
# ──────────────────────────────────────────

def play_game(screen, clock, player_types):
    """حلقهٔ بازی را اجرا و حرکت انسان یا ایجنت را مدیریت می‌کند."""
    engine = ChessEngine()

    selected_square = None
    last_move = None
    next_agent_move_at = 0

    piece_font = get_font(max(18, round(30 * UI_SCALE)), True)
    info_font = get_font(max(14, round(18 * UI_SCALE)))

    # ایجنت‌های انتخاب‌شده را می‌سازیم.
    agents = {}

    for color in [chess.WHITE, chess.BLACK]:

        player_type = player_types[color]

        # اگر بازیکن انسان نباشد، نمونهٔ ایجنت ساخته می‌شود.
        if player_type != "Human":

            agents[color] = create_agent(player_type)

    # اگر نوبت آغازین متعلق به ایجنت باشد، زمان اولین حرکت تنظیم می‌شود.
    if player_types[engine.board.turn] != "Human":
        next_agent_move_at = pygame.time.get_ticks() + next_agent_move_delay()

    while True:

        for event in pygame.event.get():

            # اگر کاربر پنجره را ببندد، منو پایان می‌یابد.
            if event.type == pygame.QUIT:
                return "exit"

            # اگر رویداد فشردن کلید باشد، میانبرهای بازی بررسی می‌شوند.
            if event.type == pygame.KEYDOWN:

                # اگر Escape فشرده شود، بازی بسته می‌شود.
                if event.key == pygame.K_ESCAPE:
                    return "exit"

                # اگر M فشرده شود، بازی به منو بازمی‌گردد.
                if event.key == pygame.K_m:
                    return "menu"

                # اگر R فشرده شود، صفحه و انتخاب حرکت بازنشانی می‌شوند.
                if event.key == pygame.K_r:

                    engine.reset()

                    selected_square = None
                    last_move = None
                    # اگر نوبت آغازین متعلق به ایجنت باشد، زمان اولین حرکت تنظیم می‌شود.
                    next_agent_move_at = (
                        pygame.time.get_ticks() + next_agent_move_delay()
                        if player_types[engine.board.turn] != "Human"
                        else 0
                    )

            # ورودی حرکت انسان را پردازش می‌کنیم.
            # اگر دکمهٔ ماوس فشرده شود، ورودی حرکت انسان بررسی می‌شود.
            if event.type == pygame.MOUSEBUTTONDOWN:

                # اگر کلیک چپ نباشد، رویداد نادیده گرفته می‌شود.
                if event.button != 1:
                    continue

                # اگر بازی تمام شده باشد، نتیجهٔ آن را برای نمایش آماده می‌کنیم.
                if engine.is_game_over():
                    continue

                current_color = engine.board.turn

                # اگر شرط «player_types[current_color] != "Human"» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
                if player_types[current_color] != "Human":
                    continue

                x, y = event.pos

                # اگر شرط «x >= BOARD_SIZE or y < BOARD_TOP or y >= BOARD_TOP + BOARD_SIZE» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
                if x >= BOARD_SIZE or y < BOARD_TOP or y >= BOARD_TOP + BOARD_SIZE:
                    continue

                col = x // SQUARE_SIZE
                row = (y - BOARD_TOP) // SQUARE_SIZE

                clicked_square = chess.square(col, 7 - row)

                piece = engine.piece_at(clicked_square)

                # اگر مهره‌ای انتخاب نشده باشد، خانهٔ کلیک‌شده بررسی می‌شود.
                if selected_square is None:

                    # اگر شرط «piece and piece.color == current_color» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
                    if piece and piece.color == current_color:
                        selected_square = clicked_square

                # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.

                else:

                    candidates = [
                        move
                        for move in engine.legal_moves_from(selected_square)
                        if move.to_square == clicked_square
                    ]

                    # اگر مقصد حرکت قانونی باشد، حرکت را اجرا می‌کنیم.
                    if candidates:

                        # ارتقای پیاده در رابط به‌طور خودکار به وزیر انجام می‌شود.
                        move = next(
                            (m for m in candidates if m.promotion == chess.QUEEN),
                            candidates[0],
                        )

                        engine.make_move(move)
                        last_move = move
                        next_agent_move_at = (
                            pygame.time.get_ticks() + next_agent_move_delay()
                        )

                        selected_square = None

                    # اگر شرط «piece and piece.color == current_color» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
                    elif piece and piece.color == current_color:

                        selected_square = clicked_square

                    # اگر شرط‌های پیشین برقرار نباشند، مسیر جایگزین اجرا می‌شود.

                    else:

                        selected_square = None

        # اگر بازی ادامه دارد، نوبت عامل بررسی می‌شود.
        if not engine.is_game_over():

            current_color = engine.board.turn

            # اگر شرط «player_types[current_color] != "Human" and pygame.time.get_ticks() >= next_agent_move_at» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
            if (
                player_types[current_color] != "Human"
                and pygame.time.get_ticks() >= next_agent_move_at
            ):

                agent = agents[current_color]

                move = agent.choose_move(engine.get_board_copy())

                # اگر ایجنت حرکتی برگرداند، آن را اجرا می‌کنیم.
                if move is not None:
                    engine.make_move(move)
                    last_move = move
                    next_agent_move_at = (
                        pygame.time.get_ticks() + next_agent_move_delay()
                    )

                selected_square = None

        # صفحه و پنل بازی را رسم می‌کنیم.
        screen.fill(BACKGROUND)

        draw_board(screen, engine, selected_square, piece_font, last_move)

        draw_game_panel(screen, player_types, engine, info_font)

        pygame.display.flip()

        clock.tick(60)

# نقطهٔ ورود برنامه

def main():
    """Pygame را راه‌اندازی می‌کند و منو و بازی را تا زمان خروج اجرا می‌کند."""
    global BOARD_SIZE, SQUARE_SIZE, PANEL_WIDTH, WINDOW_WIDTH, WINDOW_HEIGHT
    global BOARD_TOP, UI_SCALE, PANEL_CONTENT_WIDTH

    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_width, screen_height = screen.get_size()

    # اندازهٔ صفحه را طوری محاسبه می‌کنیم که خانه‌ها مربع بمانند و پنل فضای باقی‌مانده را بگیرد.
    board_limit = min(screen_height, int(screen_width * 0.68))
    SQUARE_SIZE = max(1, board_limit // 8)
    BOARD_SIZE = SQUARE_SIZE * 8
    PANEL_WIDTH = screen_width - BOARD_SIZE
    WINDOW_WIDTH = screen_width
    WINDOW_HEIGHT = screen_height
    BOARD_TOP = (screen_height - BOARD_SIZE) // 2
    UI_SCALE = SQUARE_SIZE / 80
    panel_padding = round(16 * UI_SCALE)
    PANEL_CONTENT_WIDTH = min(
        PANEL_WIDTH - 2 * panel_padding,
        round(360 * UI_SCALE),
    )

    pygame.display.set_caption("Offline Multi-Agent Chess")

    clock = pygame.time.Clock()

    load_piece_images()

    while True:

        # منوی آغازین را نمایش می‌دهیم.
        player_types = run_menu(screen, clock)

        # اگر منو درخواست خروج بدهد، حلقهٔ اصلی پایان می‌یابد.
        if player_types is None:
            break

        # بازی را با بازیکنان انتخاب‌شده آغاز می‌کنیم.
        result = play_game(screen, clock, player_types)

        # اگر صفحهٔ بازی خروج را برگرداند، برنامه بسته می‌شود.
        if result == "exit":
            break

    pygame.quit()

# اگر شرط «__name__ == "__main__"» برقرار باشد، شاخهٔ زیر اجرا می‌شود.
if __name__ == "__main__":
    main()
