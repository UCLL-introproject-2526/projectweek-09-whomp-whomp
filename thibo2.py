import pygame, sys, random, os
pygame.init()

# ================= PADEN =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")

# ================= SCHERM =================
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()

# ================= AFBEELDINGEN =================
start_bg = pygame.image.load(os.path.join(IMG_DIR, "Startscherm.jpg")).convert()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(
    os.path.join(IMG_DIR, "stone.jpg")
).convert()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

# ================= FONTS =================
ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56)

# ================= KLEUREN =================
WHITE = (255,255,255)
RED = (230,50,50)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

# ================= SPELER =================
player = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
player_speed = 5
player_dir = "down"
max_hp = 5
hp = max_hp
invul_ms = 500
last_hit = -9999

# ================= COMBAT =================
tokens = 0
has_metal_spear = False
attack_range = 50
attack_cd_ms = 300
last_attack = -9999

player_name = ""
current_room = "starting_room"

# ================= ENEMIES =================
def make_enemy(x, y, hp=3, speed=2):
    return {
        "rect": pygame.Rect(x, y, 42, 42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed, speed]),
        "dy": random.choice([-speed, speed])
    }

def make_enemies(amount, speed):
    return [
        make_enemy(
            random.randint(50, WIDTH-90),
            random.randint(50, HEIGHT-90),
            3, speed
        )
        for _ in range(amount)
    ]

# ================= ROOMS =================
rooms = {
    "starting_room": {
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90),
             "target": "lobby", "spawn": (WIDTH//2, HEIGHT-120)}
        ],
        "enemies": []
    },
    "lobby": {
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110),
             "target": "kitchen", "spawn": (120, HEIGHT//2)}
        ],
        "enemies": make_enemies(random.randint(1, 2), 2)
    },
    "kitchen": {
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110),
             "target": "lobby", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH-110, 60, 80, 110),
             "target": "library", "spawn": (WIDTH//2, HEIGHT-140)}
        ],
        "enemies": make_enemies(random.randint(2, 5), 2)
    },
    "library": {
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80),
             "target": "kitchen", "spawn": (WIDTH-140, HEIGHT//2)}
        ],
        "enemies": make_enemies(random.randint(1, 3), 1)
    }
}

# ================= NAAM =================
def ask_player_name():
    global player_name
    player_name = ""
    while True:
        screen.blit(start_bg, (0,0))
        txt = ui.render("Voer je naam in: " + player_name, True, WHITE)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 + 200))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    if player_name == "":
                        player_name = "Speler"
                    return
                elif ev.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif ev.unicode.isprintable():
                    player_name += ev.unicode

# ================= STARTSCHERM =================
def show_start_screen():
    while True:
        screen.blit(start_bg, (0,0))
        screen.blit(title.render("Hotel Transylvania", True, WHITE), (220, 80))
        screen.blit(ui.render("Druk ENTER om te starten", True, YELLOW), (320, 520))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                return

# ================= HUD =================
def draw_hud():
    for i in range(max_hp):
        col = (220,60,60) if i < hp else (90,40,40)
        pygame.draw.circle(screen, col, (20 + i*22, 20), 8)

# ================= ROOM =================
def draw_room():
    screen.blit(floor_bg, (0,0))

    for d in rooms[current_room]["doors"]:
        pygame.draw.rect(screen, YELLOW, d["rect"], border_radius=6)
        pygame.draw.rect(screen, BROWN, d["rect"], 3, border_radius=6)
        hint = ui.render("E", True, WHITE)
        screen.blit(hint, (d["rect"].centerx-6, d["rect"].top-18))

    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            pygame.draw.rect(screen, GREEN, e["rect"], border_radius=6)
            bar_w = e["rect"].width
            hp_w = int(bar_w * (e["hp"]/e["max_hp"]))
            pygame.draw.rect(screen, (60,60,60),
                             (e["rect"].x, e["rect"].y-10, bar_w, 6))
            pygame.draw.rect(screen, (220,60,60),
                             (e["rect"].x, e["rect"].y-10, hp_w, 6))

    pygame.draw.rect(screen, RED, player, border_radius=10)

# ================= INPUT =================
def handle_input(keys):
    global player_dir
    if keys[pygame.K_q] or keys[pygame.K_a]:
        player.x -= player_speed; player_dir="left"
    if keys[pygame.K_d]:
        player.x += player_speed; player_dir="right"
    if keys[pygame.K_z] or keys[pygame.K_w]:
        player.y -= player_speed; player_dir="up"
    if keys[pygame.K_s]:
        player.y += player_speed; player_dir="down"
    player.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))

# ================= ENEMIES =================
def update_enemies():
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            e["rect"].x += e["dx"]
            e["rect"].y += e["dy"]
            if e["rect"].left < 0 or e["rect"].right > WIDTH:
                e["dx"] *= -1
            if e["rect"].top < 0 or e["rect"].bottom > HEIGHT:
                e["dy"] *= -1

# ================= DEUREN =================
def switch_room(target, spawn):
    global current_room
    current_room = target
    player.center = spawn

def process_doors(keys):
    for d in rooms[current_room]["doors"]:
        if player.colliderect(d["rect"]) and keys[pygame.K_e]:
            switch_room(d["target"], d["spawn"])

# ================= ATTACK =================
def attack_rect():
    if player_dir == "up":
        return pygame.Rect(player.centerx-8, player.top-attack_range, 16, attack_range)
    if player_dir == "down":
        return pygame.Rect(player.centerx-8, player.bottom, 16, attack_range)
    if player_dir == "left":
        return pygame.Rect(player.left-attack_range, player.centery-8, attack_range, 16)
    return pygame.Rect(player.right, player.centery-8, attack_range, 16)

def try_attack():
    global last_attack, tokens, has_metal_spear
    now = pygame.time.get_ticks()
    if now - last_attack < attack_cd_ms:
        return
    last_attack = now
    dmg = 3 if has_metal_spear else 1
    hb = attack_rect()

    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0 and hb.colliderect(e["rect"]):
            e["hp"] -= dmg
            if e["hp"] <= 0:
                tokens += 1
                if tokens >= 10:
                    has_metal_spear = True

# ================= START =================
ask_player_name()
show_start_screen()

running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            try_attack()

    keys = pygame.key.get_pressed()
    handle_input(keys)
    if keys[pygame.K_SPACE]:
        try_attack()

    update_enemies()
    process_doors(keys)
    draw_room()
    draw_hud()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

 