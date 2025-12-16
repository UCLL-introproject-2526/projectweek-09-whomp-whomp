import pygame, sys, random
pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()

ui = pygame.font.SysFont(None, 32)
title = pygame.font.SysFont(None, 56)

WHITE = (255,255,255)
RED = (230,50,50)
GREEN = (80,220,120)
YELLOW = (230,200,60)
BROWN = (120,80,40)
DARK = (20,10,22)

# Player
player = pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56)
player_speed = 5
player_dir = "down"
max_hp = 5
hp = max_hp
invul_ms = 500
last_hit = -9999

# Combat / progression
tokens = 0
has_metal_spear = False
wood_damage = 1
metal_damage = 3
diamond_damage = 10
attack_range = 50
attack_cd_ms = 300
last_attack = -9999
popup_msg = None
popup_until = 0

# Enemy helper
def make_enemy(x, y, hp=3, speed=2):
    return {
        "rect": pygame.Rect(x, y, 42, 42),
        "hp": hp,
        "max_hp": hp,
        "dx": random.choice([-speed, speed]),
        "dy": random.choice([-speed, speed])
    }

# Rooms
rooms = {
    "lobby": {
        "color": (32, 12, 36),
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110),
             "target": "kitchen", "spawn": (120, HEIGHT//2)}
        ],
        "enemy": make_enemy(220, 180, hp=3, speed=2)
    },
    "kitchen": {
        "color": (60, 25, 5),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110),
             "target": "lobby", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH-110, 60, 80, 110),
             "target": "library", "spawn": (WIDTH//2, HEIGHT-140)}
        ],
        "enemy": make_enemy(520, 340, hp=4, speed=2)
    },
    "library": {
        "color": (5, 40, 62),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80),
             "target": "kitchen", "spawn": (WIDTH-140, HEIGHT//2)}
        ],
        "enemy": make_enemy(380, 160, hp=5, speed=2)
    }
}
current_room = "lobby"

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

def draw_room(name):
    room = rooms[name]
    screen.fill(room["color"])
    # doors
    for d in room["doors"]:
        pygame.draw.rect(screen, YELLOW, d["rect"], border_radius=6)
        pygame.draw.rect(screen, BROWN, d["rect"], 3, border_radius=6)
        tag = ui.render(d["target"], True, WHITE)
        screen.blit(tag, (d["rect"].centerx - tag.get_width()//2, d["rect"].top - 24))
    # enemy
    e = room["enemy"]
    if e and e["hp"] > 0:
        pygame.draw.rect(screen, GREEN, e["rect"], border_radius=6)
        # health bar boven monster
        bar_w = e["rect"].width
        hp_ratio = e["hp"] / e["max_hp"]
        hp_w = int(bar_w * hp_ratio)
        bar_x = e["rect"].x
        bar_y = e["rect"].y - 10
        pygame.draw.rect(screen, (60,60,60), (bar_x, bar_y, bar_w, 6))
        pygame.draw.rect(screen, (220,60,60), (bar_x, bar_y, hp_w, 6))

def draw_player():
    pygame.draw.rect(screen, RED, player, border_radius=10)

def attack_rect():
    r = player
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
    e = rooms[current_room]["enemy"]
    if e and e["hp"] > 0 and hb.colliderect(e["rect"]):
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
        pygame.draw.rect(screen, (255,220,120), hb)
        pygame.display.flip()

def update_enemy():
    e = rooms[current_room]["enemy"]
    if e and e["hp"] > 0:
        e["rect"].x += e["dx"]; e["rect"].y += e["dy"]
        if e["rect"].left < 0 or e["rect"].right > WIDTH: e["dx"] *= -1
        if e["rect"].top < 0 or e["rect"].bottom > HEIGHT: e["dy"] *= -1

def handle_damage(amount=1):
    global hp, last_hit
    now = pygame.time.get_ticks()
    if now - last_hit >= invul_ms:
        last_hit = now
        hp -= amount

def process_collisions(keys):
    e = rooms[current_room]["enemy"]
    if e and e["hp"] > 0 and player.colliderect(e["rect"]):
        handle_damage(1)
    for d in rooms[current_room]["doors"]:
        if player.colliderect(d["rect"]):
            hint = ui.render("E: enter " + d["target"], True, WHITE)
            screen.blit(hint, (16, HEIGHT-36))
            if keys[pygame.K_e]:
                switch_room(d["target"], d["spawn"])

def switch_room(target, spawn):
    global current_room
    current_room = target
    player.center = spawn

def handle_input(keys):
    global player_dir
    vx = vy = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        vx = -player_speed; player_dir = "left"
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vx = player_speed; player_dir = "right"
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        vy = -player_speed; player_dir = "up"
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        vy = player_speed; player_dir = "down"
    player.x += vx; player.y += vy
    player.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))

# Main loop
running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:  # 1 = linkermuisknop
                try_attack()

    keys = pygame.key.get_pressed()
    handle_input(keys)

    update_enemy()
    draw_room(current_room)
    draw_player()
    draw_hud()
    process_collisions(keys)


    if hp <= 0:
        # Game over scherm
        screen.fill(DARK)
        over1 = title.render("Hahahahhaha Tang is verloren", True, (255,200,200))
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
                player.update(WIDTH//2-20, HEIGHT//2-28, 40, 56)
                hp = max_hp
                tokens = 0
                has_metal_spear = False
                # respawn enemies
                for name in rooms:
                    rooms[name]["enemy"] = make_enemy(
                        random.randint(120, WIDTH-160),
                        random.randint(120, HEIGHT-160),
                        hp=random.randint(2,4),
                        speed=2
                    )
                current_room = "lobby"
                waiting = False
            elif k[pygame.K_ESCAPE]:
                waiting = False
                running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()