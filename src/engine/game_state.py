import numpy as np
import random

class PlayerInfo:
    def __init__(self, player_id, color, name):
        self.id = player_id
        self.name = name
        self.color = color
        self.troops = 100.0 # Troupes de départ
        self.land = 1 
        self.alive = True
        self.attack_percentage = 0.5 
        
        # Centre de masse pour l'affichage du texte
        self.center_x = 0
        self.center_y = 0

class GameState:
    def __init__(self, width=400, height=400):
        self.width = width
        self.height = height
        
        # 0 = Eau, -1 = Terre Neutre, >0 = Joueurs
        self.grid = np.full((height, width), -1, dtype=np.int16)
        self.generate_map()
        
        self.players = {}
        self.tick_count = 0
        self.cycle_step = 0 # 0 à 100 pour la barre de revenu

    def generate_map(self):
        # Génère une forme d'île basique : les bords deviennent de l'eau
        y, x = np.ogrid[-self.height//2:self.height//2, -self.width//2:self.width//2]
        radius = min(self.width, self.height) // 2 * 0.95
        
        # Modifie légèrement le rayon avec du bruit très basique pour faire un rivage
        angle = np.arctan2(y, x)
        noise = np.sin(angle * 5) * (self.width * 0.05) + np.cos(angle * 8) * (self.width * 0.05)
        
        water_mask = x**2 + y**2 > (radius + noise)**2
        self.grid[water_mask] = 0 # Eau

    def add_player(self, player_id, color, name, start_x=None, start_y=None):
        if start_x is None or start_y is None:
            # Spawn aléatoire sur la terre
            ys, xs = np.where(self.grid == -1)
            if len(ys) == 0: return
            idx = random.randint(0, len(ys)-1)
            start_x, start_y = xs[idx], ys[idx]
            
        self.players[player_id] = PlayerInfo(player_id, color, name)
        self.grid[start_y, start_x] = player_id
        self.players[player_id].center_x = start_x
        self.players[player_id].center_y = start_y
        
    def recalculate_land_and_centers(self):
        ids, counts = np.unique(self.grid, return_counts=True)
        land_dict = dict(zip(ids, counts))
        
        for player_id, player in self.players.items():
            if not player.alive: continue
            
            player.land = land_dict.get(player_id, 0)
            if player.land == 0:
                player.alive = False
            else:
                # Calcul approximatif du centre pour le texte
                ys, xs = np.where(self.grid == player_id)
                # On prend la médiane au lieu de la moyenne pour éviter que le texte ne tombe dans l'eau
                # si le territoire a une forme de U.
                player.center_x = int(np.median(xs))
                player.center_y = int(np.median(ys))
