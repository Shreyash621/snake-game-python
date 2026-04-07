"""
====================================================
  SNAKE GAME — Built with Python & Pygame
====================================================
Author   : Generated for Interview-Ready Portfolio
Language : Python 3.x
Library  : pygame

How to Run:
  1. Install pygame:  pip install pygame
  2. Run the game:    python snake_game.py

Controls:
  Arrow Keys → Move snake
  SPACE      → Start game
  P          → Pause / Resume
  R          → Restart (on Game Over screen)
  Q          → Quit (on Game Over screen)
====================================================
"""

import pygame
import sys
import random
import os

# ─────────────────────────────────────────────────
#  CONSTANTS  (easy to tweak, central config)
# ─────────────────────────────────────────────────

# Window
WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 650   # extra 50 px for the HUD strip at the top
HUD_HEIGHT    = 50    # header bar that holds score / title

# Grid
CELL_SIZE  = 20                              # each grid square is 20×20 px
COLS       = WINDOW_WIDTH  // CELL_SIZE      # 30 columns
ROWS       = (WINDOW_HEIGHT - HUD_HEIGHT) // CELL_SIZE  # 30 rows

# Speed (frames per second)
BASE_FPS      = 8    # starting speed
MAX_FPS       = 20   # cap so the game stays playable
FPS_INCREMENT = 0.5  # added for every 5 points scored

# ── Colour palette ──────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
BG_COLOR   = ( 15,  15,  30)   # deep navy background
GRID_COLOR = ( 25,  25,  45)   # subtle grid lines

SNAKE_HEAD  = ( 80, 220, 100)  # bright green head
SNAKE_BODY  = ( 50, 170,  70)  # slightly darker body
SNAKE_EYE   = (  0,   0,   0)  # eye dot

FOOD_COLOR  = (230,  60,  60)  # red food
FOOD_SHINE  = (255, 140, 140)  # highlight on food circle

HUD_BG      = ( 20,  20,  40)
TITLE_COLOR = ( 80, 220, 100)
SCORE_COLOR = (200, 200, 200)
HISC_COLOR  = (255, 215,   0)  # gold for high-score

OVERLAY_BG  = (  0,   0,   0, 180)  # semi-transparent overlay

# Directions (dx, dy)
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# ─────────────────────────────────────────────────
#  SNAKE CLASS
# ─────────────────────────────────────────────────

class Snake:
    """
    Manages the snake's state:
      - body  : list of (col, row) tuples, head = body[0]
      - direction : current movement direction
      - next_dir  : queued direction change (prevents double-turn bugs)
      - growing   : flag set when food is eaten
    """

    def __init__(self):
        # Start in the middle of the grid, moving right
        start_col = COLS // 2
        start_row = ROWS // 2
        self.body      = [(start_col, start_row),
                          (start_col - 1, start_row),
                          (start_col - 2, start_row)]
        self.direction = RIGHT
        self.next_dir  = RIGHT
        self.growing   = False

    # ── direction queuing ───────────────────────
    def change_direction(self, new_dir):
        """
        Queue a direction change.
        Ignores the request if it would instantly reverse the snake
        (e.g. moving RIGHT → cannot go LEFT next step).
        """
        opposite = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
        if new_dir != opposite[self.direction]:
            self.next_dir = new_dir

    # ── movement ────────────────────────────────
    def move(self):
        """
        Advance the snake by one cell.
        Commits the queued direction first so turns feel immediate
        yet safe (no mid-step reversal possible).
        """
        self.direction = self.next_dir          # commit queued direction
        head_col, head_row = self.body[0]
        dc, dr = self.direction
        new_head = (head_col + dc, head_row + dr)

        self.body.insert(0, new_head)           # grow by adding new head

        if self.growing:
            self.growing = False                # keep the extra segment
        else:
            self.body.pop()                     # remove tail to maintain length

    def grow(self):
        """Signal that the snake should grow on the next move."""
        self.growing = True

    @property
    def head(self):
        return self.body[0]

    @property
    def length(self):
        return len(self.body)


# ─────────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────────

def grid_to_pixel(col, row):
    """Convert grid coordinates to top-left pixel of that cell."""
    return col * CELL_SIZE, HUD_HEIGHT + row * CELL_SIZE


def draw_snake(surface, snake):
    """
    Render every snake segment.
    Head gets a distinct colour + small eye dots for personality.
    """
    for i, (col, row) in enumerate(snake.body):
        px, py = grid_to_pixel(col, row)
        rect   = pygame.Rect(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2)

        if i == 0:
            # ── head ──
            pygame.draw.rect(surface, SNAKE_HEAD, rect, border_radius=5)
            _draw_eyes(surface, col, row, snake.direction)
        else:
            # ── body ──
            # Slightly rounded corners give a "chunky" look
            pygame.draw.rect(surface, SNAKE_BODY, rect, border_radius=4)


def _draw_eyes(surface, col, row, direction):
    """
    Draw two tiny eye circles on the snake head
    positioned relative to the movement direction.
    """
    px, py = grid_to_pixel(col, row)
    cx, cy = px + CELL_SIZE // 2, py + CELL_SIZE // 2
    offset = CELL_SIZE // 4

    # Choose eye positions based on direction
    if direction == RIGHT:
        eye_positions = [(cx + offset, cy - 4), (cx + offset, cy + 4)]
    elif direction == LEFT:
        eye_positions = [(cx - offset, cy - 4), (cx - offset, cy + 4)]
    elif direction == UP:
        eye_positions = [(cx - 4, cy - offset), (cx + 4, cy - offset)]
    else:  # DOWN
        eye_positions = [(cx - 4, cy + offset), (cx + 4, cy + offset)]

    for ex, ey in eye_positions:
        pygame.draw.circle(surface, SNAKE_EYE, (ex, ey), 2)


def generate_food(snake_body):
    """
    Pick a random grid cell that is NOT occupied by the snake.
    Keeps retrying until it finds a free cell.
    """
    all_cells  = {(c, r) for c in range(COLS) for r in range(ROWS)}
    snake_set  = set(snake_body)
    free_cells = list(all_cells - snake_set)

    if not free_cells:
        return None  # edge case: snake fills the entire grid (you win!)
    return random.choice(free_cells)


def draw_food(surface, food_pos):
    """
    Render food as a filled circle with a small highlight dot
    to give it a 3-D appearance.
    """
    col, row = food_pos
    px, py   = grid_to_pixel(col, row)
    cx       = px + CELL_SIZE // 2
    cy       = py + CELL_SIZE // 2
    radius   = CELL_SIZE // 2 - 2

    pygame.draw.circle(surface, FOOD_COLOR, (cx, cy), radius)
    # shine highlight (top-left quadrant)
    pygame.draw.circle(surface, FOOD_SHINE, (cx - 3, cy - 3), radius // 3)


def draw_grid(surface):
    """Draw subtle grid lines on the play area."""
    for c in range(COLS + 1):
        x = c * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR,
                         (x, HUD_HEIGHT), (x, WINDOW_HEIGHT))
    for r in range(ROWS + 1):
        y = HUD_HEIGHT + r * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))


def check_collision(snake):
    """
    Return True if the snake has hit a wall OR its own body.
      - Wall : head outside grid bounds
      - Self : head overlaps any body segment
    """
    col, row = snake.head
    # wall collision
    if col < 0 or col >= COLS or row < 0 or row >= ROWS:
        return True
    # self collision (skip head itself → body[1:])
    if snake.head in snake.body[1:]:
        return True
    return False


def show_score(surface, font_small, font_title, score, high_score):
    """Draw the HUD bar at the top with title, score, and high-score."""
    pygame.draw.rect(surface, HUD_BG, (0, 0, WINDOW_WIDTH, HUD_HEIGHT))

    # Title on the left
    title_surf = font_title.render("🐍 Snake", True, TITLE_COLOR)
    surface.blit(title_surf, (10, 8))

    # Score in the centre
    score_surf = font_small.render(f"Score: {score}", True, SCORE_COLOR)
    score_rect = score_surf.get_rect(center=(WINDOW_WIDTH // 2, HUD_HEIGHT // 2))
    surface.blit(score_surf, score_rect)

    # High-score on the right
    hi_surf = font_small.render(f"Best: {high_score}", True, HISC_COLOR)
    hi_rect = hi_surf.get_rect(midright=(WINDOW_WIDTH - 10, HUD_HEIGHT // 2))
    surface.blit(hi_surf, hi_rect)


def _draw_overlay(surface, font_big, font_med, font_small, lines):
    """
    Generic helper: darkens the screen and blits a centred list of text lines.
    `lines` = list of (text, font, color, y_offset_from_center) tuples.
    """
    # Semi-transparent dark overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surface.blit(overlay, (0, 0))

    cx = WINDOW_WIDTH  // 2
    cy = WINDOW_HEIGHT // 2

    for text, font, color, dy in lines:
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(cx, cy + dy))
        surface.blit(surf, rect)


def show_start_screen(surface, font_big, font_med, font_small):
    """Render the initial title / instructions screen."""
    surface.fill(BG_COLOR)
    draw_grid(surface)

    lines = [
        ("SNAKE",             font_big,   TITLE_COLOR, -80),
        ("Classic Edition",   font_small, SCORE_COLOR, -30),
        ("",                  font_small, WHITE,          0),
        ("Arrow Keys  →  Move",  font_small, WHITE,       30),
        ("P           →  Pause", font_small, WHITE,       60),
        ("Press SPACE to Start", font_med,  HISC_COLOR,  120),
    ]
    _draw_overlay(surface, font_big, font_med, font_small, lines)
    pygame.display.flip()


def show_game_over_screen(surface, font_big, font_med, font_small,
                          score, high_score):
    """Render the game-over overlay with final score and options."""
    lines = [
        ("GAME OVER",              font_big,   (220,  60,  60), -90),
        (f"Score: {score}",        font_med,   SCORE_COLOR,     -30),
        (f"Best:  {high_score}",   font_med,   HISC_COLOR,       10),
        ("",                       font_small, WHITE,            50),
        ("R  →  Restart",          font_small, WHITE,            80),
        ("Q  →  Quit",             font_small, WHITE,           110),
    ]
    _draw_overlay(surface, font_big, font_med, font_small, lines)
    pygame.display.flip()


def show_pause_screen(surface, font_big, font_small):
    """Render a simple PAUSED banner."""
    lines = [
        ("PAUSED",             font_big,   HISC_COLOR, -20),
        ("Press P to Resume",  font_small, WHITE,       40),
    ]
    _draw_overlay(surface, font_big, None, font_small, lines)
    pygame.display.flip()


def compute_fps(score):
    """
    Gradually increase game speed every 5 points.
    Capped at MAX_FPS so it never becomes unplayable.
    """
    return min(BASE_FPS + (score // 5) * FPS_INCREMENT, MAX_FPS)


def load_high_score(filepath="high_score.txt"):
    """Read high score from a local file; return 0 if not found."""
    try:
        with open(filepath, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(score, filepath="high_score.txt"):
    """Persist high score to a local file."""
    with open(filepath, "w") as f:
        f.write(str(score))


def play_eat_sound(eat_sound):
    """Play the eating sound if it was loaded successfully."""
    if eat_sound:
        eat_sound.play()


# ─────────────────────────────────────────────────
#  CORE GAME LOOP
# ─────────────────────────────────────────────────

def game_loop(surface, clock, fonts, high_score, eat_sound):
    """
    Main gameplay loop.
    Returns the updated high_score after the session ends.
    """
    font_big, font_med, font_small, font_title = fonts

    # ── Initialise game objects ──────────────────
    snake = Snake()
    food  = generate_food(snake.body)
    score = 0
    paused = False

    while True:
        fps = compute_fps(score)
        clock.tick(fps)            # regulate speed

        # ── Event handling ───────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused

                if not paused:
                    if event.key == pygame.K_UP:
                        snake.change_direction(UP)
                    elif event.key == pygame.K_DOWN:
                        snake.change_direction(DOWN)
                    elif event.key == pygame.K_LEFT:
                        snake.change_direction(LEFT)
                    elif event.key == pygame.K_RIGHT:
                        snake.change_direction(RIGHT)

        # ── Pause ────────────────────────────────
        if paused:
            show_pause_screen(surface, font_big, font_small)
            continue

        # ── Update ───────────────────────────────
        snake.move()

        # Food collision
        if snake.head == food:
            score += 1
            snake.grow()
            play_eat_sound(eat_sound)
            food = generate_food(snake.body)   # spawn new food

            if food is None:
                # Snake fills the board — player wins!
                break

        # Wall / self collision → game over
        if check_collision(snake):
            break

        # ── Draw ─────────────────────────────────
        surface.fill(BG_COLOR)
        draw_grid(surface)
        draw_snake(surface, snake)
        draw_food(surface, food)
        show_score(surface, font_small, font_title, score, high_score)

        pygame.display.flip()

    # ── Session ended ─────────────────────────────
    if score > high_score:
        high_score = score
        save_high_score(high_score)

    return high_score, score


# ─────────────────────────────────────────────────
#  MAIN — entry point
# ─────────────────────────────────────────────────

def main():
    """
    Initialise pygame, set up the window and fonts,
    then drive the state machine:
      START  →  PLAYING  →  GAME OVER  →  (RESTART or QUIT)
    """
    pygame.init()
    pygame.mixer.init()

    # ── Window ───────────────────────────────────
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Snake Game")

    # ── Clock ────────────────────────────────────
    clock = pygame.time.Clock()

    # ── Fonts ────────────────────────────────────
    font_big   = pygame.font.SysFont("Arial", 64, bold=True)
    font_med   = pygame.font.SysFont("Arial", 36, bold=True)
    font_small = pygame.font.SysFont("Arial", 22)
    font_title = pygame.font.SysFont("Arial", 26, bold=True)
    fonts = (font_big, font_med, font_small, font_title)

    # ── Sound (optional) ─────────────────────────
    # Place a file named "eat.wav" alongside the script to enable sound.
    eat_sound = None
    try:
        eat_sound = pygame.mixer.Sound("eat.wav")
        eat_sound.set_volume(0.4)
    except FileNotFoundError:
        pass   # silently continue without sound

    # ── High score ───────────────────────────────
    high_score = load_high_score()

    # ── State machine ────────────────────────────
    state = "START"

    while True:
        # ── START SCREEN ─────────────────────────
        if state == "START":
            show_start_screen(surface, font_big, font_med, font_small)
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            waiting = False
                            state = "PLAYING"

        # ── PLAYING ──────────────────────────────
        elif state == "PLAYING":
            high_score, last_score = game_loop(
                surface, clock, fonts, high_score, eat_sound
            )
            state = "GAME_OVER"

        # ── GAME OVER SCREEN ─────────────────────
        elif state == "GAME_OVER":
            show_game_over_screen(surface, font_big, font_med, font_small,
                                  last_score, high_score)
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            waiting = False
                            state = "PLAYING"
                        elif event.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()


# ─────────────────────────────────────────────────
if __name__ == "__main__":
    main()
