## Game logic code
import random
import math
import os
from enum import Enum

# *** IMPORTANT: Don't initialize Pygame at import time on macOS ***
# pygame will be imported and initialized only when needed

## Game Constants
WIDTH, HEIGHT = 1400, 750
ROOM_WIDTH, ROOM_HEIGHT = 600, 600
PLAYER_SIZE = 30
NPC_SIZE = 24
ENEMY_SIZE = 30
RESOURCE_SIZE = 24
OBSTACLE_SIZE = 40
FPS = 30

## Color setting
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
BROWN = (165, 42, 42)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)

## Pixel Art Coloring and Settings
PIXEL_RED = (220, 50, 47)
PIXEL_GREEN = (94, 190, 84)
PIXEL_BLUE = (52, 101, 164)
PIXEL_YELLOW = (255, 200, 47)
PIXEL_PURPLE = (108, 113, 196)
PIXEL_BROWN = (150, 75, 0)
PIXEL_GRAY = (85, 87, 83)
PIXEL_DARK_GRAY = (46, 52, 54)
PIXEL_WALL = (70, 40, 20)
PIXEL_FLOOR = (110, 85, 47)
PIXEL_DOOR = (185, 122, 87)
PIXEL_OBSTACLE = (62, 67, 73)

## Game parameters
MAX_HEALTH = 100
ENEMY_DAMAGE = 20
RESOURCE_HEAL = 10
NOTIFY_RADIUS = 150
ENEMY_DETECTION_RADIUS = 250
ATTACK_RADIUS = 60

## Player and NPC combat stats
PLAYER_DAMAGE = 100
NPC_DAMAGE = 20

## Player movement
PLAYER_SPEED = 4
NPC_SPEED = 2.5
ENEMY_SPEED = 1.5

## Obstacle generation parameters
MIN_OBSTACLES = 3
MAX_OBSTACLES = 8

## Class Enums
class PlayerAction(Enum):
    IDLE = "idle"
    MOVE = "move"
    ATTACK = "attack"

class NPCEmotion(Enum):
    ANTICIPATION = "anticipation"
    HAPPINESS = "happiness"
    FEAR = "fear"
    ANGER = "anger"
    SURPRISE = "surprise"
    SADNESS = "sadness"

class NPCReaction(Enum):
    FOLLOW = "follow"
    NOTIFY_RESOURCE = "notify_resource"
    NOTIFY_DANGER = "notify_danger"
    ATTACK_ENEMY = "attack_enemy"
    NOTIFY_SURPRISE = "notify_surprise"
    PROVIDE_HEALING = "provide_healing"

class GameState(Enum):
    START_SCREEN = "start_screen"
    PLAYING = "playing"
    COMPLETED = "completed"

class EmotionSystem(Enum):
    RANDOM = "random"
    RULE_BASED = "rule_based"
    MACHINE_LEARNING = "machine_learning"

## Helper function for pixel art rendering

## Main Game class logic
class Game:
    def __init__(self, emotion_system_instance, game_time_limit=120, show_debug_info=False, participant_id=None, condition=None):
        ## Import pygame here instead of at the module level
        import pygame
        self.pygame = pygame
        
        ## Initialize pygame
        self.pygame.init()

        ## Helper functions for pygames
        self.draw_pixel_rect = self._draw_pixel_rect
        self.draw_pixel_circle = self._draw_pixel_circle
        
        self.screen = self.pygame.display.set_mode((WIDTH, HEIGHT))
        
        ## Set the window caption based on the emotion system
        emotion_system_type = emotion_system_instance.get_system_type()
        if hasattr(self, 'show_debug_info') and self.show_debug_info:
            ## Only show condition name in title if debug mode is enabled
            self.pygame.display.set_caption(f"NPC Emotion Game - {emotion_system_type.name}")
        else:
            ## Otherwise just show generic title so no one can indetify the condition they are playing
            self.pygame.display.set_caption("NPC Emotion Game")
        
        self.clock = self.pygame.time.Clock()
        self.font = self.pygame.font.SysFont(None, 32)
        self.small_font = self.pygame.font.SysFont(None, 24)
        self.large_font = self.pygame.font.SysFont(None, 48)
        self.running = True
        self.game_over = False
        self.debug_mode = False
        
        ## Store participant info
        self.participant_id = participant_id
        self.condition = condition
        
        ## Set the emotion system
        self.emotion_system = emotion_system_instance
        
        ## Setting to show emotion and reaction text in UI
        self.show_debug_info = show_debug_info
        
        ## Timer feature
        self.game_time_limit = game_time_limit
        
        ## Track room transitions to prevent rapid toggling
        self.last_room_transition = 0
        self.room_transition_cooldown = 500  # milliseconds
        
        ## Game state
        self.state = GameState.START_SCREEN
        
        ## Frame counter
        self.frame = 0
        
        self.reset()
    
    def _draw_pixel_rect(self, surface, color, rect, border_radius=0):
        self.pygame.draw.rect(surface, color, rect, 0, border_radius)
        ## Add pixel-style shading
        dark_shade = (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40))
        light_shade = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
        
        ## Draw dark edge on right and bottom
        self.pygame.draw.line(surface, dark_shade, 
                        (rect.x + rect.width - 1, rect.y), 
                        (rect.x + rect.width - 1, rect.y + rect.height - 1), 2)
        self.pygame.draw.line(surface, dark_shade, 
                        (rect.x, rect.y + rect.height - 1), 
                        (rect.x + rect.width - 1, rect.y + rect.height - 1), 2)
        
        ## Draw light edge on top and left
        self.pygame.draw.line(surface, light_shade, 
                        (rect.x, rect.y), 
                        (rect.x + rect.width - 1, rect.y), 2)
        self.pygame.draw.line(surface, light_shade, 
                        (rect.x, rect.y), 
                        (rect.x, rect.y + rect.height - 1), 2)

    def _draw_pixel_circle(self, surface, color, center, radius):
        self.pygame.draw.circle(surface, color, center, radius)
        ## Add pixel-style shading - draw a slightly smaller circle with lighter color to add depth
        highlight_color = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))
        self.pygame.draw.circle(surface, highlight_color, 
                          (center[0] - int(radius * 0.2), center[1] - int(radius * 0.2)), 
                          int(radius * 0.4))
    
    def reset(self):
        self.running = True
        self.game_over = False
        self.resources_collected = 0
        self.enemies_killed = 0
        self.door_opened = False
        self.current_room = 1  ## Start in room 1
        self.frame = 0  ## Reset frame counter for each run
        
        ## Door unlock effect variables
        self.door_unlock_effect = False
        self.door_unlock_timer = -1  ## -1 means permanent until door is used
        
        ## Track player's previous action (lagged)
        self.lagged_player_action = PlayerAction.IDLE
        
        ## Adjust room positions to center in the larger window
        room_x_offset = (WIDTH - (2 * ROOM_WIDTH + 150)) // 2
        room_y_offset = (HEIGHT - ROOM_HEIGHT) // 2
        
        self.player = {
            "x": room_x_offset + 150,
            "y": room_y_offset + 150,
            "health": 100,
            "action": PlayerAction.IDLE,
            "speed": PLAYER_SPEED,
            "resources_collected": 0,
            "enemies_killed": 0
        }
        
        self.npc = {
            "x": room_x_offset + 100,
            "y": room_y_offset + 100,
            "emotion": NPCEmotion.ANTICIPATION,
            "emotion_lagged": NPCEmotion.ANTICIPATION,
            "reaction": NPCReaction.FOLLOW,
            "speed": NPC_SPEED,
            "attack_cooldown": 0  
        }
        
        ## Define rooms with new positions
        self.rooms = {
            1: {"x": room_x_offset, "y": room_y_offset, "width": ROOM_WIDTH, "height": ROOM_HEIGHT},
            2: {"x": room_x_offset + ROOM_WIDTH + 150, "y": room_y_offset, "width": ROOM_WIDTH, "height": ROOM_HEIGHT}
        }
        
        ## Generate obstacles for each room
        self.obstacles = self.generate_obstacles()
        
        ## Initialize enemies with health, avoiding spawning on obstacles
        self.enemies = []
        for _ in range(7):
            position = self.get_valid_position(1)
            self.enemies.append({
                "x": position[0],
                "y": position[1],
                "speed": random.uniform(ENEMY_SPEED * 0.8, ENEMY_SPEED * 1.2),
                "alive": True,
                "room": 1,
                "health": 100
            })
        
        for _ in range(8):
            position = self.get_valid_position(2)
            self.enemies.append({
                "x": position[0],
                "y": position[1],
                "speed": random.uniform(ENEMY_SPEED * 0.8, ENEMY_SPEED * 1.2),
                "alive": True,
                "room": 2,
                "health": 100
            })
        
        ## Initialize resources, avoiding spawning on obstacles
        self.resources = []
        for _ in range(2):
            position = self.get_valid_position(1)
            self.resources.append({
                "x": position[0],
                "y": position[1],
                "collected": False,
                "room": 1
            })
        
        for _ in range(2):
            position = self.get_valid_position(2)
            self.resources.append({
                "x": position[0],
                "y": position[1],
                "collected": False,
                "room": 2
            })
        
        ## Define door - position between rooms
        self.door = {
            "x": self.rooms[1]["x"] + ROOM_WIDTH,
            "y": self.rooms[1]["y"] + ROOM_HEIGHT // 2 - 50,
            "width": 150,
            "height": 100,
            "open": False
        }
        
        ## Define exit - in room 2
        self.exit = {
            "x": self.rooms[2]["x"] + ROOM_WIDTH - 70,
            "y": self.rooms[2]["y"] + ROOM_HEIGHT // 2 - 40,
            "width": 60,
            "height": 80,
            "room": 2
        }
        
        ## Initialize the emotion system
        self.emotion_system.initialize(self)
    
    def generate_obstacles(self):
        ## Generate random obstacles for both rooms that don't block critical paths
        obstacles = {1: [], 2: []}
        
        for room_id in [1, 2]:
            ## Determine number of obstacles for this room
            num_obstacles = random.randint(MIN_OBSTACLES, MAX_OBSTACLES)
            
            ## Create safe zones for spawn points and door/exit
            safe_zones = []
            room = self.rooms[room_id]
            
            ## Safe zone for player spawn (room 1) or door entry (room 2)
            if room_id == 1:
                ## Player spawn area in room 1
                safe_zones.append((room["x"] + 100, room["y"] + 100, 150, 150))
            else:
                ## Door entry area in room 2
                safe_zones.append((room["x"], room["y"] + ROOM_HEIGHT // 2 - 100, 150, 200))
            
            ## Safe zone for exit in room 2 or door in room 1
            if room_id == 1:
                ## Door area in room 1
                safe_zones.append((room["x"] + ROOM_WIDTH - 150, room["y"] + ROOM_HEIGHT // 2 - 100, 150, 200))
            else:
                ## Exit area in room 2
                safe_zones.append((room["x"] + ROOM_WIDTH - 150, room["y"] + ROOM_HEIGHT // 2 - 100, 150, 200))
            
            ## Generate the obstacles
            for _ in range(num_obstacles):
                max_attempts = 50
                for attempt in range(max_attempts):
                    x = random.randint(room["x"] + OBSTACLE_SIZE, room["x"] + room["width"] - OBSTACLE_SIZE)
                    y = random.randint(room["y"] + OBSTACLE_SIZE, room["y"] + room["height"] - OBSTACLE_SIZE)
                    
                    ## Check if this position is in a safe zone
                    in_safe_zone = False
                    for safe_x, safe_y, safe_w, safe_h in safe_zones:
                        if (safe_x <= x <= safe_x + safe_w and 
                            safe_y <= y <= safe_y + safe_h):
                            in_safe_zone = True
                            break
                    
                    if not in_safe_zone:
                        ## Check if it overlaps with existing obstacles
                        overlapping = False
                        for obs_x, obs_y in obstacles[room_id]:
                            if math.sqrt((x - obs_x)**2 + (y - obs_y)**2) < OBSTACLE_SIZE * 1.5:
                                overlapping = True
                                break
                        
                        if not overlapping:
                            obstacles[room_id].append((x, y))
                            break
        
        return obstacles
    
    def get_valid_position(self, room_id):
        ## Get a valid position in the room that's not on an obstacle
        room = self.rooms[room_id]
        
        ## Try to find a valid position
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(room["x"] + 40, room["x"] + room["width"] - 40)
            y = random.randint(room["y"] + 40, room["y"] + room["height"] - 40)
            
            ## Check if position is too close to any obstacle
            too_close = False
            for obs_x, obs_y in self.obstacles[room_id]:
                if math.sqrt((x - obs_x)**2 + (y - obs_y)**2) < OBSTACLE_SIZE + 30:
                    too_close = True
                    break
            
            if not too_close:
                return (x, y)
        
        ## If we couldn't find a valid position, use a default position
        if room_id == 1:
            return (room["x"] + 150, room["y"] + 150)
        else:
            return (room["x"] + 150, room["y"] + 150)
    
    def is_valid_move(self, x, y, size):
        ## Check if a position is valid (not inside an obstacle)
        room_id = self.current_room
        
        for obs_x, obs_y in self.obstacles[room_id]:
            if math.sqrt((x - obs_x)**2 + (y - obs_y)**2) < (OBSTACLE_SIZE + size) / 2:
                return False
        
        return True
    
    def get_nearest_enemy_distance(self):
        min_distance = float('inf')
        for enemy in self.enemies:
            if enemy["room"] == self.current_room and enemy["alive"]:
                distance = math.sqrt((self.player["x"] - enemy["x"])**2 + (self.player["y"] - enemy["y"])**2)
                min_distance = min(min_distance, distance)
        return min_distance if min_distance != float('inf') else 1000
    
    def get_nearest_resource_distance(self):
        min_distance = float('inf')
        for resource in self.resources:
            if resource["room"] == self.current_room and not resource["collected"]:
                distance = math.sqrt((self.player["x"] - resource["x"])**2 + (self.player["y"] - resource["y"])**2)
                min_distance = min(min_distance, distance)
        return min_distance if min_distance != float('inf') else 1000
    
    def update_npc_emotion(self):
        self.npc["emotion_lagged"] = self.npc["emotion"]
        
        ## Use the emotion system to determine the next emotion
        self.npc["emotion"] = self.emotion_system.determine_emotion(
            self.player["health"],
            self.get_nearest_enemy_distance(),
            self.get_nearest_resource_distance(),
            self.lagged_player_action,
            self.current_room,
            self.player["x"],
            self.player["y"],
            self.npc["x"],
            self.npc["y"],
            self.player["resources_collected"],
            self.player["enemies_killed"],
            self.npc["emotion_lagged"],
            self.player["action"]
        )
        
        ## Set reaction based on emotion
        self.update_npc_reaction()
    
    def update_npc_reaction(self):
        ## Update NPC reaction based on its emotion --> decoupled system advantage
        if self.npc["emotion"] == NPCEmotion.ANTICIPATION:
            self.npc["reaction"] = NPCReaction.FOLLOW
        elif self.npc["emotion"] == NPCEmotion.HAPPINESS:
            self.npc["reaction"] = NPCReaction.NOTIFY_RESOURCE
        elif self.npc["emotion"] == NPCEmotion.FEAR:
            self.npc["reaction"] = NPCReaction.NOTIFY_DANGER
        elif self.npc["emotion"] == NPCEmotion.ANGER:
            self.npc["reaction"] = NPCReaction.ATTACK_ENEMY
        elif self.npc["emotion"] == NPCEmotion.SURPRISE:
            self.npc["reaction"] = NPCReaction.NOTIFY_SURPRISE
        elif self.npc["emotion"] == NPCEmotion.SADNESS:
            self.npc["reaction"] = NPCReaction.PROVIDE_HEALING
    
    def update_npc_position(self):
        IDEAL_DISTANCE = 60
        MIN_DISTANCE = 40
        
        ## Decrease attack cooldown
        if self.npc["attack_cooldown"] > 0:
            self.npc["attack_cooldown"] -= 1
        
        ## Save the current position
        old_x, old_y = self.npc["x"], self.npc["y"]
        moved = False
        
        if self.npc["reaction"] == NPCReaction.FOLLOW:
            dx = self.player["x"] - self.npc["x"]
            dy = self.player["y"] - self.npc["y"]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                dx /= distance
                dy /= distance
                
                ## Only move if sufficiently far from ideal position to prevent twitching 
                if distance > IDEAL_DISTANCE + 10:
                    speed_factor = 1.5
                    self.npc["x"] += dx * self.npc["speed"] * speed_factor
                    self.npc["y"] += dy * self.npc["speed"] * speed_factor
                    moved = True
                elif distance < MIN_DISTANCE:
                    speed_factor = -0.5
                    self.npc["x"] += dx * self.npc["speed"] * speed_factor
                    self.npc["y"] += dy * self.npc["speed"] * speed_factor
                    moved = True
                elif distance > IDEAL_DISTANCE:
                    ## Add a threshold to prevent minor glithcy movements
                    if distance > IDEAL_DISTANCE + 5:
                        speed_factor = 1.0
                        self.npc["x"] += dx * self.npc["speed"] * speed_factor
                        self.npc["y"] += dy * self.npc["speed"] * speed_factor
                        moved = True
        
        elif self.npc["reaction"] == NPCReaction.NOTIFY_RESOURCE or self.npc["reaction"] == NPCReaction.NOTIFY_DANGER:
            dx = self.player["x"] - self.npc["x"]
            dy = self.player["y"] - self.npc["y"]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > IDEAL_DISTANCE * 1.5:
                dx /= distance
                dy /= distance
                self.npc["x"] += dx * self.npc["speed"] * 1.2
                self.npc["y"] += dy * self.npc["speed"] * 1.2
                moved = True
        
        elif self.npc["reaction"] == NPCReaction.ATTACK_ENEMY:
            nearest_enemy = None
            min_distance = float('inf')
            
            for i, enemy in enumerate(self.enemies):
                if enemy["room"] == self.current_room and enemy["alive"]:
                    distance = math.sqrt((self.npc["x"] - enemy["x"])**2 + (self.npc["y"] - enemy["y"])**2)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_enemy = i
            
            if nearest_enemy is not None:
                if min_distance > ATTACK_RADIUS + 5:  # Added threshold
                    dx = self.enemies[nearest_enemy]["x"] - self.npc["x"]
                    dy = self.enemies[nearest_enemy]["y"] - self.npc["y"]
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        dx /= dist
                        dy /= dist
                        self.npc["x"] += dx * self.npc["speed"] * 1.2
                        self.npc["y"] += dy * self.npc["speed"] * 1.2
                        moved = True
                elif min_distance < ATTACK_RADIUS and self.npc["attack_cooldown"] == 0:
                    self.enemies[nearest_enemy]["health"] -= NPC_DAMAGE
                    self.npc["attack_cooldown"] = 30 
                    
                    ## Only kill enemy if health drops to zero or below
                    if self.enemies[nearest_enemy]["health"] <= 0:
                        self.enemies[nearest_enemy]["alive"] = False
                        self.player["enemies_killed"] += 1
                        self.enemies_killed += 1
                        if self.debug_mode:
                            print(f"NPC killed an enemy! Total: {self.player['enemies_killed']}/8")
        
        elif self.npc["reaction"] == NPCReaction.PROVIDE_HEALING:
            dx = self.player["x"] - self.npc["x"]
            dy = self.player["y"] - self.npc["y"]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > ATTACK_RADIUS + 5: 
                dx /= distance
                dy /= distance
                self.npc["x"] += dx * self.npc["speed"] * 1.5
                self.npc["y"] += dy * self.npc["speed"] * 1.5
                moved = True
            else:
                healing_amount = 10
                old_health = self.player["health"]
                self.player["health"] = min(self.player["health"] + healing_amount, 100)
        
        ## Check if NPC's new position is valid
        if not self.is_valid_move(self.npc["x"], self.npc["y"], NPC_SIZE):
            ## If not valid, revert to old position
            self.npc["x"], self.npc["y"] = old_x, old_y
        
        ## Keep NPC in the current room
        current_room = self.rooms[self.current_room]
        self.npc["x"] = max(current_room["x"] + NPC_SIZE//2, min(self.npc["x"], current_room["x"] + current_room["width"] - NPC_SIZE//2))
        self.npc["y"] = max(current_room["y"] + NPC_SIZE//2, min(self.npc["y"], current_room["y"] + current_room["height"] - NPC_SIZE//2))
        
        ## Round the NPC position to prevent sub-pixel rendering which can cause twitching
        if not moved:
            self.npc["x"] = round(self.npc["x"])
            self.npc["y"] = round(self.npc["y"])
    
    def update_enemies(self):
        for enemy in self.enemies:
            if enemy["room"] == self.current_room and enemy["alive"]:
                ## Save current position
                old_x, old_y = enemy["x"], enemy["y"]
                
                ## Random movement --> reduced to make enemies less erratic
                enemy["x"] += random.uniform(-enemy["speed"] * 0.5, enemy["speed"] * 0.5)
                enemy["y"] += random.uniform(-enemy["speed"] * 0.5, enemy["speed"] * 0.5)
                
                ## enemies chase player if within detection radius
                player_distance = math.sqrt((self.player["x"] - enemy["x"])**2 + (self.player["y"] - enemy["y"])**2)
                if player_distance < ENEMY_DETECTION_RADIUS:
                    ## Calculate direct path to player
                    dx = self.player["x"] - enemy["x"]
                    dy = self.player["y"] - enemy["y"]
                    if player_distance > 0:
                        dx /= player_distance
                        dy /= player_distance
                        
                        ## Try direct movement first
                        new_x = enemy["x"] + dx * enemy["speed"]
                        new_y = enemy["y"] + dy * enemy["speed"]
                        
                        ## Check if direct path is blocked
                        if not self.is_valid_move(new_x, new_y, ENEMY_SIZE):
                            ## Try horizontal movement only
                            new_x = enemy["x"] + dx * enemy["speed"]
                            new_y = enemy["y"]
                            
                            ## If still blocked, try vertical movement only
                            if not self.is_valid_move(new_x, new_y, ENEMY_SIZE):
                                new_x = enemy["x"]
                                new_y = enemy["y"] + dy * enemy["speed"]
                                
                                ## If still blocked, try a random direction to avoid getting stuck
                                if not self.is_valid_move(new_x, new_y, ENEMY_SIZE) and random.random() < 0.3:
                                    angle = random.uniform(0, 2 * math.pi)
                                    new_x = enemy["x"] + math.cos(angle) * enemy["speed"]
                                    new_y = enemy["y"] + math.sin(angle) * enemy["speed"]
                            
                        ## Update position if possible
                        if self.is_valid_move(new_x, new_y, ENEMY_SIZE):
                            enemy["x"], enemy["y"] = new_x, new_y
                
                ## Check if the enemy's final position is valid
                if not self.is_valid_move(enemy["x"], enemy["y"], ENEMY_SIZE):
                    ## If not valid, revert to old position
                    enemy["x"], enemy["y"] = old_x, old_y
                
                ## Keep within room boundaries
                enemy["x"] = max(self.rooms[self.current_room]["x"] + ENEMY_SIZE//2, 
                               min(enemy["x"], self.rooms[self.current_room]["x"] + self.rooms[self.current_room]["width"] - ENEMY_SIZE//2))
                enemy["y"] = max(self.rooms[self.current_room]["y"] + ENEMY_SIZE//2, 
                               min(enemy["y"], self.rooms[self.current_room]["y"] + self.rooms[self.current_room]["height"] - ENEMY_SIZE//2))
                
                ## Damage player if close enough
                if player_distance < ATTACK_RADIUS:
                    self.player["health"] -= ENEMY_DAMAGE / FPS
                    self.player["health"] = max(0, self.player["health"])
                    if self.player["health"] <= 0:
                        print("You were defeated by an enemy!")
    
    def check_resource_collection(self):
        for resource in self.resources:
            if (resource["room"] == self.current_room and not resource["collected"] and
                math.sqrt((self.player["x"] - resource["x"])**2 + (self.player["y"] - resource["y"])**2) < ATTACK_RADIUS):
                resource["collected"] = True
                self.player["resources_collected"] += 1
                self.resources_collected += 1
                self.player["health"] = min(self.player["health"] + RESOURCE_HEAL, 100)
                
                ## Open door in room 1 if 2 resources collected (minimum requirement)
                if self.resources_collected >= 2 and not self.door["open"]:
                    self.door["open"] = True
                    ## Add door unlock effect that persists until door is used
                    self.door_unlock_effect = True
                    self.door_unlock_timer = -1  ## -1 indicates persist until door is used
                    if self.debug_mode:
                        print(f"Door opened! Collected {self.resources_collected} resources.")
    
    def is_player_at_door(self):
        ## Dedicated function to handle door detection and player interaction
        ## Player center position
        player_center_x = self.player["x"]
        player_center_y = self.player["y"]
        
        ## Door center and dimensions
        door_center_x = self.door["x"] + self.door["width"] / 2
        door_center_y = self.door["y"] + self.door["height"] / 2
        
        ## Check if player is close to the center of the door (horizontally and vertically)
        dx = abs(player_center_x - door_center_x)
        dy = abs(player_center_y - door_center_y)
        
        ## Only consider the player at the door if they're close to the center horizontally and within the vertical span of the door
        door_x_threshold = self.door["width"] / 2 + PLAYER_SIZE / 2
        door_y_threshold = self.door["height"] / 2 + PLAYER_SIZE / 2
        
        return dx < door_x_threshold and dy < door_y_threshold
    
    def check_door_interaction(self):
        ## Check if player is at door using improved detection
        if self.is_player_at_door():
            current_time = self.pygame.time.get_ticks()
            
            ## Only allow room transitions after cooldown has passed
            if current_time - self.last_room_transition > self.room_transition_cooldown:
                if self.door["open"]:
                    ## Turn off the door unlock effect when player uses the door
                    if hasattr(self, 'door_unlock_effect') and self.door_unlock_effect:
                        self.door_unlock_effect = False
                    
                    ## Change rooms
                    if self.current_room == 1:
                        if self.debug_mode:
                            print("Transitioning to Room 2")
                        self.current_room = 2
                        ## Position the player on the left side of room 2
                        self.player["x"] = self.rooms[2]["x"] + 50
                        self.player["y"] = self.rooms[2]["y"] + ROOM_HEIGHT/2
                        ## Position NPC near the player
                        self.npc["x"] = self.player["x"] - 30
                        self.npc["y"] = self.player["y"]
                        self.last_room_transition = current_time
                    else:
                        if self.debug_mode:
                            print("Transitioning to Room 1")
                        self.current_room = 1
                        ## Position the player on the right side of room 1
                        self.player["x"] = self.rooms[1]["x"] + ROOM_WIDTH - 50
                        self.player["y"] = self.rooms[1]["y"] + ROOM_HEIGHT/2
                        ## Position NPC near the player
                        self.npc["x"] = self.player["x"] - 30
                        self.npc["y"] = self.player["y"]
                        self.last_room_transition = current_time
                else:
                    ## Indicate the door is locked
                    if self.debug_mode:
                        print("Door is locked. Collect more resources!")
                    ## Push player away from closed door
                    if self.player["x"] < self.door["x"]:
                        self.player["x"] -= 10
                    else:
                        self.player["x"] += 10
    
    def check_exit_interaction(self):
        if self.current_room == 2:
            player_rect = self.pygame.Rect(self.player["x"] - PLAYER_SIZE/2, self.player["y"] - PLAYER_SIZE/2, PLAYER_SIZE, PLAYER_SIZE)
            exit_rect = self.pygame.Rect(self.exit["x"], self.exit["y"], self.exit["width"], self.exit["height"])
            
            if player_rect.colliderect(exit_rect):
                if self.player["enemies_killed"] >= 8 and self.player["resources_collected"] >= 4:
                    self.state = GameState.COMPLETED
                    if self.debug_mode:
                        print("Congratulations! You've completed the game!")
                else:
                    ## Give feedback on what's missing
                    missing_resources = max(0, 4 - self.player["resources_collected"])
                    missing_enemies = max(0, 5 - self.player["enemies_killed"])
                    
                    if self.debug_mode:
                        if missing_resources > 0 and missing_enemies > 0:
                            print(f"You need {missing_resources} more resources and {missing_enemies} more enemies defeated!")
                        elif missing_resources > 0:
                            print(f"You need {missing_resources} more resources!")
                        elif missing_enemies > 0:
                            print(f"You need to defeat {missing_enemies} more enemies!")
    
    def check_attack(self):
        if self.player["action"] == PlayerAction.ATTACK:
            for i, enemy in enumerate(self.enemies):
                if enemy["room"] == self.current_room and enemy["alive"]:
                    if math.sqrt((self.player["x"] - enemy["x"])**2 + (self.player["y"] - enemy["y"])**2) < ATTACK_RADIUS:
                        ## Player does high damage to guarantee one-hit kills
                        enemy["health"] -= PLAYER_DAMAGE
                        
                        if enemy["health"] <= 0:
                            enemy["alive"] = False
                            self.player["enemies_killed"] += 1
                            self.enemies_killed += 1
                            if self.debug_mode:
                                print(f"Player killed enemy! Total: {self.player['enemies_killed']}/8")
    
    def handle_start_screen_events(self):
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                ## Removed ability to quit
                pass
            elif event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_ESCAPE:
                    ## Removed ability to quit
                    pass
                elif event.key == self.pygame.K_RETURN or event.key == self.pygame.K_SPACE:
                    self.state = GameState.PLAYING
                ## Debug mode toggle
                elif event.key == self.pygame.K_d and self.pygame.key.get_mods() & self.pygame.KMOD_CTRL:
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
    
    
    def handle_completed_screen_events(self):
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                ## Enable ability to quit when in completed state for all three games
                self.running = False
            elif event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_ESCAPE:
                    ## Enable ability to quit when in completed state
                    self.running = False
                elif event.key == self.pygame.K_r:
                    ## Removed ability to restart
                    pass
    
    def handle_playing_events(self):
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                ## Removed ability to quit
                pass
            elif event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_ESCAPE:
                    ## Removed ability to quit
                    pass
                elif event.key == self.pygame.K_r:
                    ## Removed ability to restart
                    pass
                elif event.key == self.pygame.K_SPACE:
                    self.player["action"] = PlayerAction.ATTACK
                    self.check_attack()
                ## Debug mode toggle
                elif event.key == self.pygame.K_d and self.pygame.key.get_mods() & self.pygame.KMOD_CTRL:
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
                ## Debug keys in debug mode
                elif self.debug_mode and event.key == self.pygame.K_o:
                    self.door["open"] = True
                    print("DEBUG: Door opened")
                elif self.debug_mode and event.key == self.pygame.K_1:
                    self.current_room = 1
                    self.player["x"] = self.rooms[1]["x"] + ROOM_WIDTH // 2
                    self.player["y"] = self.rooms[1]["y"] + ROOM_HEIGHT // 2
                    print("DEBUG: Moved to room 1")
                elif self.debug_mode and event.key == self.pygame.K_2:
                    self.current_room = 2
                    self.player["x"] = self.rooms[2]["x"] + ROOM_WIDTH // 2
                    self.player["y"] = self.rooms[2]["y"] + ROOM_HEIGHT // 2
                    print("DEBUG: Moved to room 2")
            elif event.type == self.pygame.KEYUP:
                if event.key == self.pygame.K_SPACE:
                    ## Only change from attack if space is released
                    if self.player["action"] == PlayerAction.ATTACK:
                        self.player["action"] = PlayerAction.IDLE
        
        ## Handle continuous key presses
        keys = self.pygame.key.get_pressed()
        old_x, old_y = self.player["x"], self.player["y"]
        moved = False
        
        if keys[self.pygame.K_w] or keys[self.pygame.K_UP]:
            self.player["y"] -= self.player["speed"]
            moved = True
        if keys[self.pygame.K_s] or keys[self.pygame.K_DOWN]:
            self.player["y"] += self.player["speed"]
            moved = True
        if keys[self.pygame.K_a] or keys[self.pygame.K_LEFT]:
            self.player["x"] -= self.player["speed"]
            moved = True
        if keys[self.pygame.K_d] or keys[self.pygame.K_RIGHT]:
            self.player["x"] += self.player["speed"]
            moved = True
        
        ## Update player action state
        if moved and self.player["action"] != PlayerAction.ATTACK:
            self.player["action"] = PlayerAction.MOVE
        elif not moved and self.player["action"] != PlayerAction.ATTACK:
            self.player["action"] = PlayerAction.IDLE
        
        ## Check if player's new position is valid (not inside an obstacle)
        if not self.is_valid_move(self.player["x"], self.player["y"], PLAYER_SIZE):
            # If not valid, revert to old position
            self.player["x"], self.player["y"] = old_x, old_y
        
        ## Special door handling - check if player is trying to go through the door
        at_door = self.is_player_at_door()
        
        if at_door and self.door["open"]:
            ## If at an open door, check for door interaction immediately
            self.check_door_interaction()
        else:
            ## Normal boundary checking - only if we're not going through the door
            current_room = self.rooms[self.current_room]
            self.player["x"] = max(current_room["x"] + PLAYER_SIZE//2, 
                                 min(self.player["x"], current_room["x"] + current_room["width"] - PLAYER_SIZE//2))
            self.player["y"] = max(current_room["y"] + PLAYER_SIZE//2, 
                                 min(self.player["y"], current_room["y"] + current_room["height"] - PLAYER_SIZE//2))
    
    def draw_start_screen(self):
        self.screen.fill(BLACK)
        
        ## Draw pixel art title with necessary information
        emotion_type = self.emotion_system.get_system_type().name.replace('_', ' ').title()
        title_text = self.large_font.render(f"NPC EMOTION GAME!", True, PIXEL_YELLOW)
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//4))
        shadow_rect = title_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        
        ## Draw shadow first then text
        shadow_text = self.large_font.render(f"NPC EMOTION GAME!", True, PIXEL_DARK_GRAY)
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        ## Get condition-specific description
        description = self.emotion_system.get_description()
        
        instructions = [
            "You are an explorer in a dungeon, accompanied by an NPC companion.",
            description,
            "",
            "OBJECTIVES:",
            "• Collect all 4 resources (yellow squares)",
            "• Defeat 8 enemies (red circles)",
            "• Collect 2 resources in Room 1 to open the door",
            "• Reach the exit in Room 2 after completing all objectives",
            "",
            "CONTROLS:",
            "WASD or Arrow Keys: Move",
            "SPACE: Attack (must be close to enemy)",
            "",
            "Press ENTER or SPACE to start"
        ]
        
        y_pos = HEIGHT//3
        for instruction in instructions:
            if instruction.startswith("OBJECTIVES:") or instruction.startswith("CONTROLS:"):
                text = self.font.render(instruction, True, PIXEL_YELLOW)
                y_pos += 10
            elif instruction == "":
                y_pos += 15
            else:
                text = self.small_font.render(instruction, True, WHITE)
            
            if instruction != "":
                text_rect = text.get_rect(center=(WIDTH//2, y_pos))
                self.screen.blit(text, text_rect)
            
            y_pos += 30
        
        ## Show participant ID 
        if self.participant_id:
            id_text = self.small_font.render(f"Participant ID: {self.participant_id}", True, WHITE)
            id_rect = id_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
            self.screen.blit(id_text, id_rect)
        
            ## Only show condition if debug info is enabled
            if hasattr(self, 'show_debug_info') and self.show_debug_info:
                condition_text = self.small_font.render(f"Condition: {self.condition}", True, WHITE)
                condition_rect = condition_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 45))
                self.screen.blit(condition_text, condition_rect)
        
        self.pygame.display.flip()
    
    def draw_completed_screen(self):
        self.screen.fill(BLACK)
        
        ## Pixel art completion text
        completion_text = self.large_font.render("CONGRATULATIONS!", True, PIXEL_GREEN)
        completion_rect = completion_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        shadow_rect = completion_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        
        shadow_text = self.large_font.render("CONGRATULATIONS!", True, PIXEL_DARK_GRAY)
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(completion_text, completion_rect)
        
        message_text = self.font.render("You've successfully completed the game!", True, WHITE)
        message_rect = message_text.get_rect(center=(WIDTH//2, HEIGHT//3 + 60))
        self.screen.blit(message_text, message_rect)
        
        stats = [
            f"Resources Collected: {self.player['resources_collected']}/4",
            f"Enemies Defeated: {self.player['enemies_killed']}/8",
            f"Final Health: {int(self.player['health'])}/100"
        ]
        
        y_pos = HEIGHT//2
        for stat in stats:
            text = self.font.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH//2, y_pos))
            self.screen.blit(text, text_rect)
            y_pos += 40
        
        ## Show instructions to return to QUualtrics
        if self.participant_id:
            continue_text = self.font.render("Please press esc or close the game and return to the survey to continue", True, PIXEL_YELLOW)
            continue_rect = continue_text.get_rect(center=(WIDTH//2, HEIGHT - 100))
            self.screen.blit(continue_text, continue_rect)
            
            # Show participant ID and condition (only if debug info is enabled)
            id_text = self.small_font.render(f"Participant ID: {self.participant_id}", True, WHITE)
            id_rect = id_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
            self.screen.blit(id_text, id_rect)
            
            ## Only show condition if debug info is enabled
            if hasattr(self, 'show_debug_info') and self.show_debug_info:
                condition_text = self.small_font.render(f"Condition: {self.condition}", True, WHITE)
                condition_rect = condition_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 45))
                self.screen.blit(condition_text, condition_rect)
        else:
            
            restart_text = self.font.render("Press R to play again or ESC to quit", True, PIXEL_YELLOW)
            restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT - 100))
            self.screen.blit(restart_text, restart_rect)
        
        self.pygame.display.flip()
    
    def draw_game(self):
        self.screen.fill(BLACK)
        
        ## Draw rooms with pixel art styling
        for room_id, room in self.rooms.items():
            if room_id == self.current_room:
                ## Draw floor for current room
                floor_rect = self.pygame.Rect(room["x"], room["y"], room["width"], room["height"])
                self.draw_pixel_rect(self.screen, PIXEL_FLOOR, floor_rect)
                
                ## Draw walls with pixel art style
                wall_thickness = 8
                
                ## Top wall
                top_wall = self.pygame.Rect(room["x"], room["y"], room["width"], wall_thickness)
                self.draw_pixel_rect(self.screen, PIXEL_WALL, top_wall)
                
                ## Bottom wall
                bottom_wall = self.pygame.Rect(room["x"], room["y"] + room["height"] - wall_thickness, 
                                        room["width"], wall_thickness)
                self.draw_pixel_rect(self.screen, PIXEL_WALL, bottom_wall)
                
                ## Left wall
                left_wall = self.pygame.Rect(room["x"], room["y"], wall_thickness, room["height"])
                self.draw_pixel_rect(self.screen, PIXEL_WALL, left_wall)
                
                ## Right wall
                right_wall = self.pygame.Rect(room["x"] + room["width"] - wall_thickness, room["y"], 
                                       wall_thickness, room["height"])
                self.draw_pixel_rect(self.screen, PIXEL_WALL, right_wall)
            else:
                ## Draw outline for non-current room
                self.pygame.draw.rect(self.screen, PIXEL_DARK_GRAY, 
                               (room["x"], room["y"], room["width"], room["height"]), 3)
        
        if self.current_room == 1 or self.current_room == 2:
            room = self.rooms[self.current_room]
            
            ## Draw obstacles in the current room
            for obs_x, obs_y in self.obstacles[self.current_room]:
                obstacle_rect = self.pygame.Rect(obs_x - OBSTACLE_SIZE//2, obs_y - OBSTACLE_SIZE//2, 
                                          OBSTACLE_SIZE, OBSTACLE_SIZE)
                self.draw_pixel_rect(self.screen, PIXEL_OBSTACLE, obstacle_rect, border_radius=3)
            
            ## Draw resources
            for resource in self.resources:
                if resource["room"] == self.current_room and not resource["collected"]:
                    resource_rect = self.pygame.Rect(resource["x"] - RESOURCE_SIZE/2, 
                                             resource["y"] - RESOURCE_SIZE/2, 
                                             RESOURCE_SIZE, RESOURCE_SIZE)
                    self.draw_pixel_rect(self.screen, PIXEL_YELLOW, resource_rect)
            
            ## Draw enemies
            for enemy in self.enemies:
                if enemy["room"] == self.current_room and enemy["alive"]:
                    self.draw_pixel_circle(self.screen, PIXEL_RED, 
                                    (int(enemy["x"]), int(enemy["y"])), 
                                    ENEMY_SIZE//2)
                    
                    ## Draw health bar for enemies in debug mode
                    if self.debug_mode:
                        health_width = ENEMY_SIZE * (enemy["health"] / 100)
                        self.pygame.draw.rect(self.screen, RED, 
                                        (int(enemy["x"] - ENEMY_SIZE/2), 
                                         int(enemy["y"] - ENEMY_SIZE/2 - 8), 
                                         ENEMY_SIZE, 5))
                        self.pygame.draw.rect(self.screen, GREEN, 
                                        (int(enemy["x"] - ENEMY_SIZE/2), 
                                         int(enemy["y"] - ENEMY_SIZE/2 - 8), 
                                         health_width, 5))
            
            ## Draw exit in room 2
            if self.current_room == 2:
                ## Draw exit with frame and glow effect
                exit_rect = self.pygame.Rect(self.exit["x"], self.exit["y"], 
                                      self.exit["width"], self.exit["height"])
                
                ## Draw a subtle glow/halo effect around the exit
                for i in range(3):
                    glow_rect = self.pygame.Rect(
                        self.exit["x"] - i*2, 
                        self.exit["y"] - i*2,
                        self.exit["width"] + i*4, 
                        self.exit["height"] + i*4
                    )
                    glow_color = (min(255, PIXEL_GREEN[0] + 20), 
                                min(255, PIXEL_GREEN[1] + 20), 
                                min(255, PIXEL_GREEN[2] + 20), 
                                100 - i*30) 
                    
                    s = self.pygame.Surface((glow_rect.width, glow_rect.height), self.pygame.SRCALPHA)
                    self.pygame.draw.rect(s, glow_color, (0, 0, glow_rect.width, glow_rect.height))
                    self.screen.blit(s, (glow_rect.x, glow_rect.y))
                
                ## Draw the actual exit
                self.draw_pixel_rect(self.screen, PIXEL_GREEN, exit_rect)
                
                ## Add "EXIT" text
                exit_text = self.small_font.render("EXIT", True, BLACK)
                exit_text_rect = exit_text.get_rect(center=(
                    self.exit["x"] + self.exit["width"]//2,
                    self.exit["y"] + self.exit["height"]//2
                ))
                self.screen.blit(exit_text, exit_text_rect)
            
            ## Draw player and NPC with pixel art style
            self.draw_pixel_circle(self.screen, PIXEL_BLUE, 
                            (int(self.player["x"]), int(self.player["y"])), 
                            PLAYER_SIZE//2)
            
            self.draw_pixel_circle(self.screen, PIXEL_GREEN, 
                            (int(self.npc["x"]), int(self.npc["y"])), 
                            NPC_SIZE//2)
            
            ## Room-specific emotion symbols for ML condition
            if self.emotion_system.get_system_type() == EmotionSystem.MACHINE_LEARNING:
                if self.current_room == 1:
                    emotion_symbols = {
                        NPCEmotion.ANTICIPATION: "...",
                        NPCEmotion.HAPPINESS: ":)",
                        NPCEmotion.FEAR: "!!",
                        NPCEmotion.ANGER: "!!",
                        NPCEmotion.SURPRISE: "?!",
                        NPCEmotion.SADNESS: ":("
                    }
                else:  # Room 2
                    emotion_symbols = {
                        NPCEmotion.ANTICIPATION: "..?",
                        NPCEmotion.HAPPINESS: ":D",
                        NPCEmotion.FEAR: "??",
                        NPCEmotion.ANGER: ">:(",
                        NPCEmotion.SURPRISE: ":O",
                        NPCEmotion.SADNESS: ":'("
                    }
            else:
                ## Standard emotion symbols for non-ML conditions
                emotion_symbols = {
                    NPCEmotion.ANTICIPATION: "...",
                    NPCEmotion.HAPPINESS: ":)",
                    NPCEmotion.FEAR: "!!",
                    NPCEmotion.ANGER: "!!",
                    NPCEmotion.SURPRISE: "?!",
                    NPCEmotion.SADNESS: ":("
                }
            
            emotion_color = {
                NPCEmotion.ANTICIPATION: PIXEL_YELLOW,
                NPCEmotion.HAPPINESS: PIXEL_GREEN,
                NPCEmotion.FEAR: WHITE,
                NPCEmotion.ANGER: PIXEL_RED,
                NPCEmotion.SURPRISE: PIXEL_PURPLE,
                NPCEmotion.SADNESS: PIXEL_BLUE
            }
            
            ## Draw emotion bubble with pixel art style
            bubble_radius = 20
            self.pygame.draw.circle(self.screen, WHITE, 
                             (int(self.npc["x"]), int(self.npc["y"] - 35)), 
                             bubble_radius)
            self.pygame.draw.circle(self.screen, PIXEL_GRAY, 
                             (int(self.npc["x"]), int(self.npc["y"] - 35)), 
                             bubble_radius, 1)
            
            emotion_text = self.small_font.render(emotion_symbols[self.npc["emotion"]], True, emotion_color[self.npc["emotion"]])
            emotion_rect = emotion_text.get_rect(center=(int(self.npc["x"]), int(self.npc["y"] - 35)))
            self.screen.blit(emotion_text, emotion_rect)
            
            ## Room-specific reaction visuals for ML condition
            if self.emotion_system.get_system_type() == EmotionSystem.MACHINE_LEARNING:
                ## Draw NPC reactions with room-specific styles
                if self.npc["reaction"] == NPCReaction.NOTIFY_RESOURCE:
                    nearest_resource = None
                    min_distance = float('inf')
                    for resource in self.resources:
                        if resource["room"] == self.current_room and not resource["collected"]:
                            distance = math.sqrt((self.npc["x"] - resource["x"])**2 + (self.npc["y"] - resource["y"])**2)
                            if distance < min_distance:
                                min_distance = distance
                                nearest_resource = resource
                    if nearest_resource:
                        ## Use simple line for both rooms
                        self.pygame.draw.line(self.screen, PIXEL_YELLOW, 
                                    (int(self.npc["x"]), int(self.npc["y"])),
                                    (int(nearest_resource["x"]), int(nearest_resource["y"])),
                                    2)
                
                elif self.npc["reaction"] == NPCReaction.NOTIFY_DANGER:
                    ## Simple text for both rooms
                    danger_text = self.small_font.render("DANGER", True, PIXEL_RED)
                    self.screen.blit(danger_text, (int(self.npc["x"]) + 20, int(self.npc["y"]) - 15))
                
                elif self.npc["reaction"] == NPCReaction.ATTACK_ENEMY:
                    ## Simple red circle for both rooms
                    self.pygame.draw.circle(self.screen, PIXEL_RED, 
                                    (int(self.npc["x"]), int(self.npc["y"])),
                                    NPC_SIZE, 2)
                
                elif self.npc["reaction"] == NPCReaction.PROVIDE_HEALING:
                    ## Simple green circle for both rooms
                    self.pygame.draw.circle(self.screen, PIXEL_GREEN, 
                                    (int(self.npc["x"]), int(self.npc["y"])),
                                    NPC_SIZE + 5, 2)
            else:
                ## Standard reaction visuals for non-ML conditions
                if self.npc["reaction"] == NPCReaction.NOTIFY_RESOURCE:
                    nearest_resource = None
                    min_distance = float('inf')
                    for resource in self.resources:
                        if resource["room"] == self.current_room and not resource["collected"]:
                            distance = math.sqrt((self.npc["x"] - resource["x"])**2 + (self.npc["y"] - resource["y"])**2)
                            if distance < min_distance:
                                min_distance = distance
                                nearest_resource = resource
                    if nearest_resource:
                        self.pygame.draw.line(self.screen, PIXEL_YELLOW, 
                                    (int(self.npc["x"]), int(self.npc["y"])),
                                    (int(nearest_resource["x"]), int(nearest_resource["y"])),
                                    2)
                
                elif self.npc["reaction"] == NPCReaction.NOTIFY_DANGER:
                    danger_text = self.small_font.render("DANGER", True, PIXEL_RED)
                    self.screen.blit(danger_text, (int(self.npc["x"]) + 20, int(self.npc["y"]) - 15))
                
                elif self.npc["reaction"] == NPCReaction.ATTACK_ENEMY:
                    self.pygame.draw.circle(self.screen, PIXEL_RED, 
                                    (int(self.npc["x"]), int(self.npc["y"])),
                                    NPC_SIZE, 2)
                
                elif self.npc["reaction"] == NPCReaction.PROVIDE_HEALING:
                    self.pygame.draw.circle(self.screen, PIXEL_GREEN, 
                                    (int(self.npc["x"]), int(self.npc["y"])),
                                    NPC_SIZE + 5, 2)
        
        ## Draw door with pixel art style
        door_color = PIXEL_GREEN if self.door["open"] else PIXEL_RED
        door_rect = self.pygame.Rect(self.door["x"], self.door["y"], 
                              self.door["width"], self.door["height"])
        
        ## Door unlock effect - persists until player uses the door
        if hasattr(self, 'door_unlock_effect') and self.door_unlock_effect:
            ## Create a pulsing/glowing effect around the door
            glow_size = 10 + int(5 * math.sin(self.frame * 0.2))
            glow_rect = self.pygame.Rect(
                door_rect.x - glow_size, 
                door_rect.y - glow_size,
                door_rect.width + glow_size*2, 
                door_rect.height + glow_size*2
            )
            
            ## Create a semi-transparent surface for the glow
            s = self.pygame.Surface((glow_rect.width, glow_rect.height), self.pygame.SRCALPHA)
            glow_color = (PIXEL_GREEN[0], PIXEL_GREEN[1], PIXEL_GREEN[2], 150)  # Semi-transparent green
            self.pygame.draw.rect(s, glow_color, (0, 0, glow_rect.width, glow_rect.height), border_radius=5)
            self.screen.blit(s, (glow_rect.x, glow_rect.y))
        
            if self.door_unlock_timer > 0:
                self.door_unlock_timer -= 1
                if self.door_unlock_timer <= 0:
                    self.door_unlock_effect = False
        
        ## Draw the door
        self.draw_pixel_rect(self.screen, door_color, door_rect)
        self.draw_pixel_rect(self.screen, PIXEL_DOOR, door_rect, 3)  # Door frame
        
        ## Add text indicator
        door_text = self.small_font.render("DOOR", True, BLACK)
        door_text_rect = door_text.get_rect(center=(
            self.door["x"] + self.door["width"]//2,
            self.door["y"] + self.door["height"]//2
        ))
        self.screen.blit(door_text, door_text_rect)
        
        ## Draw UI elements with pixel art styling
        ## Health bar
        health_border = self.pygame.Rect(20, 20, 200, 30)
        health_fill = self.pygame.Rect(20, 20, int(self.player["health"] * 2), 30)
        
        ## Draw health bar background and fill
        self.draw_pixel_rect(self.screen, PIXEL_RED, health_border)
        self.draw_pixel_rect(self.screen, PIXEL_GREEN, health_fill)
        
        health_text = self.font.render(f"Health: {int(self.player['health'])}", True, WHITE)
        self.screen.blit(health_text, (25, 25))
        
        ## Room indicator
        room_text = self.font.render(f"Room {self.current_room}", True, WHITE)
        self.screen.blit(room_text, (WIDTH - 120, 25))
        
        ## Draw progress indicators at the top right
        resources_text = self.small_font.render(f"Resources: {self.player['resources_collected']}/4", True, PIXEL_YELLOW)
        self.screen.blit(resources_text, (WIDTH - 200, 60))
        
        enemies_text = self.small_font.render(f"Enemies: {self.player['enemies_killed']}/8", True, PIXEL_RED)
        self.screen.blit(enemies_text, (WIDTH - 200, 85))
        
        ## Draw door status indicator
        door_status = "OPEN" if self.door["open"] else "LOCKED"
        door_color = PIXEL_GREEN if self.door["open"] else PIXEL_RED
        door_text = self.small_font.render(f"Door: {door_status}", True, door_color)
        self.screen.blit(door_text, (WIDTH // 2 - 40, 25))
        
        ## Draw timer (if enabled)
        if hasattr(self, 'game_time_limit') and self.game_time_limit > 0:
            seconds_left = max(0, self.game_time_limit - (self.frame / FPS))
            minutes = int(seconds_left // 60)
            seconds = int(seconds_left % 60)
            timer_text = self.small_font.render(f"Time: {minutes}:{seconds:02d}", True, WHITE)
            self.screen.blit(timer_text, (WIDTH - 120, 115))
            
        ## Draw emotion and reaction info if debug info is enabled
        if self.show_debug_info:
            emotion_debug_text = self.small_font.render(f"Emotion: {self.npc['emotion'].value}", True, WHITE)
            reaction_debug_text = self.small_font.render(f"Reaction: {self.npc['reaction'].value}", True, WHITE)
            self.screen.blit(emotion_debug_text, (25, 120))
            self.screen.blit(reaction_debug_text, (25, 145))
        
        ## Show participant ID
        if self.participant_id:
            id_text = self.small_font.render(f"Participant ID: {self.participant_id}", True, WHITE)
            id_rect = id_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
            self.screen.blit(id_text, id_rect)
            
            ## Only show condition if debug info is enabled
            if hasattr(self, 'show_debug_info') and self.show_debug_info:
                condition_text = self.small_font.render(f"Condition: {self.condition}", True, WHITE)
                condition_rect = condition_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 45))
                self.screen.blit(condition_text, condition_rect)
        
        ## Update display
        self.pygame.display.flip()
    
    def update(self):
        if self.state == GameState.START_SCREEN:
            self.handle_start_screen_events()
            self.draw_start_screen()
        elif self.state == GameState.COMPLETED:
            self.handle_completed_screen_events()
            self.draw_completed_screen()
        elif self.state == GameState.PLAYING:
            ## Increment frame counter
            self.frame += 1
            
            ## Save the previous action for the emotion prediction
            self.lagged_player_action = self.player["action"]
            
            ## Handle user input
            self.handle_playing_events()
            
            ## Update game state
            self.update_npc_emotion()
            self.update_npc_position()
            self.update_enemies()
            self.check_resource_collection()
            self.check_exit_interaction()
            
            # Draw the game
            self.draw_game()
            
            ## Check game over conditions
            if self.player["health"] <= 0:
                if self.debug_mode:
                    print("Game over! Player died.")
                self.reset()
                
            ## Check time limit if enabled
            if hasattr(self, 'game_time_limit') and self.game_time_limit > 0:
                if self.frame >= self.game_time_limit * FPS:
                    if self.debug_mode:
                        print("Time's up!")
                    self.state = GameState.COMPLETED
    
    def run(self):
        ## Main game run
        emotion_system_type = self.emotion_system.get_system_type().name.replace('_', ' ').title()
        print(f"Game started! {emotion_system_type} NPC emotions with Pixel Art style")
        
        ## Main game loop
        while self.running:
            self.clock.tick(FPS)
            self.update()
        
        ## Before closing, gather and return game data if in a study
        if self.participant_id:
            ## Return game data for the study
            return {
                'participant_id': self.participant_id,
                'condition': self.condition,
                'resources_collected': self.player['resources_collected'],
                'enemies_killed': self.player['enemies_killed'],
                'health': int(self.player['health']),
                'completed': self.state == GameState.COMPLETED,
                'play_time': self.frame / FPS, 
            }
        
        self.pygame.quit()