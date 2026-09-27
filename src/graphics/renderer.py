import pygame
import numpy as np
import math

class Renderer:
    def __init__(self, width, height, scale=3):
        self.width = width
        self.height = height
        self.scale = scale
        pygame.init()
        self.screen = pygame.display.set_mode((width * scale, height * scale))
        pygame.display.set_caption("Territorial.io Exact Clone")
        
        self.leaderboard_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.map_fonts = {}
        
        # Couleurs exactes de Territorial.io
        self.colors = {
            0: (170, 200, 230),      # Eau (Bleu très clair)
            -1: (245, 245, 245),     # Terre Neutre (Blanc cassé)
            1: (50, 150, 250),       # Bleu
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
        # Rendu du texte avec un véritable contour (stroke)
        base = font.render(text, True, text_color)
        outline = font.render(text, True, outline_color)
        
        # On crée une surface légèrement plus grande pour contenir le contour
        w, h = base.get_size()
        surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        
        # On dessine le contour dans toutes les directions
        for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (-2,0), (2,0), (0,-2), (0,2)]:
            surf.blit(outline, (dx + 2, dy + 2))
            
        # On dessine le texte par-dessus
        surf.blit(base, (2, 2))
        return surf

    def draw(self, game_state):
        rgb_array = np.zeros((self.width, self.height, 3), dtype=np.uint8)
        
        for entity_id, color in self.colors.items():
            if entity_id not in np.unique(game_state.grid):
                continue
                
            mask = (game_state.grid.T == entity_id) 
            
            if entity_id <= 0:
                rgb_array[mask] = color
            else:
                rgb_array[mask] = color
                
                # Bordure noire autour du territoire
                border_mask = mask & ~(
                    np.roll(mask, 1, axis=0) &
                    np.roll(mask, -1, axis=0) &
                    np.roll(mask, 1, axis=1) &
                    np.roll(mask, -1, axis=1)
                )
                rgb_array[border_mask] = (0, 0, 0) # Bordure 100% noire dans Territorial.io
                
        surface = pygame.surfarray.make_surface(rgb_array)
        scaled_surface = pygame.transform.scale(surface, (self.width * self.scale, self.height * self.scale))
        self.screen.blit(scaled_surface, (0, 0))
        
        # Textes sur la carte
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

        # Leaderboard
        sorted_players = sorted([p for p in game_state.players.values() if p.alive], key=lambda x: x.land, reverse=True)
        y_leaderboard = 10
        for i, p in enumerate(sorted_players[:10]):
            lb_text = self.render_text_with_outline(self.leaderboard_font, f"#{i+1} {p.name} - {p.land} px", p.color, (0,0,0))
            lb_rect = lb_text.get_rect(topright=(self.width * self.scale - 10, y_leaderboard))
            self.screen.blit(lb_text, lb_rect)
            y_leaderboard += 30
            
        pygame.display.flip()
