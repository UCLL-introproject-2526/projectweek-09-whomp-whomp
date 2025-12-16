import pygame
import sys

# --- Pygame initialisatie ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mystery Chamber: De Schaduwhal")
clock = pygame.time.Clock()

# --- Kleuren ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GRAY = (50, 50, 50)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 100)

# --- Player ---
player_size = 40
player_pos = [100, HEIGHT // 2]
player_speed = 5

# --- Upyr ---
upyr_size = 60
upyr_pos = [600, HEIGHT // 2]
upyr_speed = 2
upyr_health = 3
upyr_visible = True

# --- Deur ---
door = pygame.Rect(WIDTH - 80, HEIGHT//2 - 50, 60, 100)
door_open = False

# --- Kaarsen (lichtbron) ---
candles = [
    pygame.Rect(250, 150, 20, 60),
    pygame.Rect(400, 450, 20, 60),
    pygame.Rect(600, 200, 20, 60)
]

# --- Functies ---
def move_player(keys, pos):
    if keys[pygame.K_w]:
        pos[1] -= player_speed
    if keys[pygame.K_s]:
        pos[1] += player_speed
    if keys[pygame.K_a]:
        pos[0] -= player_speed
    if keys[pygame.K_d]:
        pos[0] += player_speed
    # Grenzen van scherm
    pos[0] = max(0, min(WIDTH - player_size, pos[0]))
    pos[1] = max(0, min(HEIGHT - player_size, pos[1]))

def move_upyr(player_pos, upyr_pos):
    if upyr_visible:
        if upyr_pos[0] < player_pos[0]:
            upyr_pos[0] += upyr_speed
        if upyr_pos[0] > player_pos[0]:
            upyr_pos[0] -= upyr_speed
        if upyr_pos[1] < player_pos[1]:
            upyr_pos[1] += upyr_speed
        if upyr_pos[1] > player_pos[1]:
            upyr_pos[1] -= upyr_speed

def check_collision(rect_list, player_rect):
    for obj in rect_list:
        if player_rect.colliderect(obj):
            return obj
    return None

# --- Main loop ---
running = True
while running:
    clock.tick(60)
    screen.fill(GRAY)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    move_player(keys, player_pos)
    player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
    upyr_rect = pygame.Rect(upyr_pos[0], upyr_pos[1], upyr_size, upyr_size)

    # --- Kaarsen interactie: licht maakt Upyr kwetsbaar ---
    candle_hit = check_collision(candles, player_rect)
    if candle_hit and upyr_health > 0:
        upyr_health -= 1
        print(f"Upyr health: {upyr_health}")
        if upyr_health <= 0:
            upyr_visible = False
            door_open = True

    move_upyr(player_pos, upyr_pos)

    # --- Teken kamer ---
    for candle in candles:
        pygame.draw.rect(screen, YELLOW, candle)
    pygame.draw.rect(screen, WHITE, player_rect)
    if upyr_visible:
        pygame.draw.rect(screen, RED, upyr_rect)
    door_color = GREEN if door_open else (100, 100, 100)
    pygame.draw.rect(screen, door_color, door)

    # --- Check exit ---
    if door_open and player_rect.colliderect(door):
        font = pygame.font.SysFont(None, 48)
        text = font.render("Je hebt de kamer verlaten!", True, WHITE)
        screen.blit(text, (WIDTH//2 - 180, HEIGHT//2))
        pygame.display.update()
        pygame.time.delay(3000)
        running = False

    pygame.display.flip()
