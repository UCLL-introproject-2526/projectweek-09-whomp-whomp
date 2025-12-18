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

# ================= AFBEELDINGEN =================
start_bg = pygame.image.load(os.path.join(IMG_DIR, "Startscherm.jpg")).convert()
start_bg = pygame.transform.scale(start_bg, (WIDTH, HEIGHT))

floor_bg = pygame.image.load(os.path.join(IMG_DIR, "stone.jpg")).convert()
floor_bg = pygame.transform.scale(floor_bg, (WIDTH, HEIGHT))

# FIX 1: Correct player sprite path
player_sheet = pygame.image.load(os.path.join(IMG_DIR, "player.png")).convert_alpha()

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

# ================= ENEMIES =================
def make_enemy(x,y,hp=3,speed=2):
    return {
        "rect": pygame.Rect(x,y,42,42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed,speed]),
        "dy": random.choice([-speed,speed])
    }

def make_enemies(n,s):
    return [make_enemy(random.randint(50,ROOM_WIDTH-90),
                       random.randint(50,ROOM_HEIGHT-90),
                       3,s) for _ in range(n)]

# ================= ROOMS =================
rooms = {
    "starting_room":{
        "doors":[{"rect":pygame.Rect(760,20,80,90),"target":"lobby","spawn":(200,HEIGHT//2)}],
        "enemies":[]
    },
    "lobby":{
        "doors":[{"rect":pygame.Rect(WIDTH-110,HEIGHT//2-55,80,110),
                  "target":"kitchen","spawn":(200,HEIGHT//2)}],
        "enemies":make_enemies(random.randint(1,2),3)
    },
    "kitchen":{
        "doors":[
            {"rect":pygame.Rect(30,HEIGHT//2-55,80,110),"target":"lobby","spawn":(WIDTH-200,HEIGHT//2)},
            {"rect":pygame.Rect(WIDTH-110,60,80,110),"target":"library","spawn":(WIDTH//2,HEIGHT-160)}
        ],
        "enemies":make_enemies(random.randint(2,5),2)
    },
    "library":{
        "doors":[{"rect":pygame.Rect(WIDTH//2-40,HEIGHT-100,80,80),
                  "target":"kitchen","spawn":(WIDTH-200,HEIGHT//2)}],
        "enemies":make_enemies(random.randint(1,3),1)
    }
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
    global hp,last_hit
    now = pygame.time.get_ticks()
    if now-last_hit>=invul_ms:
        last_hit=now
        hp-=1

# FIX 2: Add enemy boundary collision
def update_enemies():
    for e in rooms[current_room]["enemies"]:
        if e["hp"]>0:
            e["rect"].x+=e["dx"]
            e["rect"].y+=e["dy"]
            
            # Bounce off walls
            if e["rect"].left<=0 or e["rect"].right>=ROOM_WIDTH:
                e["dx"]*=-1
            if e["rect"].top<=0 or e["rect"].bottom>=ROOM_HEIGHT:
                e["dy"]*=-1
            
            # Clamp to room bounds
            e["rect"].clamp_ip(pygame.Rect(0,0,ROOM_WIDTH,ROOM_HEIGHT))
            
            if player_rect.colliderect(e["rect"]): 
                handle_damage()

# FIX 3: Add door collision detection
def check_doors():
    global current_room, player_rect
    for door in rooms[current_room]["doors"]:
        if player_rect.colliderect(door["rect"]):
            current_room = door["target"]
            player_rect.center = door["spawn"]
            break

# FIX 4: Check game state
def check_game_state():
    # Check win condition
    total_enemies = sum(1 for room_data in rooms.values() 
                       for e in room_data["enemies"] if e["hp"]>0)
    if total_enemies == 0:
        return "win"
    
    # Check game over
    if hp <= 0:
        return "game_over"
    
    return "playing"

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

# ================= ENDSCREENS =================
def game_over_screen():
    while True:
        screen.fill(DARK)
        screen.blit(title.render("GAME OVER",True,RED),(280,250))
        screen.blit(ui.render("ESC om af te sluiten",True,WHITE),(320,350))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
                return

def win_screen():
    while True:
        screen.fill(DARK)
        screen.blit(title.render("GEWONNEN!",True,GREEN),(280,250))
        screen.blit(ui.render("ESC om af te sluiten",True,WHITE),(320,350))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE):
                return

# ================= STARTSCREENS =================
def ask_name():
    name=""
    while True:
        screen.blit(start_bg,(0,0))
        # FIX 7: Corrected Y coordinate (was 900, now within screen)
        screen.blit(ui.render("Naam: "+name,True,WHITE),(300,400))
        screen.blit(ui.render("ENTER om door te gaan",True,YELLOW),(280,450))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_RETURN: return name
                elif e.key==pygame.K_BACKSPACE: name=name[:-1]
                elif e.unicode.isprintable(): name+=e.unicode

def start_screen():
    while True:
        screen.blit(start_bg,(0,0))
        screen.blit(title.render("Hotel Transylvania",True,WHITE),(220,80))
        screen.blit(ui.render("ENTER om te starten",True,YELLOW),(330,520))
        screen.blit(ui.render("- Gebruik de toetsen zqsd of maak gebruik van de pijltjes.",True,YELLOW),(150,150))
        screen.blit(ui.render("- Gebruik SPATIE of linkermuisklik om aan te vallen",True,YELLOW),(150,220))
        screen.blit(ui.render("- Probeer alle monsters te verslaan!",True,YELLOW),(150,290))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN: return

# ================= MAIN =================
player_name = ask_name()
start_screen()

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: 
            running=False
        # FIX 5: Add mouse click attack
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            try_attack()

    keys = pygame.key.get_pressed()
    handle_input(keys)
    if keys[pygame.K_SPACE]: try_attack()

    # FIX 2: Use new enemy update function
    update_enemies()
    
    # FIX 3: Check door collisions
    check_doors()
    
    # FIX 6: Check game state
    game_state = check_game_state()
    if game_state == "game_over":
        game_over_screen()
        running = False
    elif game_state == "win":
        win_screen()
        running = False

    draw_room()
    draw_player()
    draw_hud()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()