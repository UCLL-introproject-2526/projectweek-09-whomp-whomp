import pygame, sys, random
pygame.init()
pygame.mixer.init()

DEBUG = True

shop_cd_ms = 300
last_shop_action = 0

NORMAL_ENEMY_SIZE = 64   # <-- pas aan: 64 / 72 / 80
BOSS_MULT = 2.2          # bosses worden 2.2x zo groot


is_attacking = False
attack_anim_time = 150  # ms
attack_anim_start = 0
attack_frame = 0.0
attack_anim_speed = 0.35

ATTACK_HIT_FRAME = 2
attack_hit_done = False


dodge_cd = 10000      # cooldown ms
dodge_time = 2000    # hoe lang dodge duurt
last_dodge = -9999  # meteen dodgen bij start
is_dodging = False
blink_interval = 80  # ms tussen aan/uit




WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()
WALL_THICKNESS = 30

ROOM_WIDTH, ROOM_HEIGHT = 1800, 1200

ui = pygame.font.SysFont(None, 26)
title = pygame.font.SysFont(None, 56)
info_font = pygame.font.SysFont(None, 22)
hint_font = pygame.font.SysFont(None, 44)

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

def remove_blank_frames(frames, min_alpha=1):
    cleaned = []
    for f in frames:
        # bounding rect van niet-transparante pixels
        r = f.get_bounding_rect(min_alpha=min_alpha)
        if r.width > 0 and r.height > 0:
            cleaned.append(f)
    return cleaned




# Playerplayer_rect = pyg
# Start in het midden van de kamer, rekening houdend met muren
player_rect = pygame.Rect(0, 0, 40, 56)
player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
player_speed = 5
player_dir = "down"
max_hp = 10
hp = max_hp
invul_ms = 500
last_hit = -9999

#Animation
player_frame = 0.0
animation_speed= 0.001

door_img = pygame.image.load("projectweek-09-whomp-whomp\img\door3.jpg").convert_alpha()
door_img = pygame.transform.scale(door_img, (80, 100))  # pas grootte aan

bedroom_bg = pygame.image.load("projectweek-09-whomp-whomp/img/bedroom.png").convert_alpha()
bedroom_bg = pygame.transform.scale(bedroom_bg, (ROOM_WIDTH, ROOM_HEIGHT))  # full-room background

torture_bg = pygame.image.load("projectweek-09-whomp-whomp\img\Torture_chamber.png").convert_alpha()
torture_bg = pygame.transform.scale(torture_bg, (ROOM_WIDTH, ROOM_HEIGHT))

library_bg = pygame.image.load("projectweek-09-whomp-whomp\img\library.png").convert_alpha()
library_bg = pygame.transform.scale(library_bg, (ROOM_WIDTH, ROOM_HEIGHT))

basement_bg = pygame.image.load("projectweek-09-whomp-whomp/img/basement.png").convert_alpha()
basement_bg = pygame.transform.scale(basement_bg, (ROOM_WIDTH, ROOM_HEIGHT))

start_bg = pygame.image.load(("projectweek-09-whomp-whomp\img\Startscherm.jpg")).convert_alpha()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(("projectweek-09-whomp-whomp\img\stone.jpg")).convert_alpha()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

corridor_bg = pygame.image.load("projectweek-09-whomp-whomp/img/corridor.png").convert_alpha()
corridor_bg = pygame.transform.scale(corridor_bg, (ROOM_WIDTH, ROOM_HEIGHT))


frame_width, frame_height = 64, 64
player_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\img\character-spritesheet (2).png").convert_alpha()

skeleton_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\\img\\skeleton.png").convert_alpha()
frame_width, frame_height = 64, 64  # pas aan naar de juiste grootte van één frame
skeleton_img = skeleton_spritesheet.subsurface(pygame.Rect(0, 0, frame_width, frame_height))
skeleton_frames = load_skeleton_frames(skeleton_spritesheet, frame_width, frame_height)

skeleton_spritesheet = pygame.image.load("projectweek-09-whomp-whomp/img/skeleton.png").convert_alpha()
werewolf_sheet = pygame.image.load("projectweek-09-whomp-whomp/img/werewolf.png").convert_alpha()
zombie_sheet = pygame.image.load("projectweek-09-whomp-whomp/img/zombie2.png").convert_alpha()

FRAME_W, FRAME_H = 64, 64
WEREWOLF_FRAME_W, WEREWOLF_FRAME_H = 64, 64
ZOMBIE_FRAME_W, ZOMBIE_FRAME_H = 64, 64

skeleton_frames = remove_blank_frames(
    load_skeleton_frames(skeleton_spritesheet, FRAME_W, FRAME_H)
)

werewolf_frames = remove_blank_frames(
    load_skeleton_frames(werewolf_sheet, WEREWOLF_FRAME_W, WEREWOLF_FRAME_H)
)

zombie_frames = remove_blank_frames(
    load_skeleton_frames(zombie_sheet, ZOMBIE_FRAME_W, ZOMBIE_FRAME_H)
)



buy_sound = pygame.mixer.Sound("projectweek-09-whomp-whomp/sounds/buy_1.wav")
buy_sound.set_volume(0.6)

error_sound = pygame.mixer.Sound("projectweek-09-whomp-whomp/sounds/buy_1.wav")  # tijdelijk zelfde sound
error_sound.set_volume(0.4)

dodge_sound = pygame.mixer.Sound(
    "projectweek-09-whomp-whomp\sounds\swoosh-sound-effects.wav"
)
dodge_sound.set_volume(0.7)


enemy_death_sound = pygame.mixer.Sound(
    "projectweek-09-whomp-whomp\sounds\death_sound.wav"
)
enemy_death_sound.set_volume(0.6)

footstep_sound = pygame.mixer.Sound(
    "projectweek-09-whomp-whomp\sounds\loud-footstep.wav"
)
footstep_sound.set_volume(0.4)

footstep_channel = pygame.mixer.Channel(1)

spear_attack_sound = pygame.mixer.Sound(
    "projectweek-09-whomp-whomp\sounds\spear_sound.wav"
)
spear_attack_sound.set_volume(0.5)






def dodge_cooldown_ratio():
    now = pygame.time.get_ticks()
    elapsed = now - last_dodge
    return min(1.0, max(0.0, elapsed / dodge_cd))

    

def load_spritesheet(sheet, frame_w, frame_h):
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    for y in range(0, sheet_height, frame_h):
        row = []
        for x in range(0, sheet_width, frame_w):
            row.append(
                sheet.subsurface(pygame.Rect(x, y, frame_w, frame_h)).copy()
            )
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

ATTACK_DIRECTION_ROW = {
    "down": 4,
    "left": 5,
    "right": 6,
    "up": 7
}



# Combat / progression
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

BOSS_ROOM_NUMBERS = {
    5: "boss_zombie",
    10: "boss_skeleton",
    15: "boss_werewolf",
    20: "all_bosses"
}


# (optioneel) cache zodat we frames niet telkens opnieuw schalen
_scaled_cache = {}
def get_scaled_frames(frames, w, h):
    key = (id(frames), w, h)
    if key not in _scaled_cache:
        _scaled_cache[key] = [pygame.transform.scale(f, (w, h)) for f in frames]
    return _scaled_cache[key]

def make_enemy(x, y, enemy_type="skeleton"):
    # --- sizes ---
    NORMAL_ENEMY_SIZE = 64
    BOSS_MULT = 2.2

    if enemy_type == "skeleton":
        w = h = NORMAL_ENEMY_SIZE
        frames = get_scaled_frames(skeleton_frames, w, h)
        hp, speed, damage, attack_cd, token_drop = 3, 2, 1, 800, 1

    elif enemy_type == "zombie":
        w = h = NORMAL_ENEMY_SIZE
        frames = get_scaled_frames(zombie_frames, w, h)
        hp, speed, damage, attack_cd, token_drop = 5, 1.5, 2, 900, 1

    elif enemy_type == "werewolf":
        w = h = NORMAL_ENEMY_SIZE
        frames = get_scaled_frames(werewolf_frames, w, h)
        hp, speed, damage, attack_cd, token_drop = 4, 2.5, 0.5, 700, 1

    elif enemy_type == "boss_skeleton":
        w = h = int(NORMAL_ENEMY_SIZE * BOSS_MULT)
        frames = get_scaled_frames(skeleton_frames, w, h)
        hp, speed, damage, attack_cd, token_drop = 22, 2, 3, 600, 6

    elif enemy_type == "boss_zombie":
        w = h = int(NORMAL_ENEMY_SIZE * BOSS_MULT)
        frames = get_scaled_frames(zombie_frames, w, h)
        hp, speed, damage, attack_cd, token_drop = 28, 1, 3, 750, 6

    elif enemy_type == "boss_werewolf":
        w = h = int(NORMAL_ENEMY_SIZE * BOSS_MULT)
        frames = get_scaled_frames(werewolf_frames, w, h)
        hp, speed, damage, attack_cd, token_drop = 24, 3, 4, 550, 7

    else:
        raise ValueError(f"Unknown enemy_type: {enemy_type}")

    rect = pygame.Rect(x, y, w, h)
    return {
        "type": enemy_type,
        "rect": rect,
        "pos": pygame.Vector2(rect.center),
        "hp": hp,
        "max_hp": hp,
        "speed": speed,
        "frames": frames,
        "frame": 0,
        "frame_timer": pygame.time.get_ticks(),
        "dead": False,
        "attack_cd": attack_cd,
        "last_attack": 0,
        "damage": damage,
        "aggro_range": int((ROOM_WIDTH**2 + ROOM_HEIGHT**2) ** 0.5),
        "token_drop": token_drop
    }









def make_enemies(amount):
    enemies = []

    for _ in range(amount):
        x = random.randint(WALL_THICKNESS, ROOM_WIDTH - WALL_THICKNESS - 50)
        y = random.randint(WALL_THICKNESS, ROOM_HEIGHT - WALL_THICKNESS - 50)

        enemy_type = random.choice([
            "skeleton",
            "zombie",
            "werewolf"
        ])

        enemies.append(make_enemy(x, y, enemy_type))

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

MAX_NORMAL_ENEMIES = 8  # max aantal enemies in normale rooms

def enemies_for_room(room_number: int) -> int:
    # Room 1 = 2 enemies, room 2 = 3, room 3 = 4, ...
    # maar capped op MAX_NORMAL_ENEMIES
    return min(2 + (room_number - 1), MAX_NORMAL_ENEMIES)


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


# for i, room_name in enumerate(HAUNTED_ROOMS):
#     rooms[room_name] = {
#         "color": (
#             random.randint(40, 180),
#             random.randint(40, 180),
#             random.randint(40, 180)
#         ),
#         "doors": [],
#         "enemies": make_enemies(random.randint(2, 5))

#     }
#     if room_name == "abandoned_bedroom":
#         rooms[room_name]["bg"] = bedroom_bg
#     if room_name == "torture_chamber":
#         rooms[room_name]["bg"] = torture_bg
#     if room_name == "creepy_library":
#         rooms[room_name]["bg"] = library_bg
#     if room_name == "spider_corridor":
#         rooms[room_name]["bg"] = corridor_bg
#     if room_name == "dark_basement":
#         rooms[room_name]["bg"] = basement_bg





#     # deur terug naar vorige room
#     if i == 0:
#         back_target = "starting_room"
#     else:
#         back_target = HAUNTED_ROOMS[i - 1]

#     back_door = random_door_rect("left")
#     rooms[room_name]["doors"].append({
#         "rect": back_door,
#         "target": back_target,
#         "spawn": spawn_from_door(back_door)
#     })

#     # deur naar volgende room (behalve laatste)
#     if i < len(HAUNTED_ROOMS) - 1:
#         next_door = random_door_rect("right")
#         rooms[room_name]["doors"].append({
#             "rect": next_door,
#             "target": HAUNTED_ROOMS[i + 1],
#             "spawn": spawn_from_door(next_door)
#         })
#         room_number = i + 1  # 1..20


for i, room_name in enumerate(HAUNTED_ROOMS):
    room_number = i + 1  # 1..20  ✅ altijd correct

    rooms[room_name] = {
        "color": (
            random.randint(40, 180),
            random.randint(40, 180),
            random.randint(40, 180)
        ),
        "doors": [],
        "enemies": make_enemies(enemies_for_room(room_number))

    }

    
    if i < len(HAUNTED_ROOMS) - 1:
        next_door = random_door_rect("right")
        rooms[room_name]["doors"].append({
            "rect": next_door,
            "target": HAUNTED_ROOMS[i + 1],
            "spawn": spawn_from_door(next_door)
        })

        # ✅ BACK DOOR (altijd terug kunnen)
    back_target = "starting_room" if i == 0 else HAUNTED_ROOMS[i - 1]
    back_door = random_door_rect("left")
    rooms[room_name]["doors"].append({
        "rect": back_door,
        "target": back_target,
        "spawn": spawn_from_door(back_door),
       
    })



    if room_number in BOSS_ROOM_NUMBERS:
        boss_key = BOSS_ROOM_NUMBERS[room_number]

    # --- spawn bosses ---
        if boss_key == "all_bosses":
         # level 20: alle bosses samen
            cx, cy = ROOM_WIDTH // 2, ROOM_HEIGHT // 2

            b1 = make_enemy(0, 0, "boss_zombie")
            b1["rect"].center = (cx - 170, cy)
            b1["pos"] = pygame.Vector2(b1["rect"].center)

            b2 = make_enemy(0, 0, "boss_skeleton")
            b2["rect"].center = (cx, cy)
            b2["pos"] = pygame.Vector2(b2["rect"].center)

            b3 = make_enemy(0, 0, "boss_werewolf")
            b3["rect"].center = (cx + 170, cy)
            b3["pos"] = pygame.Vector2(b3["rect"].center)

            rooms[room_name]["enemies"] = [b1, b2, b3]

        else:
            # level 5/10/15: 1 boss
            boss = make_enemy(0, 0, boss_key)
            boss["rect"].center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
            boss["pos"] = pygame.Vector2(boss["rect"].center)
            rooms[room_name]["enemies"] = [boss]

    # ✅ shopdeur in ELKE boss room (altijd open)
        boss_shop_door = random_door_rect("bottom")
        rooms[room_name]["doors"].append({
            "rect": boss_shop_door,
            "target": "shop_room",
            "spawn": spawn_from_door(boss_shop_door),
            "always_open": True
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
    "spawn": spawn_from_door(back_door),
    "is_return": True
})


def show_info_screen():
    info_lines = [
        "DOEL:",
        "- Verken alle kamers.",
        "- Versla monsters om deuren te unlocken.",
        "- Versla bosses op level 5, 10, 15 en FINAL BOSS op level 20.",
        "",
        "TOKENS & SHOP:",
        "- Monsters droppen tokens.",
        "- In de shop kan je upgraden met tokens.",
        "- Shop vind je via de deur in de starting room (onderaan).",
        "",
        "BESTURING:",
        "- Bewegen: zqsd of pijltjes",
        "- Aanvallen: SPACE of linker muisklik",
        "- Dodge: LEFT SHIFT (heeft cooldown)",
        "- Menu: M",
        "- Shop: E = heal, R = damage, T = max HP, ESC = weg",
        "",
        "Druk ENTER of ESC om terug te gaan..."
    ]

    opened_at = pygame.time.get_ticks()

    info_running = True
    while info_running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                # kleine delay zodat ENTER van vorige scherm niet meteen sluit
                if pygame.time.get_ticks() - opened_at > 200:
                    if ev.key == pygame.K_RETURN or ev.key == pygame.K_ESCAPE:
                        info_running = False

        screen.blit(start_bg, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(170)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        screen.blit(title.render("INFO & CONTROLS", True, YELLOW), (WIDTH//2 - 220, 40))

        y = 120
        for line in info_lines:
            txt = info_font.render(line, True, WHITE)
            screen.blit(txt, (60, y))
            y += 22

        pygame.display.flip()
        clock.tick(60)




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
                    title_running = False
                elif ev.key == pygame.K_i:
                    show_info_screen()  # <- deze functie moet bestaan


        
        
        screen.blit(start_bg, (0, 0))
        screen.blit(title.render("Frankenstein mansion", True, WHITE), (250, 80))

        enter_text = ui.render("Druk ENTER om te starten", True, YELLOW)
        screen.blit(enter_text, enter_text.get_rect(center=(WIDTH//2, 520)))

        hint_text = hint_font.render("Druk I voor info & controls", True, WHITE)
        screen.blit(hint_text, hint_text.get_rect(center=(WIDTH//2, HEIGHT//2)))


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

    # Titel aanpassen afhankelijk van game over
    menu_title = "GAME OVER" if hp <= 0 else "HAUNTED HOUSE"
    title_text = title.render(menu_title, True, WHITE)
    screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, 80)))

    info_lines = []

    # GAME OVER TEKST
    if hp <= 0:
        info_lines.extend([
            f"Jammer {player_name},",
            "je bent doodgegaan.",
            "",
            "Druk R om opnieuw te beginnen",
            "of ESC om te stoppen"
        ])
    else:
        info_lines.extend([
            f"Player: {player_name}",
            f"Tokens: {tokens}",
            "",
            "CONTROLS:",
            "Move: zqsd / Arrow Keys",
            "Attack: SPACE or left mouse button",
            "Dodge: LEFT SHIFT",
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

    # ✅ ALTIJD tekenen (ook bij hp <= 0)
    y = 140
    line_h = 20
    blank_h = 10

    for line in info_lines:
        txt = ui.render(line, True, WHITE)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))
        y += blank_h if line == "" else line_h





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

def draw_heart(cx, cy, color):
    pygame.draw.circle(screen, color, (cx, cy), 8)
    pygame.draw.circle(screen, color, (cx + 10, cy), 8)
    pygame.draw.polygon(screen, color, [(cx - 5, cy + 4), (cx + 15, cy + 4), (cx + 5, cy + 16)])



def draw_hud():
    y = 18

    for i in range(max_hp):
        x = 16 + i * 32

        full_col = (220, 60, 60)
        empty_col = (90, 40, 40)

        # teken eerst een "lege" heart als achtergrond
        draw_heart(x, y, empty_col)

        remaining = hp - i  # hoeveel HP er nog in dit hartje zit

        if remaining >= 1:
            # volle heart
            draw_heart(x, y, full_col)

        elif remaining >= 0.5:
            # half heart: teken de volle heart maar knip hem half af
            old_clip = screen.get_clip()
            # bounding box van jouw heart: van (x-5, y-8) tot (x+15, y+16)
            screen.set_clip(pygame.Rect(x - 5, y - 8, 10, 24))  # alleen linker helft
            draw_heart(x, y, full_col)
            screen.set_clip(old_clip)

    # tokens/weapon (jouw bestaande code)
    weapon = "Metal spear" if has_metal_spear else "Wooden spear"
    info = f"Tokens: {tokens} | Weapon: {weapon}"
    screen.blit(ui.render(info, True, WHITE), (16, 50))

    if popup_msg and pygame.time.get_ticks() < popup_until:
        surf = ui.render(popup_msg, True, YELLOW)
        screen.blit(surf, (16, 80))



def draw_level_indicator():
    total_levels = len(HAUNTED_ROOMS)

    if current_room == "starting_room":
        level = 0
    elif current_room in HAUNTED_ROOMS:
        level = HAUNTED_ROOMS.index(current_room) + 1
    else:
        return  # shop_room → niets tonen

    text = f"Level {level} / {total_levels}"
    surf = ui.render(text, True, WHITE)

    padding = 10
    x = WIDTH - surf.get_width() - 20
    y = HEIGHT - surf.get_height() - 20

    bg = pygame.Rect(
        x - padding,
        y - padding,
        surf.get_width() + padding * 2,
        surf.get_height() + padding * 2
    )

    pygame.draw.rect(screen, (0, 0, 0), bg)
    pygame.draw.rect(screen, YELLOW, bg, 2)

    screen.blit(surf, (x, y))


def draw_minimap():
    map_w, map_h = 220, 140
    padding = 12

    x0 = WIDTH - map_w - padding
    y0 = HEIGHT - map_h - padding

    # achtergrond
    pygame.draw.rect(screen, (15, 15, 25), (x0, y0, map_w, map_h))
    pygame.draw.rect(screen, YELLOW, (x0, y0, map_w, map_h), 2)

    rooms_per_row = 5
    cell_size = 26
    gap = 6

    all_rooms = ["starting_room"] + HAUNTED_ROOMS

    for i, room in enumerate(all_rooms):
        row = i // rooms_per_row
        col = i % rooms_per_row

        cx = x0 + 12 + col * (cell_size + gap)
        cy = y0 + 12 + row * (cell_size + gap)

        # kleur huidige kamer
        if room == current_room:
            border_color = GREEN
            text_color = GREEN
        else:
            border_color = (120, 120, 140)
            text_color = WHITE

        # kader
        pygame.draw.rect(
            screen,
            border_color,
            (cx, cy, cell_size, cell_size),
            2
        )

        # nummer (1-based)
        number = str(i + 1)
        txt = ui.render(number, True, text_color)
        screen.blit(
            txt,
            (
                cx + cell_size // 2 - txt.get_width() // 2,
                cy + cell_size // 2 - txt.get_height() // 2
            )
        )

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







def handle_input(keys):
    global player_dir, player_frame

    vx = vy = 0
    moving = False

    if keys[pygame.K_LEFT] or keys[pygame.K_q]:
        vx = -player_speed
        player_dir = "left"
        moving = True

    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vx = player_speed
        player_dir = "right"
        moving = True

    if keys[pygame.K_UP] or keys[pygame.K_z]:
        vy = -player_speed
        player_dir = "up"
        moving = True

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        vy = player_speed
        player_dir = "down"
        moving = True

    move_player(vx, vy)

    # Animation logic - properly wraps frame counter
    if not is_attacking:
        if moving:
            player_frame += animation_speed
            # Wrap around when we reach the end of the animation
            max_frames = len(player_sprites[DIRECTION_ROW[player_dir]])
            if player_frame >= max_frames:
                player_frame = 0.0
        else:
            player_frame = 0.0  # Reset to idle frame when not moving

        # 🔊 voetstappen
    if moving and not is_dodging:
        if not footstep_channel.get_busy():
            footstep_channel.play(footstep_sound, loops=-1)
    else:
        footstep_channel.stop()




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

def enemy_attack(e):
    global hp
    now = pygame.time.get_ticks()

    if now - e["last_attack"] >= e["attack_cd"]:
        handle_damage(e["damage"])
        e["last_attack"] = now





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
    global last_attack, is_attacking, attack_anim_start
    global attack_frame, attack_hit_done

    now = pygame.time.get_ticks()
    if now - last_attack < attack_cd_ms:
        return

    last_attack = now
    is_attacking = True
    attack_anim_start = now
    attack_frame = 0.0
    attack_hit_done = False

    spear_attack_sound.play()  # 🔊 ATTACK SOUND


def apply_attack_damage():
    global tokens, popup_msg, popup_until, attack_hit_done

    if attack_hit_done:
        return

    if int(attack_frame) != ATTACK_HIT_FRAME:
        return

    attack_hit_done = True
    hb = attack_rect()

    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0 and hb.colliderect(e["rect"]):
            # 💥 DAMAGE
            e["hp"] -= current_damage()

            # ☠️ DEATH
            if e["hp"] <= 0 and not e["dead"]:
                e["dead"] = True
                enemy_death_sound.play()
                tokens += e.get("token_drop", 1)
                popup_msg = "+1 token"
                popup_until = pygame.time.get_ticks() + 1200







# def update_enemies():
#     now = pygame.time.get_ticks()

#     for e in rooms[current_room]["enemies"]:
#         if e["hp"] <= 0:
#             continue

#         # bewegen
#         e["rect"].x += e["dx"]
#         e["rect"].y += e["dy"]

#         if e["rect"].left < WALL_THICKNESS or e["rect"].right > ROOM_WIDTH - WALL_THICKNESS:
#             e["dx"] *= -1
#         if e["rect"].top < WALL_THICKNESS or e["rect"].bottom > ROOM_HEIGHT - WALL_THICKNESS:
#             e["dy"] *= -1

#         # animatie (identiek aan player-logica)
#         if now - e["frame_timer"] > 150:
#             e["frame_timer"] = now
#             if "frame_float" not in e:
#                 e["frame_float"] = 0.0
#                 e["last_frame"] = 0

#                 e["frame_float"] += 1
#                 e["last_frame"] = int(e["frame_float"])


#             if e["last_frame"] >= len(skeleton_frames):
#                 e["frame_float"] = 0.0
#                 e["last_frame"] = 0

def update_enemies():
    player_pos = pygame.Vector2(player_rect.center)
    bounds = pygame.Rect(
        WALL_THICKNESS, WALL_THICKNESS,
        ROOM_WIDTH - 2 * WALL_THICKNESS,
        ROOM_HEIGHT - 2 * WALL_THICKNESS
    )

    for e in rooms[current_room]["enemies"]:
        if e["hp"] <= 0:
            continue

        to_player = player_pos - e["pos"]
        dist = to_player.length()

        if dist < e["aggro_range"] and dist > 0:
            to_player.scale_to_length(e["speed"])   # blijft float
            e["pos"] += to_player
            e["rect"].center = (round(e["pos"].x), round(e["pos"].y))

        # binnen de kamer houden
        e["rect"].clamp_ip(bounds)
        e["pos"] = pygame.Vector2(e["rect"].center)





# def handle_damage(amount=1):
#     global hp, last_hit
#     now = pygame.time.get_ticks()
#     if now - last_hit >= invul_ms:
#         last_hit = now
#         hp -= amount


def handle_damage(amount=1):
    global hp, last_hit
    if is_dodging:
        return  # ❌ geen damage tijdens dodge

    now = pygame.time.get_ticks()
    if now - last_hit >= invul_ms:
        last_hit = now
        hp = max(0, hp - amount)



def room_cleared(room_name):
    for e in rooms[room_name]["enemies"]:
        if e["hp"] > 0:
            return False
    return True


def process_collisions(keys):
    # Enemy damage
    for e in rooms[current_room]["enemies"]:
        if e["hp"] > 0 and player_rect.colliderect(e["rect"]):
            enemy_attack(e)

    # Door collision → meteen doorgaan
    for d in rooms[current_room]["doors"]:
        if player_rect.colliderect(d["rect"]):

            # ❌ deur geblokkeerd als enemies leven
            if (not room_cleared(current_room)
                and current_room != "starting_room"
                and not d.get("always_open", False)):
                draw_center_message("Kill all enemies first!")
                return


            # ✅ DIRECT door de deur
            switch_room(d["target"], d["spawn"])
            return




def switch_room(target, spawn=None):
    global current_room

    # ✅ Als we de shop in gaan: stel de return-deur in naar de kamer waar we vandaan komen
    if target == "shop_room":
        prev_room = current_room
        prev_pos = player_rect.center  # terug naar waar je stond

        for door in rooms["shop_room"]["doors"]:
            if door.get("is_return", False):
                door["target"] = prev_room
                door["spawn"] = safe_spawn(prev_pos)
                break

    current_room = target

    if spawn:
        player_rect.center = safe_spawn(spawn)
    else:
        player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)




# def handle_input(keys):
#     global player_dir, player_frame

#     vx = vy = 0
#     moving = False

#     if keys[pygame.K_LEFT] or keys[pygame.K_a]:
#         vx = -player_speed
#         player_dir = "left"
#         moving = True

#     if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
#         vx = player_speed
#         player_dir = "right"
#         moving = True

#     if keys[pygame.K_UP] or keys[pygame.K_w]:
#         vy = -player_speed
#         player_dir = "up"
#         moving = True

#     if keys[pygame.K_DOWN] or keys[pygame.K_s]:
#         vy = player_speed
#         player_dir = "down"
#         moving = True

#     move_player(vx, vy)

#     # Animation logic
#     if not is_attacking:
#         if moving:
#             player_frame += animation_speed
#             # Walk animations only use first 7 frames
#             if player_frame >= 7:
#                 player_frame = 0.0
#         else:
#             player_frame = 0.0  # Idle on first frame

def enemies_remaining():
    return sum(1 for e in rooms[current_room]["enemies"] if e["hp"] > 0)

def max_enemy_damage_in_room():
    if current_room == "shop_room":
        return 0
    alive = [e for e in rooms[current_room]["enemies"] if e["hp"] > 0]
    if not alive:
        return 0
    return max(e.get("damage", 0) for e in alive)


def draw_top_right_info():
    lines = [
        "M : Menu",
        f"Enemies: {enemies_remaining()}",
        f"Enemy dmg: {max_enemy_damage_in_room()}",
        "Dodge"
    ]


    padding = 10
    line_height = 24
    bar_width = 140
    bar_height = 10

    max_width = max(ui.size(line)[0] for line in lines)
    box_width = max(max_width, bar_width) + padding * 2
    box_height = padding * 2 + line_height * len(lines) + bar_height + 6

    x = WIDTH - box_width - 12
    y = 12

    # achtergrond
    bg = pygame.Rect(x, y, box_width, box_height)
    pygame.draw.rect(screen, (0, 0, 0), bg)
    pygame.draw.rect(screen, YELLOW, bg, 2)

    # tekst
    ty = y + padding
    for line in lines:
        txt = ui.render(line, True, WHITE)
        screen.blit(txt, (x + padding, ty))
        ty += line_height

    # 🟦 cooldown bar
    ratio = dodge_cooldown_ratio()

    bar_x = x + padding
    bar_y = ty + 2

    # achtergrond bar
    pygame.draw.rect(
        screen,
        (80, 80, 80),
        (bar_x, bar_y, bar_width, bar_height)
    )

    # vulling
    pygame.draw.rect(
        screen,
        GREEN if ratio >= 1 else YELLOW,
        (bar_x, bar_y, bar_width * ratio, bar_height)
    )





def draw_room():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()

    # Floor en walls
    # Background (per room)
    if "bg" in room:
        screen.blit(room["bg"], (-cam_x, -cam_y))   # camera-offset zodat het meescrollt
    else:
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
        # Enemies
    # Enemies
    # Enemies
    for e in room["enemies"]:
        if e["hp"] <= 0:
            continue

        draw_rect = e["rect"].copy()
        draw_rect.x -= cam_x
        draw_rect.y -= cam_y

        frames = e["frames"]

    # update animatie (los van tekenen)
        now = pygame.time.get_ticks()
        if now - e["frame_timer"] >= 120:
            e["frame_timer"] = now
            e["frame"] = (e["frame"] + 1) % len(frames)

    # 🔥 ALTIJD tekenen
        img = frames[e["frame"]]
        screen.blit(img, draw_rect)

    # health bar
        hp_ratio = e["hp"] / e["max_hp"]
        bar_w = draw_rect.width
        bar_h = 5
        bar_x = draw_rect.x
        bar_y = draw_rect.y - 8

        pygame.draw.rect(screen, (120, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(
        screen, (0, 200, 0),
        (bar_x, bar_y, bar_w * hp_ratio, bar_h)
    )


            


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




def draw_debug_hud():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()

    lines = [
        f"Room: {current_room}",
        f"Player world pos: {player_rect.x}, {player_rect.y}",
        f"Camera pos: {cam_x}, {cam_y}",
        f"Room size: {ROOM_WIDTH} x {ROOM_HEIGHT}",
    ]

    padding = 8
    line_height = 20

    # bereken breedte & hoogte van het kadertje
    max_width = max(ui.size(line)[0] for line in lines)
    box_width = max_width + padding * 2
    box_height = len(lines) * line_height + padding * 2

    x = 10
    y = HEIGHT - box_height - 10

    # 🔲 achtergrond
    bg_rect = pygame.Rect(x, y, box_width, box_height)
    pygame.draw.rect(screen, (0, 0, 0), bg_rect)
    pygame.draw.rect(screen, YELLOW, bg_rect, 2)

    # ✏ tekst
    ty = y + padding
    for line in lines:
        text = ui.render(line, True, YELLOW)
        screen.blit(text, (x + padding, ty))
        ty += line_height

def draw_player():
    global player_frame, attack_frame

    # ✨ knipperen tijdens dodge
    if is_dodging:
        now = pygame.time.get_ticks()
        if (now // blink_interval) % 2 == 0:
            return  # sla tekenen over → onzichtbaar deze frame


    cam_x, cam_y = get_camera()

    if is_attacking:
        row = player_sprites[ATTACK_DIRECTION_ROW[player_dir]]
        frame_index = int(attack_frame)
        if frame_index >= len(row):
            frame_index = len(row) - 1
        img = row[frame_index]
        attack_frame = min(attack_frame + attack_anim_speed, len(row) - 1)
    else:
        row = player_sprites[DIRECTION_ROW[player_dir]]
        frame_index = int(player_frame) % len(row)
        img = row[frame_index]

    draw_rect = player_rect.copy()
    draw_rect.x -= cam_x
    draw_rect.y -= cam_y
    screen.blit(img, draw_rect)


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

        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1 and not menu_open:  # 1 = linker muisknop
                try_attack()






    keys = pygame.key.get_pressed()

    if menu_open:
        draw_menu()

        if keys[pygame.K_ESCAPE]:
            running = False

        if keys[pygame.K_r]:
            player_rect.center = (ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
            hp = max_hp
            tokens = 20
            has_metal_spear = False
            current_room = "starting_room"

            for name in rooms:
                if name == "starting_room":
                    rooms[name]["enemies"] = []
                else:
                    rooms[name]["enemies"] = make_enemies(
                    random.randint(2, 5)
)

            menu_open = False


    else:
        handle_input(keys)

        now = pygame.time.get_ticks()
        if keys[pygame.K_LSHIFT] and not is_dodging and now - last_dodge > dodge_cd:
            is_dodging = True
            last_dodge = now
            dodge_sound.play()   # 🔊 swoosh





        if keys[pygame.K_SPACE]:
            try_attack()

        if is_attacking:
            apply_attack_damage()

            if pygame.time.get_ticks() - attack_anim_start > attack_anim_time:
                is_attacking = False
                attack_frame = 0.0




        update_enemies()
        draw_room()
        draw_player()
        draw_hud()
        # draw_minimap()
        draw_top_right_info()
        draw_level_indicator()

        if current_room == "shop_room":
            handle_shop(keys)


        if is_dodging and pygame.time.get_ticks() - last_dodge > dodge_time:
            is_dodging = False


        if DEBUG:
            draw_debug_hud()

        process_collisions(keys)

        if hp <= 0:
            menu_open = True

    pygame.display.flip()
    clock.tick(60)