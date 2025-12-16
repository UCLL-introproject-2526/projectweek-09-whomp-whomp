# import pygame, sys, random
# pygame.init()

# # --- Scherm ---
# WIDTH, HEIGHT = 900, 600
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# pygame.display.set_caption("Hotel Transylvania")
# clock = pygame.time.Clock()

# # --- Fonts ---
# ui = pygame.font.SysFont(None, 32)
# title = pygame.font.SysFont(None, 56)

# # --- Kleuren ---
# WHITE = (255,255,255)
# RED = (230,50,50)
# GREEN = (80,220,120)
# YELLOW = (230,200,60)
# BROWN = (120,80,40)
# DARK = (20,10,22)

# # --- Speler ---
# player = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
# player_speed = 5
# player_dir = "down"
# max_hp = 5
# hp = max_hp
# invul_ms = 500
# last_hit = -9999

# # --- Combat / progression ---
# tokens = 0
# has_metal_spear = False
# attack_range = 50
# attack_cd_ms = 300
# last_attack = -9999
# popup_msg = None
# popup_until = 0

# player_name = ""
# current_room = "starting_room"
# current_weapon = None

# # --- Enemy functies ---
# def make_enemy(x, y, hp=3, speed=2):
#     return {
#         "rect": pygame.Rect(x, y, 42, 42),
#         "hp": hp,
#         "max_hp": hp,
#         "dx": random.choice([-speed, speed]),
#         "dy": random.choice([-speed, speed])
#     }

# def make_enemies(amount, speed):
#     return [make_enemy(random.randint(50, WIDTH-90), random.randint(50, HEIGHT-90), hp=3, speed=speed) for _ in range(amount)]

# # --- Rooms ---
# rooms = {
#     "starting_room": {
#         "color": (55, 188, 31),
#         "doors": [
#             {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "lobby", "spawn": (WIDTH//2, HEIGHT-100)}
#         ],
#         "enemies": []
#     },
#     "lobby": {
#         "color": (32, 12, 36),
#         "doors": [
#             {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "kitchen", "spawn": (120, HEIGHT//2)}
#         ],
#         "enemies": make_enemies(random.randint(1, 2), 2)
#     },
#     "kitchen": {
#         "color": (60, 25, 5),
#         "doors": [
#             {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "lobby", "spawn": (WIDTH-140, HEIGHT//2)},
#             {"rect": pygame.Rect(WIDTH-110, 60, 80, 110), "target": "library", "spawn": (WIDTH//2, HEIGHT-140)}
#         ],
#         "enemies": make_enemies(random.randint(2, 5), 2)
#     },
#     "library": {
#         "color": (5, 40, 62),
#         "doors": [
#             {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "kitchen", "spawn": (WIDTH-140, HEIGHT//2)}
#         ],
#         "enemies": make_enemies(random.randint(1,3), 1)
#     }
# }

# # --- Camera ---
# def get_camera():
#     cam_x = player.centerx - WIDTH // 2
#     cam_y = player.centery - HEIGHT // 2
#     cam_x = max(0, min(cam_x, WIDTH))
#     cam_y = max(0, min(cam_y, HEIGHT))
#     return cam_x, cam_y

# # --- Naam invoeren ---
# def ask_player_name():
#     global player_name
#     player_name = ""
#     asking = True
#     while asking:
#         screen.fill(DARK)
#         text = ui.render("Voer je naam in: " + player_name, True, WHITE)
#         screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
#         pygame.display.flip()
#         for ev in pygame.event.get():
#             if ev.type == pygame.QUIT:
#                 pygame.quit(); sys.exit()
#             if ev.type == pygame.KEYDOWN:
#                 if ev.key == pygame.K_RETURN:
#                     if player_name == "":
#                         player_name = "Speler"
#                     asking = False
#                 elif ev.key == pygame.K_BACKSPACE:
#                     player_name = player_name[:-1]
#                 elif ev.unicode.isalnum() or ev.unicode in " -_":
#                     player_name += ev.unicode

# # --- Startscherm ---
# def show_start_screen():
#     screen.fill(DARK)
#     screen.blit(title.render("Hotel Transylvania", True, WHITE), (WIDTH//2-200, HEIGHT//2-120))
#     screen.blit(ui.render("Gebruik ZQSD of pijltjes om te bewegen", True, WHITE), (WIDTH//2-180, HEIGHT//2-40))
#     screen.blit(ui.render("Linkermuisknop = aanvallen", True, WHITE), (WIDTH//2-150, HEIGHT//2))
#     screen.blit(ui.render("10 tokens = Metalen speer upgrade", True, WHITE), (WIDTH//2-160, HEIGHT//2+40))
#     screen.blit(ui.render("Druk op ENTER om te starten", True, YELLOW), (WIDTH//2-150, HEIGHT//2+160))
#     pygame.display.flip()
#     waiting = True
#     while waiting:
#         for ev in pygame.event.get():
#             if ev.type == pygame.QUIT:
#                 pygame.quit(); sys.exit()
#             if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
#                 waiting = False

# # --- Draw HUD ---
# def draw_hud():
#     for i in range(max_hp):
#         col = (220,60,60) if i < hp else (90,40,40)
#         x = 16 + i*22
#         pygame.draw.circle(screen, col, (x, 18), 8)
#         pygame.draw.circle(screen, col, (x+10, 18), 8)
#         pygame.draw.polygon(screen, col, [(x-5, 22), (x+15, 22), (x+5, 34)])
#     weapon = "Metalen speer" if has_metal_spear else "Houten speer"
#     info = f"Tokens: {tokens} | Wapen: {weapon}"
#     screen.blit(ui.render(info, True, WHITE), (16, 50))
#     if popup_msg and pygame.time.get_ticks() < popup_until:
#         surf = ui.render(popup_msg, True, YELLOW)
#         screen.blit(surf, (16, 80))

# # --- Draw Room & Player ---
# def draw_room():
#     room = rooms[current_room]
#     cam_x, cam_y = get_camera()
#     screen.fill(room["color"])
#     # deuren
#     for d in room["doors"]:
#         draw_rect = d["rect"].copy()
#         draw_rect.x -= cam_x
#         draw_rect.y -= cam_y
#         pygame.draw.rect(screen, YELLOW, draw_rect, border_radius=6)
#         pygame.draw.rect(screen, BROWN, draw_rect, 3, border_radius=6)
#         tag = ui.render(d["target"], True, WHITE)
#         screen.blit(tag, (draw_rect.centerx - tag.get_width()//2, draw_rect.top - 24))
#     # vijanden
#     for e in room["enemies"]:
#         if e["hp"] > 0:
#             draw_rect = e["rect"].copy()
#             draw_rect.x -= cam_x
#             draw_rect.y -= cam_y
#             pygame.draw.rect(screen, GREEN, draw_rect, border_radius=6)
#             # HP bar
#             bar_w = draw_rect.width
#             hp_ratio = e["hp"] / e["max_hp"]
#             hp_w = int(bar_w * hp_ratio)
#             bar_x = draw_rect.x
#             bar_y = draw_rect.y - 10
#             pygame.draw.rect(screen, (60,60,60), (bar_x, bar_y, bar_w, 6))
#             pygame.draw.rect(screen, (220,60,60), (bar_x, bar_y, hp_w, 6))
#     # speler
#     draw_rect = player.copy()
#     draw_rect.x -= cam_x
#     draw_rect.y -= cam_y
#     pygame.draw.rect(screen, RED, draw_rect, border_radius=10)

# # --- Input ---
# def handle_input(keys):
#     global player_dir
#     vx = vy = 0
#     if keys[pygame.K_LEFT] or keys[pygame.K_a]:
#         vx = -player_speed; player_dir = "left"
#     if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
#         vx = player_speed; player_dir = "right"
#     if keys[pygame.K_UP] or keys[pygame.K_w]:
#         vy = -player_speed; player_dir = "up"
#     if keys[pygame.K_DOWN] or keys[pygame.K_s]:
#         vy = player_speed; player_dir = "down"
#     player.x += vx
#     player.y += vy
#     player.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))

# # --- Enemy Update ---
# def update_enemies():
#     for e in rooms[current_room]["enemies"]:
#         if e["hp"] > 0:
#             e["rect"].x += e["dx"]r
#             e["rect"].y += e["dy"]
#             if e["rect"].left < 0 or e["rect"].right > WIDTH:
#                 e["dx"] *= -1
#             if e["rect"].top < 0 or e["rect"].bottom > HEIGHT:
#                 e["dy"] *= -1

# # --- Attack ---
# def attack_rect():
#     r = player
#     if player_dir == "up":
#         return pygame.Rect(r.centerx-8, r.top-attack_range, 16, attack_range)
#     if player_dir == "down":
#         return pygame.Rect(r.centerx-8, r.bottom, 16, attack_range)
#     if player_dir == "left":
#         return pygame.Rect(r.left-attack_range, r.centery-8, attack_range, 16)
#     return pygame.Rect(r.right, r.centery-8, attack_range, 16)

# def current_damage():
#     return 3 if has_metal_spear else 1

# def try_attack():
#     global last_attack, popup_msg, popup_until, tokens, has_metal_spear
#     now = pygame.time.get_ticks()
#     if now - last_attack < attack_cd_ms:
#         return
#     last_attack = now
#     hb = attack_rect()
#     for e in rooms[current_room]["enemies"]:
#         if e["hp"] > 0 and hb.colliderect(e["rect"]):
#             e["hp"] -= current_damage()
#             if e["hp"] <= 0:
#                 tokens += 1
#                 popup_msg = "+1 token (monster verslagen)"
#                 popup_until = now + 1500
#                 if not has_metal_spear and tokens >= 10:
#                     has_metal_spear = True
#                     popup_msg = "Metalen speer vrijgespeeld!"
#                     popup_until = now + 2000

# # --- Damage ---
# def handle_damage(amount=1):
#     global hp, last_hit
#     now = pygame.time.get_ticks()
#     if now - last_hit >= invul_ms:
#         last_hit = now
#         hp -= amount

# def process_collisions(keys):
#     for e in rooms[current_room]["enemies"]:
#         if e["hp"] > 0 and player.colliderect(e["rect"]):
#             handle_damage(1)
#     for d in rooms[current_room]["doors"]:
#         if player.colliderect(d["rect"]) and keys[pygame.K_e]:
#             switch_room(d["target"], d["spawn"])

# def switch_room(target, spawn):
#     global current_room
#     current_room = target
#     player.center = spawn

# def show_game_over():
#     screen.fill(DARK)
#     over1 = title.render(f"Jammer {player_name}, je bent doodgegaan!", True, (255,200,200))
#     over2 = ui.render("Enter: opnieuw beginnen | Esc: afsluiten", True, WHITE)
#     screen.blit(over1, over1.get_rect(center=(WIDTH//2, HEIGHT//2-20)))
#     screen.blit(over2, over2.get_rect(center=(WIDTH//2, HEIGHT//2+24)))
#     pygame.display.flip()

# def reset_game():
#     global hp, tokens, has_metal_spear, current_room, player
#     hp = max_hp
#     tokens = 0
#     has_metal_spear = False
#     current_room = "starting_room"
#     player.center = (WIDTH//2, HEIGHT//2)
#     for name in rooms:
#         if name == "starting_room":
#             rooms[name]["enemies"] = []
#         else:
#             rooms[name]["enemies"] = make_enemies(random.randint(1,3), 2)

# # --- Start ---
# ask_player_name()
# show_start_screen()

# # --- Main loop ---
# running = True
# while running:
#     for ev in pygame.event.get():
#         if ev.type == pygame.QUIT:
#             running = False
#         elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
#             try_attack()

#     keys = pygame.key.get_pressed()
#     handle_input(keys)
#     if keys[pygame.K_SPACE]:
#         try_attack()

#     update_enemies()
#     draw_room()
#     draw_hud()
#     process_collisions(keys)

#     if hp <= 0:
#         show_game_over()
#         waiting = True
#         while waiting:
#             for ev in pygame.event.get():
#                 if ev.type == pygame.QUIT:
#                     waiting = False
#                     running = False
#             k = pygame.key.get_pressed()
#             if k[pygame.K_RETURN]:
#                 reset_game()
#                 waiting = False
#             elif k[pygame.K_ESCAPE]:
#                 waiting = False
#                 running = False

#     pygame.display.flip()
#     clock.tick(60)

# pygame.quit()
# sys.exit()


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

floor_bg = pygame.image.load(os.path.join(IMG_DIR, "stone floor.jpg")).convert()
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
popup_msg = None
popup_until = 0

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
    return [make_enemy(
        random.randint(50, WIDTH-90),
        random.randint(50, HEIGHT-90),
        hp=3, speed=speed
    ) for _ in range(amount)]

# ================= ROOMS =================
rooms = {
    "starting_room": {
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90),
             "target": "lobby", "spawn": (WIDTH//2, HEIGHT-100)}
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
        "enemies": make_enemies(random.randint(1,3), 1)
    }
}

# ================= NAAM =================
def ask_player_name():
    global player_name
    player_name = ""
    asking = True
    while asking:
        screen.blit(start_bg, (0,0))
        text = ui.render("Voer je naam in: " + player_name, True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 200))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    if player_name == "":
                        player_name = "Speler"
                    asking = False
                elif ev.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif ev.unicode.isprintable():
                    player_name += ev.unicode

# ================= STARTSCHERM =================
def show_start_screen():
    waiting = True
    while waiting:
        screen.blit(start_bg, (0,0))
        screen.blit(title.render("Hotel Transylvania", True, WHITE), (220, 80))
        screen.blit(ui.render("Druk ENTER om te starten", True, YELLOW), (320, 520))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                waiting = False

# ================= HUD =================
def draw_hud():
    for i in range(max_hp):
        col = (220,60,60) if i < hp else (90,40,40)
        x = 16 + i*22
        pygame.draw.circle(screen, col, (x, 18), 8)

# ================= TEKEN KAMER =================
def draw_room():
    screen.blit(floor_bg, (0,0))

    for d in rooms[current_room]["doors"]:
        pygame.draw.rect(screen, YELLOW, d["rect"], border_radius=6)
        pygame.draw.rect(screen, BROWN, d["rect"], 3, border_radius=6)

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
    if keys[pygame.K_a]: player.x -= player_speed; player_dir="left"
    if keys[pygame.K_d]: player.x += player_speed; player_dir="right"
    if keys[pygame.K_w]: player.y -= player_speed; player_dir="up"
    if keys[pygame.K_s]: player.y += player_speed; player_dir="down"
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

# ================= AANVAL =================
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
    hb = attack_rect()
    dmg = 3 if has_metal_spear else 1
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
    draw_room()
    draw_hud()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
