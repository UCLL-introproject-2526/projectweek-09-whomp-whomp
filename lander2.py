import pygame, math, random, json, os, time, sys

# ================= CONFIG =================
WIDTH, HEIGHT = 1280, 720
FPS = 60
TILE = 64
MAP_SIZE = 28
FOV = math.pi / 3
NUM_RAYS = 320
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 900
SCALE = WIDTH // NUM_RAYS
SAVE_FILE = "save.json"
SCOREBOARD_FILE = "scoreboard.json"
MOUSE_SENS = 0.002

WHITE=(255,255,255)
GRAY=(120,120,120)
RED=(220,50,50)
BLUE=(50,100,220)
GOLD=(255,215,0)
DARK=(20,10,22)
FLOOR_COLOR = (80, 80, 80)
ORANGE=(255,140,0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Dungeon (Raycasting)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)
bigfont = pygame.font.SysFont("Arial", 48, bold=True)

def make_dungeon():
    dungeon = [[1]*MAP_SIZE for _ in range(MAP_SIZE)]
    rooms = []
    def carve(x,y,w,h):
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                dungeon[yy][xx] = 0
    def corridor(a,b):
        x1,y1=a; x2,y2=b
        for x in range(min(x1,x2),max(x1,x2)+1):
            dungeon[y1][x]=0
        for y in range(min(y1,y2),max(y1,y2)+1):
            dungeon[y][x2]=0
    for _ in range(8):
        w,h=random.randint(4,7),random.randint(4,7)
        x=random.randint(1,MAP_SIZE-w-2)
        y=random.randint(1,MAP_SIZE-h-2)
        carve(x,y,w,h)
        c=(x+w//2,y+h//2)
        if rooms: corridor(rooms[-1],c)
        rooms.append(c)
    return dungeon, rooms

def mapping(x,y): return int(x//TILE), int(y//TILE)
def normalize(a):
    while a>math.pi: a-=2*math.pi
    while a<-math.pi: a+=2*math.pi
    return a

def new_game():
    global room_map, rooms, px, py, angle
    global enemies, bullets, spells, inventory
    global hp, score, treasure_x, treasure_y, last_hit_time
    global game_over, victory, boss, shop_open, tokens, safety_until

    room_map, rooms = make_dungeon()
    px=(rooms[0][0]+0.5)*TILE
    py=(rooms[0][1]+0.5)*TILE
    angle=0

    hp=5
    score=0
    tokens=0
    last_hit_time = 0
    game_over = False
    victory = False
    shop_open = False
    safety_until = time.time() + 30  # 30 seconden veiligheid

    inventory={"potions":2, "bow":True}

    enemies=[]
    for r in rooms[1:-1]:
        for _ in range(random.randint(1, 2)):
            ex = (r[0]+random.uniform(-0.4,0.4))*TILE
            ey = (r[1]+random.uniform(-0.4,0.4))*TILE
            enemies.append({
                "x":ex,
                "y":ey,
                "spawn_x":ex,
                "spawn_y":ey,
                "hp":3,
                "max_hp":3,
                "speed":80+random.randint(-20,20),
                "cooldown":0,
                "alive":True,
                "boss":False,
                "death_time":None
            })

    boss_room = rooms[-1]
    boss = {
        "x": (boss_room[0]+0.5)*TILE,
        "y": (boss_room[1]+0.5)*TILE,
        "spawn_x": (boss_room[0]+0.5)*TILE,
        "spawn_y": (boss_room[1]+0.5)*TILE,
        "hp": 15,
        "max_hp": 15,
        "speed": 60,
        "cooldown": 0,
        "alive": True,
        "boss": True,
        "death_time": None
    }
    enemies.append(boss)

    bullets=[]
    spells=[]

    tr=rooms[-1]
    treasure_x=(tr[0]+0.5)*TILE
    treasure_y=(tr[1]+0.5)*TILE

def load_game():
    global inventory
    inventory={"potions":2,"bow":True}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE) as f:
            inventory.update(json.load(f))

def save_game():
    with open(SAVE_FILE,"w") as f:
        json.dump(inventory,f)

def enemy_can_move(x, y):
    mx, my = mapping(x, y)
    return 0 <= mx < MAP_SIZE and 0 <= my < MAP_SIZE and room_map[my][mx] == 0

def player_can_move(x, y):
    mx, my = mapping(x, y)
    return 0 <= mx < MAP_SIZE and 0 <= my < MAP_SIZE and room_map[my][mx] == 0

def melee():
    global score, tokens
    for e in enemies:
        if not e["alive"]: continue
        dx,dy=e["x"]-px,e["y"]-py
        if math.hypot(dx,dy)<120:
            e["hp"]-=1
            if e["hp"]<=0:
                e["alive"]=False
                e["death_time"]=time.time()
                if not e.get("boss",False):
                    score+=100
                    tokens+=1
                else:
                    score+=500
                    tokens+=5

def shoot():
    if inventory.get("bow", True):
        bullets.append({"x":px,"y":py,"a":angle,"alive":True})

def show_start_screen():
    screen.fill(DARK)
    title = bigfont.render("3D Dungeon", True, GOLD)
    lines = [
        "Welcome to the 3D Dungeon!",
        "",
        "Controls:",
        "  - Move: W/A/S/D or Arrow Keys (strafe: A/D or Q/E)",
        "  - Rotate: Mouse bewegen of pijltjes",
        "  - SPACE: Melee Attack",
        "  - F: Shoot Bow (you always start with a bow!)",
        "  - I: Drink Potion (heal 2 HP)",
        "  - B: Open Shop (2 tokens = 5 HP)",
        "  - R: Restart Dungeon",
        "  - ) : Quit Game",
        "",
        "Mechanics:",
        "  - Defeat all enemies (including the orange boss) to unlock the treasure.",
        "  - Walk to the yellow block to win.",
        "  - Use potions to heal. Score increases for each enemy.",
        "  - Use the bow for ranged attacks.",
        "",
        "Enter your name and press E to start!"
    ]
    scroll = 0
    max_scroll = max(0, len(lines)*32 + 80 - (HEIGHT-120))
    name = ""
    input_active = True
    while input_active:
        screen.fill(DARK)
        screen.blit(title, (WIDTH//2-title.get_width()//2, 40))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if ((event.key == pygame.K_e) or (event.unicode and event.unicode.lower() == 'e')) and name:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.key == pygame.K_DOWN:
                    scroll = min(scroll+32, max_scroll)
                elif event.key == pygame.K_UP:
                    scroll = max(scroll-32, 0)
                elif event.key == pygame.K_RIGHTPAREN:
                    pygame.quit(); sys.exit()
                elif event.key <= 127 and len(name) < 16:
                    if event.unicode.isprintable() and (event.unicode.isalnum() or event.unicode == " "):
                        name += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # scroll up
                    scroll = max(scroll-32, 0)
                if event.button == 5:  # scroll down
                    scroll = min(scroll+32, max_scroll)
        y = 120 - scroll
        for line in lines:
            surf = font.render(line, True, WHITE if line else GOLD)
            screen.blit(surf, (WIDTH//2-surf.get_width()//2, y))
            y += 32 if line else 16
        pygame.draw.rect(screen, DARK, (WIDTH//2-200, HEIGHT-70, 400, 40))
        name_surf = font.render(name, True, WHITE)
        screen.blit(name_surf, (WIDTH//2-name_surf.get_width()//2, HEIGHT-60))
        name_label = font.render("Your name:", True, GOLD)
        screen.blit(name_label, (WIDTH//2-name_label.get_width()//2, HEIGHT-90))
        if max_scroll > 0:
            bar_h = int((HEIGHT-160) * (HEIGHT-120)/(len(lines)*32+80))
            bar_y = int(120 + (HEIGHT-160-bar_h) * scroll / max_scroll)
            pygame.draw.rect(screen, GRAY, (WIDTH-30, 120, 12, HEIGHT-160), border_radius=6)
            pygame.draw.rect(screen, GOLD, (WIDTH-30, bar_y, 12, bar_h), border_radius=6)
        pygame.display.flip()
    return name

def load_scoreboard():
    if os.path.exists(SCOREBOARD_FILE):
        with open(SCOREBOARD_FILE) as f:
            return json.load(f)
    return []

def save_scoreboard(scoreboard):
    with open(SCOREBOARD_FILE, "w") as f:
        json.dump(scoreboard, f)

def update_scoreboard(name, score):
    scoreboard = load_scoreboard()
    scoreboard.append({"name": name, "score": score})
    scoreboard = sorted(scoreboard, key=lambda x: x["score"], reverse=True)[:3]
    save_scoreboard(scoreboard)
    return scoreboard

def show_end_screen(victory, name, score):
    scoreboard = update_scoreboard(name, score)
    screen.fill(DARK)
    if victory:
        title = bigfont.render("You won!", True, GOLD)
        msg = font.render(f"Congratulations {name}!", True, WHITE)
    else:
        title = bigfont.render("Too bad, you died", True, RED)
        msg = font.render(f"Better luck next time, {name}!", True, WHITE)
    screen.blit(title, (WIDTH//2-title.get_width()//2, HEIGHT//2-120))
    screen.blit(msg, (WIDTH//2-msg.get_width()//2, HEIGHT//2-60))
    score_surf = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_surf, (WIDTH//2-score_surf.get_width()//2, HEIGHT//2-20))
    sb_title = font.render("Top 3 Scores (local):", True, GOLD)
    screen.blit(sb_title, (WIDTH//2-sb_title.get_width()//2, HEIGHT//2+30))
    y = HEIGHT//2+60
    for i, entry in enumerate(scoreboard):
        highlight = (entry["name"] == name and entry["score"] == score)
        color = BLUE if highlight else WHITE
        sb_line = font.render(f"{i+1}. {entry['name']} - {entry['score']}", True, color)
        screen.blit(sb_line, (WIDTH//2-sb_line.get_width()//2, y))
        y += 30
    hint = font.render("Press E to play again, ) to quit", True, GOLD)
    screen.blit(hint, (WIDTH//2-hint.get_width()//2, y+20))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_e) or (event.unicode and event.unicode.lower() == 'e'):
                    waiting = False
                if event.key == pygame.K_RIGHTPAREN:
                    pygame.quit(); sys.exit()

def show_shop(tokens, hp):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,180))
    screen.blit(overlay, (0,0))
    shop_title = bigfont.render("SHOP", True, GOLD)
    screen.blit(shop_title, (WIDTH//2-shop_title.get_width()//2, 180))
    info = font.render("Press H to buy +5 HP for 2 tokens", True, WHITE)
    screen.blit(info, (WIDTH//2-info.get_width()//2, 260))
    tokens_surf = font.render(f"Tokens: {tokens}   HP: {hp}", True, WHITE)
    screen.blit(tokens_surf, (WIDTH//2-tokens_surf.get_width()//2, 320))
    esc = font.render("Press ESC to close shop, ) to quit", True, WHITE)
    screen.blit(esc, (WIDTH//2-esc.get_width()//2, 370))
    pygame.display.flip()

def cast_rays_and_floor():
    for y in range(HEIGHT//2, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            screen.set_at((x, y), FLOOR_COLOR)
            if x+1 < WIDTH:
                screen.set_at((x+1, y), FLOOR_COLOR)
            if y+1 < HEIGHT:
                screen.set_at((x, y+1), FLOOR_COLOR)
                if x+1 < WIDTH:
                    screen.set_at((x+1, y+1), FLOOR_COLOR)

    start = angle - FOV/2
    for r in range(NUM_RAYS):
        a = start + r * DELTA_ANGLE
        sin_a, cos_a = math.sin(a), math.cos(a)
        for d in range(1, MAX_DEPTH, 4):
            x = px + cos_a * d
            y = py + sin_a * d
            mx,my = mapping(x,y)
            if 0<=mx<MAP_SIZE and 0<=my<MAP_SIZE:
                if room_map[my][mx]:
                    dist = d * math.cos(angle-a)
                    h = min(HEIGHT, 24000/(dist+0.1))
                    shade = max(40, 255-int(dist*0.4))
                    pygame.draw.rect(
                        screen,(shade,shade,shade),
                        (r*SCALE, HEIGHT//2-h//2, SCALE+1, h)
                    )
                    break

def draw_sprite_3d(x,y,color,scale=1):
    dx,dy=x-px,y-py
    dist=math.hypot(dx,dy)
    a=normalize(math.atan2(dy,dx)-angle)
    if abs(a)<FOV/2:
        dist*=math.cos(a)
        size=min(HEIGHT, 18000/(dist+0.1))*scale
        sx=WIDTH//2+(a/FOV)*WIDTH-size//4
        sy=HEIGHT//2-size//2
        pygame.draw.rect(screen,color,(int(sx),int(sy),int(size//2),int(size)))

player_name = None
while True:
    new_game()
    load_game()
    if not player_name:
        player_name = show_start_screen()
    running=True
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    pygame.mouse.get_rel()  # reset mouse movement

    while running:
        dt=clock.tick(FPS)/1000

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN:
                if not shop_open:
                    if e.key==pygame.K_SPACE: melee()
                    if e.key==pygame.K_f: shoot()
                    if e.key==pygame.K_i and inventory["potions"]>0:
                        hp=min(5,hp+2); inventory["potions"]-=1
                    if e.key==pygame.K_r: new_game(); player_name = None; running = False
                    if e.key==pygame.K_b: shop_open = True
                    if e.key==pygame.K_RIGHTPAREN: pygame.quit(); sys.exit()
                else:
                    if e.key==pygame.K_h and tokens >= 2 and hp > 0:
                        hp += 5
                        tokens -= 2
                    if e.key==pygame.K_ESCAPE:
                        shop_open = False
                    if e.key==pygame.K_RIGHTPAREN:
                        pygame.quit(); sys.exit()

        mx, my = pygame.mouse.get_rel()
        angle += mx * MOUSE_SENS

        keys=pygame.key.get_pressed()
        sp=220*dt; rot=2.8*dt

        move_x = 0
        if keys[pygame.K_a] or keys[pygame.K_q]: move_x -= 1
        if keys[pygame.K_d] or keys[pygame.K_e]: move_x += 1

        move_y = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y += 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y -= 1

        if not shop_open:
            if move_y != 0:
                nx=px+math.cos(angle)*sp*move_y
                ny=py+math.sin(angle)*sp*move_y
                if player_can_move(nx, ny):
                    px,py=nx,ny
            if move_x != 0:
                nx=px+math.cos(angle+math.pi/2)*sp*move_x
                ny=py+math.sin(angle+math.pi/2)*sp*move_x
                if player_can_move(nx, ny):
                    px,py=nx,ny

        sprites=[]
        for b in bullets[:]:
            b["x"]+=math.cos(b["a"])*500*dt
            b["y"]+=math.sin(b["a"])*500*dt
            mx,my=mapping(b["x"],b["y"])
            if not (0<=mx<MAP_SIZE and 0<=my<MAP_SIZE) or room_map[my][mx]:
                bullets.remove(b)
                continue
            for e in enemies:
                if e["alive"] and math.hypot(e["x"]-b["x"], e["y"]-b["y"]) < 24:
                    e["hp"] -= 2
                    if e["hp"] <= 0:
                        e["alive"] = False
                        e["death_time"] = time.time()
                        if not e.get("boss",False):
                            score += 100
                            tokens += 1
                        else:
                            score += 500
                            tokens += 5
                    if b in bullets:
                        bullets.remove(b)
                    break

        for en in enemies:
            if not en["alive"]:
                if en["death_time"] and time.time() - en["death_time"] > 30:
                    en["x"], en["y"] = en["spawn_x"], en["spawn_y"]
                    en["hp"] = en["max_hp"]
                    en["alive"] = True
                    en["death_time"] = None
                continue
            if shop_open or time.time() < safety_until:
                continue
            dx,dy=px-en["x"],py-en["y"]
            d=math.hypot(dx,dy)
            attack_dist = 40
            attack_dmg = 2 if en.get("boss",False) else 1
            if d < attack_dist and time.time() - en.get("cooldown", 0) > 1.0:
                if hp > 0:
                    hp -= attack_dmg
                    if hp < 0: hp = 0
                    en["cooldown"] = time.time()
            if d>attack_dist:
                ex = en["x"] + dx/d*en["speed"]*dt
                ey = en["y"] + dy/d*en["speed"]*dt
                if enemy_can_move(ex, ey):
                    en["x"], en["y"] = ex, ey

        screen.fill(DARK)
        cast_rays_and_floor()

        for e in enemies:
            if e["alive"]:
                color = ORANGE if e.get("boss",False) else RED
                sprites.append((math.hypot(e["x"]-px,e["y"]-py),
                                lambda e=e, color=color: draw_sprite_3d(e["x"],e["y"],color)))
        sprites.append((math.hypot(treasure_x-px,treasure_y-py),
                        lambda: draw_sprite_3d(treasure_x,treasure_y,GOLD,1.2)))
        for b in bullets:
            sprites.append((math.hypot(b["x"]-px,b["y"]-py),
                            lambda b=b: draw_sprite_3d(b["x"],b["y"],WHITE,0.5)))

        for _,draw in sorted(sprites, key=lambda t: t[0], reverse=True):
            draw()

        screen.blit(font.render(f"HP:{hp}  Tokens:{tokens}  Score:{score}",True,WHITE),(10,10))
        screen.blit(font.render("SPACE Melee | F Bow | I Potion | B Shop | R Restart | ) Quit | Mouse: Look",True,WHITE),(10,HEIGHT-30))

        if time.time() < safety_until:
            left = int(safety_until - time.time())
            safe_surf = font.render(f"SAFE: {left}s", True, (0,255,0))
            screen.blit(safe_surf, (WIDTH//2-safe_surf.get_width()//2, 10))

        if shop_open:
            show_shop(tokens, hp)

        pygame.display.flip()

        all_dead = all(not e["alive"] for e in enemies)
        player_on_treasure = math.hypot(px-treasure_x, py-treasure_y) < 32
        if all_dead and player_on_treasure and hp > 0:
            victory = True
            running = False
        if hp <= 0:
            game_over = True
            running = False

    save_game()
    pygame.event.set_grab(False)
    pygame.mouse.set_visible(True)
    show_end_screen(victory, player_name, score)
    save_game()
    pygame.quit()