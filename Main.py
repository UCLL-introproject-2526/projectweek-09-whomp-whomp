import pygame, sys, random, os
pygame.init()

# ================= PADEN =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")

# ================= SCHERM =================
WIDTH, HEIGHT = 900, 600
ROOM_WIDTH, ROOM_HEIGHT = 1600, 1200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()
WALL_THICKNESS = 30

# ================= AFBEELDINGEN =================
start_bg = pygame.image.load(os.path.join(IMG_DIR, "Startscherm.jpg")).convert()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(os.path.join(IMG_DIR, "stone floor.jpg")).convert()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

player_sheet = pygame.image.load("projectweek-09-whomp-whomp\img\player.png").convert_alpha()

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
player_frame = 0
animation_speed = 0.2

max_hp = 5
hp = max_hp
invul_ms = 500
last_hit = -9999

# ================= SPRITES =================
def load_sprites(sheet, fw, fh):
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
attack_range = 42
attack_cd_ms = 300
last_attack = -9999
popup_msg = None
popup_until = 0

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

def make_enemies(n, speed):
    return [make_enemy(random.randint(50,ROOM_WIDTH-90),
                       random.randint(50,ROOM_HEIGHT-90),
                       3, speed) for _ in range(n)]


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


    player_rect.x += vx
    player_rect.y += vy
    player_rect.clamp_ip(pygame.Rect(0,0,ROOM_WIDTH,ROOM_HEIGHT))

    player_frame = player_frame + animation_speed if moving else 0

# ================= ATTACK =================
def attack_rect():
    r = player_rect
    if player_dir=="up": return pygame.Rect(r.centerx-8,r.top-attack_range,16,attack_range)
    if player_dir=="down": return pygame.Rect(r.centerx-8,r.bottom,16,attack_range)
    if player_dir=="left": return pygame.Rect(r.left-attack_range,r.centery-8,attack_range,16)
    return pygame.Rect(r.right,r.centery-8,attack_range,16)

def try_attack():
    global last_attack, tokens, has_metal_spear, popup_msg, popup_until
    now = pygame.time.get_ticks()
    if now-last_attack < attack_cd_ms: return
    last_attack = now

    dmg = metal_damage if has_metal_spear else wood_damage
    hb = attack_rect()

    for e in rooms[current_room]["enemies"]:
        if e["hp"]>0 and hb.colliderect(e["rect"]):
            e["hp"] -= dmg
            if e["hp"]<=0:
                tokens+=1
                popup_msg="+1 token"
                popup_until=now+1200
                if tokens>=10 and not has_metal_spear:
                    has_metal_spear=True
                    popup_msg="Metal spear unlocked!"
                    popup_until=now+2000

# ================= DAMAGE =================
def handle_damage():
    global hp, last_hit
    now = pygame.time.get_ticks()
    if now - last_hit >= invul_ms:
        last_hit = now
        hp -= 1
    if hp <= 0:
        game_over(player_name)

def game_over(name):
    while True:
        screen.fill((0,0,0))
        screen.blit(title.render(f"Jammer {name}, je bent verloren.", True, RED),(120,250))
        screen.blit(ui.render("Druk ENTER om af te sluiten", True, WHITE),(280,320))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                pygame.quit()
                sys.exit()


# ================= DEUREN =================
def switch_room(target, spawn):
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

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False

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


    draw_room()
    draw_player()
    draw_hud()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
