import pygame
from .base_player import BasePlayer

class HumanPlayer(BasePlayer):
    def __init__(self, player_id):
        super().__init__(player_id)
        # Rects UI initialisés à None, remplis par le renderer à chaque frame
        self._minus_rect = None
        self._plus_rect  = None
        self._slider_rect = None
        self._slider_x   = 0
        self._slider_w   = 370
        self._zoom_plus_rect  = None
        self._zoom_minus_rect = None

    def get_action(self, game_state, events, renderer):
        for event in events:
            # ── Molette de souris : changer le pourcentage ───────────────────
            if event.type == pygame.MOUSEWHEEL:
                p = game_state.players[self.id]
                new_pct = max(0.01, min(1.0, p.attack_percentage + event.y * 0.05))
                return ("set_pct", new_pct)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # ── Zoom avec boutons + / - ──────────────────────────────────
                if self._zoom_plus_rect and self._zoom_plus_rect.collidepoint(mx, my):
                    return ("zoom", 0.25)
                if self._zoom_minus_rect and self._zoom_minus_rect.collidepoint(mx, my):
                    return ("zoom", -0.25)

                # ── Boutons - / + de la barre inférieure ────────────────────
                if self._minus_rect and self._minus_rect.collidepoint(mx, my):
                    p = game_state.players[self.id]
                    new_pct = max(0.01, p.attack_percentage - 0.10)
                    return ("set_pct", new_pct)
                if self._plus_rect and self._plus_rect.collidepoint(mx, my):
                    p = game_state.players[self.id]
                    new_pct = min(1.0, p.attack_percentage + 0.10)
                    return ("set_pct", new_pct)

                # ── Clic sur le slider ───────────────────────────────────────
                if self._slider_rect and self._slider_rect.collidepoint(mx, my):
                    rel = mx - self._slider_x
                    new_pct = max(0.01, min(1.0, rel / self._slider_w))
                    return ("set_pct", new_pct)

                # ── Clic sur la carte → Attaque ! ────────────────────────────
                bottom_ui_y = renderer.WINDOW_H - renderer.UI_BOTTOM
                if my < bottom_ui_y:
                    wx, wy = renderer.screen_to_world(mx, my)
                    if 0 <= wx < game_state.width and 0 <= wy < game_state.height:
                        return ("attack", int(wx), int(wy))

            # ── Clavier : raccourcis rapides ─────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                p = game_state.players[self.id]
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    return ("zoom", 0.25)
                if event.key == pygame.K_MINUS:
                    return ("zoom", -0.25)
                if event.key == pygame.K_SPACE:
                    return ("attack", None, None)  # Expansion globale

        return ("idle",)
