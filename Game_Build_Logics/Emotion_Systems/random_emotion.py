## Random Condition
import random
from game_engine import EmotionSystem, NPCEmotion
from emotion_systems import BaseEmotionSystem

## Renadom Condition class
class RandomEmotionSystem(BaseEmotionSystem):
    def __init__(self):
        super().__init__()
        self.emotion_change_cooldown = 0
        self.emotion_change_interval = 35  ## Change emotion every ~2 seconds
    
    def initialize(self, game_instance):
        super().initialize(game_instance)
        self.emotion_change_cooldown = 0
    
    def determine_emotion(self, player_health, enemy_proximity, resource_proximity,
                         lagged_player_action, level, player_x, player_y, npc_x, npc_y,
                         resources_collected, enemies_killed, npc_emotion_lagged, current_player_action):
        ## Random emotions-->  only change emotion periodically to avoid erratic behavior
        self.emotion_change_cooldown -= 1
        if self.emotion_change_cooldown <= 0:
            ## Randomly select a new emotion
            emotion_list = list(NPCEmotion)
            new_emotion = random.choice(emotion_list)
            
            ## Reset cooldown with some randomness
            self.emotion_change_cooldown = self.emotion_change_interval + random.randint(-15, 15)
            return new_emotion
        else:
            # Keep the current emotion
            return npc_emotion_lagged
    
    def get_system_type(self):
        ## Return the emotion type system
        return EmotionSystem.RANDOM

    def get_description(self):
        return "You are accompanied by an NPC companion."