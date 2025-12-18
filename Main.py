import pygame, sys, random
pygame.init()

DEBUG = True

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()
WALL_THICKNESS = 30

ROOM_WIDTH, ROOM_HEIGHT = 1800, 1200

ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56)

menu_open = False

WHITE = (255,255,255)
RED = (230,50,50)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

def load_skeleton_frames(sheet, frame_w, frame_h):
    frames = []
    sheet_width, sheet_height = sheet.get_size()
    for y in range(0, sheet_height, frame_h):
        for x in range(0, sheet_width, frame_w):
            if x + frame_w <= sheet_width and y + frame_h <= sheet_height:
                frames.append(
                    sheet.subsurface(pygame.Rect(x, y, frame_w, frame_h)).copy()
                )
    return frames



# Playerplayer_rect = pyg
# Start in het midden van de kamer, rekening houdend met muren
player_rect = pygame.Rect(0, 0, 40, 56)
player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
player_speed = 5
player_dir = "down"
max_hp = 5
hp = max_hp
invul_ms = 500
last_hit = -9999

#Animation
player_frame = 0
animation_speed= 0.2

door_img = pygame.image.load("projectweek-09-whomp-whomp\img\door3.jpg").convert_alpha()
door_img = pygame.transform.scale(door_img, (80, 100))  # pas grootte aan


start_bg = pygame.image.load(("projectweek-09-whomp-whomp\img\Startscherm.jpg")).convert_alpha()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(("projectweek-09-whomp-whomp\img\stone.jpg")).convert_alpha()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

frame_width, frame_height = 64, 64
player_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\img\player.png").convert_alpha()

skeleton_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\\img\\skeleton.png").convert_alpha()
frame_width, frame_height = 64, 64  # pas aan naar de juiste grootte van één frame
skeleton_img = skeleton_spritesheet.subsurface(pygame.Rect(0, 0, frame_width, frame_height))
skeleton_frames = load_skeleton_frames(skeleton_spritesheet, frame_width, frame_height)


    

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

def make_enemy(x, y, hp=3, speed=2):
    return {
        "rect": pygame.Rect(x, y, 42, 42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed, speed]),
        "dy": random.choice([-speed, speed]),
        "frame": 0,
        "frame_timer": 0
    }


def make_enemies(amount, speed):
    enemies = []
    for _ in range(amount):
        x = random.randint(WALL_THICKNESS, ROOM_WIDTH - WALL_THICKNESS - 50)
        y = random.randint(WALL_THICKNESS, ROOM_HEIGHT - WALL_THICKNESS - 50)
        enemies.append(make_enemy(x, y, hp=3, speed=speed))
    return enemies

def random_door_rect(side, width=70, height=100):
    margin = WALL_THICKNESS + 20

    if side == "top":
        x = random.randint(margin, ROOM_WIDTH - margin - width)
        y = WALL_THICKNESS
    elif side == "bottom":
        x = random.randint(margin, ROOM_WIDTH - margin - width)
        y = ROOM_HEIGHT - WALL_THICKNESS - height
    elif side == "left":
        x = WALL_THICKNESS
        y = random.randint(margin, ROOM_HEIGHT - margin - height)
    elif side == "right":
        x = ROOM_WIDTH - WALL_THICKNESS - width
        y = random.randint(margin, ROOM_HEIGHT - margin - height)
    else:
        raise ValueError("Side must be top, bottom, left or right")

    return pygame.Rect(x, y, width, height)

def spawn_from_door(door_rect, offset=120):
    if door_rect.top == WALL_THICKNESS:
        return (door_rect.centerx, door_rect.bottom + offset)
    if door_rect.bottom == ROOM_HEIGHT - WALL_THICKNESS:
        return (door_rect.centerx, door_rect.top - offset)
    if door_rect.left == WALL_THICKNESS:
        return (door_rect.right + offset, door_rect.centery)
    if door_rect.right == ROOM_WIDTH - WALL_THICKNESS:
        return (door_rect.left - offset, door_rect.centery)

    return (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)


# Rooms
# Rooms
# ======================
# ROOMS (basis)
# ======================
HAUNTED_ROOMS = [
    "dusty_attic",
    "bloody_kitchen",
    "creepy_library",
    "abandoned_bedroom",
    "mirror_hall",
    "torture_chamber",
    "dark_basement",
    "spider_corridor",
    "broken_ballroom",
    "whispering_gallery",
    "forgotten_nursery",
    "rotting_dining_hall",
    "shadow_lab",
    "cursed_storage",
    "hidden_passage",
    "burned_chapel",
    "underground_crypt",
    "moonlit_garden",
    "ritual_room",
    "final_sanctum"
]


door_to_lobby = random_door_rect("top")

rooms = {}

# --- starting room ---
start_door = random_door_rect("top")

rooms["starting_room"] = {
    "color": (55, 188, 31),
    "doors": [
        {
            "rect": start_door,
            "target": HAUNTED_ROOMS[0],
            "spawn": spawn_from_door(start_door)
        }
    ],
    "enemies": []
}

for i, room_name in enumerate(HAUNTED_ROOMS):
    rooms[room_name] = {
        "color": (
            random.randint(40, 180),
            random.randint(40, 180),
            random.randint(40, 180)
        ),
        "doors": [],
        "enemies": make_enemies(random.randint(2, 5), speed=2)
    }

    # deur terug naar vorige room
    if i == 0:
        back_target = "starting_room"
    else:
        back_target = HAUNTED_ROOMS[i - 1]

    back_door = random_door_rect("left")
    rooms[room_name]["doors"].append({
        "rect": back_door,
        "target": back_target,
        "spawn": spawn_from_door(back_door)
    })

    # deur naar volgende room (behalve laatste)
    if i < len(HAUNTED_ROOMS) - 1:
        next_door = random_door_rect("right")
        rooms[room_name]["doors"].append({
            "rect": next_door,
            "target": HAUNTED_ROOMS[i + 1],
            "spawn": spawn_from_door(next_door)
        })



# rooms = {
#     "starting_room": {
#         "color": (55, 188, 31),
#         "doors": [
#             {
#                 "rect": door_to_lobby,
#                 "target": "lobby",
#                 "spawn": spawn_from_door(door_to_lobby)
#             }
#         ],
#         "enemies": []
#     },

#     "lobby": {   # <-- wordt zo overschreven
#         "color": (41, 90, 96),
#         "doors": [],
#         "enemies": []
#     },

#     "hallway right": {
#         "color": (41, 90, 96),
#         "doors": [],
#         "enemies": make_enemies(5, speed=2)
#     },

#     "hallway left": {
#         "color": (41, 90, 96),
#         "doors": [],
#         "enemies": make_enemies(5, speed=2)
#     },

#     "crypt": {
#         "color": (30, 30, 30),
#         "doors": [],
#         "enemies": make_enemies(5, speed=2)
#     },

#     "chapel": {
#         "color": (200, 200, 160),
#         "doors": [],
#         "enemies": make_enemies(5, speed=2)
#     },

#     "boss_room": {
#         "color": (120, 0, 0),
#         "doors": [],
#         "enemies": make_enemies(1, 1)
#     }
# }


current_room = "starting_room"

# # ======================
# # RANDOM LOBBY (FIX)
# # ======================

# lobby_to_start = random_door_rect("top")
# lobby_to_right = random_door_rect("left")
# lobby_to_left  = random_door_rect("right")

# rooms["lobby"]["doors"] = [
#     {
#         "rect": lobby_to_start,
#         "target": "starting_room",
#         "spawn": spawn_from_door(lobby_to_start)
#     },
#     {
#         "rect": lobby_to_right,
#         "target": "hallway right",
#         "spawn": spawn_from_door(lobby_to_right)
#     },
#     {
#         "rect": lobby_to_left,
#         "target": "hallway left",
#         "spawn": spawn_from_door(lobby_to_left)
#     }
# ]

# rooms["lobby"]["enemies"] = make_enemies(5, speed=2)


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

def safe_spawn(pos):
    x, y = pos
    x = max(WALL_THICKNESS + 20, min(x, ROOM_WIDTH - WALL_THICKNESS - 20))
    y = max(WALL_THICKNESS + 20, min(y, ROOM_HEIGHT - WALL_THICKNESS - 20))
    return x, y



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

def draw_menu():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(220)
    overlay.fill((10, 10, 20))
    screen.blit(overlay, (0, 0))

    title_text = title.render("HAUNTED HOUSE", True, WHITE)
    screen.blit(title_text, title_text.get_rect(center=(WIDTH//2, 80)))

    info_lines = []

    # 🔴 GAME OVER TEKST
    if hp <= 0:
        info_lines.append(f"Jammer {player_name},")
        info_lines.append("je bent doodgegaan.")
        info_lines.append("")
        info_lines.append("Druk R om opnieuw te beginnen")
        info_lines.append("of ESC om te stoppen")

    else:
        info_lines.extend([
            f"Player: {player_name}",
            f"Tokens: {tokens}",
            "",
            "CONTROLS:",
            "Move: WASD / Arrow Keys",
            "Attack: SPACE",
            "Interact: E",
            "Menu: M",
            "",
            "OBJECTIVE:",
            "Explore the haunted house.",
            "Defeat monsters.",
            "Reach the final sanctum.",
            "",
            "OPTIONS:",
            "R  - Restart game",
            "ESC - Quit game",
            "M  - Close menu"
        ])

    y = 160
    for line in info_lines:
        txt = ui.render(line, True, WHITE)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y))
        y += 28



def draw_walls():
    cam_x, cam_y = get_camera()
    for wall in get_room_walls():
        draw_rect = wall.copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y
        pygame.draw.rect(screen, (70, 70, 70), draw_rect)

def draw_floor():
    cam_x, cam_y = get_camera()

    tile_w = floor_bg.get_width()
    tile_h = floor_bg.get_height()

    start_x = -(cam_x % tile_w)
    start_y = -(cam_y % tile_h)

    for x in range(start_x, WIDTH, tile_w):
        for y in range(start_y, HEIGHT, tile_h):
            screen.blit(floor_bg, (x, y))


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






def draw_player():
    global player_frame
    cam_x, cam_y = get_camera()
    frame_index = int(player_frame) % len(player_sprites[DIRECTION_ROW[player_dir]])
    img = player_sprites[DIRECTION_ROW[player_dir]][frame_index]
    draw_rect = player_rect.copy()
    draw_rect.x -= cam_x
    draw_rect.y -= cam_y
    screen.blit(img, draw_rect)

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

def update_enemies():
    now = pygame.time.get_ticks()
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            # bewegen
            e["rect"].x += e["dx"]
            e["rect"].y += e["dy"]

            if e["rect"].left < WALL_THICKNESS or e["rect"].right > ROOM_WIDTH - WALL_THICKNESS:
                e["dx"] *= -1
            if e["rect"].top < WALL_THICKNESS or e["rect"].bottom > ROOM_HEIGHT - WALL_THICKNESS:
                e["dy"] *= -1

            # animatie update
            if now - e["frame_timer"] > 150:  # 150 ms per frame
                e["frame_timer"] = now
                e["frame"] = (e["frame"] + 1) % len(skeleton_frames)



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

def switch_room(target, spawn=None):
    global current_room
    current_room = target
    if spawn:
        player_rect.center = safe_spawn(spawn)
    else:
        player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)



def handle_input(keys):
    global player_dir, player_frame

    vx = vy = 0
    moving = False

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        vx = -player_speed
        player_dir = "left"

    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vx = player_speed
        player_dir = "right"

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        vy = -player_speed
        player_dir = "up"

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        vy = player_speed
        player_dir = "down"

    # check of we bewegen
    if vx != 0 or vy != 0:
        moving = True

    move_player(vx, vy)

    # animatie
    if moving:
        player_frame += animation_speed
    else:
        player_frame = 0

def draw_room():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()

    # Floor en walls
    draw_floor()
    draw_walls()

    # Doors
    for d in room["doors"]:
        draw_rect = d["rect"].copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y
        # Gebruik de afbeelding van de deur
        if "img" in d:
            screen.blit(d["img"], draw_rect.topleft)
        else:
            pygame.draw.rect(screen, YELLOW, draw_rect, border_radius=6)
            pygame.draw.rect(screen, BROWN, draw_rect, 3, border_radius=6)
        # toon de kamernaam erboven
        tag = ui.render(d["target"], True, WHITE)
        screen.blit(tag, (draw_rect.centerx - tag.get_width()//2, draw_rect.top - 24))

    # Enemies
    for e in room["enemies"]:
        if e["hp"] > 0:
            draw_rect = e["rect"].copy()
            draw_rect.x -= cam_x
            draw_rect.y -= cam_y
            # animatie frame
            img = skeleton_frames[e["frame"]]
            screen.blit(img, draw_rect)

            # health bar
            hp_ratio = e["hp"] / e["max_hp"]
            bar_w = draw_rect.width
            bar_h = 5
            bar_x = draw_rect.x
            bar_y = draw_rect.y - 8
            pygame.draw.rect(screen, (120, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, bar_w * hp_ratio, bar_h))


def draw_debug_hud():
    room = rooms[current_room]
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

    # Enemies
    for e in room["enemies"]:
        if e["hp"] > 0:
            draw_rect = e["rect"].copy()
            draw_rect.x -= cam_x
            draw_rect.y -= cam_y
            img = skeleton_frames[e["frame"]]
            screen.blit(img, draw_rect)

            # health bar
            hp_ratio = e["hp"] / e["max_hp"]
            bar_w = draw_rect.width
            bar_h = 5
            bar_x = draw_rect.x
            bar_y = draw_rect.y - 8
            pygame.draw.rect(screen, (120, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, bar_w * hp_ratio, bar_h))

# Voeg de afbeelding toe aan alle deuren in alle kamers
for room_name in rooms:
    for d in rooms[room_name]["doors"]:
        d["img"] = door_img

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
            if ev.key == pygame.K_m:
                menu_open = not menu_open

    keys = pygame.key.get_pressed()

    if menu_open:
        draw_menu()

        if keys[pygame.K_ESCAPE]:
            running = False

        if keys[pygame.K_r]:
            player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
            hp = max_hp
            tokens = 0
            has_metal_spear = False
            current_room = "starting_room"

            for name in rooms:
                if name == "starting_room":
                    rooms[name]["enemies"] = []
                else:
                    rooms[name]["enemies"] = make_enemies(
                        random.randint(2, 5), speed=2
                    )

            menu_open = False

    else:
        handle_input(keys)

        if keys[pygame.K_SPACE]:
            try_attack()

        update_enemies()
        draw_room()
        draw_player()
        draw_hud()

        if DEBUG:
            draw_debug_hud()

        process_collisions(keys)

        if hp <= 0:
            menu_open = True

    pygame.display.flip()
    clock.tick(60)


# running = True
# while running:
#     for ev in pygame.event.get():
#         if ev.type == pygame.QUIT:
#             running = False
#         elif ev.type == pygame.KEYDOWN:
#             if ev.key == pygame.K_F3:
#                 DEBUG = not DEBUG

#             if ev.key == pygame.K_m:
#              menu_open = not menu_open



#     keys = pygame.key.get_pressed()
#     if not menu_open:
#         handle_input(keys)

#     if keys[pygame.K_SPACE]:
#         try_attack()

#     update_enemies()
#     draw_room()
#     draw_player()
#     draw_hud()
# else:
#     draw_menu()

#     if DEBUG:
#        draw_debug_hud()
#     process_collisions(keys)

# if menu_open:
#     if keys[pygame.K_ESCAPE]:
#         running = False

#     if keys[pygame.K_r]:
#         # reset game
#         player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
#         hp = max_hp
#         tokens = 0
#         has_metal_spear = False
#         current_room = "starting_room"

#         for name in rooms:
#             if name == "starting_room":
#                 rooms[name]["enemies"] = []
#             else:
#                 rooms[name]["enemies"] = make_enemies(random.randint(2, 5), speed=2)

#         menu_open = False

#     if hp <= 0:
#         # Game over scherm
#         screen.fill(DARK)
#         over1 = title.render("You suck a googus", True, (255,200,200))
#         over2 = ui.render("Enter: opnieuw beginnen | Esc: afsluiten", True, WHITE)
#         screen.blit(over1, over1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
#         screen.blit(over2, over2.get_rect(center=(WIDTH//2, HEIGHT//2 + 24)))
#         pygame.display.flip()
#         waiting = True 
#         while waiting:
#             for ev in pygame.event.get():
#                 if ev.type == pygame.QUIT:
#                     waiting = False
#                     running = False
#             k = pygame.key.get_pressed()
#             if k[pygame.K_RETURN]:
#                 # reset spel
#                 player_rect.update(0, 0, 40, 56)
#                 player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)

#                 hp = max_hp
#                 tokens = 0
#                 has_metal_spear = False
#                 # respawn enemies
#                 for name in rooms:
#                     if name == "starting_room":
#                         rooms[name]["enemies"] = []
                    
#                     else:
#                         rooms[name]["enemies"] = make_enemies(random.randint(1,3),speed=2
#                     )
#                 current_room = "starting_room"
#                 waiting = False
#             elif k[pygame.K_ESCAPE]:
#                 waiting = False
#                 running = False

#     pygame.display.flip()
#     clock.tick(60)

# pygame.quit()

