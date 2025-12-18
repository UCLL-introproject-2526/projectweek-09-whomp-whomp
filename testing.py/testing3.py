import pygame
import random
import sys

pygame.init()

# ================= CONSTANTS =================
WIDTH, HEIGHT = 900, 600
ROOM_W, ROOM_H = 1600, 1200
FPS = 60

PLAYER_SPEED = 5
PLAYER_HP = 5
ATTACK_RANGE = 40
ATTACK_COOLDOWN = 300

COLORS = {
    "bg": (40, 30, 50),
    "player": (80, 150, 255),
    "enemy": (100, 220, 120),
    "red": (220, 60, 60),
    "white": (255, 255, 255),
}

# ================= SETUP =================
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ================= PLAYER =================
player = {
    "rect": pygame.Rect(WIDTH//2, HEIGHT//2, 40, 50),
    "dir": "down",
    "hp": PLAYER_HP,
    "last_hit": 0,
    "last_attack": 0,
}

# ================= ENEMIES =================
def make_enemy(x, y):
    return {
        "rect": pygame.Rect(x, y, 32, 32),
        "hp": 3,
        "dx": random.choice([-2, 2]),
        "dy": random.choice([-2, 2]),
    }

enemies = [make_enemy(300, 300), make_enemy(700, 500)]

# ================= CAMERA =================
def camera():
    x = max(0, min(player["rect"].centerx - WIDTH//2, ROOM_W - WIDTH))
    y = max(0, min(player["rect"].centery - HEIGHT//2, ROOM_H - HEIGHT))
    return x, y

# ================= GAME LOOP =================
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Movement
    vx = vy = 0
    if keys[pygame.K_a]: vx = -PLAYER_SPEED; player["dir"] = "left"
    if keys[pygame.K_d]: vx = PLAYER_SPEED; player["dir"] = "right"
    if keys[pygame.K_w]: vy = -PLAYER_SPEED; player["dir"] = "up"
    if keys[pygame.K_s]: vy = PLAYER_SPEED; player["dir"] = "down"

    player["rect"].x += vx
    player["rect"].y += vy
    player["rect"].clamp_ip((0, 0, ROOM_W, ROOM_H))

    # Attack
    now = pygame.time.get_ticks()
    if keys[pygame.K_SPACE] and now - player["last_attack"] > ATTACK_COOLDOWN:
        player["last_attack"] = now
        atk = player["rect"].inflate(ATTACK_RANGE, ATTACK_RANGE)
        for en in enemies:
            if atk.colliderect(en["rect"]):
                en["hp"] -= 1

    # Update enemies
    for en in enemies:
        if en["hp"] <= 0:
            continue
        en["rect"].x += en["dx"]
        en["rect"].y += en["dy"]

    enemies = [e for e in enemies if e["hp"] > 0]

    # Draw
    cam_x, cam_y = camera()
    screen.fill(COLORS["bg"])

    for en in enemies:
        r = en["rect"].move(-cam_x, -cam_y)
        pygame.draw.rect(screen, COLORS["enemy"], r)

    pr = player["rect"].move(-cam_x, -cam_y)
    pygame.draw.rect(screen, COLORS["player"], pr)

    hp = font.render(f"HP: {player['hp']}", True, COLORS["white"])
    screen.blit(hp, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
