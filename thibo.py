import haunted_house

import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()

ui_font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

# speler
player_size = (50, 70)
player = pygame.Rect(WIDTH//2, HEIGHT//2, *player_size)
player_speed = 5
player_color = (255, 0, 0)
max_health = 3
health = max_health
hit_cooldown_ms = 600
last_hit_time = -9999

# helper voor vijanden (monsters)
def make_enemy(x, y, w, h, speed):
    # willekeurige richting: dx, dy
    dx = random.choice([-1, 1]) * speed
    dy = random.choice([-1, 1]) * speed
    return {"rect": pygame.Rect(x, y, w, h), "dx": dx, "dy": dy}

rooms = {
    "lobby": {
        "name": "Lobby",
        "color": (32, 12, 36),
        "doors": [
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "kitchen", "spawn": (120, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "library", "spawn": (WIDTH//2, HEIGHT-140)}
        ],
        "enemies": [make_enemy(200, 200, 40, 40, 3)],
        "hazards": []
    },
    "kitchen": {
        "name": "Keuken",
        "color": (60, 25, 5),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "lobby", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH-110, 50, 80, 110), "target": "cellar", "spawn": (120, HEIGHT-160)}
        ],
        "enemies": [make_enemy(400, 300, 40, 40, 2)],
        "hazards": []
    },
    "library": {
        "name": "Bibliotheek",
        "color": (5, 40, 62),
        "doors": [
            {"rect": pygame.Rect(WIDTH//2-40, HEIGHT-100, 80, 80), "target": "lobby", "spawn": (WIDTH//2, 140)},
            {"rect": pygame.Rect(WIDTH-110, HEIGHT//2-55, 80, 110), "target": "cellar", "spawn": (120, HEIGHT//2)}
        ],
        "enemies": [make_enemy(100, 100, 40, 40, 4)],
        "hazards": []
    },
    "cellar": {
        "name": "Kelder",
        "color": (12, 4, 14),
        "doors": [
            {"rect": pygame.Rect(30, HEIGHT//2-55, 80, 110), "target": "kitchen", "spawn": (WIDTH-140, HEIGHT//2)},
            {"rect": pygame.Rect(WIDTH//2-40, 20, 80, 90), "target": "library", "spawn": (WIDTH//2, HEIGHT-140)}
        ],
        "enemies": [make_enemy(500, 400, 40, 40, 3)],
        "hazards": []
    }
}

current_room = "lobby"

def draw_door(rect, label):
    pygame.draw.rect(screen, (220, 190, 60), rect, border_radius=6)
    pygame.draw.rect(screen, (140, 110, 30), rect, 3, border_radius=6)
    tag = small_font.render(label, True, (255, 255, 255))
    screen.blit(tag, (rect.centerx-20, rect.top-20))

def draw_health():
    for i in range(max_health):
        heart_color = (220, 60, 60) if i < health else (90, 40, 40)
        x = 20 + i * 32
        y = 20
        pygame.draw.circle(screen, heart_color, (x, y), 10)
        pygame.draw.circle(screen, heart_color, (x+12, y), 10)
        pygame.draw.polygon(screen, heart_color, [(x-6, y+6), (x+18, y+6), (x+6, y+22)])

def update_enemies(room):
    for e in room["enemies"]:
        e["rect"].x += e["dx"]
        e["rect"].y += e["dy"]
        # bots tegen muren → verander richting
        if e["rect"].left < 0 or e["rect"].right > WIDTH:
            e["dx"] *= -1
        if e["rect"].top < 0 or e["rect"].bottom > HEIGHT:
            e["dy"] *= -1

def handle_damage():
    global health, last_hit_time
    now = pygame.time.get_ticks()
    if now - last_hit_time >= hit_cooldown_ms:
        health -= 1
        last_hit_time = now

def draw_room(room_key):
    room = rooms[room_key]
    screen.fill(room["color"])
    label = ui_font.render(room["name"], True, (255, 255, 255))
    screen.blit(label, (20, 20))
    for d in room["doors"]:
        draw_door(d["rect"], d["target"])

def process_collisions(room_key, keys):
    room = rooms[room_key]
    # invisible enemies → check collision maar niet tekenen
    for e in room["enemies"]:
        if player.colliderect(e["rect"]):
            handle_damage()
            break
    target = None
    spawn = None
    for d in room["doors"]:
        if player.colliderect(d["rect"]):
            hint = f"Druk op E om naar {d['target']} te gaan"
            hint_surf = ui_font.render(hint, True, (255, 255, 255))
            screen.blit(hint_surf, (20, HEIGHT - 50))
            if keys[pygame.K_e]:
                target = d["target"]
                spawn = d["spawn"]
    return target, spawn

def draw_player():
    pygame.draw.rect(screen, player_color, player, border_radius=10)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  player.x -= player_speed
    if keys[pygame.K_RIGHT]: player.x += player_speed
    if keys[pygame.K_UP]:    player.y -= player_speed
    if keys[pygame.K_DOWN]:  player.y += player_speed

    player.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    update_enemies(rooms[current_room])

    draw_room(current_room)
    draw_player()
    draw_health()

    target, spawn = process_collisions(current_room, keys)
    if target:
        current_room = target
        player.center = spawn

    if health <= 0:
        screen.fill((10, 5, 12))
        msg1 = ui_font.render("Jammer genoeg heb je verloren!", True, (255, 200, 200))
        msg2 = small_font.render("Druk op R om te herstarten of Esc om af te sluiten", True, (220, 220, 220))
        screen.blit(msg1, msg1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
        screen.blit(msg2, msg2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
        pygame.display.flip()
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    waiting = False
                    running = False
            k = pygame.key.get_pressed()
            if k[pygame.K_r]:
                health = max_health
                current_room = "lobby"
                player.update(WIDTH//2, HEIGHT//2, *player_size)
                waiting = False
            elif k[pygame.K_ESCAPE]:
                waiting = False
                running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()