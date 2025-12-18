import pygame
import sys
import random

pygame.init()

# Constants
WIDTH, HEIGHT = 900, 600
WALL_THICKNESS = 30
ROOM_WIDTH, ROOM_HEIGHT = 2500, 2000
FRAME_SIZE = 64
SPRITE_ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}
ENEMY_ROWS = {"up": 8, "left": 9, "down": 10, "right": 11}
COLORS = {
    'white': (255, 255, 255),
    'red': (230, 50, 50),
    'green': (80, 220, 120),
    'yellow': (230, 200, 60),
    'brown': (120, 80, 40),
    'dark': (20, 10, 22),
    'wall': (70, 70, 70)
}

# Initialize display and fonts
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania")
clock = pygame.time.Clock()
ui_font = pygame.font.SysFont(None, 32)
title_font = pygame.font.SysFont(None, 56)

# Load images
def load_image(path, scale=None):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, scale) if scale else img

start_bg = load_image("img/Startscherm.jpg", (WIDTH, HEIGHT))
floor_bg = load_image("img/stone.jpg", (WIDTH, HEIGHT))

# Load spritesheets
def load_spritesheet(path, frame_w, frame_h, row_map):
    sheet = load_image(path)
    sprites = {}
    for direction, row in row_map.items():
        sprites[direction] = []
        for col in range(9):
            rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
            sprites[direction].append(sheet.subsurface(rect))
    return sprites

player_sprites = load_spritesheet("img/player.png", FRAME_SIZE, FRAME_SIZE, SPRITE_ROWS)
enemy_sprites = load_spritesheet("img/skeleton.png", FRAME_SIZE, FRAME_SIZE, ENEMY_ROWS)

# Game state
game_state = {
    'debug': True,
    'current_room': 'starting_room',
    'player_name': ''
}

player = {
    'rect': pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56),
    'speed': 7,
    'dir': 'down',
    'frame': 0.0,
    'hp': 10,
    'max_hp': 10,
    'last_hit': -9999,
    'invul_ms': 500
}

combat = {
    'tokens': 0,
    'has_metal_spear': False,
    'wood_damage': 1,
    'metal_damage': 3,
    'range': 100,
    'cooldown': 300,
    'last_attack': -9999,
    'popup_msg': None,
    'popup_until': 0
}

# Helper functions
def make_enemy(x, y, hp=3, speed=2):
    return {
        'rect': pygame.Rect(x, y, 32, 48),
        'hp': hp,
        'max_hp': hp,
        'speed': speed,
        'dir': 'down',
        'frame': 0.0
    }

def spawn_enemies(count, speed):
    return [
        make_enemy(
            random.randint(WALL_THICKNESS + 100, ROOM_WIDTH - WALL_THICKNESS - 100),
            random.randint(WALL_THICKNESS + 100, ROOM_HEIGHT - WALL_THICKNESS - 100),
            hp=3, speed=speed
        )
        for _ in range(count)
    ]

def make_door(x, y, w, h, target, spawn_x, spawn_y):
    return {
        'rect': pygame.Rect(x, y, w, h),
        'target': target,
        'spawn': (spawn_x, spawn_y)
    }

# Room definitions
rooms = {
    'starting_room': {
        'color': (55, 188, 31),
        'doors': [make_door(1000, 50, 80, 90, 'lobby', 1000, 750)],
        'enemies': []
    },
    'lobby': {
        'color': (41, 90, 96),
        'doors': [
            make_door(100, 50, 70, 100, 'starting_room', 200, 200),
            make_door(300, 50, 70, 100, 'hallway right', 200, 200),
            make_door(500, 50, 70, 100, 'hallway left', 200, 200)
        ],
        'enemies': spawn_enemies(random.randint(10, 50), 5)
    },
    'hallway right': {
        'color': (41, 90, 96),
        'doors': [make_door(WIDTH//2-40, 50, 70, 100, 'lobby', 200, 200)],
        'enemies': spawn_enemies(random.randint(4, 6), 4)
    },
    'hallway left': {
        'color': (41, 90, 96),
        'doors': [make_door(WIDTH//2-40, 50, 70, 100, 'lobby', 200, 200)],
        'enemies': spawn_enemies(random.randint(4, 6), 4)
    },
    'crypt': {
        'color': (30, 30, 30),
        'doors': [make_door(WIDTH-110, HEIGHT//2-55, 80, 110, 'chapel', 200, 200)],
        'enemies': spawn_enemies(random.randint(4, 6), 4)
    },
    'chapel': {
        'color': (200, 200, 160),
        'doors': [
            make_door(30, HEIGHT//2-55, 80, 110, 'crypt', WIDTH-140, HEIGHT//2),
            make_door(WIDTH//2-40, 20, 80, 90, 'boss_room', WIDTH//2, HEIGHT-140)
        ],
        'enemies': spawn_enemies(random.randint(3, 5), 4)
    },
    'boss_room': {
        'color': (120, 0, 0),
        'doors': [],
        'enemies': spawn_enemies(1, 1)
    }
}

# Camera system
def get_camera():
    cam_x = max(0, min(player['rect'].centerx - WIDTH // 2, ROOM_WIDTH - WIDTH))
    cam_y = max(0, min(player['rect'].centery - HEIGHT // 2, ROOM_HEIGHT - HEIGHT))
    return cam_x, cam_y

def get_walls():
    return [
        pygame.Rect(0, 0, ROOM_WIDTH, WALL_THICKNESS),
        pygame.Rect(0, ROOM_HEIGHT - WALL_THICKNESS, ROOM_WIDTH, WALL_THICKNESS),
        pygame.Rect(0, 0, WALL_THICKNESS, ROOM_HEIGHT),
        pygame.Rect(ROOM_WIDTH - WALL_THICKNESS, 0, WALL_THICKNESS, ROOM_HEIGHT)
    ]

# Movement and collision
def move_entity(rect, vx, vy):
    rect.x += vx
    for wall in get_walls():
        if rect.colliderect(wall):
            rect.right = wall.left if vx > 0 else rect.left
            rect.left = wall.right if vx < 0 else rect.left
    
    rect.y += vy
    for wall in get_walls():
        if rect.colliderect(wall):
            rect.bottom = wall.top if vy > 0 else rect.bottom
            rect.top = wall.bottom if vy < 0 else rect.top

def update_direction(dx, dy):
    if abs(dx) > abs(dy):
        return 'right' if dx > 0 else 'left'
    return 'down' if dy > 0 else 'up'

def handle_input(keys):
    vx = vy = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        vx, player['dir'] = -player['speed'], 'left'
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        vx, player['dir'] = player['speed'], 'right'
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        vy, player['dir'] = -player['speed'], 'up'
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        vy, player['dir'] = player['speed'], 'down'
    
    move_entity(player['rect'], vx, vy)
    player['frame'] = (player['frame'] + 0.2) if (vx or vy) else int(player['frame'])

def update_enemies():
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] <= 0:
            continue
        
        dx = player['rect'].centerx - e['rect'].centerx
        dy = player['rect'].centery - e['rect'].centery
        dist = max(1, (dx*dx + dy*dy) ** 0.5)
        
        move_entity(e['rect'], int(e['speed'] * dx / dist), int(e['speed'] * dy / dist))
        e['dir'] = update_direction(dx, dy)
        e['frame'] = (e['frame'] + 0.2) % 9

# Combat system
def get_attack_rect():
    r = player['rect']
    rng = combat['range']
    if player['dir'] == 'up':
        return pygame.Rect(r.centerx-8, r.top-rng, 16, rng)
    if player['dir'] == 'down':
        return pygame.Rect(r.centerx-8, r.bottom, 16, rng)
    if player['dir'] == 'left':
        return pygame.Rect(r.left-rng, r.centery-8, rng, 16)
    return pygame.Rect(r.right, r.centery-8, rng, 16)

def try_attack():
    now = pygame.time.get_ticks()
    if now - combat['last_attack'] < combat['cooldown']:
        return
    
    combat['last_attack'] = now
    dmg = combat['metal_damage'] if combat['has_metal_spear'] else combat['wood_damage']
    atk_rect = get_attack_rect()
    
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] > 0 and atk_rect.colliderect(e['rect']):
            e['hp'] -= dmg
            if e['hp'] <= 0:
                combat['tokens'] += 1
                combat['popup_msg'] = '+1 token (monster defeated)'
                combat['popup_until'] = now + 1500
                if not combat['has_metal_spear'] and combat['tokens'] >= 10:
                    combat['has_metal_spear'] = True
                    combat['popup_msg'] = 'Metal spear unlocked!'
                    combat['popup_until'] = now + 2000
    
    # Flash attack
    cam_x, cam_y = get_camera()
    draw_rect = atk_rect.copy()
    draw_rect.x -= cam_x
    draw_rect.y -= cam_y
    pygame.draw.rect(screen, (255, 220, 120), draw_rect)

def handle_collisions(keys):
    now = pygame.time.get_ticks()
    
    # Enemy collisions
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] > 0 and player['rect'].colliderect(e['rect']):
            if now - player['last_hit'] >= player['invul_ms']:
                player['last_hit'] = now
                player['hp'] -= 1
    
    # Door collisions
    for door in rooms[game_state['current_room']]['doors']:
        if player['rect'].colliderect(door['rect']):
            hint = ui_font.render(f"E: enter {door['target']}", True, COLORS['white'])
            screen.blit(hint, (16, HEIGHT-36))
            if keys[pygame.K_e]:
                game_state['current_room'] = door['target']
                player['rect'].center = door['spawn']

# Drawing functions
def draw_sprite(sprites, rect, direction, frame, cam_x, cam_y):
    frame_idx = int(frame) % len(sprites[direction])
    img = sprites[direction][frame_idx]
    draw_rect = rect.copy()
    draw_rect.x -= cam_x + (img.get_width() - rect.width) // 2
    draw_rect.y -= cam_y + (img.get_height() - rect.height) // 2
    screen.blit(img, draw_rect)

def draw_room():
    room = rooms[game_state['current_room']]
    cam_x, cam_y = get_camera()
    
    screen.fill(room['color'])
    screen.blit(floor_bg, (-cam_x, -cam_y))
    
    # Walls
    for wall in get_walls():
        r = wall.copy()
        r.x -= cam_x
        r.y -= cam_y
        pygame.draw.rect(screen, COLORS['wall'], r)
    
    # Doors
    for door in room['doors']:
        r = door['rect'].copy()
        r.x -= cam_x
        r.y -= cam_y
        pygame.draw.rect(screen, COLORS['yellow'], r, border_radius=6)
        pygame.draw.rect(screen, COLORS['brown'], r, 3, border_radius=6)
        tag = ui_font.render(door['target'], True, COLORS['white'])
        screen.blit(tag, (r.centerx - tag.get_width()//2, r.top - 24))

def draw_entities():
    cam_x, cam_y = get_camera()
    
    # Enemies
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] > 0:
            draw_sprite(enemy_sprites, e['rect'], e['dir'], e['frame'], cam_x, cam_y)
            # Health bar
            ratio = e['hp'] / e['max_hp']
            x, y = e['rect'].x - cam_x, e['rect'].y - cam_y - 10
            pygame.draw.rect(screen, COLORS['red'], (x, y, e['rect'].width, 6))
            pygame.draw.rect(screen, COLORS['green'], (x, y, e['rect'].width * ratio, 6))
    
    # Player
    draw_sprite(player_sprites, player['rect'], player['dir'], player['frame'], cam_x, cam_y)

def draw_hud():
    # Hearts
    for i in range(player['max_hp']):
        col = (220, 60, 60) if i < player['hp'] else (90, 40, 40)
        x = 16 + i * 22
        pygame.draw.circle(screen, col, (x, 18), 8)
        pygame.draw.circle(screen, col, (x+10, 18), 8)
        pygame.draw.polygon(screen, col, [(x-5, 22), (x+15, 22), (x+5, 34)])
    
    # Info
    weapon = 'Metal spear' if combat['has_metal_spear'] else 'Wooden spear'
    info = f"Tokens: {combat['tokens']} | Weapon: {weapon}"
    screen.blit(ui_font.render(info, True, COLORS['white']), (16, 50))
    
    # Popup
    if combat['popup_msg'] and pygame.time.get_ticks() < combat['popup_until']:
        screen.blit(ui_font.render(combat['popup_msg'], True, COLORS['yellow']), (16, 80))
    
    # Debug
    if game_state['debug']:
        cam_x, cam_y = get_camera()
        lines = [
            f"Room: {game_state['current_room']}",
            f"Player pos: {player['rect'].x}, {player['rect'].y}",
            f"Camera: {cam_x}, {cam_y}"
        ]
        for i, line in enumerate(lines):
            text = ui_font.render(line, True, COLORS['yellow'])
            screen.blit(text, (10, HEIGHT - 70 + i * 20))

# Start screen
def show_start_screen():
    # Title screen
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                break
        else:
            screen.blit(start_bg, (0, 0))
            screen.blit(title_font.render('Frankenstein mansion', True, COLORS['white']), (250, 80))
            screen.blit(ui_font.render('Druk ENTER om te starten', True, COLORS['yellow']), (320, 520))
            pygame.display.flip()
            clock.tick(60)
            continue
        break
    
    # Name input
    name = ''
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    game_state['player_name'] = name.strip() or 'speler'
                    return
                elif ev.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif ev.unicode.isprintable():
                    name += ev.unicode
        
        screen.blit(start_bg, (0, 0))
        prompt = ui_font.render(f'Voer je naam in: {name}', True, COLORS['white'])
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 200))
        pygame.display.flip()
        clock.tick(60)

def reset_game():
    player.update({
        'rect': pygame.Rect(WIDTH//2-20, HEIGHT//2-28, 40, 56),
        'hp': 10,
        'frame': 0.0,
        'last_hit': -9999
    })
    combat.update({
        'tokens': 0,
        'has_metal_spear': False,
        'popup_msg': None,
        'last_attack': -9999
    })
    game_state['current_room'] = 'starting_room'
    
    for name in rooms:
        if name == 'starting_room':
            rooms[name]['enemies'] = []
        else:
            rooms[name]['enemies'] = spawn_enemies(random.randint(1, 3), 2)

def game_over_screen():
    screen.fill(COLORS['dark'])
    over1 = title_font.render('game over', True, (255, 200, 200))
    over2 = ui_font.render('Enter: opnieuw beginnen | Esc: afsluiten', True, COLORS['white'])
    screen.blit(over1, over1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
    screen.blit(over2, over2.get_rect(center=(WIDTH//2, HEIGHT//2 + 24)))
    pygame.display.flip()
    
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            reset_game()
            return True
        elif keys[pygame.K_ESCAPE]:
            return False

# Main game
def main():
    show_start_screen()
    
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_F3:
                game_state['debug'] = not game_state['debug']
        
        keys = pygame.key.get_pressed()
        handle_input(keys)
        if keys[pygame.K_SPACE]:
            try_attack()
        
        update_enemies()
        draw_room()
        draw_entities()
        draw_hud()
        handle_collisions(keys)
        pygame.display.flip()
        
        if player['hp'] <= 0:
            if not game_over_screen():
                running = False
        
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()