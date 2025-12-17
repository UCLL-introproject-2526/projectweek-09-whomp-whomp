import pygame, sys, random
pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()

ROOM_WIDTH, ROOM_HEIGHT = 1600, 1200

ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56)

WHITE = (255,255,255)
RED = (230,50,50)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

# Player
player_rect = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
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
player_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\player.png").convert_alpha()

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

# Enemy helper
def make_enemy(x, y, hp=3, speed=2,):
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

# Rooms
rooms = {
    "starting_room": {
        "color": (55, 188, 31),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "lobby", "spawn": (2, HEIGHT//2)},
        ],
        "enemies": [],
    },

    "lobby": {
        "color": (32, 12, 36),
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "kitchen", "spawn": (WIDTH//2, HEIGHT//2)},
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "hallway", "spawn": (WIDTH-140, HEIGHT//2)},
        ],
        "enemies": make_enemies(random.randint(1, 2), 10),
    },

    "hallway": {
        "color": (80, 80, 80),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "armory", "spawn": (WIDTH//2, HEIGHT-140)},
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "lobby", "spawn": (WIDTH//2, 120)},
        ],
        "enemies": make_enemies(random.randint(1, 3), 8),
    },

    "kitchen": {
        "color": (60, 25, 5),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "lobby", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH-110, 60, 80, 110), "target": "library", "spawn": (WIDTH//2, HEIGHT-140)},
        ],
        "enemies": make_enemies(random.randint(2, 5), 5),
    },

    "library": {
        "color": (5, 40, 62),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "kitchen", "spawn": (WIDTH//2, 120)},
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "study", "spawn": (120, HEIGHT//2)},
        ],
        "enemies": make_enemies(random.randint(1, 3), 3),
    },

    "study": {
        "color": (90, 60, 30),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "library", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "archive", "spawn": (WIDTH//2, HEIGHT-140)},
        ],
        "enemies": make_enemies(random.randint(2, 4), 4),
    },

    "archive": {
        "color": (20, 20, 50),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "study", "spawn": (WIDTH//2, 120)},
        ],
        "enemies": make_enemies(random.randint(3, 5), 3),
    },

    "armory": {
        "color": (120, 120, 120),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "hallway", "spawn": (WIDTH//2, 120)},
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "barracks", "spawn": (120, HEIGHT//2)},
        ],
        "enemies": make_enemies(random.randint(2, 4), 6),
    },

    "barracks": {
        "color": (100, 80, 60),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "armory", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "training_room", "spawn": (WIDTH//2, HEIGHT-140)},
        ],
        "enemies": make_enemies(random.randint(3, 6), 6),
    },

    "training_room": {
        "color": (150, 50, 50),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "barracks", "spawn": (WIDTH//2, 120)},
        ],
        "enemies": make_enemies(random.randint(4, 7), 5),
    },

    # --- FINAL WING ---
    "crypt": {
        "color": (30, 30, 30),
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "chapel", "spawn": (120, HEIGHT//2)},
        ],
        "enemies": make_enemies(random.randint(4, 6), 4),
    },

    "chapel": {
        "color": (200, 200, 160),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "crypt", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "boss_room", "spawn": (WIDTH//2, HEIGHT-140)},
        ],
        "enemies": make_enemies(random.randint(3, 5), 4),
    },

    "boss_room": {
        "color": (120, 0, 0),
        "doors": [],
        "enemies": make_enemies(1, 1),
    },
}

current_room = "starting_room"

# --- Camera ---
def get_camera():
    cam_x = player_rect.centerx - WIDTH // 2
    cam_y = player_rect.centery - HEIGHT // 2
    # Clamp camera to room bounds
    cam_x = max(0, min(cam_x, ROOM_WIDTH - WIDTH))
    cam_y = max(0, min(cam_y, ROOM_HEIGHT - HEIGHT))
    return cam_x, cam_y

def draw_hud():
    # hearts
    for i in range(max_hp):
        col = (220,60,60) if i < hp else (90,40,40)
        x = 16 + i*22
        pygame.draw.circle(screen, col, (x, 18), 8)
        pygame.draw.circle(screen, col, (x+10, 18), 8)
        pygame.draw.polygon(screen, col, [(x-5, 22), (x+15, 22), (x+5, 34)])
    # tokens and weapon
    weapon = "Metal spear" if has_metal_spear else "Wooden spear"
    info = f"Tokens: {tokens} | Weapon: {weapon}"
    screen.blit(ui.render(info, True, WHITE), (16, 50))
    # popup
    if popup_msg and pygame.time.get_ticks() < popup_until:
        surf = ui.render(popup_msg, True, YELLOW)
        screen.blit(surf, (16, 80))

def draw_room():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()
    screen.fill(room["color"])
    # doors
    for d in room["doors"]:
        draw_rect = d["rect"].copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y
        pygame.draw.rect(screen, YELLOW, draw_rect, border_radius=6)
        pygame.draw.rect(screen, BROWN, draw_rect, 3, border_radius=6)
        tag = ui.render(d["target"], True, WHITE)
        screen.blit(tag, (draw_rect.centerx - tag.get_width()//2, draw_rect.top - 24))
    # enemies
    for e in room["enemies"]:
        if e["hp"] > 0:
            draw_rect = e["rect"].copy()
            draw_rect.x -= cam_x
            draw_rect.y -= cam_y
            pygame.draw.rect(screen, GREEN, draw_rect, border_radius=6)

def draw_enemies():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            draw_rect = e["rect"].copy()
            draw_rect.x -= cam_x
            draw_rect.y -= cam_y
            pygame.draw.rect(screen, GREEN, e["rect"], border_radius=6)

def draw_player():
    global player_frame
    cam_x, cam_y = get_camera()
    frame_index = int(player_frame) % len(player_sprites[DIRECTION_ROW[player_dir]])
    img = player_sprites[DIRECTION_ROW[player_dir]][frame_index]
    draw_rect = player_rect.copy()
    draw_rect.x -= cam_x
    draw_rect.y -= cam_y
    screen.blit(img, draw_rect)


def update_enemies():
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            e["rect"].x += e["dx"]
            e["rect"].y += e["dy"]
            if e["rect"].left < 0 or e["rect"].right > WIDTH:
                e["dx"] *= -1
            if e["rect"].top < 0 or e["rect"].bottom > HEIGHT:
                e["dy"] *= -1


def attack_rect():
    r = player_rect
    if player_dir == "up":
        return pygame.Rect(r.centerx-8, r.top-attack_range, 16, attack_range)
    if player_dir == "down":
        return pygame.Rect(r.centerx-8, r.bottom, 16, attack_range)
    if player_dir == "left":
        return pygame.Rect(r.left-attack_range, r.centery-8, attack_range, 16)
    return pygame.Rect(r.right, r.centery-8, attack_range, 16)

def current_damage():
    return metal_damage if has_metal_spear else wood_damage

def try_attack():
    global last_attack, tokens, has_metal_spear, popup_msg, popup_until
    now = pygame.time.get_ticks()
    if now - last_attack < attack_cd_ms:
        return
    last_attack = now
    hb = attack_rect()
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0 and hb.colliderect(e["rect"]):
           e["hp"] -= current_damage()
        if e["hp"] <= 0:
            tokens += 1
            popup_msg = "+1 token (monster defeated)"
            popup_until = now + 1500
            if not has_metal_spear and tokens >= 10:
                has_metal_spear = True
                popup_msg = "Metal spear unlocked!"
                popup_until = now + 2000
        # attack flash
    cam_x, cam_y = get_camera()
    draw_rect = hb.copy()
    draw_rect.x -= cam_x
    draw_rect.y -= cam_y
    pygame.draw.rect(screen, (255,220,120), draw_rect)
    pygame.display.flip()


def handle_damage(amount=1):
    global hp, last_hit
    now = pygame.time.get_ticks()
    if now - last_hit >= invul_ms:
        last_hit = now
        hp -= amount

def process_collisions(keys):
    for e in rooms[current_room]["enemies"]:
     if e["hp"] > 0 and player_rect.colliderect(e["rect"]):
        handle_damage(1)
    for d in rooms[current_room]["doors"]:
        if player_rect.colliderect(d["rect"]):
            hint = ui.render("E: enter " + d["target"], True, WHITE)
            screen.blit(hint, (16, HEIGHT-36))
            if keys[pygame.K_e]:
                switch_room(d["target"], d["spawn"])

def switch_room(target, spawn):
    global current_room
    current_room = target
    player_rect.center = spawn

def handle_input(keys):
    global player_dir
    vx = vy = 0
    moving = False
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        vx = -player_speed; player_dir = "left"
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vx = player_speed; player_dir = "right"
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        vy = -player_speed; player_dir = "up"
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        vy = player_speed; player_dir = "down"
    player_rect.x += vx
    player_rect.y += vy
    player_rect.clamp_ip(pygame.Rect(0,0,ROOM_WIDTH,ROOM_HEIGHT))

    if moving:
        player_frame += animation_speed
    else:
        player_frame = 0


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

    update_enemies()
    draw_room()
    draw_player()
    draw_hud()
    process_collisions(keys)

    if hp <= 0:
        # Game over scherm
        screen.fill(DARK)
        over1 = title.render("Trash", True, (255,200,200))
        over2 = ui.render("Enter: opnieuw beginnen | Esc: afsluiten", True, WHITE)
        screen.blit(over1, over1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
        screen.blit(over2, over2.get_rect(center=(WIDTH//2, HEIGHT//2 + 24)))
        pygame.display.flip()
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    waiting = False
                    running = False
            k = pygame.key.get_pressed()
            if k[pygame.K_RETURN]:
                # reset spel
                player_rect.update(WIDTH//2-20, HEIGHT//2-28, 40, 56)
                hp = max_hp
                tokens = 0
                has_metal_spear = False
                # respawn enemies
                for name in rooms:
                    if name == "starting_room":
                        rooms[name]["enemies"] = []
                    
                    else:
                        rooms[name]["enemies"] = make_enemies(random.randint(1,3),speed=2
                    )
                current_room = "starting_room"
                waiting = False
            elif k[pygame.K_ESCAPE]:
                waiting = False
                running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()