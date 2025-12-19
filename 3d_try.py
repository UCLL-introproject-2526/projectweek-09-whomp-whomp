import pygame, math, random, json, os

# ================= SAFE PERFORMANCE CONFIG =================
WIDTH, HEIGHT = 1280, 720
FPS = 1084                    # STABLE FPS
TILE = 64
MAP_SIZE = 28

FOV = math.pi / 3
NUM_RAYS = 480              # OPTIMIZED (not WIDTH!)
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 900
SCALE = WIDTH // NUM_RAYS

SAVE_FILE = "save.json"

# ================= COLORS =================
WHITE=(255,255,255)
GRAY=(120,120,120)
RED=(220,50,50)
BLUE=(50,100,220)
GOLD=(255,215,0)
DARK=(20,10,22)

# ================= INIT =================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Dungeon (Stable)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

# ================= MAP =================
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

# ================= HELPERS =================
def mapping(x,y): return int(x//TILE), int(y//TILE)

def normalize(a):
    while a>math.pi: a-=2*math.pi
    while a<-math.pi: a+=2*math.pi
    return a

# ================= GAME INIT =================
def new_game():
    global room_map, rooms, px, py, angle
    global enemies, bullets, spells, inventory
    global hp, score, treasure_x, treasure_y

    room_map, rooms = make_dungeon()
    px=(rooms[0][0]+0.5)*TILE
    py=(rooms[0][1]+0.5)*TILE
    angle=0

    hp=5
    score=0

    inventory={"potions":2, "bow":True}

    enemies=[]
    for r in rooms[1:-1]:
        enemies.append({
            "x":(r[0]+0.5)*TILE,
            "y":(r[1]+0.5)*TILE,
            "hp":3,
            "speed":80,
            "cooldown":0,
            "alive":True
        })

    bullets=[]
    spells=[]

    tr=rooms[-1]
    treasure_x=(tr[0]+0.5)*TILE
    treasure_y=(tr[1]+0.5)*TILE

# ================= SAVE / LOAD =================
def load_game():
    global inventory
    inventory={"potions":2,"bow":True}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE) as f:
            inventory.update(json.load(f))

def save_game():
    with open(SAVE_FILE,"w") as f:
        json.dump(inventory,f)

# ================= RAYCAST =================
def cast_rays():
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

# ================= SPRITES =================
def draw_sprite(x,y,color,scale=1):
    dx,dy=x-px,y-py
    dist=math.hypot(dx,dy)
    a=normalize(math.atan2(dy,dx)-angle)
    if abs(a)<FOV/2:
        dist*=math.cos(a)
        size=min(HEIGHT, 18000/(dist+0.1))*scale
        sx=WIDTH//2+(a/FOV)*WIDTH-size//4
        sy=HEIGHT//2-size//2
        pygame.draw.rect(screen,color,(sx,sy,size//2,size))

# ================= COMBAT =================
def melee():
    global score
    for e in enemies:
        if not e["alive"]: continue
        dx,dy=e["x"]-px,e["y"]-py
        if math.hypot(dx,dy)<120:
            e["hp"]-=1
            if e["hp"]<=0:
                e["alive"]=False
                score+=100

def shoot():
    if inventory.get("bow", False):
        bullets.append({"x":px,"y":py,"a":angle})

# ================= MAIN LOOP =================
new_game()
load_game()
running=True

while running:
    dt=clock.tick(FPS)/1000

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_SPACE: melee()
            if e.key==pygame.K_f: shoot()
            if e.key==pygame.K_i and inventory["potions"]>0:
                hp=min(5,hp+2); inventory["potions"]-=1
            if e.key==pygame.K_r: new_game()

    keys=pygame.key.get_pressed()
    sp=220*dt; rot=2.8*dt
    if keys[pygame.K_LEFT]: angle-=rot
    if keys[pygame.K_RIGHT]: angle+=rot
    if keys[pygame.K_UP]:
        nx=px+math.cos(angle)*sp
        ny=py+math.sin(angle)*sp
        mx,my=mapping(nx,ny)
        if room_map[my][mx]==0:
            px,py=nx,ny

    # bullets
    for b in bullets[:]:
        b["x"]+=math.cos(b["a"])*500*dt
        b["y"]+=math.sin(b["a"])*500*dt
        mx,my=mapping(b["x"],b["y"])
        if not (0<=mx<MAP_SIZE and 0<=my<MAP_SIZE) or room_map[my][mx]:
            bullets.remove(b)

    # enemies
    for en in enemies:
        if not en["alive"]: continue
        dx,dy=px-en["x"],py-en["y"]
        d=math.hypot(dx,dy)
        if d>40:
            en["x"]+=dx/d*en["speed"]*dt
            en["y"]+=dy/d*en["speed"]*dt

    # ===== RENDER =====
    screen.fill(DARK)
    cast_rays()

    sprites=[]
    for e in enemies:
        if e["alive"]:
            sprites.append((math.hypot(e["x"]-px,e["y"]-py),
                            lambda e=e: draw_sprite(e["x"],e["y"],RED)))
    sprites.append((math.hypot(treasure_x-px,treasure_y-py),
                    lambda: draw_sprite(treasure_x,treasure_y,GOLD,1.2)))

    for _,draw in sorted(sprites, reverse=True):
        draw()

    screen.blit(font.render(f"HP:{hp}  Score:{score}",True,WHITE),(10,10))
    screen.blit(font.render("SPACE Melee | F Bow | I Potion | R Restart",True,WHITE),(10,HEIGHT-30))

    pygame.display.flip()

save_game()
pygame.quit()
