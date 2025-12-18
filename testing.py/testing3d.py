import pygame
import sys
import random
import math

pygame.init()

# Constants
WIDTH, HEIGHT = 900, 600
ROOM_SIZE = 2000
WALL_HEIGHT = 300
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = 120
MAX_DEPTH = 1000
DELTA_ANGLE = FOV / NUM_RAYS

COLORS = {
    'white': (255, 255, 255),
    'red': (230, 50, 50),
    'green': (80, 220, 120),
    'yellow': (230, 200, 60),
    'brown': (120, 80, 40),
    'dark': (20, 10, 22),
    'wall': (70, 70, 70),
    'floor': (40, 40, 40),
    'ceiling': (20, 20, 30),
    'enemy': (200, 50, 50),
    'door': (230, 200, 60)
}

# Initialize display and fonts
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hotel Transylvania 3D")
clock = pygame.time.Clock()
ui_font = pygame.font.SysFont(None, 32)
title_font = pygame.font.SysFont(None, 56)

# Game state
game_state = {
    'debug': False,
    'current_room': 'starting_room',
    'player_name': ''
}

player = {
    'x': ROOM_SIZE // 2,
    'y': ROOM_SIZE // 2,
    'angle': 0,
    'speed': 5,
    'rot_speed': 0.05,
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
    'range': 150,
    'cooldown': 300,
    'last_attack': -9999,
    'popup_msg': None,
    'popup_until': 0
}

# Helper functions
def make_enemy(x, y, hp=3, speed=2):
    return {
        'x': x,
        'y': y,
        'hp': hp,
        'max_hp': hp,
        'speed': speed,
        'size': 30
    }

def spawn_enemies(count, speed):
    enemies = []
    for _ in range(count):
        x = random.randint(200, ROOM_SIZE - 200)
        y = random.randint(200, ROOM_SIZE - 200)
        enemies.append(make_enemy(x, y, hp=3, speed=speed))
    return enemies

def make_door(x, y, target, spawn_x, spawn_y):
    return {
        'x': x,
        'y': y,
        'size': 80,
        'target': target,
        'spawn': (spawn_x, spawn_y)
    }

# Room definitions with 3D coordinates
rooms = {
    'starting_room': {
        'color': (55, 188, 31),
        'doors': [make_door(ROOM_SIZE // 2, 50, 'lobby', ROOM_SIZE // 2, ROOM_SIZE - 200)],
        'enemies': []
    },
    'lobby': {
        'color': (41, 90, 96),
        'doors': [
            make_door(200, 50, 'starting_room', ROOM_SIZE // 2, 200),
            make_door(ROOM_SIZE // 2, 50, 'hallway right', ROOM_SIZE // 2, ROOM_SIZE - 200),
            make_door(ROOM_SIZE - 200, 50, 'hallway left', ROOM_SIZE // 2, ROOM_SIZE - 200)
        ],
        'enemies': spawn_enemies(random.randint(5, 10), 3)
    },
    'hallway right': {
        'color': (41, 90, 96),
        'doors': [make_door(ROOM_SIZE // 2, 50, 'lobby', ROOM_SIZE // 2, ROOM_SIZE - 200)],
        'enemies': spawn_enemies(random.randint(4, 6), 3)
    },
    'hallway left': {
        'color': (41, 90, 96),
        'doors': [make_door(ROOM_SIZE // 2, 50, 'lobby', ROOM_SIZE // 2, ROOM_SIZE - 200)],
        'enemies': spawn_enemies(random.randint(4, 6), 3)
    },
    'crypt': {
        'color': (30, 30, 30),
        'doors': [make_door(ROOM_SIZE // 2, 50, 'chapel', ROOM_SIZE // 2, ROOM_SIZE - 200)],
        'enemies': spawn_enemies(random.randint(4, 6), 3)
    },
    'chapel': {
        'color': (200, 200, 160),
        'doors': [
            make_door(200, 50, 'crypt', ROOM_SIZE // 2, ROOM_SIZE - 200),
            make_door(ROOM_SIZE // 2, 50, 'boss_room', ROOM_SIZE // 2, ROOM_SIZE - 200)
        ],
        'enemies': spawn_enemies(random.randint(3, 5), 3)
    },
    'boss_room': {
        'color': (120, 0, 0),
        'doors': [],
        'enemies': spawn_enemies(1, 2)
    }
}

# 3D Raycasting functions
def cast_ray(angle):
    """Cast a single ray and return distance to wall"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    for depth in range(0, MAX_DEPTH, 5):
        x = player['x'] + depth * cos_a
        y = player['y'] + depth * sin_a
        
        # Check room boundaries
        if x < 50 or x > ROOM_SIZE - 50 or y < 50 or y > ROOM_SIZE - 50:
            return depth, 'wall'
    
    return MAX_DEPTH, 'wall'

def get_sprites_in_view():
    """Get all enemies and doors visible to player"""
    sprites = []
    room = rooms[game_state['current_room']]
    
    # Add enemies
    for e in room['enemies']:
        if e['hp'] > 0:
            dx = e['x'] - player['x']
            dy = e['y'] - player['y']
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            
            # Normalize angle difference
            angle_diff = angle - player['angle']
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            if abs(angle_diff) < HALF_FOV + 0.3 and dist < MAX_DEPTH:
                sprites.append({
                    'type': 'enemy',
                    'obj': e,
                    'dist': dist,
                    'angle': angle_diff,
                    'size': e['size']
                })
    
    # Add doors
    for door in room['doors']:
        dx = door['x'] - player['x']
        dy = door['y'] - player['y']
        dist = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)
        
        angle_diff = angle - player['angle']
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        if abs(angle_diff) < HALF_FOV + 0.3 and dist < MAX_DEPTH:
            sprites.append({
                'type': 'door',
                'obj': door,
                'dist': dist,
                'angle': angle_diff,
                'size': door['size']
            })
    
    return sorted(sprites, key=lambda s: s['dist'], reverse=True)

# Movement and collision
def check_collision(x, y):
    """Check if position collides with walls"""
    if x < 60 or x > ROOM_SIZE - 60 or y < 60 or y > ROOM_SIZE - 60:
        return True
    return False

def handle_input(keys):
    # Rotation
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player['angle'] -= player['rot_speed']
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player['angle'] += player['rot_speed']
    
    # Normalize angle
    player['angle'] %= 2 * math.pi
    
    # Movement
    dx = dy = 0
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dx = player['speed'] * math.cos(player['angle'])
        dy = player['speed'] * math.sin(player['angle'])
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dx = -player['speed'] * math.cos(player['angle'])
        dy = -player['speed'] * math.sin(player['angle'])
    
    # Strafe
    if keys[pygame.K_q]:
        dx = player['speed'] * math.cos(player['angle'] - math.pi/2)
        dy = player['speed'] * math.sin(player['angle'] - math.pi/2)
    if keys[pygame.K_e]:
        dx = player['speed'] * math.cos(player['angle'] + math.pi/2)
        dy = player['speed'] * math.sin(player['angle'] + math.pi/2)
    
    # Apply movement if no collision
    new_x = player['x'] + dx
    new_y = player['y'] + dy
    if not check_collision(new_x, player['y']):
        player['x'] = new_x
    if not check_collision(player['x'], new_y):
        player['y'] = new_y

def update_enemies():
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] <= 0:
            continue
        
        dx = player['x'] - e['x']
        dy = player['y'] - e['y']
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        
        # Move towards player
        e['x'] += e['speed'] * dx / dist
        e['y'] += e['speed'] * dy / dist
        
        # Keep in bounds
        e['x'] = max(60, min(e['x'], ROOM_SIZE - 60))
        e['y'] = max(60, min(e['y'], ROOM_SIZE - 60))

# Combat system
def try_attack():
    now = pygame.time.get_ticks()
    if now - combat['last_attack'] < combat['cooldown']:
        return
    
    combat['last_attack'] = now
    dmg = combat['metal_damage'] if combat['has_metal_spear'] else combat['wood_damage']
    
    # Attack enemies in front of player
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] <= 0:
            continue
        
        dx = e['x'] - player['x']
        dy = e['y'] - player['y']
        dist = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)
        
        angle_diff = abs(angle - player['angle'])
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
        
        if dist < combat['range'] and angle_diff < 0.3:
            e['hp'] -= dmg
            if e['hp'] <= 0:
                combat['tokens'] += 1
                combat['popup_msg'] = '+1 token'
                combat['popup_until'] = now + 1500
                if not combat['has_metal_spear'] and combat['tokens'] >= 10:
                    combat['has_metal_spear'] = True
                    combat['popup_msg'] = 'Metal spear unlocked!'
                    combat['popup_until'] = now + 2000

def handle_collisions(keys):
    now = pygame.time.get_ticks()
    
    # Enemy collisions
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] <= 0:
            continue
        dx = e['x'] - player['x']
        dy = e['y'] - player['y']
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 50:
            if now - player['last_hit'] >= player['invul_ms']:
                player['last_hit'] = now
                player['hp'] -= 1
    
    # Door collisions
    for door in rooms[game_state['current_room']]['doors']:
        dx = door['x'] - player['x']
        dy = door['y'] - player['y']
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 100 and keys[pygame.K_SPACE]:
            game_state['current_room'] = door['target']
            player['x'], player['y'] = door['spawn']

# Drawing functions
def draw_3d_view():
    # Draw ceiling
    pygame.draw.rect(screen, COLORS['ceiling'], (0, 0, WIDTH, HEIGHT // 2))
    # Draw floor
    pygame.draw.rect(screen, COLORS['floor'], (0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    
    # Cast rays for walls
    depths = []
    ray_angle = player['angle'] - HALF_FOV
    for ray in range(NUM_RAYS):
        depth, obj_type = cast_ray(ray_angle)
        depths.append(depth)
        
        # Calculate wall height
        depth = max(depth, 0.1)
        wall_height = min(WALL_HEIGHT / depth * 277, HEIGHT)
        
        # Shading based on distance
        shade = max(0, 255 - depth * 0.5)
        color = (shade * 0.3, shade * 0.3, shade * 0.3)
        
        # Draw wall slice
        x = ray * (WIDTH / NUM_RAYS)
        y = (HEIGHT - wall_height) / 2
        
        pygame.draw.rect(screen, color, (x, y, WIDTH / NUM_RAYS + 1, wall_height))
        
        ray_angle += DELTA_ANGLE
    
    # Draw sprites (enemies and doors)
    sprites = get_sprites_in_view()
    for sprite in sprites:
        dist = sprite['dist']
        angle_diff = sprite['angle']
        
        # Project sprite position
        screen_x = (angle_diff / HALF_FOV) * (WIDTH / 2) + WIDTH / 2
        
        # Calculate sprite size
        sprite_height = min(WALL_HEIGHT / dist * 277, HEIGHT)
        sprite_width = sprite_height
        
        # Check if sprite is visible (not behind wall)
        ray_index = int((angle_diff + HALF_FOV) / DELTA_ANGLE)
        if 0 <= ray_index < len(depths) and dist < depths[ray_index]:
            x = screen_x - sprite_width / 2
            y = (HEIGHT - sprite_height) / 2
            
            if sprite['type'] == 'enemy':
                # Draw enemy as red circle/rectangle
                color = COLORS['enemy']
                pygame.draw.ellipse(screen, color, (x, y, sprite_width, sprite_height))
                pygame.draw.ellipse(screen, (255, 100, 100), (x, y, sprite_width, sprite_height), 2)
                
                # Health bar
                if sprite['obj']['hp'] > 0:
                    bar_w = sprite_width
                    bar_h = 8
                    ratio = sprite['obj']['hp'] / sprite['obj']['max_hp']
                    pygame.draw.rect(screen, COLORS['red'], (x, y - 15, bar_w, bar_h))
                    pygame.draw.rect(screen, COLORS['green'], (x, y - 15, bar_w * ratio, bar_h))
            
            elif sprite['type'] == 'door':
                # Draw door as yellow rectangle
                color = COLORS['door']
                pygame.draw.rect(screen, color, (x, y, sprite_width, sprite_height))
                pygame.draw.rect(screen, COLORS['brown'], (x, y, sprite_width, sprite_height), 3)

def draw_minimap():
    map_size = 150
    map_x = WIDTH - map_size - 10
    map_y = 10
    scale = map_size / ROOM_SIZE
    
    # Draw minimap background
    pygame.draw.rect(screen, (0, 0, 0, 128), (map_x, map_y, map_size, map_size))
    pygame.draw.rect(screen, COLORS['white'], (map_x, map_y, map_size, map_size), 2)
    
    # Draw player
    px = map_x + player['x'] * scale
    py = map_y + player['y'] * scale
    pygame.draw.circle(screen, COLORS['green'], (int(px), int(py)), 4)
    
    # Draw direction line
    end_x = px + 15 * math.cos(player['angle'])
    end_y = py + 15 * math.sin(player['angle'])
    pygame.draw.line(screen, COLORS['green'], (px, py), (end_x, end_y), 2)
    
    # Draw enemies
    for e in rooms[game_state['current_room']]['enemies']:
        if e['hp'] > 0:
            ex = map_x + e['x'] * scale
            ey = map_y + e['y'] * scale
            pygame.draw.circle(screen, COLORS['red'], (int(ex), int(ey)), 3)
    
    # Draw doors
    for door in rooms[game_state['current_room']]['doors']:
        dx = map_x + door['x'] * scale
        dy = map_y + door['y'] * scale
        pygame.draw.circle(screen, COLORS['yellow'], (int(dx), int(dy)), 4)

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
    
    # Controls
    controls = "WASD/Arrows: Move | Q/E: Strafe | Space: Attack/Enter Door"
    screen.blit(ui_font.render(controls, True, COLORS['white']), (16, HEIGHT - 30))
    
    # Popup
    if combat['popup_msg'] and pygame.time.get_ticks() < combat['popup_until']:
        screen.blit(ui_font.render(combat['popup_msg'], True, COLORS['yellow']), (16, 80))
    
    # Debug
    if game_state['debug']:
        lines = [
            f"Room: {game_state['current_room']}",
            f"Pos: ({int(player['x'])}, {int(player['y'])})",
            f"Angle: {int(math.degrees(player['angle']))}"
        ]
        for i, line in enumerate(lines):
            text = ui_font.render(line, True, COLORS['yellow'])
            screen.blit(text, (10, 110 + i * 25))

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
            screen.fill(COLORS['dark'])
            screen.blit(title_font.render('Frankenstein Mansion 3D', True, COLORS['white']), (200, 80))
            screen.blit(ui_font.render('Press ENTER to start', True, COLORS['yellow']), (320, 520))
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
                    game_state['player_name'] = name.strip() or 'player'
                    return
                elif ev.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif ev.unicode.isprintable():
                    name += ev.unicode
        
        screen.fill(COLORS['dark'])
        prompt = ui_font.render(f'Enter your name: {name}', True, COLORS['white'])
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 200))
        pygame.display.flip()
        clock.tick(60)

def reset_game():
    player.update({
        'x': ROOM_SIZE // 2,
        'y': ROOM_SIZE // 2,
        'angle': 0,
        'hp': 10,
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
    over1 = title_font.render('GAME OVER', True, (255, 200, 200))
    over2 = ui_font.render('Enter: Restart | Esc: Quit', True, COLORS['white'])
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
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F3:
                    game_state['debug'] = not game_state['debug']
                elif ev.key == pygame.K_SPACE:
                    try_attack()
        
        keys = pygame.key.get_pressed()
        handle_input(keys)
        
        update_enemies()
        draw_3d_view()
        draw_minimap()
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