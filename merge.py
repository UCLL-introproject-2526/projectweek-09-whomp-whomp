import pygame
import sys
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum

# ================= INITIALIZATION =================
pygame.init()
pygame.mixer.init()

# ================= CONSTANTS =================
class Config:
    """Game configuration constants"""
    # Display
    SCREEN_WIDTH = 900
    SCREEN_HEIGHT = 600
    ROOM_WIDTH = 1600
    ROOM_HEIGHT = 1200
    FPS = 60

    # Player
    PLAYER_SPEED = 5
    PLAYER_MAX_HP = 5
    PLAYER_INVULNERABILITY_MS = 500
    PLAYER_FRAME_WIDTH = 64
    PLAYER_FRAME_HEIGHT = 64
    ANIMATION_SPEED = 0.2

    # Combat
    WOOD_DAMAGE = 1
    METAL_DAMAGE = 3
    ATTACK_RANGE = 42
    ATTACK_COOLDOWN_MS = 300
    METAL_SPEAR_TOKEN_REQUIREMENT = 15

    # Enemy
    ENEMY_SIZE = 42
    ENEMY_DEFAULT_HP = 3

    # Map
    MAP_CELL_SIZE = 35
    MAP_MARGIN = 10
    MAP_COLS = 5
    MAP_ROWS = 4
    ROOMS_PER_FLOOR = 20
    TOTAL_FLOORS = 4

class Direction(Enum):
    """Player movement directions"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class RoomType(Enum):
    """Different room types"""
    ENTRANCE = "entrance"
    COMBAT = "combat"
    BOSS = "boss"
    STAIRS_UP = "stairs_up"
    STAIRS_DOWN = "stairs_down"
    TREASURE = "treasure"

class Color:
    """Color palette"""
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (230, 50, 50)
    GREEN = (80, 220, 120)
    YELLOW = (230, 200, 60)
    BROWN = (120, 80, 40)
    DARK = (20, 10, 22)
    LIGHT_RED = (255, 200, 200)
    DARK_HEART = (90, 40, 40)
    BLUE = (50, 100, 200)
    PURPLE = (150, 50, 200)
    ORANGE = (255, 150, 50)
    GRAY = (100, 100, 100)
    DARK_GRAY = (40, 40, 40)

# ================= DATA CLASSES =================
@dataclass
class Enemy:
    """Enemy entity"""
    rect: pygame.Rect
    hp: int
    max_hp: int
    dx: int
    dy: int
    sprite: pygame.surface

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> bool:
        """Returns True if enemy died"""
        self.hp -= amount
        return self.hp <= 0

    def update_position(self, room_width: int, room_height: int):
        """Update enemy position with wall collision"""
        self.rect.x += self.dx
        self.rect.y += self.dy

        if self.rect.left <= 0 or self.rect.right >= room_width:
            self.dx *= -1
        if self.rect.top <= 0 or self.rect.bottom >= room_height:
            self.dy *= -1

        self.rect.clamp_ip(pygame.Rect(0, 0, room_width, room_height))

@dataclass
class Door:
    """Door/portal entity"""
    rect: pygame.Rect
    target_room: str
    spawn_position: Tuple[int, int]
    label: str = ""

@dataclass
class Room:
    """Game room"""
    id: str
    name: str
    floor: int
    room_type: RoomType
    color: Tuple[int, int, int]
    doors: List[Door]
    enemies: List[Enemy]
    visited: bool = False
    cleared: bool = False

    @property
    def alive_enemy_count(self) -> int:
        return sum(1 for e in self.enemies if e.is_alive)

    def update_cleared_status(self):
        """Update cleared status based on enemies"""
        if not self.cleared and self.alive_enemy_count == 0 and len(self.enemies) > 0:
            self.cleared = True

# ================= ROOM GENERATOR =================
class RoomGenerator:
    """Generate rooms for each floor"""

    FLOOR_THEMES = {
        1: {"name": "Ground Floor", "base_color": (45, 25, 15), "enemy_speed": 2, "enemy_count": (1, 3)},
        2: {"name": "First Floor", "base_color": (25, 15, 45), "enemy_speed": 3, "enemy_count": (2, 4)},
        3: {"name": "Second Floor", "base_color": (45, 15, 25), "enemy_speed": 3, "enemy_count": (2, 5)},
        4: {"name": "Penthouse", "base_color": (15, 25, 45), "enemy_speed": 4, "enemy_count": (3, 6)}
    }

    ROOM_NAMES = [
        "Lobby", "Kitchen", "Library", "Dining Hall", "Guest Room",
        "Suite", "Bathroom", "Corridor", "Storage", "Ballroom",
        "Office", "Lounge", "Garden", "Wine Cellar", "Attic",
        "Balcony", "Study", "Chamber", "Gallery", "Terrace"
    ]

    @staticmethod
    def generate_floor(floor_num: int) -> Dict[str, Room]:
        """Generate all rooms for a floor"""
        rooms = {}
        theme = RoomGenerator.FLOOR_THEMES[floor_num]

        # Create grid layout (5x4 = 20 rooms)
        room_positions = []
        for row in range(Config.MAP_ROWS):
            for col in range(Config.MAP_COLS):
                room_positions.append((row, col))

        # Create rooms
        for idx, (row, col) in enumerate(room_positions):
            room_id = f"floor{floor_num}_room{idx}"

            # Determine room type
            if idx == 0:
                room_type = RoomType.ENTRANCE
            elif idx == Config.ROOMS_PER_FLOOR - 1:
                room_type = RoomType.BOSS
            elif idx == 10 and floor_num < Config.TOTAL_FLOORS: # Middle of floor
                room_type = RoomType.STAIRS_UP
            elif idx == 5 and floor_num > 1: # Top-right area
                room_type = RoomType.STAIRS_DOWN
            elif idx % 7 == 0 and idx > 0:
                room_type = RoomType.TREASURE
            else:
                room_type = RoomType.COMBAT

            # Create room
            room = RoomGenerator._create_room(
                room_id, floor_num, idx, row, col, room_type, theme
            )
            rooms[room_id] = room

        # Connect rooms with doors
        RoomGenerator._connect_rooms(rooms, floor_num, room_positions)

        return rooms

    @staticmethod
    def _create_room(room_id: str, floor: int, idx: int, row: int, col: int,
                     room_type: RoomType, theme: dict) -> Room:
        """Create a single room"""
        # Color variation
        base = theme["base_color"]
        color = (
            base[0] + random.randint(-20, 20),
            base[1] + random.randint(-20, 20),
            base[2] + random.randint(-20, 20)
        )
        color = tuple(max(10, min(255, c)) for c in color)

        # Room name
        name = RoomGenerator.ROOM_NAMES[idx % len(RoomGenerator.ROOM_NAMES)]
        if room_type == RoomType.ENTRANCE:
            name = "Entrance"
        elif room_type == RoomType.BOSS:
            name = f"Boss Chamber"
        elif room_type == RoomType.STAIRS_UP:
            name = "Stairs Up"
        elif room_type == RoomType.STAIRS_DOWN:
            name = "Stairs Down"
        elif room_type == RoomType.TREASURE:
            name = "Treasure Room"

        # Enemies
        enemies = []
        if room_type == RoomType.COMBAT:
            enemy_count = random.randint(*theme["enemy_count"])
            enemies = RoomGenerator._create_enemies(enemy_count, theme["enemy_speed"])
        elif room_type == RoomType.BOSS:
            # Boss room with tougher enemies
            enemies = RoomGenerator._create_enemies(1, 2, hp=10)
            enemies.extend(RoomGenerator._create_enemies(3, theme["enemy_speed"]))
        elif room_type == RoomType.TREASURE:
            enemies = RoomGenerator._create_enemies(random.randint(1, 2), theme["enemy_speed"] + 1)

        return Room(
            id=room_id,
            name=name,
            floor=floor,
            room_type=room_type,
            color=color,
            doors=[],
            enemies=enemies
        )

    @staticmethod
    def _create_enemies(count: int, speed: int, hp: int = Config.ENEMY_DEFAULT_HP) -> List[Enemy]:
        """Create enemies"""
        enemies = []
        for _ in range(count):
            x = random.randint(100, Config.ROOM_WIDTH - 150)
            y = random.randint(100, Config.ROOM_HEIGHT - 150)
            enemies.append(Enemy(
                rect=pygame.Rect(x, y, Config.ENEMY_SIZE, Config.ENEMY_SIZE),
                hp=hp,
                max_hp=hp,
                dx=random.choice([-speed, speed]),
                dy=random.choice([-speed, speed])
                sprite=Game.instance.enemy_sprite
            ))
        return enemies

    @staticmethod
    def _connect_rooms(rooms: Dict[str, Room], floor: int, positions: List[Tuple[int, int]]):
        """Create doors between adjacent rooms"""
        for idx, (row, col) in enumerate(positions):
            room_id = f"floor{floor}_room{idx}"
            room = rooms[room_id]

            # Right door
            if col < Config.MAP_COLS - 1:
                target_idx = idx + 1
                target_id = f"floor{floor}_room{target_idx}"
                room.doors.append(Door(
                    pygame.Rect(Config.SCREEN_WIDTH - 110, Config.SCREEN_HEIGHT//2 - 55, 80, 110),
                    target_id,
                    (150, Config.SCREEN_HEIGHT//2),
                    "→"
                ))

            # Left door
            if col > 0:
                target_idx = idx - 1
                target_id = f"floor{floor}_room{target_idx}"
                room.doors.append(Door(
                    pygame.Rect(30, Config.SCREEN_HEIGHT//2 - 55, 80, 110),
                    target_id,
                    (Config.SCREEN_WIDTH - 150, Config.SCREEN_HEIGHT//2),
                    "←"
                ))

            # Down door
            if row < Config.MAP_ROWS - 1:
                target_idx = idx + Config.MAP_COLS
                target_id = f"floor{floor}_room{target_idx}"
                room.doors.append(Door(
                    pygame.Rect(Config.SCREEN_WIDTH//2 - 40, Config.SCREEN_HEIGHT - 100, 80, 80),
                    target_id,
                    (Config.SCREEN_WIDTH//2, 150),
                    "↓"
                ))

            # Up door
            if row > 0:
                target_idx = idx - Config.MAP_COLS
                target_id = f"floor{floor}_room{target_idx}"
                room.doors.append(Door(
                    pygame.Rect(Config.SCREEN_WIDTH//2 - 40, 20, 80, 80),
                    target_id,
                    (Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT - 150),
                    "↑"
                ))

# ================= GAME MANAGER =================
class Game:
    """Main game manager"""

    def __init__(self):
        # Display setup
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Hotel Transylvania - 4 Floors Edition")
        self.clock = pygame.time.Clock()

        # Fonts
        self.ui_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.title_font = pygame.font.SysFont('Arial', 64, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 18)
        self.tiny_font = pygame.font.SysFont('Arial', 14)

        # Load sprites
        self.load_sprites()

        # Initialize all floors
        self.all_rooms: Dict[str, Room] = {}
        for floor in range(1, Config.TOTAL_FLOORS + 1):
            self.all_rooms.update(RoomGenerator.generate_floor(floor))

        # Game state
        self.current_room_id = "floor1_room0"
        self.current_floor = 1
        self.show_map = False

        # Player state
        self.reset_player()

        # Game flags
        self.running = True
        self.game_over = False
        self.victory = False
        self.show_start_screen_flag = True

    def reset_player(self):
        """Reset player state"""
        self.player_rect = pygame.Rect(
            Config.SCREEN_WIDTH // 2 - 20,
            Config.SCREEN_HEIGHT // 2 - 28,
            40, 56
        )
        self.player_direction = Direction.DOWN
        self.player_frame = 0.0
        self.player_hp = Config.PLAYER_MAX_HP
        self.last_hit_time = -9999
        self.tokens = 0
        self.has_metal_spear = False
        self.last_attack_time = -9999
        self.popup_message: Optional[str] = None
        self.popup_until = 0

    def load_sprites(self):
        """Load and prepare sprite sheets"""
        try:
            self.player_spritesheet = pygame.image.load("projectweek-09-whomp-whomp\img\player.png").convert_alpha()
            self.player_sprites = self._load_spritesheet(
                self.player_spritesheet,
                Config.PLAYER_FRAME_WIDTH,
                Config.PLAYER_FRAME_HEIGHT
            )
        except:
            self.player_sprites = self._create_fallback_sprites()

        # Enemy
            try:
                self.enemy_sprite = pygame.image.load("projectweek-09-whomp-whomp\img\skeleton.png").convert_alpha()
                self.enemy_sprite = pygame.transform.scale(
                self.enemy_sprite,
                (Config.ENEMY_SIZE, Config.ENEMY_SIZE)
        )
            except:
                self.enemy_sprite = self._create_enemy_fallback()
    
    def _create_enemy_fallback(self):
        surf = pygame.Surface((Config.ENEMY_SIZE, Config.ENEMY_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(
        surf, Color.GREEN,
        (Config.ENEMY_SIZE // 2, Config.ENEMY_SIZE // 2),
        Config.ENEMY_SIZE // 2
    )
        return surf


    def _load_spritesheet(self, sheet: pygame.Surface, frame_w: int, frame_h: int) -> List[List[pygame.Surface]]:
        """Extract frames from sprite sheet"""
        frames = []
        for y in range(0, sheet.get_height(), frame_h):
            row = []
            for x in range(0, sheet.get_width(), frame_w):
                row.append(sheet.subsurface(pygame.Rect(x, y, frame_w, frame_h)))
            frames.append(row)
        return frames

    def _create_fallback_sprites(self) -> List[List[pygame.Surface]]:
        """Create simple colored rectangles as fallback sprites"""
        fallback = []
        colors = [(100, 150, 200), (150, 100, 200), (200, 150, 100), (150, 200, 100)]
        for color in colors:
            row = []
            for _ in range(4):
                surf = pygame.Surface((Config.PLAYER_FRAME_WIDTH, Config.PLAYER_FRAME_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (32, 32), 20)
                row.append(surf)
            fallback.append(row)
        return fallback

    @property
    def current_room(self) -> Room:
        """Get current room object"""
        room = self.all_rooms[self.current_room_id]
        if not room.visited:
            room.visited = True
        return room

    @property
    def current_damage(self) -> int:
        """Get current weapon damage"""
        return Config.METAL_DAMAGE if self.has_metal_spear else Config.WOOD_DAMAGE

    @property
    def total_alive_enemies(self) -> int:
        """Count all alive enemies in all rooms"""
        return sum(room.alive_enemy_count for room in self.all_rooms.values())

    @property
    def floor_progress(self) -> str:
        """Get floor completion progress"""
        floor_rooms = [r for r in self.all_rooms.values() if r.floor == self.current_floor]
        cleared = sum(1 for r in floor_rooms if r.cleared)
        return f"{cleared}/{len(floor_rooms)}"

    def get_camera_offset(self) -> Tuple[int, int]:
        """Calculate camera offset for scrolling"""
        cam_x = max(0, min(
            self.player_rect.centerx - Config.SCREEN_WIDTH // 2,
            Config.ROOM_WIDTH - Config.SCREEN_WIDTH
        ))
        cam_y = max(0, min(
            self.player_rect.centery - Config.SCREEN_HEIGHT // 2,
            Config.ROOM_HEIGHT - Config.SCREEN_HEIGHT
        ))
        return cam_x, cam_y

    def handle_input(self, keys: pygame.key.ScancodeWrapper):
        """Process player input"""
        vx = vy = 0
        moving = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]:
            vx = -Config.PLAYER_SPEED
            self.player_direction = Direction.LEFT
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx = Config.PLAYER_SPEED
            self.player_direction = Direction.RIGHT
            moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_z]:
            vy = -Config.PLAYER_SPEED
            self.player_direction = Direction.UP
            moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            vy = Config.PLAYER_SPEED
            self.player_direction = Direction.DOWN
            moving = True

        self.player_rect.x += vx
        self.player_rect.y += vy
        self.player_rect.clamp_ip(pygame.Rect(0, 0, Config.ROOM_WIDTH, Config.ROOM_HEIGHT))

        self.player_frame = (self.player_frame + Config.ANIMATION_SPEED) if moving else 0

    def get_attack_rect(self) -> pygame.Rect:
        """Get attack hitbox based on player direction"""
        r = self.player_rect
        if self.player_direction == Direction.UP:
            return pygame.Rect(r.centerx-8, r.top-Config.ATTACK_RANGE, 16, Config.ATTACK_RANGE)
        elif self.player_direction == Direction.DOWN:
            return pygame.Rect(r.centerx-8, r.bottom, 16, Config.ATTACK_RANGE)
        elif self.player_direction == Direction.LEFT:
            return pygame.Rect(r.left-Config.ATTACK_RANGE, r.centery-8, Config.ATTACK_RANGE, 16)
        else:
            return pygame.Rect(r.right, r.centery-8, Config.ATTACK_RANGE, 16)

    def try_attack(self):
        """Attempt to attack enemies"""
        now = pygame.time.get_ticks()
        if now - self.last_attack_time < Config.ATTACK_COOLDOWN_MS:
            return

        self.last_attack_time = now
        attack_box = self.get_attack_rect()

        for enemy in self.current_room.enemies:
            if enemy.is_alive and attack_box.colliderect(enemy.rect):
                if enemy.take_damage(self.current_damage):
                    self.tokens += 1
                    self.show_popup("+1 Token", 1200)

                if self.tokens >= Config.METAL_SPEAR_TOKEN_REQUIREMENT and not self.has_metal_spear:
                    self.has_metal_spear = True
                    self.show_popup("🗡️ Metal Spear Unlocked!", 2500)

    def show_popup(self, message: str, duration_ms: int):
        """Display temporary popup message"""
        self.popup_message = message
        self.popup_until = pygame.time.get_ticks() + duration_ms

    def take_damage(self, amount: int = 1):
        """Player takes damage with invulnerability period"""
        now = pygame.time.get_ticks()
        if now - self.last_hit_time >= Config.PLAYER_INVULNERABILITY_MS:
            self.last_hit_time = now
            self.player_hp -= amount
            if self.player_hp <= 0:
                self.game_over = True

    def check_collisions(self, keys: pygame.key.ScancodeWrapper):
        """Check all collision types"""
        # Enemy collisions
        for enemy in self.current_room.enemies:
            if enemy.is_alive and self.player_rect.colliderect(enemy.rect):
                self.take_damage()

        # Door collisions
        for door in self.current_room.doors:
            if self.player_rect.colliderect(door.rect):
                target_room = self.all_rooms[door.target_room]
                hint = self.small_font.render(f"Press E: {target_room.name}", True, Color.YELLOW)
                self.screen.blit(hint, (Config.SCREEN_WIDTH//2 - hint.get_width()//2, Config.SCREEN_HEIGHT - 40))

                if keys[pygame.K_e]:
                    self.current_room_id = door.target_room
                    self.current_floor = target_room.floor
                    self.player_rect.center = door.spawn_position

        # Stairs
        if self.current_room.room_type == RoomType.STAIRS_UP and self.current_room.cleared:
            if keys[pygame.K_e]:
                # Go to next floor
                if self.current_floor < Config.TOTAL_FLOORS:
                    self.current_floor += 1
                    self.current_room_id = f"floor{self.current_floor}_room0"
                    self.player_rect.center = (Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2)
                    self.show_popup(f"📍 Floor {self.current_floor}", 2000)

        if self.current_room.room_type == RoomType.STAIRS_DOWN:
            if keys[pygame.K_e]:
                # Go to previous floor
                if self.current_floor > 1:
                    self.current_floor -= 1
                    self.current_room_id = f"floor{self.current_floor}_room10"
                    self.player_rect.center = (Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2)
                    self.show_popup(f"📍 Floor {self.current_floor}", 2000)


    def update(self):
        """Update game state"""
        # Update enemies
        for enemy in self.current_room.enemies:
            if enemy.is_alive:
                enemy.update_position(Config.ROOM_WIDTH, Config.ROOM_HEIGHT)

        # Update room status
        self.current_room.update_cleared_status()

        # Check victory
        if self.total_alive_enemies == 0:
            self.victory = True

    def draw(self):
        """Render everything"""
        cam_x, cam_y = self.get_camera_offset()

        # Background
        self.screen.fill(self.current_room.color)

        # Draw doors
        for door in self.current_room.doors:
            draw_rect = door.rect.move(-cam_x, -cam_y)
            pygame.draw.rect(self.screen, Color.YELLOW, draw_rect, border_radius=8)
            pygame.draw.rect(self.screen, Color.BROWN, draw_rect, 3, border_radius=8)

            if door.label:
                label = self.ui_font.render(door.label, True, Color.WHITE)
                self.screen.blit(label, (draw_rect.centerx - label.get_width()//2,
                                         draw_rect.centery - label.get_height()//2))

        # Draw stairs indicators
        if self.current_room.room_type == RoomType.STAIRS_UP:
            if self.current_room.cleared:
                msg = self.ui_font.render("⬆️ Press E: Go Up", True, Color.GREEN)
            else:
                msg = self.ui_font.render("⬆️ Clear room first!", True, Color.RED)
            self.screen.blit(msg, (Config.SCREEN_WIDTH//2 - msg.get_width()//2, 100))

        if self.current_room.room_type == RoomType.STAIRS_DOWN:
            msg = self.ui_font.render("⬇️ Press E: Go Down", True, Color.GREEN)
            self.screen.blit(msg, (Config.SCREEN_WIDTH//2 - msg.get_width()//2, 100))

        # Draw enemies
        for enemy in self.current_room.enemies:
            if enemy.is_alive:
                draw_rect = enemy.rect.move(-cam_x, -cam_y)
                pygame.draw.rect(self.screen, Color.GREEN, draw_rect, border_radius=6)

                # Health bar
                hp_ratio = enemy.hp / enemy.max_hp
                health_width = int(draw_rect.width * hp_ratio)
                health_rect = pygame.Rect(draw_rect.x, draw_rect.y - 8, health_width, 4)
                pygame.draw.rect(self.screen, Color.RED, health_rect)

        # Draw player
        direction_row = {Direction.DOWN: 0, Direction.LEFT: 1, Direction.RIGHT: 2, Direction.UP: 3}
        frame_idx = int(self.player_frame) % len(self.player_sprites[0])
        player_sprite = self.player_sprites[direction_row[self.player_direction]][frame_idx]
        draw_rect = self.player_rect.move(-cam_x, -cam_y)
        self.screen.blit(player_sprite, draw_rect)

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        """Draw heads-up display"""
        # Health hearts
        for i in range(Config.PLAYER_MAX_HP):
            color = Color.RED if i < self.player_hp else Color.DARK_HEART
            x, y = 20 + i * 30, 20
            pygame.draw.circle(self.screen, color, (x, y), 10)
            pygame.draw.circle(self.screen, color, (x + 12, y), 10)
            pygame.draw.polygon(self.screen, color, [(x-8, y+4), (x+20, y+4), (x+6, y+24)])

        # Stats line 1
        weapon = "⚔️ Metal" if self.has_metal_spear else "🪵 Wood"
        info = f"Tokens: {self.tokens} | {weapon} | Floor {self.current_floor}"
        info_surf = self.ui_font.render(info, True, Color.WHITE)
        self.screen.blit(info_surf, (16, 55))

        # Stats line 2
        room_info = f"{self.current_room.name} | Enemies: {self.current_room.alive_enemy_count}"
        room_surf = self.small_font.render(room_info, True, Color.YELLOW)
        self.screen.blit(room_surf, (16, 85))

        # Map hint
        map_hint = self.tiny_font.render("Press M for Map", True, Color.WHITE)
        self.screen.blit(map_hint, (Config.SCREEN_WIDTH - 120, 20))

        # Popup message
        if self.popup_message and pygame.time.get_ticks() < self.popup_until:
            popup_surf = self.ui_font.render(self.popup_message, True, Color.YELLOW)
            self.screen.blit(popup_surf, (Config.SCREEN_WIDTH//2 - popup_surf.get_width()//2, 150))

    def show_start_screen(self):
        """Display start/intro screen"""
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        overlay.fill((15, 5, 25))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.title_font.render("HOTEL TRANSYLVANIA", True, Color.RED)
        self.screen.blit(title, title.get_rect(center=(Config.SCREEN_WIDTH//2, 100)))

        subtitle = self.ui_font.render("4 Floors | 80 Rooms | Survive the Night", True, Color.YELLOW)
        self.screen.blit(subtitle, subtitle.get_rect(center=(Config.SCREEN_WIDTH//2, 180)))

        # Instructions
        instructions = [
            "CONTROLS:",
            "WASD / Arrow Keys - Move",
            "SPACE / Left Click - Attack",
            "M - Open Map",
            "E - Enter Doors / Use Stairs",
            "ESC - Quit",
            "",
            "GOAL:",
            "Clear all 4 floors of enemies!",
            "Collect 15 tokens for Metal Spear upgrade",
            "",
            "Press ENTER to start"
        ]

        y = 240
        for line in instructions:
            if line == "CONTROLS:" or line == "GOAL:":
                color = Color.GREEN
                font = self.ui_font
            elif line == "":
                y += 10
                continue
            elif "Press ENTER" in line:
                color = Color.YELLOW
                font = self.ui_font
            else:
                color = Color.WHITE
                font = self.small_font

            text = font.render(line, True, color)
            self.screen.blit(text, text.get_rect(center=(Config.SCREEN_WIDTH//2, y)))
            y += 30 if font == self.ui_font else 25

    def show_game_over(self):
        """Display game over screen"""
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(Color.DARK)
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("GAME OVER", True, Color.LIGHT_RED)
        stats = self.ui_font.render(f"Floor {self.current_floor} | Tokens: {self.tokens}", True, Color.WHITE)
        subtitle = self.small_font.render("Press ENTER to restart or ESC to quit", True, Color.WHITE)

        self.screen.blit(title, title.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 - 60)))
        self.screen.blit(stats, stats.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 + 60)))

    def show_victory(self):
        """Display victory screen"""
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 20, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("🎉 VICTORY! 🎉", True, Color.GREEN)
        subtitle = self.ui_font.render(f"All 4 floors cleared! Tokens: {self.tokens}", True, Color.WHITE)
        hint = self.small_font.render("Press ENTER to play again or ESC to quit", True, Color.YELLOW)

        self.screen.blit(title, title.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 - 60)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2)))
        self.screen.blit(hint, hint.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 + 60)))

    def reset(self):
        """Reset game state"""
        self.all_rooms = {}
        for floor in range(1, Config.TOTAL_FLOORS + 1):
            self.all_rooms.update(RoomGenerator.generate_floor(floor))

        self.current_room_id = "floor1_room0"
        self.current_floor = 1
        self.show_map = False
        self.reset_player()
        self.game_over = False
        self.victory = False
        self.show_start_screen_flag = False

    def draw_map(self):
        """Draw the floor map"""
        # Semi-transparent overlay
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        overlay.set_alpha(240)
        overlay.fill((10, 10, 20))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.title_font.render(f"Floor {self.current_floor} Map", True, Color.WHITE)
        self.screen.blit(title, (Config.SCREEN_WIDTH//2 - title.get_width()//2, 20))

        # Instructions
        inst = self.small_font.render("Click a room to travel | M to close | Arrow keys to change floor", True, Color.YELLOW)
        self.screen.blit(inst, (Config.SCREEN_WIDTH//2 - inst.get_width()//2, 80))

        # Floor buttons
        for f in range(1, Config.TOTAL_FLOORS + 1):
            btn_x = 50 + (f - 1) * 80
            btn_rect = pygame.Rect(btn_x, 120, 70, 35)
            color = Color.GREEN if f == self.current_floor else Color.GRAY
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, Color.WHITE, btn_rect, 2, border_radius=5)
            txt = self.ui_font.render(f"F{f}", True, Color.WHITE)
            self.screen.blit(txt, (btn_x + 20, 125))

        # Draw grid
        start_x = Config.SCREEN_WIDTH//2 - (Config.MAP_COLS * Config.MAP_CELL_SIZE)//2
        start_y = 180

        for idx in range(Config.ROOMS_PER_FLOOR):
            row = idx // Config.MAP_COLS
            col = idx % Config.MAP_COLS
            x = start_x + col * Config.MAP_CELL_SIZE
            y = start_y + row * Config.MAP_CELL_SIZE

            room_id = f"floor{self.current_floor}_room{idx}"
            room = self.all_rooms[room_id]

            # Determine color
            if room.id == self.current_room_id:
                color = Color.YELLOW
            elif room.cleared:
                color = Color.GREEN
            elif room.visited:
                color = Color.BLUE
            elif not room.visited:
                color = Color.DARK_GRAY
            else:
                color = Color.GRAY

            # Draw cell
            cell_rect = pygame.Rect(x, y, Config.MAP_CELL_SIZE - 2, Config.MAP_CELL_SIZE - 2)
            pygame.draw.rect(self.screen, color, cell_rect, border_radius=4)
            pygame.draw.rect(self.screen, Color.WHITE, cell_rect, 1, border_radius=4)

            # Room type icon
            icon = ""
            if room.room_type == RoomType.ENTRANCE:
                icon = "🚪"
            elif room.room_type == RoomType.BOSS:
                icon = "👹"
            elif room.room_type == RoomType.STAIRS_UP:
                icon = "⬆️"
            elif room.room_type == RoomType.STAIRS_DOWN:
                icon = "⬇️"
            elif room.room_type == RoomType.TREASURE:
                icon = "💎"
            elif room.alive_enemy_count > 0:
                icon = str(room.alive_enemy_count)

            if icon:
                txt = self.tiny_font.render(icon, True, Color.WHITE)
                self.screen.blit(txt, (x + Config.MAP_CELL_SIZE//2 - txt.get_width()//2,
                                       y + Config.MAP_CELL_SIZE//2 - txt.get_height()//2))

        # Legend
        legend_y = start_y + Config.MAP_ROWS * Config.MAP_CELL_SIZE + 20
        legends = [
            ("Current", Color.YELLOW),
            ("Cleared", Color.GREEN),
            ("Visited", Color.BLUE),
            ("Unknown", Color.DARK_GRAY)
        ]
        for i, (label, color) in enumerate(legends):
            x = start_x + i * 100
            pygame.draw.rect(self.screen, color, (x, legend_y, 20, 20), border_radius=3)
            txt = self.tiny_font.render(label, True, Color.WHITE)
            self.screen.blit(txt, (x + 25, legend_y + 2))

    def handle_map_click(self, pos: Tuple[int, int]):
        """Handle click on map"""
        start_x = Config.SCREEN_WIDTH//2 - (Config.MAP_COLS * Config.MAP_CELL_SIZE)//2
        start_y = 180

        mx, my = pos

        # Check floor buttons
        for f in range(1, Config.TOTAL_FLOORS + 1):
            btn_x = 50 + (f - 1) * 80
            if pygame.Rect(btn_x, 120, 70, 35).collidepoint(pos):
                self.current_floor = f
                return

        # Check room cells
        for idx in range(Config.ROOMS_PER_FLOOR):
            row = idx // Config.MAP_COLS
            col = idx % Config.MAP_COLS
            x = start_x + col * Config.MAP_CELL_SIZE
            y = start_y + row * Config.MAP_CELL_SIZE

            cell_rect = pygame.Rect(x, y, Config.MAP_CELL_SIZE - 2, Config.MAP_CELL_SIZE - 2)
            if cell_rect.collidepoint(mx, my):
                room_id = f"floor{self.current_floor}_room{idx}"
                room = self.all_rooms[room_id]
                if room.visited:
                    self.current_room_id = room_id
                    self.player_rect.center = (Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2)
                    self.show_map = False

    def run(self):
        """Main game loop"""
        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.show_map:
                            self.handle_map_click(event.pos)
                        elif not self.game_over and not self.victory and not self.show_start_screen_flag:
                            self.try_attack()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m and not self.game_over and not self.victory and not self.show_start_screen_flag:
                        self.show_map = not self.show_map
                    elif event.key == pygame.K_ESCAPE:
                        if self.show_map:
                            self.show_map = False
                        else:
                            self.running = False
                    elif event.key == pygame.K_RETURN:
                        if self.show_start_screen_flag:
                            self.show_start_screen_flag = False

            keys = pygame.key.get_pressed()

            # Start screen
            if self.show_start_screen_flag:
                self.show_start_screen()
                pygame.display.flip()
                self.clock.tick(Config.FPS)
                continue

            # Game over/victory handling
            if self.game_over or self.victory:
                self.draw()
                if self.game_over:
                    self.show_game_over()
                else:
                    self.show_victory()

                pygame.display.flip()

                if keys[pygame.K_RETURN]:
                    self.reset()
                elif keys[pygame.K_ESCAPE]:
                    self.running = False

                self.clock.tick(Config.FPS)
                continue

            # Map mode
            if self.show_map:
                self.draw_map()
                pygame.display.flip()
                self.clock.tick(Config.FPS)
                continue

            # Normal gameplay
            self.handle_input(keys)

            if keys[pygame.K_SPACE]:
                self.try_attack()

            self.check_collisions(keys)
            self.update()
            self.draw()

            pygame.display.flip()
            self.clock.tick(Config.FPS)

        pygame.quit()
        sys.exit()

# ================= ENTRY POINT =================
if __name__ == "__main__":
    game = Game()
    game.run()