import pygame, sys, random, math
pygame.init()

WIDTH, HEIGHT = 900, 600
ROOM_WIDTH, ROOM_HEIGHT = 1600, 1200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()

ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56)

WHITE = (255,255,255)
RED = (220,60,60)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

# ---------------- PLAYER ----------------
player_rect = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
player_speed = 5
player_dir = "down"
max_hp = 5
hp = max_hp
invul_ms = 600
last_hit = -9999

player_frame = 0
animation_speed = 0.2

frame_width, frame_height = 64, 64
player_sheet = pygame.image.load("player.png").convert_alpha()

def load_sprites(sheet):
    frames = []
    for y in range(0, sheet.get_height(), frame_height):
        row = []
        for x in range(0, sheet.get_width(), frame_width):
            row.append(sheet.subsurface((x,y,frame_width,frame_height)))
        frames.append(row)
    return frames

player_sprites = load_sprites(player_sheet)

DIRECTION_ROW = {"down":0,"left":1,"right":2,"up":3}

# ---------------- COMBAT ----------------
tokens = 0
has_metal_spear = False
wood_damage = 1
metal_damage = 3
attack_range = 42
attack_cd = 300
last_attack = -9999

popup_msg = None
popup_until = 0

shake = 0

# ---------------- ENEMIES ----------------
def make_enemy(x, y, hp=3, speed=2):
    return {
        "rect": pygame.Rect(x, y, 42, 42),
        "hp": hp,
        "max_hp": hp,
        "speed": speed,
        "dx": random.choice([-1,1])*speed,
        "dy": random.choice([-1,1])*speed,
        "hit_flash": 0
    }

def make_enemies(n, speed):
    return [make_enemy(random.randint(80, ROOM_WIDTH-80),
                       random.randint(80, ROOM_HEIGHT-80),
                       3, speed) for _ in range(n)]

# ---------------- ROOMS ----------------
rooms = {
    "starting_room": {"color":(55,188,31),"doors":[
        {"rect":pygame.Rect(WIDTH//2-40,20,80,90),"target":"lobby","spawn":(200,HEIGHT//2)}
    ],"enemies":[]},

    "lobby":{"color":(32,12,36),"doors":[
        {"rect":pygame.Rect(WIDTH-110,HEIGHT//2-55,80,110),"target":"hallway","spawn":(200,HEIGHT//2)}
    ],"enemies":make_enemies(2,2)},

    "hallway":{"color":(80,80,80),"doors":[
        {"rect":pygame.Rect(WIDTH//2-40,HEIGHT-100,80,80),"target":"boss_room","spawn":(WIDTH//2,HEIGHT-150)}
    ],"enemies":make_enemies(3,3)},

    "boss_room":{"color":(120,0,0),"doors":[],
        "enemies":[make_enemy(ROOM_WIDTH//2,ROOM_HEIGHT//2,30,1)]
    }
}

current_room = "starting_room"

# ---------------- CAMERA ----------------
def get_camera():
    global shake
    cx = player_rect.centerx - WIDTH//2
    cy = player_rect.centery - HEIGHT//2
    cx = max(0, min(cx, ROOM_WIDTH-WIDTH))
    cy = max(0, min(cy, ROOM_HEIGHT-HEIGHT))
    if shake > 0:
        cx += random.randint(-shake,shake)
        cy += random.randint(-shake,shake)
        shake -= 1
    return cx, cy

# ---------------- DRAW ----------------
def draw_room():
    room = rooms[current_room]
    cam_x, cam_y = get_camera()
    screen.fill(room["color"])

    for d in room["doors"]:
        if not room_cleared():
            continue
        r = d["rect"].move(-cam_x,-cam_y)
        pygame.draw.rect(screen,YELLOW,r,border_radius=6)
        pygame.draw.rect(screen,BROWN,r,3,border_radius=6)

    for e in room["enemies"]:
        if e["hp"]<=0: continue
        r = e["rect"].move(-cam_x,-cam_y)
        color = RED if pygame.time.get_ticks()-e["hit_flash"]<100 else GREEN
        pygame.draw.rect(screen,color,r,border_radius=6)
        hp_ratio = e["hp"]/e["max_hp"]
        pygame.draw.rect(screen,(40,40,40),(r.x,r.y-6,r.width,4))
        pygame.draw.rect(screen,RED,(r.x,r.y-6,int(r.width*hp_ratio),4))

def draw_player():
    global player_frame
    cam_x, cam_y = get_camera()
    row = DIRECTION_ROW[player_dir]
    frame = int(player_frame)%len(player_sprites[row])
    img = player_sprites[row][frame]
    r = player_rect.move(-cam_x,-cam_y)
    screen.blit(img,r)

def draw_hud():
    for i in range(max_hp):
        c = RED if i<hp else (90,40,40)
        pygame.draw.circle(screen,c,(20+i*22,20),8)
    txt = f"Tokens: {tokens} | {'Metal' if has_metal_spear else 'Wood'} spear"
    screen.blit(ui.render(txt,True,WHITE),(16,50))
    if popup_msg and pygame.time.get_ticks()<popup_until:
        screen.blit(ui.render(popup_msg,True,YELLOW),(16,80))

# ---------------- LOGIC ----------------
def room_cleared():
    return all(e["hp"]<=0 for e in rooms[current_room]["enemies"])

def update_enemies():
    for e in rooms[current_room]["enemies"]:
        if e["hp"]<=0: continue
        dx = player_rect.centerx-e["rect"].centerx
        dy = player_rect.centery-e["rect"].centery
        dist = max(1,math.hypot(dx,dy))
        if dist<300:
            e["rect"].x += int(dx/dist*e["speed"])
            e["rect"].y += int(dy/dist*e["speed"])
        else:
            e["rect"].x += e["dx"]
            e["rect"].y += e["dy"]

def handle_input(keys):
    global player_dir, player_frame
    vx = vy = 0
    moving = False

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        vx = -player_speed
        player_dir = "left"
        moving = True

    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vx = player_speed
        player_dir = "right"
        moving = True

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        vy = -player_speed
        player_dir = "up"
        moving = True

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        vy = player_speed
        player_dir = "down"
        moving = True

    player_rect.x += vx
    player_rect.y += vy
    player_rect.clamp_ip(pygame.Rect(0, 0, ROOM_WIDTH, ROOM_HEIGHT))

    if moving:
        player_frame += animation_speed
    else:
        player_frame = 0

def attack_rect():
    r=player_rect
    if player_dir=="up": return pygame.Rect(r.centerx-8,r.top-attack_range,16,attack_range)
    if player_dir=="down": return pygame.Rect(r.centerx-8,r.bottom,16,attack_range)
    if player_dir=="left": return pygame.Rect(r.left-attack_range,r.centery-8,attack_range,16)
    return pygame.Rect(r.right,r.centery-8,attack_range,16)

def try_attack():
    global last_attack,tokens,has_metal_spear,popup_msg,popup_until
    now=pygame.time.get_ticks()
    if now-last_attack<attack_cd: return
    last_attack=now
    hb=attack_rect()
    for e in rooms[current_room]["enemies"]:
        if e["hp"]>0 and hb.colliderect(e["rect"]):
            e["hp"]-=metal_damage if has_metal_spear else wood_damage
            e["hit_flash"]=now
            if e["hp"]<=0:
                tokens+=1
                popup_msg="+1 token"
                popup_until=now+1200
                if tokens>=10 and not has_metal_spear:
                    has_metal_spear=True
                    popup_msg="Metal spear unlocked!"
                    popup_until=now+2000

def handle_damage():
    global hp,last_hit,shake
    now=pygame.time.get_ticks()
    if now-last_hit>invul_ms:
        hp-=1
        last_hit=now
        shake=8

def process_collisions(keys):
    for e in rooms[current_room]["enemies"]:
        if e["hp"]>0 and player_rect.colliderect(e["rect"]):
            handle_damage()
    if room_cleared():
        for d in rooms[current_room]["doors"]:
            if player_rect.colliderect(d["rect"]) and keys[pygame.K_e]:
                switch_room(d["target"],d["spawn"])

def switch_room(target,spawn):
    global current_room
    current_room=target
    player_rect.center=spawn

# ---------------- MAIN LOOP ----------------
running=True
while running:
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            running=False

    keys=pygame.key.get_pressed()
    handle_input(keys)
    if keys[pygame.K_SPACE]: try_attack()

    update_enemies()
    draw_room()
    draw_player()
    draw_hud()
    process_collisions(keys)

    if hp<=0:
        screen.fill(DARK)
        screen.blit(title.render("Game Over",True,RED),(WIDTH//2-120,HEIGHT//2-40))
        pygame.display.flip()
        pygame.time.wait(2000)
        pygame.quit(); sys.exit()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
