
import pygame
import chess
import math
import random
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display

from chess_engine import ChessEngine
from agents import create_agent


# ==========================================
# Configuration
# ==========================================

BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8

PANEL_WIDTH = 260
WINDOW_WIDTH = BOARD_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = 700
AGENT_MOVE_MIN_MS = 3000
AGENT_MOVE_MAX_MS = 6000


def next_agent_move_delay():
    return random.randint(AGENT_MOVE_MIN_MS, AGENT_MOVE_MAX_MS)

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

BACKGROUND = (30, 32, 40)
PANEL_COLOR = (43, 46, 56)
BUTTON_COLOR = (65, 72, 88)
ACCENT_COLOR = (70, 145, 110)

ASSETS_DIR = Path(__file__).parent / "assets"

PLAYER_OPTIONS = [
    "Human",
    "Aggressive",
    "Defensive",
    "Material",
    "Positional"
]

AGENT_DESCRIPTIONS = {
    "Human": (
        "بازیکن انسانی\n"
        "تمام تصمیمات و انتخاب حرکت‌ها توسط خود شما انجام می‌شود."
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
    )
}

PIECE_NAMES = {
    chess.PAWN: "pawn",
    chess.ROOK: "rook",
    chess.KNIGHT: "knight",
    chess.BISHOP: "bishop",
    chess.QUEEN: "queen",
    chess.KING: "king"
}

PIECE_IMAGES = {}


# ==========================================
# Fonts
# ==========================================

def draw_persian_text(screen, text, font, color, center):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)

    text_surface = font.render(
        bidi_text,
        True,
        color
    )

    text_rect = text_surface.get_rect(
        center=center
    )

    screen.blit(text_surface, text_rect)

def get_font(size, bold=False):

    font_path = "fonts/Vazirmatn-Regular.ttf"

    return pygame.font.Font(font_path, size)


# ==========================================
# Draw Text
# ==========================================

def draw_text(screen, text, font, color, x, y):

    image = font.render(
        text,
        True,
        color
    )

    screen.blit(image, (x, y))


# ==========================================
# Draw Button
# ==========================================

def draw_button(screen, rect, text, font,
                color=BUTTON_COLOR):

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=10
    )

    image = font.render(
        text,
        True,
        (255, 255, 255)
    )

    screen.blit(
        image,
        image.get_rect(center=rect.center)
    )


# ==========================================
# Load Piece Images
# ==========================================

def load_piece_images():

    for color, color_name in [
        (chess.WHITE, "white"),
        (chess.BLACK, "black")
    ]:

        for piece_type, piece_name in PIECE_NAMES.items():

            path = (
                ASSETS_DIR /
                f"{color_name}_{piece_name}.png"
            )

            if not path.exists():
                continue

            image = pygame.image.load(
                str(path)
            ).convert_alpha()

            width, height = image.get_size()

            scale = min(
                SQUARE_SIZE * 0.82 / width,
                SQUARE_SIZE * 0.82 / height
            )

            image = pygame.transform.smoothscale(
                image,
                (
                    int(width * scale),
                    int(height * scale)
                )
            )

            PIECE_IMAGES[
                (color, piece_type)
            ] = image


# ==========================================
# Start Menu
# ==========================================
def draw_agent_description(screen, font, player_type, x, y, width):
    description = AGENT_DESCRIPTIONS[player_type]

    lines = description.split("\n")

    line_height = 27

    for index, line in enumerate(lines):
        color = (255, 215, 120) if index == 0 else (210, 210, 210)

        text_surface = font.render(line, True, color)

        text_rect = text_surface.get_rect(
            center=(x + width // 2, y + index * line_height)
        )

        screen.blit(text_surface, text_rect)

def prepare_menu_art(image, size):
    """Scale and frame the cover image once when the menu opens."""
    panel = pygame.Surface(size).convert()
    panel.fill((10, 18, 42))

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
    screen_width, screen_height = screen.get_size()
    art_width = min(500, max(300, int(screen_width * 0.36)))
    content_width = screen_width - art_width
    art_rect = pygame.Rect(content_width, 0, art_width, screen_height)

    image_path = Path(__file__).parent / "Offline Multi-Agent Chess Environment-image.jpg"
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
            screen.blit(selected_image, selected_image.get_rect(center=option_rect.center))

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
            "Use the arrows to choose players",
            hint_font,
            (170, 180, 195),
            padding + 4,
            cards[chess.BLACK].bottom + 8,
        )
        draw_button(screen, start_button, "START GAME", title_font, ACCENT_COLOR)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            position = event.pos
            for color, card in cards.items():
                left_button = pygame.Rect(card.x + 18, card.y + 48, 44, 38)
                right_button = pygame.Rect(card.right - 62, card.y + 48, 44, 38)
                current = white_player if color == chess.WHITE else black_player
                index = PLAYER_OPTIONS.index(current)

                if left_button.collidepoint(position):
                    index = (index - 1) % len(PLAYER_OPTIONS)
                elif right_button.collidepoint(position):
                    index = (index + 1) % len(PLAYER_OPTIONS)
                else:
                    continue

                if color == chess.WHITE:
                    white_player = PLAYER_OPTIONS[index]
                else:
                    black_player = PLAYER_OPTIONS[index]

            if start_button.collidepoint(position):
                return {
                    chess.WHITE: white_player,
                    chess.BLACK: black_player,
                }

        clock.tick(60)

# Draw Piece
# ==========================================

def draw_piece(screen, piece, rect, font):

    if piece is None:
        return

    key = (
        piece.color,
        piece.piece_type
    )

    if key in PIECE_IMAGES:

        image = PIECE_IMAGES[key]

        screen.blit(
            image,
            image.get_rect(center=rect.center)
        )

    else:

        fill = (
            (245, 245, 240)
            if piece.color == chess.WHITE
            else (40, 40, 45)
        )

        text_color = (
            (35, 35, 35)
            if piece.color == chess.WHITE
            else (245, 245, 245)
        )

        pygame.draw.circle(
            screen,
            fill,
            rect.center,
            27
        )

        pygame.draw.circle(
            screen,
            text_color,
            rect.center,
            27,
            2
        )

        image = font.render(
            piece.symbol().upper(),
            True,
            text_color
        )

        screen.blit(
            image,
            image.get_rect(center=rect.center)
        )


# ==========================================
# Draw Board
# ==========================================

def draw_board(screen, engine, selected, font, last_move=None):

    board = engine.board

    legal_targets = []

    if selected is not None:

        legal_targets = [
            move.to_square
            for move in engine.legal_moves_from(selected)
        ]

    for row in range(8):

        for col in range(8):

            square = chess.square(
                col,
                7 - row
            )

            rect = pygame.Rect(
                col * SQUARE_SIZE,
                row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )

            color = (
                LIGHT_SQUARE
                if (row + col) % 2 == 0
                else DARK_SQUARE
            )

            pygame.draw.rect(
                screen,
                color,
                rect
            )

            if last_move is not None and square in (
                last_move.from_square, last_move.to_square
            ):
                pygame.draw.rect(screen, (205, 190, 75), rect, 5)

            if square == selected:

                pygame.draw.rect(
                    screen,
                    (255, 220, 0),
                    rect,
                    4
                )

            if square in legal_targets:

                if board.piece_at(square) is None:

                    pygame.draw.circle(
                        screen,
                        (40, 100, 40),
                        rect.center,
                        10
                    )

                else:

                    pygame.draw.circle(
                        screen,
                        (40, 100, 40),
                        rect.center,
                        35,
                        4
                    )

    # Draw the pieces after the board squares and markers.
    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row)
            rect = pygame.Rect(
                col * SQUARE_SIZE,
                row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            )
            draw_piece(screen, engine.piece_at(square), rect, font)

    if last_move is not None:
        draw_move_arrow(screen, last_move)


def draw_move_arrow(screen, move):
    """Overlay a clear, translucent arrow for the most recent move."""
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
    if distance == 0:
        return

    direction = (dx / distance, dy / distance)
    tip = (
        target[0] - direction[0] * 25,
        target[1] - direction[1] * 25,
    )
    base = (
        tip[0] - direction[0] * 18,
        tip[1] - direction[1] * 18,
    )
    perpendicular = (-direction[1], direction[0])
    wing = 12
    arrowhead = [
        (round(tip[0]), round(tip[1])),
        (round(base[0] + perpendicular[0] * wing),
         round(base[1] + perpendicular[1] * wing)),
        (round(base[0] - perpendicular[0] * wing),
         round(base[1] - perpendicular[1] * wing)),
    ]

    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    pygame.draw.line(overlay, (10, 35, 48, 175), start, tip, 13)
    pygame.draw.polygon(overlay, (10, 35, 48, 175), arrowhead)
    pygame.draw.line(overlay, (55, 225, 190, 200), start, tip, 7)
    pygame.draw.polygon(overlay, (55, 225, 190, 220), arrowhead)
    screen.blit(overlay, (0, 0))


# ==========================================
# Game Status
# ==========================================

def get_status(engine):

    board = engine.board

    if engine.is_game_over():

        outcome = engine.outcome()

        if outcome.winner is None:
            return "Draw"

        return (
            "White wins"
            if outcome.winner == chess.WHITE
            else "Black wins"
        )

    turn = (
        "White"
        if board.turn == chess.WHITE
        else "Black"
    )

    if board.is_check():
        return turn + " to move - Check!"

    return turn + " to move"


# ==========================================
# Draw Game Information
# ==========================================

def draw_game_panel(screen, player_types, engine, font):

    panel_x = BOARD_SIZE

    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        pygame.Rect(
            panel_x,
            0,
            PANEL_WIDTH,
            WINDOW_HEIGHT
        )
    )

    draw_text(
        screen,
        "GAME INFO",
        font,
        (255, 255, 255),
        panel_x + 25,
        35
    )

    draw_text(
        screen,
        "WHITE",
        font,
        (230, 230, 230),
        panel_x + 25,
        105
    )

    draw_text(
        screen,
        player_types[chess.WHITE],
        font,
        (120, 210, 160),
        panel_x + 25,
        140
    )

    draw_text(
        screen,
        "BLACK",
        font,
        (230, 230, 230),
        panel_x + 25,
        205
    )

    draw_text(
        screen,
        player_types[chess.BLACK],
        font,
        (120, 210, 160),
        panel_x + 25,
        240
    )

    pygame.draw.line(
        screen,
        (90, 95, 110),
        (panel_x + 20, 300),
        (WINDOW_WIDTH - 20, 300),
        2
    )

    draw_text(
        screen,
        "STATUS",
        font,
        (255, 255, 255),
        panel_x + 25,
        335
    )

    status = get_status(engine)

    status_image = font.render(
        status,
        True,
        (245, 205, 100)
    )

    screen.blit(
        status_image,
        (panel_x + 25, 375)
    )

    draw_text(
        screen,
        "R : Restart",
        font,
        (190, 190, 200),
        panel_x + 25,
        480
    )

    draw_text(
        screen,
        "M : Main Menu",
        font,
        (190, 190, 200),
        panel_x + 25,
        520
    )

    draw_text(
        screen,
        "ESC : Exit",
        font,
        (190, 190, 200),
        panel_x + 25,
        560
    )


# ==========================================
# Game Loop
# ==========================================

def play_game(screen, clock, player_types):

    engine = ChessEngine()

    selected_square = None
    last_move = None
    next_agent_move_at = 0

    piece_font = get_font(30, True)
    info_font = get_font(18)

    # Create selected agents
    agents = {}

    for color in [chess.WHITE, chess.BLACK]:

        player_type = player_types[color]

        if player_type != "Human":

            agents[color] = create_agent(
                player_type
            )

    if player_types[engine.board.turn] != "Human":
        next_agent_move_at = pygame.time.get_ticks() + next_agent_move_delay()

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return "exit"

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    return "exit"

                if event.key == pygame.K_m:
                    return "menu"

                if event.key == pygame.K_r:

                    engine.reset()

                    selected_square = None
                    last_move = None
                    next_agent_move_at = (
                        pygame.time.get_ticks() + next_agent_move_delay()
                        if player_types[engine.board.turn] != "Human"
                        else 0
                    )

            # Human input
            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button != 1:
                    continue

                if engine.is_game_over():
                    continue

                current_color = engine.board.turn

                if player_types[current_color] != "Human":
                    continue

                x, y = event.pos

                if x >= BOARD_SIZE or y >= BOARD_SIZE:
                    continue

                col = x // SQUARE_SIZE
                row = y // SQUARE_SIZE

                clicked_square = chess.square(
                    col,
                    7 - row
                )

                piece = engine.piece_at(
                    clicked_square
                )

                if selected_square is None:

                    if (
                        piece
                        and piece.color == current_color
                    ):
                        selected_square = clicked_square

                else:

                    candidates = [
                        move
                        for move in engine.legal_moves_from(
                            selected_square
                        )
                        if move.to_square == clicked_square
                    ]

                    if candidates:

                        # Automatic Queen promotion
                        move = next(
                            (
                                m for m in candidates
                                if m.promotion == chess.QUEEN
                            ),
                            candidates[0]
                        )

                        engine.make_move(move)
                        last_move = move
                        next_agent_move_at = (
                            pygame.time.get_ticks() + next_agent_move_delay()
                        )

                        selected_square = None

                    elif (
                        piece
                        and piece.color == current_color
                    ):

                        selected_square = clicked_square

                    else:

                        selected_square = None

        # Agent turn; keep the interface responsive and pace automated moves.
        if not engine.is_game_over():

            current_color = engine.board.turn

            if (player_types[current_color] != "Human"
                    and pygame.time.get_ticks() >= next_agent_move_at):

                agent = agents[current_color]

                move = agent.choose_move(
                    engine.get_board_copy()
                )

                if move is not None:
                    engine.make_move(move)
                    last_move = move
                    next_agent_move_at = (
                        pygame.time.get_ticks() + next_agent_move_delay()
                    )

                selected_square = None

        # Draw screen
        screen.fill(BACKGROUND)

        draw_board(
            screen,
            engine,
            selected_square,
            piece_font,
            last_move
        )

        draw_game_panel(
            screen,
            player_types,
            engine,
            info_font
        )

        pygame.display.flip()

        clock.tick(60)


# ==========================================
# Main
# ==========================================

def main():

    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_size()

    pygame.display.set_caption(
        "Offline Multi-Agent Chess"
    )

    clock = pygame.time.Clock()

    load_piece_images()

    while True:

        # Show start menu
        player_types = run_menu(
            screen,
            clock
        )

        if player_types is None:
            break

        # Start selected game
        result = play_game(
            screen,
            clock,
            player_types
        )

        if result == "exit":
            break

    pygame.quit()


if __name__ == "__main__":
    main()

