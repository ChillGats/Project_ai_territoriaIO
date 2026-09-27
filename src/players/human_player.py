import pygame
from .base_player import BasePlayer

class HumanPlayer(BasePlayer):
    def __init__(self, player_id, scale=3):
        super().__init__(player_id)
        self.scale = scale

    def get_action(self, game_state, events):
        for event in events:
            # 1. Gérer le pourcentage d'attaque (Molette de la souris)
            if event.type == pygame.MOUSEWHEEL:
                player = game_state.players[self.id]
                # Modifie le pourcentage entre 10% (0.1) et 100% (1.0)
                new_pct = max(0.1, min(1.0, player.attack_percentage + (event.y * 0.1)))
                return (None, None, 1, new_pct) # L'action de type 1 met à jour le %
                
            # 2. Lancer une attaque (Clic gauche)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # On divise par le "scale" car la fenêtre est agrandie par rapport à la vraie matrice
                grid_x = mouse_x // self.scale
                grid_y = mouse_y // self.scale
                
                return (grid_x, grid_y, 2, None) # Action de type 2 (Attaque)
                
        # Si le joueur n'a rien cliqué, on attend
        return (None, None, 0, None)
