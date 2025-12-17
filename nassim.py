import pygame, sys, random, json
pygame.init()

DEBUG = True

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()
WALL_THICKNESS = 30

ROOM_WIDTH, ROOM_HEIGHT = 5000, 3000

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

# Map directions to sheet rows
DIRECTION_ROW = {
    "down": 0,
    "left": 1,
    "right": 2,
    "up": 3
}
ENEMY_DIRECTION_ROW = {
    "up": 8,    # 0-indexed row 9
    "left": 9,  # row 10
    "down": 10, # row 11
    "right": 11 # row 12
}

# enemy sprite
enemy_spritesheet = pygame.image.load(("img\skeleton.png")).convert_alpha()

ENEMY_FRAME_WIDTH = 42   # width of a single frame
ENEMY_FRAME_HEIGHT = 42  # height of a single frame
FRAMES_PER_ROW = 9       # number of frames per walking animation row

enemy_sprites = {}
for dir_name, row in ENEMY_DIRECTION_ROW.items():
    frames = []
    for col in range(FRAMES_PER_ROW):
        rect = pygame.Rect(col*ENEMY_FRAME_WIDTH, row*ENEMY_FRAME_HEIGHT, ENEMY_FRAME_WIDTH, ENEMY_FRAME_HEIGHT)
        frames.append(enemy_spritesheet.subsurface(rect))
    enemy_sprites[dir_name] = frames

#Animation
player_frame = 0
animation_speed= 0.2

start_bg = pygame.image.load(("img\Startscherm.jpg")).convert_alpha()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(("img\stone.jpg")).convert_alpha()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

# player sprite
frame_width, frame_height = 64, 64
player_spritesheet = pygame.image.load("img\player.png").convert_alpha()

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

#Save and Load
def save_game():
    data = {
        "hp": hp,
        "tokens": tokens,
        "weapon": has_metal_spear,
        "room": current_room
    }
    with open("save.json", "w") as f:
        json.dump(data, f)

def load_game():
    global hp, tokens, has_metal_spear, current_room
    try:
        with open("save.json") as f:
            data = json.load(f)
        hp = data["hp"]
        tokens = data["tokens"]
        has_metal_spear = data["weapon"]
        current_room = data["room"]
    except:
        pass


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
def make_enemy(x, y, hp=3, speed=2):
    dir_choices = ["up", "down", "left", "right"]
    initial_dir = random.choice(dir_choices)
    return {
        "rect": pygame.Rect(x, y, ENEMY_FRAME_WIDTH, ENEMY_FRAME_HEIGHT),  # match sprite size
        "hp": hp,
        "max_hp": hp,
        "dx": speed,  # movement speed along normalized direction
        "dy": speed,
        "dir": initial_dir,
        "frame": random.randint(0, FRAMES_PER_ROW-1),  # random start frame to avoid uniform movement
        "animation_speed": 0.01  # tweak this for slower/faster animation
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
            {"rect": pygame.Rect(1000, 50, 80, 90), "target": "lobby", "spawn": (2500, 1500)},
        ],
        "enemies": [],
    },

    "lobby": {
        "color": (41,90,96),
        "doors": [{"rect": pygame.Rect(100, 50, 70, 100), "target": "starting_room", "spawn": (200,200)},
                  {"rect": pygame.Rect(300, 50, 70, 100), "target": "hallway right", "spawn": (200,200)},
                  {"rect": pygame.Rect(500, 50, 70, 100), "target": "hallway left", "spawn": (200,200)}], 
        "enemies": make_enemies(random.randint(20,50), speed=2), 
    },

    "hallway right": {
        "color": (41,90,96),
        "doors": [{"rect": pygame.Rect(WIDTH//2-40, 50, 70, 100), "target": "lobby", "spawn": (200,200)}
        ], 
        "enemies": make_enemies(random.randint(1,2), speed=2), 
    },

     "hallway left": {
        "color": (41,90,96),
        "doors": [{"rect": pygame.Rect(WIDTH//2-40, 50, 70, 100), "target": "lobby", "spawn": (200,200)}
        ], 
        "enemies": make_enemies(random.randint(1,2), speed=2), 
    },

    # --- FINAL WING ---
    "crypt": {
        "color": (30, 30, 30),
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "chapel", "spawn": (200,200)},
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

# Slice spritesheet into a dict of lists for each direction
enemy_sprites = {}
for dir_name, row in ENEMY_DIRECTION_ROW.items():
    frames = []
    for col in range(FRAMES_PER_ROW):
        rect = pygame.Rect(col*ENEMY_FRAME_WIDTH, row*ENEMY_FRAME_HEIGHT, ENEMY_FRAME_WIDTH, ENEMY_FRAME_HEIGHT)
        frames.append(enemy_spritesheet.subsurface(rect))
    enemy_sprites[dir_name] = frames

# ================= NAAM =================
def show_start_screen_and_ask_name():
    global player_name
    player_name = ""

    # --- Title screen ---
    title_running = True
    while title_running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    title_running = False  # Exit the title screen

        screen.blit(start_bg, (0, 0))
        screen.blit(title.render("Frankenstein mansion", True, WHITE), (250, 80))
        screen.blit(ui.render("Druk ENTER om te starten", True, YELLOW), (320, 520))
        pygame.display.flip()
        clock.tick(60)

    # --- Ask for player name ---
    asking_name = True
    while asking_name:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    if player_name.strip() == "":
                        player_name = "speler"
                    asking_name = False
                elif ev.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif ev.unicode.isprintable():
                    player_name += ev.unicode

        screen.blit(start_bg, (0, 0))
        prompt_text = ui.render("Voer je naam in: " + player_name, True, WHITE)
        screen.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//2 + 200))
        pygame.display.flip()
        clock.tick(60)


# --- Camera ---
def get_camera():
    cam_x = player_rect.centerx - WIDTH // 2
    cam_y = player_rect.centery - HEIGHT // 2
    # Clamp camera to room bounds
    cam_x = max(0, min(cam_x, ROOM_WIDTH - WIDTH))
    cam_y = max(0, min(cam_y, ROOM_HEIGHT - HEIGHT))
    return cam_x, cam_y

def get_room_walls():
    return [
        # Top wall
        pygame.Rect(0, 0, ROOM_WIDTH, WALL_THICKNESS),

        # Bottom wall
        pygame.Rect(0, ROOM_HEIGHT - WALL_THICKNESS, ROOM_WIDTH, WALL_THICKNESS),

        # Left wall
        pygame.Rect(0, 0, WALL_THICKNESS, ROOM_HEIGHT),

        # Right wall
        pygame.Rect(ROOM_WIDTH - WALL_THICKNESS, 0, WALL_THICKNESS, ROOM_HEIGHT),
    ]

def draw_walls():
    cam_x, cam_y = get_camera()
    for wall in get_room_walls():
        draw_rect = wall.copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y
        pygame.draw.rect(screen, (70, 70, 70), draw_rect)


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

def draw_debug_hud():
    cam_x, cam_y = get_camera()

    lines = [
        f"Room: {current_room}",
        f"Player world pos: {player_rect.x}, {player_rect.y}",
        f"Camera pos: {cam_x}, {cam_y}",
        f"Room size: {ROOM_WIDTH} x {ROOM_HEIGHT}",
    ]

    y = HEIGHT - 20 * len(lines) - 10
    for line in lines:
        text = ui.render(line, True, (255, 255, 0))
        screen.blit(text, (10, y))
        y += 20

def draw_room():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()
    screen.fill(room["color"])
    draw_walls()
    # doors
    for d in room["doors"]:
        draw_rect = d["rect"].copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y
        pygame.draw.rect(screen, YELLOW, draw_rect, border_radius=6)
        pygame.draw.rect(screen, BROWN, draw_rect, 3, border_radius=6)
        tag = ui.render(d["target"], True, WHITE)
        screen.blit(tag, (draw_rect.centerx - tag.get_width()//2, draw_rect.top - 24))

def draw_enemies():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            draw_rect = e["rect"].copy()
            draw_rect.x -= cam_x
            draw_rect.y -= cam_y
           # Optional: offset to center the sprite
            draw_rect.x -= (img.get_width() - e["rect"].width)//2
            draw_rect.y -= (img.get_height() - e["rect"].height)//2

            screen.blit(img, draw_rect)

def draw_enemy_health(e, cam_x, cam_y):
    if e["hp"] <= 0:
        return
    ratio = e["hp"] / e["max_hp"]
    bar_w = e["rect"].width
    bar_h = 6
    x = e["rect"].x - cam_x
    y = e["rect"].y - cam_y - 10

    pygame.draw.rect(screen, RED, (x, y, bar_w, bar_h))
    pygame.draw.rect(screen, GREEN, (x, y, bar_w * ratio, bar_h))


def draw_player():
    global player_frame
    cam_x, cam_y = get_camera()
    frame_index = int(player_frame) % len(player_sprites[DIRECTION_ROW[player_dir]])
    img = player_sprites[DIRECTION_ROW[player_dir]][frame_index]
    draw_rect = player_rect.copy()
    draw_rect.x -= cam_x
    draw_rect.y -= cam_y
    screen.blit(img, draw_rect)

def draw_enemies():
    cam_x, cam_y = get_camera()
    for e in rooms[current_room]["enemies"]:
        if e["hp"] <= 0:
            continue

        frame_index = int(e["frame"]) % FRAMES_PER_ROW
        img = enemy_sprites[e["dir"]][frame_index]

        # Center the sprite on the enemy rect
        draw_rect = e["rect"].copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y

        # Offset if sprite is bigger than Rect
        draw_rect.x -= (img.get_width() - e["rect"].width) // 2
        draw_rect.y -= (img.get_height() - e["rect"].height) // 2

        screen.blit(img, draw_rect)

        # Optional: draw health bar
        draw_enemy_health(e, cam_x, cam_y)


def move_player(vx, vy):
    # Move X axis
    player_rect.x += vx
    for wall in get_room_walls():
        if player_rect.colliderect(wall):
            if vx > 0:
                player_rect.right = wall.left
            elif vx < 0:
                player_rect.left = wall.right

    # Move Y axis
    player_rect.y += vy
    for wall in get_room_walls():
        if player_rect.colliderect(wall):
            if vy > 0:
                player_rect.bottom = wall.top
            elif vy < 0:
                player_rect.top = wall.bottom


# def update_enemies():
#     for e in rooms[current_room]["enemies"]:
#         if e["hp"] > 0:
#             e["rect"].x += e["dx"]
#             e["rect"].y += e["dy"]
#             if e["rect"].left < 0 or e["rect"].right > WIDTH:
#                 e["dx"] *= -1
#             if e["rect"].top < 0 or e["rect"].bottom > HEIGHT:
#                 e["dy"] *= -1
def update_enemies():
    for e in rooms[current_room]["enemies"]:
        if e["hp"] <= 0:
            continue

        # Chase player
        dx = player_rect.centerx - e["rect"].centerx
        dy = player_rect.centery - e["rect"].centery
        dist = max(1, (dx*dx + dy*dy) ** 0.5)

        move_x = int(e["dx"] * dx / dist)
        move_y = int(e["dy"] * dy / dist)
        e["rect"].x += move_x
        e["rect"].y += move_y

        # --- Update direction for sprite ---
        if abs(dx) > abs(dy):
            e["dir"] = "right" if dx > 0 else "left"
        else:
            e["dir"] = "down" if dy > 0 else "up"

        # --- Wall collision ---
        if e["rect"].left <= WALL_THICKNESS:
            e["rect"].left = WALL_THICKNESS
        elif e["rect"].right >= ROOM_WIDTH - WALL_THICKNESS:
            e["rect"].right = ROOM_WIDTH - WALL_THICKNESS
        if e["rect"].top <= WALL_THICKNESS:
            e["rect"].top = WALL_THICKNESS
        elif e["rect"].bottom >= ROOM_HEIGHT - WALL_THICKNESS:
            e["rect"].bottom = ROOM_HEIGHT - WALL_THICKNESS

        # --- Update animation frame ---
        e["frame"] += e["animation_speed"]
        if e["frame"] >= FRAMES_PER_ROW:
            e["frame"] -= FRAMES_PER_ROW

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
    
    move_player(vx, vy)

    if moving:
        player_frame += animation_speed
    else:
        player_frame = 0


# Main loop


show_start_screen_and_ask_name()

running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_F3:
                DEBUG = not DEBUG


    keys = pygame.key.get_pressed()
    handle_input(keys)
    if keys[pygame.K_SPACE]:
        try_attack()

    update_enemies()
    draw_room()
    draw_enemies()
    draw_player()
    draw_hud()
    if DEBUG:
       draw_debug_hud()
    process_collisions(keys)

    if hp <= 0:
        # Game over scherm
        screen.fill(DARK)
        over1 = title.render("game over", True, (255,200,200))
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

save_game()
pygame.quit()

