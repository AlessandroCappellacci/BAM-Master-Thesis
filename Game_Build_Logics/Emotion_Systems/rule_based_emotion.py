## Rule-based Codnition
from game_engine import EmotionSystem, NPCEmotion, PlayerAction
from emotion_systems import BaseEmotionSystem

## Rule-based Condition class
class RuleBasedEmotionSystem(BaseEmotionSystem):
    def __init__(self):
        super().__init__()
    
    def determine_emotion(self, player_health, enemy_proximity, resource_proximity,
                         lagged_player_action, level, player_x, player_y, npc_x, npc_y,
                         resources_collected, enemies_killed, npc_emotion_lagged, current_player_action):
       ## Rule-based emotion logic:
        ## Default emotion - will be overridden by conditions
        emotion = NPCEmotion.ANTICIPATION
        
        ## Resource nearby - be happy
        if resource_proximity < 150:
            emotion = NPCEmotion.HAPPINESS
        
        ## Enemy at medium distance - be fearful
        if enemy_proximity < 125:
            emotion = NPCEmotion.FEAR
        
        ## Check if any enemy is in attack range of player - be angry
        if enemy_proximity < 60:
            emotion = NPCEmotion.ANGER
        
        ## If player attacks near NPC - be surprised
        if (current_player_action == PlayerAction.ATTACK and 
            ((player_x - npc_x)**2 + (player_y - npc_y)**2)**0.5 < 60):
            emotion = NPCEmotion.SURPRISE
        
        ## If player health is low - be sad
        if player_health <= 30:
            emotion = NPCEmotion.SADNESS
        
        return emotion
    
    def get_system_type(self):
        # Return the type of emotion system
        return EmotionSystem.RULE_BASED

    def get_description(self):
        return "You are accompanied by an NPC companion."

