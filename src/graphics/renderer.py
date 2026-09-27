import pygame
import numpy as np
import math

class Renderer:
    def __init__(self, width, height, scale=3):
        self.width = width
        self.height = height
        self.scale = scale
        pygame.init()
        
        # Espace supplémentaire en bas pour l'UI (ex: 80 pixels)
        self.ui_height = 80
        self.screen = pygame.display.set_mode((width * scale, height * scale + self.ui_height))
        pygame.display.set_caption("Territorial.io Exact Clone")
        
        self.leaderboard_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.ui_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.map_fonts = {}
        
        self.colors = {
            0: (170, 200, 230),      # Eau
            -1: (245, 245, 245),     # Terre Neutre
            1: (50, 150, 250),       # Bleu (Toi)
            2: (250, 50, 50),        # Rouge
            3: (50, 200, 50),        # Vert
            4: (250, 200, 50),       # Jaune
            5: (200, 50, 250),       # Violet
            6: (50, 250, 250),       # Cyan
            7: (250, 100, 50),       # Orange
            8: (100, 100, 100),      # Gris
            9: (50, 50, 50),         # Noir
            10: (250, 150, 200)      # Rose
        }
        
    def get_map_font(self, size):
        size = max(10, min(150, int(size)))
        if size not in self.map_fonts:
            self.map_fonts[size] = pygame.font.SysFont("Arial", size, bold=True)
        return self.map_fonts[size]
        
    def render_text_with_outline(self, font, text, text_color, outline_color):
        base = font.render(text, True, text_color)
        outline = font.render(text, True, outline_color)
        w, h = base.get_size()
        surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (-2,0), (2,0), (0,-2), (0,2)]:
            surf.blit(outline, (dx + 2, dy + 2))
        surf.blit(base, (2, 2))
        return surf

    def draw(self, game_state):
        # 1. Rendu de la carte
        rgb_array = np.zeros((self.width, self.height, 3), dtype=np.uint8)
        
        for entity_id, color in self.colors.items():
            if entity_id not in np.unique(game_state.grid): continue
            mask = (game_state.grid.T == entity_id) 
            
            if entity_id <= 0:
                rgb_array[mask] = color
            else:
                rgb_array[mask] = color
                border_mask = mask & ~(
                    np.roll(mask, 1, axis=0) &
                    np.roll(mask, -1, axis=0) &
                    np.roll(mask, 1, axis=1) &
                    np.roll(mask, -1, axis=1)
                )
                rgb_array[border_mask] = (0, 0, 0) 
                
        surface = pygame.surfarray.make_surface(rgb_array)
        scaled_surface = pygame.transform.scale(surface, (self.width * self.scale, self.height * self.scale))
        self.screen.blit(scaled_surface, (0, 0))
        
        # 2. Textes sur la carte
        for p in game_state.players.values():
            if not p.alive or p.land < 20: continue
            
            font_size = int(math.sqrt(p.land) * 0.4 * self.scale)
            if font_size >= 12:
                font = self.get_map_font(font_size)
                
                if p.troops > 1000000:
                    troop_str = f"{p.troops/1000000:.1f}M"
                elif p.troops > 1000:
                    troop_str = f"{p.troops/1000:.1f}k"
                else:
                    troop_str = str(int(p.troops))
                    
                name_surf = self.render_text_with_outline(font, p.name, (255, 255, 255), (0, 0, 0))
                troop_surf = self.render_text_with_outline(font, troop_str, (255, 255, 255), (0, 0, 0))
                
                cx, cy = p.center_x * self.scale, p.center_y * self.scale
                name_rect = name_surf.get_rect(center=(cx, cy - font_size//1.8))
                troop_rect = troop_surf.get_rect(center=(cx, cy + font_size//1.8))
                
                self.screen.blit(name_surf, name_rect)
                self.screen.blit(troop_surf, troop_rect)

        # 3. Leaderboard avec fond semi-transparent
        sorted_players = sorted([p for p in game_state.players.values() if p.alive], key=lambda x: x.land, reverse=True)
        y_leaderboard = 10
        lb_width = 250
        lb_height = min(len(sorted_players) * 30 + 10, 310)
        
        # Surface transparente pour le fond du leaderboard
        lb_bg = pygame.Surface((lb_width, lb_height), pygame.SRCALPHA)
        lb_bg.fill((0, 0, 0, 100)) # Noir transparent
        self.screen.blit(lb_bg, (self.width * self.scale - lb_width, 0))
        
        for i, p in enumerate(sorted_players[:10]):
            crown = "👑 " if i == 0 else ""
            lb_text = self.render_text_with_outline(self.leaderboard_font, f"{crown}#{i+1} {p.name} - {p.land} px", p.color, (0,0,0))
            lb_rect = lb_text.get_rect(topright=(self.width * self.scale - 10, y_leaderboard))
            self.screen.blit(lb_text, lb_rect)
            y_leaderboard += 30
            
        # 4. Interface Utilisateur du bas (Slider Premium)
        ui_rect = pygame.Rect(0, self.height * self.scale, self.width * self.scale, self.ui_height)
        pygame.draw.rect(self.screen, (20, 25, 30), ui_rect) # Fond UI légèrement plus bleuté/foncé
        pygame.draw.line(self.screen, (50, 55, 60), (0, self.height * self.scale), (self.width * self.scale, self.height * self.scale), 2)
        
        human_player = game_state.players.get(1)
        if human_player:
            pct = human_player.attack_percentage
            
            # Slider de pourcentage
            slider_w = int(self.width * self.scale * 0.6) # Moins large pour laisser place à la balance
            slider_h = 24
            slider_x = (self.width * self.scale - slider_w) // 2
            slider_y = self.height * self.scale + (self.ui_height - slider_h) // 2
            
            # Fond du slider avec un bord
            pygame.draw.rect(self.screen, (40, 40, 40), (slider_x, slider_y, slider_w, slider_h), border_radius=12)
            pygame.draw.rect(self.screen, (10, 10, 10), (slider_x, slider_y, slider_w, slider_h), width=2, border_radius=12)
            
            # Partie remplie (Rouge dégradé simulé)
            filled_w = int(slider_w * pct)
            if filled_w > 10:
                pygame.draw.rect(self.screen, (220, 40, 40), (slider_x+1, slider_y+1, filled_w-2, slider_h-2), border_radius=12)
                # Petit reflet pour le "Premium" look
                pygame.draw.rect(self.screen, (255, 100, 100), (slider_x+1, slider_y+1, filled_w-2, (slider_h-2)//2), border_radius=12)
            
            # Repères sur le slider (25%, 50%, 75%)
            for mark in [0.25, 0.5, 0.75]:
                mx = slider_x + int(slider_w * mark)
                pygame.draw.line(self.screen, (100, 100, 100), (mx, slider_y + 4), (mx, slider_y + slider_h - 4), 2)
            
            # Texte du pourcentage centré
            pct_text = self.render_text_with_outline(self.ui_font, f"{int(pct * 100)} %", (255,255,255), (0,0,0))
            pct_rect = pct_text.get_rect(center=(slider_x + slider_w//2, slider_y + slider_h//2))
            self.screen.blit(pct_text, pct_rect)
            
            # Affichage de la Balance
            if human_player.troops > 1000000:
                tr_str = f"{human_player.troops/1000000:.2f}M"
            elif human_player.troops > 1000:
                tr_str = f"{human_player.troops/1000:.2f}k"
            else:
                tr_str = str(int(human_player.troops))
                
            # Ratio (Couleur rouge si on approche de la limite)
            max_troops = human_player.land * 150
            ratio = human_player.troops / max(1, max_troops)
            balance_color = (255, 50, 50) if ratio > 0.8 else (255, 255, 255)
            
            bal_text = self.render_text_with_outline(self.ui_font, f"Balance: {tr_str}", balance_color, (0,0,0))
            self.screen.blit(bal_text, (20, self.height * self.scale + 25))
            
        pygame.display.flip()
