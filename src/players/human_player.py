import pygame
from .base_player import BasePlayer

class HumanPlayer(BasePlayer):
    def __init__(self, player_id, scale=1):
        super().__init__(player_id)
        self.scale = scale

    def get_action(self, game_state, events):
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                player = game_state.players[self.id]
                new_pct = max(0.01, min(1.0, player.attack_percentage + (event.y * 0.05)))
                return (None, None, 1, new_pct)
                
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Vérifie si on a cliqué sur la zone de la carte ou sur l'UI en bas
                map_pixel_height = game_state.height * self.scale
                
                if mouse_y >= map_pixel_height:
                    # Clic dans l'UI ! Vérifier si on a cliqué sur le slider
                    slider_w = int(game_state.width * self.scale * 0.8)
                    slider_h = 20
                    slider_x = (game_state.width * self.scale - slider_w) // 2
                    slider_y = map_pixel_height + (80 - slider_h) // 2
                    
                    # Hitbox du slider (un peu plus large pour faciliter le clic)
                    if slider_x - 10 <= mouse_x <= slider_x + slider_w + 10 and slider_y - 10 <= mouse_y <= slider_y + slider_h + 10:
                        # Calculer le nouveau pourcentage en fonction du X
                        relative_x = mouse_x - slider_x
                        new_pct = max(0.01, min(1.0, relative_x / slider_w))
                        return (None, None, 1, new_pct)
                        
                else:
                    # Clic sur la carte : on attaque !
                    grid_x = mouse_x // self.scale
                    grid_y = mouse_y // self.scale
                    return (grid_x, grid_y, 2, None)
                    
        return (None, None, 0, None)
