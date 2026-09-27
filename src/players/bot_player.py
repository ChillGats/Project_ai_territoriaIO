import random
from .base_player import BasePlayer

class BotPlayer(BasePlayer):
    def __init__(self, player_id):
        super().__init__(player_id)
        self.attack_timer = 0
        self.delay = random.randint(30, 90)

    def get_action(self, game_state, events=None):
        self.attack_timer += 1
        
        if self.attack_timer >= self.delay:
            self.attack_timer = 0
            self.delay = random.randint(30, 90)
            
            # Comportement Territorial.io :
            # En début de partie, les bots font de petites attaques (10-20%)
            # pour s'étendre lentement sans vider leur armée.
            pct = random.uniform(0.1, 0.25)
            game_state.players[self.id].attack_percentage = pct
            
            # Expansion globale la plupart du temps (None, None)
            # Sinon, attaque un voisin au hasard
            if random.random() < 0.8:
                return (None, None, 2, None)
            else:
                target_x = random.randint(0, game_state.width - 1)
                target_y = random.randint(0, game_state.height - 1)
                return (target_x, target_y, 2, None)
                
        return (None, None, 0, None)
