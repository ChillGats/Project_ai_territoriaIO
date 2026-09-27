import pygame
from .base_player import BasePlayer

class HumanPlayer(BasePlayer):
    def __init__(self, player_id):
        super().__init__(player_id)

    def get_action(self, game_state, events, renderer):
        for event in events:
            # Zoom molette (délégué à la caméra mais on vérifie si on clique sur UI)
            if event.type == pygame.MOUSEWHEEL:
                renderer.camera.handle_event(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # Bouton "-" de la barre inférieure
                if renderer.minus_btn_rect and renderer.minus_btn_rect.collidepoint(mx, my):
                    p = game_state.players[self.id]
                    return ("set_pct", max(0.01, p.attack_percentage - 0.10))
                
                # Bouton "+" de la barre inférieure
                if renderer.plus_btn_rect and renderer.plus_btn_rect.collidepoint(mx, my):
                    p = game_state.players[self.id]
                    return ("set_pct", min(1.0, p.attack_percentage + 0.10))
                
                # Clic sur le slider
                if renderer.slider_rect and renderer.slider_rect.collidepoint(mx, my):
                    rel = mx - renderer.slider_x
                    new_pct = max(0.01, min(1.0, rel / renderer.slider_w))
                    return ("set_pct", new_pct)
                
                # Bouton zoom +
                if renderer.zoom_plus_rect.collidepoint(mx, my):
                    renderer.camera.zoom_by(0.3)
                
                # Bouton zoom -
                if renderer.zoom_minus_rect.collidepoint(mx, my):
                    renderer.camera.zoom_by(-0.3)
                
                # Clic gauche sur la carte = Attaque
                if event.button == 1:
                    # Vérifie qu'on ne clique pas sur un panneau UI
                    # Leaderboard (haut-gauche approx 250x350)
                    if mx < 250 and my < 350: return ("idle",)
                    # Stats panel (haut-droit approx 200x160)
                    if mx > renderer.WIN_W - 200 and my < 160: return ("idle",)
                    # Boutons de zoom (milieu-droit)
                    if mx > renderer.WIN_W - 100 and renderer.WIN_H//2 - 60 < my < renderer.WIN_H//2 + 50: return ("idle",)
                    # Barre du bas (bas-centre approx 400x60)
                    if renderer.WIN_W//2 - 250 < mx < renderer.WIN_W//2 + 250 and my > renderer.WIN_H - 70: return ("idle",)
                    # Pie chart (bas-gauche)
                    if mx < 150 and my > renderer.WIN_H - 150: return ("idle",)

                    wx, wy = renderer.camera.screen_to_world(mx, my)
                    if 0 <= wx < game_state.width and 0 <= wy < game_state.height:
                        return ("attack", int(wx), int(wy))
                
                # Clic droit = drag (géré par la caméra)
                renderer.camera.handle_event(event)
                
            elif event.type == pygame.MOUSEBUTTONUP:
                renderer.camera.handle_event(event)
                
            elif event.type == pygame.MOUSEMOTION:
                renderer.camera.handle_event(event)
                
            elif event.type == pygame.KEYDOWN:
                p = game_state.players[self.id]
                if event.key == pygame.K_SPACE:
                    return ("attack", None, None)   # Expansion globale
                if event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                    renderer.camera.zoom_by(0.3)
                if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    renderer.camera.zoom_by(-0.3)
                    
        return ("idle",)
