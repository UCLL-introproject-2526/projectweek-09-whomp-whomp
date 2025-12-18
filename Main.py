import pygame, sys, random, os
pygame.init()
pygame.mixer.init()

# ================= PADEN =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")

shop_cd_ms = 300
last_shop_action = 0

runs_played = 0
best_tokens = 0

def reset_run():
    global hp, tokens, damage_bonus, has_metal_spear
    global current_room, keys_owned, last_hit

    hp = max_hp
    tokens = 0
    damage_bonus = 0
    has_metal_spear = False
    keys_owned.clear()
    last_hit = -9999

    current_room = "starting_room"
    player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)

    # enemies opnieuw spawnen
    for name in rooms:
        if name == "starting_room" or name == "shop_room":
            rooms[name]["enemies"] = []
        else:
            rooms[name]["enemies"] = make_enemies(
                random.randint(2, 5), speed=2
            )


WIDTH, HEIGHT = 900, 600
ROOM_WIDTH, ROOM_HEIGHT = 1600, 1200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()
WALL_THICKNESS = 30

# ================= AFBEELDINGEN =================
start_bg = pygame.image.load(("img\Startscherm.jpg")).convert_alpha()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(("img\stone.jpg")).convert_alpha()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

player_sheet = pygame.image.load("img\player.png").convert_alpha()

# ================= FONTS =================
ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56,)

# ================= KLEUREN =================
WHITE = (255,255,255)
RED = (230,50,50)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

# ================= PLAYER =================
player_rect = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
player_speed = 5
player_dir = "down"
max_hp = 10
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

buy_sound = pygame.mixer.Sound("projectweek-09-whomp-whomp/sounds/buy_1.wav")
buy_sound.set_volume(0.6)

error_sound = pygame.mixer.Sound("projectweek-09-whomp-whomp/sounds/buy_1.wav")  # tijdelijk zelfde sound
error_sound.set_volume(0.4)




    

def load_spritesheet(sheet, frame_w, frame_h):
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    for y in range(0, sheet.get_height(), fh):
        row = []
        for x in range(0, sheet.get_width(), fw):
            row.append(sheet.subsurface(pygame.Rect(x,y,fw,fh)))
        frames.append(row)
    return frames

player_sprites = load_sprites(player_sheet, 64, 64)
DIR_ROW = {"down":0,"left":1,"right":2,"up":3}

# ================= COMBAT =================
tokens = 0
has_metal_spear = False
wood_damage = 1
metal_damage = 3
attack_range = 100000
attack_cd_ms = 300
last_attack = -9999
popup_msg = None
popup_until = 0
damage_bonus = 0

def make_enemy(x, y, hp=3, speed=2):
    return {
        "rect": pygame.Rect(x, y, 42, 42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed, speed]),
        "dy": random.choice([-speed, speed]),
        "frame": 0,
        "frame_timer": 0,
        "dead": False
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

# --- extra deur naar de shop ---
shop_door = random_door_rect("bottom")

rooms["starting_room"]["doors"].append({
    "rect": shop_door,
    "target": "shop_room",
    "spawn": spawn_from_door(shop_door)
})


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

current_room = "starting_room"

# ======================
# SHOP ROOM
# ======================

rooms["shop_room"] = {
    "color": (60, 40, 80),
    "doors": [],
    "enemies": []
}
# --- deur terug naar starting_room ---
back_door = random_door_rect("top")

rooms["shop_room"]["doors"].append({
    "rect": back_door,
    "target": "starting_room",
    "spawn": spawn_from_door(back_door)
})



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

def draw_walls():
    cam_x, cam_y = get_camera()
    for wall in get_room_walls():
        draw_rect = wall.copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y
        pygame.draw.rect(screen, (70, 70, 70), draw_rect)

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

# ================= ENEMIES =================
def make_enemy(x,y,hp=3,speed=2):
    return {
        "rect": pygame.Rect(x,y,42,42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed,speed]),
        "dy": random.choice([-speed,speed])
    }

    title_text = title.render("HAUNTED HOUSE", True, WHITE)
    screen.blit(title_text, title_text.get_rect(center=(WIDTH//2, 80)))

    info_lines = []

    # GAME OVER TEKST
    if hp <= 0:
        if hp <= 0:
            info_lines.append("💀 GAME OVER 💀")
            info_lines.append("")
            info_lines.append(f"Runs played: {runs_played}")
            info_lines.append(f"Best tokens: {best_tokens}")
            info_lines.append("")
            info_lines.append("R - New Run")
            info_lines.append("ESC - Quit")


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


# ================= ROOMS =================
# rooms = {
#     "starting_room":{
#         "doors":[{"rect":pygame.Rect(760,20,80,90),"target":"lobby","spawn":(200,HEIGHT//2)}],
#         "enemies":[]
#     },
#     "lobby":{
#         "doors":[{"rect":pygame.Rect(WIDTH-110,HEIGHT//2-55,80,110),
#                   "target":"kitchen","spawn":(200,HEIGHT//2)}],
#         "enemies":make_enemies(random.randint(1,2),3)
#     },
#     "kitchen":{
#         "doors":[
#             {"rect":pygame.Rect(30,HEIGHT//2-55,80,110),"target":"lobby","spawn":(WIDTH-200,HEIGHT//2)},
#             {"rect":pygame.Rect(WIDTH-110,60,80,110),"target":"library","spawn":(WIDTH//2,HEIGHT-160)}
#         ],
#         "enemies":make_enemies(random.randint(2,5),2)
#     },
#     "library":{
#         "doors":[{"rect":pygame.Rect(WIDTH//2-40,HEIGHT-100,80,80),
#                   "target":"kitchen","spawn":(WIDTH-200,HEIGHT//2)}],
#         "enemies":make_enemies(random.randint(1,3),1)
#     }
# }

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
        "enemies": make_enemies(random.randint(1,2), speed=2), 
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

# ================= CAMERA =================
def camera():
    return (
        max(0, min(player_rect.centerx-WIDTH//2, ROOM_WIDTH-WIDTH)),
        max(0, min(player_rect.centery-HEIGHT//2, ROOM_HEIGHT-HEIGHT))
    )

# ================= HUD =================
def draw_hud():
    for i in range(max_hp):
        col = RED if i < hp else (90,40,40)
        pygame.draw.circle(screen,col,(20+i*22,20),8)

    info = f"Tokens: {tokens} | Weapon: {'Metal' if has_metal_spear else 'Wood'}"
    screen.blit(ui.render(info,True,WHITE),(16,45))

    if popup_msg and pygame.time.get_ticks() < popup_until:
        screen.blit(ui.render(popup_msg,True,YELLOW),(16,75))

# ================= INPUT =================
def handle_input(keys):
    global player_dir, player_frame
    vx = vy = 0
    moving = False

    if keys[pygame.K_q]: vx=-player_speed; player_dir="left"; moving=True
    if keys[pygame.K_d]: vx= player_speed; player_dir="right"; moving=True
    if keys[pygame.K_z]: vy=-player_speed; player_dir="up"; moving=True
    if keys[pygame.K_s]: vy= player_speed; player_dir="down"; moving=True
    if keys[pygame.K_LEFT]:vx = -player_speed; player_dir = "left"; moving = True
    if keys[pygame.K_RIGHT]: vx = player_speed ; player_dir = "right"; moving = True
    if keys[pygame.K_UP]:vy = -player_speed; player_dir = "up"; moving = True
    if keys[pygame.K_DOWN]:vy= player_speed; player_dir = "down"; moving = True

def draw_minimap():
    map_w, map_h = 220, 140
    padding = 12

    x0 = WIDTH - map_w - padding
    y0 = HEIGHT - map_h - padding

    # achtergrond
    pygame.draw.rect(screen, (15, 15, 25), (x0, y0, map_w, map_h))
    pygame.draw.rect(screen, YELLOW, (x0, y0, map_w, map_h), 2)

    # layout
    rooms_per_row = 5
    cell_size = 26
    gap = 6

    all_rooms = ["starting_room"] + HAUNTED_ROOMS

    for i, room in enumerate(all_rooms):
        row = i // rooms_per_row
        col = i % rooms_per_row

        cx = x0 + 12 + col * (cell_size + gap)
        cy = y0 + 12 + row * (cell_size + gap)

        # kleur
        if room == current_room:
            color = GREEN
        else:
            color = (100, 100, 120)

        pygame.draw.rect(screen, color, (cx, cy, cell_size, cell_size))


def draw_room_name():
    room_text = ui.render(f"Room: {current_room}", True, WHITE)
    padding = 12

    x = WIDTH - room_text.get_width() - padding
    y = padding

    # optionele achtergrond (netter leesbaar)
    bg_rect = pygame.Rect(
        x - 8,
        y - 6,
        room_text.get_width() + 16,
        room_text.get_height() + 12
    )
    pygame.draw.rect(screen, (0, 0, 0), bg_rect)
    pygame.draw.rect(screen, YELLOW, bg_rect, 2)

    screen.blit(room_text, (x, y))


    player_rect.x += vx
    player_rect.y += vy
    player_rect.clamp_ip(pygame.Rect(0,0,ROOM_WIDTH,ROOM_HEIGHT))

    player_frame = player_frame + animation_speed if moving else 0

# ================= ATTACK =================
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
    base = metal_damage if has_metal_spear else wood_damage
    return base + damage_bonus


def try_attack():
    global last_attack, tokens, has_metal_spear, popup_msg, popup_until

    now = pygame.time.get_ticks()
    if now-last_attack < attack_cd_ms: return
    last_attack = now

    hb = attack_rect()

    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0 and hb.colliderect(e["rect"]):
            e["hp"] -= current_damage()

            # 👇 check of enemy NU sterft
            if e["hp"] <= 0 and not e["dead"]:
                e["dead"] = True
                tokens += 1
                global best_tokens
                best_tokens = max(best_tokens, tokens)

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
    pygame.draw.rect(screen, (255, 220, 120), draw_rect)
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
        hp -= 1
    if hp <= 0:
        game_over(player_name)

def room_cleared(room_name):
    for e in rooms[room_name]["enemies"]:
        if e["hp"] > 0:
            return False
    return True


def process_collisions(keys):
    # Enemy collision (damage player)
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0 and player_rect.colliderect(e["rect"]):
            handle_damage(1)

    # Door interaction
    for d in rooms[current_room]["doors"]:
        if player_rect.colliderect(d["rect"]):

            # 🚪 Check of room leeg is
            if not room_cleared(current_room) and current_room != "starting_room":
                draw_center_message("Kill all enemies first!")


                # deur is geblokkeerd
                return

            # ✅ Room cleared → deur mag open
            hint = ui.render("E: enter " + d["target"], True, WHITE)
            screen.blit(hint, (16, HEIGHT - 36))

            if keys[pygame.K_e]:
                switch_room(d["target"], d["spawn"])


def switch_room(target, spawn=None):
    global current_room
    current_room = target
    player_rect.center = spawn

def process_doors(keys):
    for d in rooms[current_room]["doors"]:
        if player_rect.colliderect(d["rect"]) and keys[pygame.K_e]:
            switch_room(d["target"], d["spawn"])

# ================= DRAW =================
def draw_room():
    camx,camy = camera()
    screen.blit(floor_bg,(0,0))

    for d in rooms[current_room]["doors"]:
        r=d["rect"].move(-camx,-camy)
        pygame.draw.rect(screen,YELLOW,r,3)

    for e in rooms[current_room]["enemies"]:
        if e["hp"]>0:
            r=e["rect"].move(-camx,-camy)
            pygame.draw.rect(screen,GREEN,r)

def draw_player():
    camx,camy = camera()
    img = player_sprites[DIR_ROW[player_dir]][int(player_frame)%4]
    screen.blit(img,(player_rect.x-camx,player_rect.y-camy))

# ================= STARTSCREENS =================
def ask_name():
    name = ""
    while True:
        screen.blit(start_bg, (0,0))
        screen.blit(ui.render("Vul hier je naam in: " + name, True, WHITE), (300,550))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    return name  # <-- teruggeven van de ingevoerde naam
                elif e.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif e.unicode.isprintable():
                    name += e.unicode

def draw_center_message(text, color=RED):
    surf = ui.render(text, True, color)

    x = WIDTH // 2 - surf.get_width() // 2
    y = HEIGHT // 2 - surf.get_height() // 2

    bg = pygame.Rect(
        x - 20,
        y - 12,
        surf.get_width() + 40,
        surf.get_height() + 24
    )

    pygame.draw.rect(screen, (0, 0, 0), bg)
    pygame.draw.rect(screen, color, bg, 2)

    screen.blit(surf, (x, y))

def handle_shop(keys):
    global tokens, hp, max_hp, damage_bonus, popup_msg, popup_until, last_shop_action

    lines = [
        "=== SHOP ===",
        "E : Heal +1 HP (3 tokens)",
        "R : Damage +1 (5 tokens)",
        "T : Max HP +1 (8 tokens)",
        "ESC : Leave shop"
    ]

    y = HEIGHT // 2 - 80
    for line in lines:
        txt = ui.render(line, True, WHITE)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))
        y += 32

    now = pygame.time.get_ticks()
    if now - last_shop_action < shop_cd_ms:
        return

    # ❤️ HEAL
    if keys[pygame.K_e]:
        last_shop_action = now
        if tokens >= 3 and hp < max_hp:
            tokens -= 3
            hp += 1
            buy_sound.play()
            popup_msg = "+1 HP bought"
        else:
            error_sound.play()
            popup_msg = "Cannot heal"
        popup_until = now + 1200

    # ⚔️ DAMAGE
    if keys[pygame.K_r]:
        last_shop_action = now
        if tokens >= 5:
            tokens -= 5
            damage_bonus += 1
            buy_sound.play()
            popup_msg = "+1 damage bought"
        else:
            error_sound.play()
            popup_msg = "Not enough tokens"
        popup_until = now + 1200

    # 💖 MAX HP
    if keys[pygame.K_t]:
        last_shop_action = now
        if tokens >= 8:
            tokens -= 8
            max_hp += 1
            hp = max_hp
            buy_sound.play()
            popup_msg = "+1 max HP bought"
        else:
            error_sound.play()
            popup_msg = "Not enough tokens"
        popup_until = now + 1200




def start_screen():
    while True:
        screen.blit(start_bg,(0,0))
        screen.blit(title.render("Hotel Transylvania",True,WHITE),(220,80))
        screen.blit(ui.render("ENTER om te starten",True,YELLOW),(330,520))
        screen.blit(ui.render("- Gebruik de toetsen zqsd of maak gebruik van de pijltjes.",True,YELLOW),(150,150))
        screen.blit(ui.render("- Gebruik linkermuisklik om de monsters aan te vallen", True,YELLOW),(150,220))
        screen.blit(ui.render("- Probeer al de monsters te verslaan, om zo het speel uit te spelen.", True, YELLOW),(150,290))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN: return

# ================= START ================
player_name = ask_name()

# ================= MAIN =================
start_screen()

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

shop_action = None


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
    handle_input(keys)
    process_doors(keys)
    if keys[pygame.K_SPACE]: try_attack()

    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0:
            e["rect"].x += e["dx"]
            e["rect"].y += e["dy"]
        if player_rect.colliderect(e["rect"]):
            handle_damage()


        if keys[pygame.K_r]:
            runs_played += 1
            reset_run()

        menu_open = False

            # player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
            # hp = max_hp
            # tokens = 0
            # has_metal_spear = False
            # current_room = "starting_room"

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
        draw_room_name()
        draw_minimap()

        if current_room == "shop_room":
            handle_shop(keys)




        if DEBUG:
            draw_debug_hud()

        process_collisions(keys)

        if hp <= 0:
            menu_open = True

    pygame.display.flip()
    clock.tick(60)
