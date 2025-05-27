from game_engine import EmotionSystem, NPCEmotion

## Emotion system choice
class BaseEmotionSystem:
    def __init__(self):
        pass
    
    def initialize(self, game_instance):
        ## Initialize emotion system with game instance
        self.game = game_instance
    
    def determine_emotion(self, player_health, enemy_proximity, resource_proximity,
                         lagged_player_action, level, player_x, player_y, npc_x, npc_y,
                         resources_collected, enemies_killed, npc_emotion_lagged, current_player_action):
        ## etermine NPC emotion based on game state - must be implemented by subclasses
        raise NotImplementedError
    
    def get_system_type(self):
        ## Return the type of emotion system
        raise NotImplementedError
    
    def get_description(self):
        raise NotImplementedError