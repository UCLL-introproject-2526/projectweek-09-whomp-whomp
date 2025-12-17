import pygame, sys, random
pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()

ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56)

WHITE = (255,255,255)
RED = (230,50,50)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

# Player
player = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
player_speed = 5
player_dir = "down"
max_hp = 5
hp = max_hp
invul_ms = 500
last_hit = -9999

#Animation
player_frame = 0
animation_speed= 0.2

frame_width, frame_height = 64, 64
player_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\img\player.png").convert_alpha()

def load_spritesheet(sheet, frame_w, frame_h):
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    for y in range(0, sheet_height, frame_h):
        row = []
        for x in range(0, sheet_width, frame_w):
            row.append(sheet.subsurface(pygame.Rect(x, y, frame_w, frame_h)))
        frames.append(row)
    return frames

player_sprites = load_spritesheet(player_spritesheet, frame_width, frame_height)

# Map directions to sheet rows
DIRECTION_ROW = {
    "down": 0,
    "left": 1,
    "right": 2,
    "up": 3
}

# Combat / progression
tokens = 0
has_metal_spear = False
wood_damage = 1
metal_damage = 3
attack_range = 42
attack_cd_ms = 300
last_attack = -9999
popup_msg = None
popup_until = 0

# >>> WEAPON SYSTEM
current_weapon = None

# Enemy helper
def make_enemy(x, y, hp=3, speed=2):
    return {
        "rect": pygame.Rect(x, y, 42, 42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed, speed]),
        "dy": random.choice([-speed, speed])
    }

def make_enemies(amount, speed):
    enemies = []
    for _ in range(amount):
        x = random.randint(50, WIDTH - 90)
        y = random.randint(50, HEIGHT - 90)
        enemies.append(make_enemy(x, y, hp=3, speed=speed))
    return enemies

# >>> WEAPON HELPER
def make_weapon(x, y, wtype, speed=2):
    return {
        "rect": pygame.Rect(x, y, 26, 26),
        "type": wtype,
        "dx": random.choice([-speed, speed]),
        "dy": random.choice([-speed, speed]),
        "picked": False
    }

# Rooms
rooms = {
    "lobby": {
        "color": (32, 12, 36),
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110),
             "target": "kitchen", "spawn": (120, HEIGHT//2)}
        ],
        "enemy": make_enemy(220, 180),
        "weapon": make_weapon(300, 300, "dagger")
    },
    "kitchen": {
        "color": (60, 25, 5),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110),
             "target": "lobby", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH-110, 60, 80, 110),
             "target": "library", "spawn": (WIDTH//2, HEIGHT-140)}
        ],
        "enemy": make_enemy(520, 340, hp=4),
        "weapon": make_weapon(420, 200, "axe")
    },
    "library": {
        "color": (5, 40, 62),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80),
             "target": "kitchen", "spawn": (WIDTH-140, HEIGHT//2)}
        ],
        "enemy": make_enemy(380, 160, hp=5),
        "weapon": make_weapon(250, 250, "spear")
    }
}

current_room = "lobby"

def draw_hud():
    for i in range(max_hp):
        col = (220,60,60) if i < hp else (90,40,40)
        x = 16 + i*22
        pygame.draw.circle(screen, col, (x, 18), 8)
        pygame.draw.circle(screen, col, (x+10, 18), 8)
        pygame.draw.polygon(screen, col, [(x-5, 22), (x+15, 22), (x+5, 34)])

    weapon = current_weapon if current_weapon else "None"
    info = f"Tokens: {tokens} | Weapon: {weapon}"
    screen.blit(ui.render(info, True, WHITE), (16, 50))

    if popup_msg and pygame.time.get_ticks() < popup_until:
        screen.blit(ui.render(popup_msg, True, YELLOW), (16, 80))

def draw_room(name):
    room = rooms[name]
    screen.fill(room["color"])

    for d in room["doors"]:
        pygame.draw.rect(screen, YELLOW, d["rect"], border_radius=6)
        pygame.draw.rect(screen, BROWN, d["rect"], 3, border_radius=6)

    e = room["enemy"]
    if e and e["hp"] > 0:
        pygame.draw.rect(screen, GREEN, e["rect"], border_radius=6)

def draw_player():
    pygame.draw.rect(screen, RED, player, border_radius=10)

def draw_weapon():
    w = rooms[current_room]["weapon"]
    if w and not w["picked"]:
        pygame.draw.rect(screen, (180,180,255), w["rect"], border_radius=6)

def attack_rect():
    r = player
    if player_dir == "up":
        return pygame.Rect(r.centerx-8, r.top-attack_range, 16, attack_range)
    if player_dir == "down":
        return pygame.Rect(r.centerx-8, r.bottom, 16, attack_range)
    if player_dir == "left":
        return pygame.Rect(r.left-attack_range, r.centery-8, attack_range, 16)
    return pygame.Rect(r.right, r.centery-8, attack_range, 16)

def current_damage():
    if current_weapon == "dagger": return 2
    if current_weapon == "axe": return 4
    if current_weapon == "spear": return 3
    return 1

def try_attack():
    global last_attack, popup_msg, popup_until
    now = pygame.time.get_ticks()
    if now - last_attack < attack_cd_ms:
        return
    last_attack = now

    e = rooms[current_room]["enemy"]
    if e and e["hp"] > 0 and attack_rect().colliderect(e["rect"]):
        e["hp"] -= current_damage()
        if e["hp"] <= 0:
            popup_msg = "Monster defeated!"
            popup_until = now + 1200

def update_enemy():
    e = rooms[current_room]["enemy"]
    if e and e["hp"] > 0:
        e["rect"].x += e["dx"]
        e["rect"].y += e["dy"]
        if e["rect"].left < 0 or e["rect"].right > WIDTH: e["dx"] *= -1
        if e["rect"].top < 0 or e["rect"].bottom > HEIGHT: e["dy"] *= -1

def update_weapon():
    w = rooms[current_room]["weapon"]
    if not w or w["picked"]: return
    w["rect"].x += w["dx"]
    w["rect"].y += w["dy"]
    if w["rect"].left < 0 or w["rect"].right > WIDTH: w["dx"] *= -1
    if w["rect"].top < 0 or w["rect"].bottom > HEIGHT: w["dy"] *= -1

def handle_damage(amount):
    global hp, last_hit
    now = pygame.time.get_ticks()
    if now - last_hit >= invul_ms:
        last_hit = now
        hp -= amount

def process_collisions(keys):
    global current_weapon, popup_msg, popup_until

    e = rooms[current_room]["enemy"]
    if e and e["hp"] > 0 and player.colliderect(e["rect"]):
        handle_damage(1)

    w = rooms[current_room]["weapon"]
    if w and not w["picked"] and player.colliderect(w["rect"]):
        w["picked"] = True
        current_weapon = w["type"]
        popup_msg = f"Picked up {current_weapon}!"
        popup_until = pygame.time.get_ticks() + 1500

    for d in rooms[current_room]["doors"]:
        if player.colliderect(d["rect"]) and keys[pygame.K_e]:
            switch_room(d["target"], d["spawn"])

def switch_room(target, spawn):
    global current_room, current_weapon
    w = rooms[current_room]["weapon"]
    if w: w["picked"] = False
    current_weapon = None
    current_room = target
    player.center = spawn

def handle_input(keys):
    global player_dir
    vx = vy = 0
    if keys[pygame.K_a]: vx = -player_speed; player_dir = "left"
    if keys[pygame.K_d]: vx = player_speed; player_dir = "right"
    if keys[pygame.K_w]: vy = -player_speed; player_dir = "up"
    if keys[pygame.K_s]: vy = player_speed; player_dir = "down"
    player.x += vx
    player.y += vy
    player.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))

# Main loop
running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    handle_input(keys)
    if keys[pygame.K_SPACE]:
        try_attack()

    update_enemy()
    update_weapon()

    draw_room(current_room)
    draw_weapon()
    draw_player()
    draw_hud()
    process_collisions(keys)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
