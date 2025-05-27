## ML-Condition
import os
import sys
import numpy as np
import joblib
from game_engine import EmotionSystem, NPCEmotion, PlayerAction
from emotion_systems import BaseEmotionSystem

## Add XGBoost VERSION file handling
def fix_xgboost_version():
    ## Create the VERSION file if it's missing
    try:
        ## Get the XGBoost directory in the temp folder or the current directory
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        xgboost_dir = os.path.join(base_dir, 'xgboost')
        
        ## Check if VERSION file is missing
        version_path = os.path.join(xgboost_dir, 'VERSION')
        if os.path.exists(xgboost_dir) and not os.path.exists(version_path):
            ## Create the VERSION file with a standard version number
            with open(version_path, 'w') as f:
                f.write('2.0.0')
            print(f"Created missing XGBoost VERSION file at: {version_path}")
            return True
    except Exception as e:
        print(f"Note: Could not create XGBoost VERSION file: {e}")
    return False

## Try to fix XGBoost VERSION file
fix_xgboost_version()

## Create emotion class prediction
class MLEmotionSystem(BaseEmotionSystem):
    def __init__(self, model_path='model/game_npc_model.pkl'):
        super().__init__()
        self.model = None
        self.model_path = model_path
        self.model_loaded = False
        
        ## Dictionary to map emotion indices to emotion enum
        self.index_to_emotion = {
            0: NPCEmotion.ANTICIPATION,
            1: NPCEmotion.HAPPINESS,
            2: NPCEmotion.FEAR,
            3: NPCEmotion.ANGER,
            4: NPCEmotion.SURPRISE,
            5: NPCEmotion.SADNESS
        }
    
    def initialize(self, game_instance):
        super().initialize(game_instance)
        
        try:
            ## Find and load the pre-trained model
            if not os.path.isabs(self.model_path):
                ## Try relative paths
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                possible_paths = [
                    self.model_path,
                    os.path.join(base_dir, self.model_path),
                    os.path.join(base_dir, 'model', os.path.basename(self.model_path)),
                    os.path.join(os.path.dirname(base_dir), self.model_path)
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        print(f"Found model at {path}")
                        fix_xgboost_version()
                        self.model = joblib.load(path)
                        self.model_loaded = True
                        print(f"Successfully loaded the trained model from {path}")
                        break
            else:
                ## Use absolute path
                if os.path.exists(self.model_path):
                    fix_xgboost_version()
                    self.model = joblib.load(self.model_path)
                    self.model_loaded = True
                    print(f"Successfully loaded the trained model from {self.model_path}")
            
            if not self.model_loaded:
                print(f"WARNING: Could not find model at {self.model_path}")
                print(f"Attempted paths: {possible_paths}")
                print(f"ML-based NPC emotions will fall back to rule-based logic")
        except Exception as e:
            print(f"WARNING: Could not load model: {e}")
            print(f" ML-based NPC emotions will fall back to rule-based logic")
    
    def determine_emotion(self, player_health, enemy_proximity, resource_proximity,
                         lagged_player_action, level, player_x, player_y, npc_x, npc_y,
                         resources_collected, enemies_killed, npc_emotion_lagged, current_player_action):
        ## Predict NPC emotion based on game state using the ML model
        
        ## If model isn't loaded, fall back to the current emotion
        if not self.model_loaded or self.model is None:
            ## Fall back to rule-based emotion logic in this case --> should not happen but just in case
            emotion = NPCEmotion.ANTICIPATION
            
            ## Resource nearby - be happy
            if resource_proximity < 150:
                emotion = NPCEmotion.HAPPINESS
            
            ## Enemy at medium distance - be fearful
            if enemy_proximity < 125:
                emotion = NPCEmotion.FEAR
            
            ## Enemy is very close - be angry
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
        
        try:
            ## Convert action enum to string with _lagged suffix
            if isinstance(lagged_player_action, PlayerAction):
                action_str = lagged_player_action.value + "_lagged"
            else:
                # If it's already a value, map it back
                action_map = {0: "idle", 1: "move", 2: "attack"}
                action_str = action_map.get(lagged_player_action, "idle") + "_lagged"
            
            ## Convert current player action to string
            if isinstance(current_player_action, PlayerAction):
                current_action_str = current_player_action.value
            else:
                current_action_str = action_map.get(current_player_action, "idle")
            
            ## Convert NPC emotion_lagged to string
            if isinstance(npc_emotion_lagged, NPCEmotion):
                emotion_lagged_str = npc_emotion_lagged.value
            else:
                # If it's already a string
                emotion_lagged_str = npc_emotion_lagged
            
            ## Create a feature dictionary with all expected features set to 0
            feature_dict = {
                'Player_x': player_x,
                'Player_y': player_y,
                'NPC_x': npc_x,
                'NPC_y': npc_y,
                'Player_health': player_health,
                'Enemy_proximity': enemy_proximity,
                'Resource_proximity': resource_proximity,
                'resources_collected': resources_collected,
                'enemies_killed': enemies_killed,
                'level': level,
                'idle': 0,
                'move': 0,
                'attack': 0,
                'idle_lagged': 0,
                'move_lagged': 0,
                'attack_lagged': 0,
                'anticipation': 0,
                'happiness': 0,
                'fear': 0,
                'anger': 0,
                'surprise': 0,
                'sadness': 0
            }
            
            ## Set the appropriate dummies to 1
            ## Current player action
            feature_dict[current_action_str] = 1
            
            ## Set lagged player action
            feature_dict[action_str] = 1
            
            ## Set lagged NPC emotion
            feature_dict[emotion_lagged_str] = 1
            
            ## Convert to list in a consistent order
            features = np.array([[
                feature_dict['Player_x'],
                feature_dict['Player_y'],
                feature_dict['NPC_x'],
                feature_dict['NPC_y'],
                feature_dict['Player_health'],
                feature_dict['Enemy_proximity'],
                feature_dict['Resource_proximity'],
                feature_dict['resources_collected'],
                feature_dict['enemies_killed'],
                feature_dict['level'],
                feature_dict['idle'],
                feature_dict['move'],
                feature_dict['attack'],
                feature_dict['idle_lagged'],
                feature_dict['move_lagged'],
                feature_dict['attack_lagged'],
                feature_dict['anticipation'],
                feature_dict['happiness'],
                feature_dict['fear'],
                feature_dict['anger'],
                feature_dict['surprise'],
                feature_dict['sadness']
            ]])
            
            ## Predict using the model
            prediction = self.model.predict(features)[0]
            return self.index_to_emotion[prediction]
        
        except Exception as e:
            print(f"Model prediction error: {e}")
            ## Just maintain current emotion on error
            return npc_emotion_lagged
        
    def get_system_type(self):
        ## Return the type of emotion system
        return EmotionSystem.MACHINE_LEARNING

    def get_description(self):
        ## Return a minimal description
        return "You are accompanied by an NPC companion."