import pygame
import numpy as np
import math

class Renderer:
    def __init__(self, width, height):
        self.base_width = width
        self.base_height = height
        
        # Zoom & Camera
        self.zoom = 1.0
        self.cam_x = 0.0  # coin haut-gauche de la caméra dans l'espace monde
        self.cam_y = 0.0
        
        # Taille de la fenêtre (fixe)
        self.WINDOW_W = 1200
        self.WINDOW_H = 800
        self.UI_BOTTOM = 60   # Hauteur barre inférieure
        self.UI_LEFT = 220    # Largeur panneau leaderboard gauche
        self.STATS_W = 170    # Largeur panneau stats droite
        
        pygame.init()
        pygame.font.init()
        
        self.screen = pygame.display.set_mode((self.WINDOW_W, self.WINDOW_H))
        pygame.display.set_caption("Territorial.io Clone")
        
        # Fonts
        self.font_tiny  = pygame.font.SysFont("Arial", 11, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_mid   = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_big   = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_huge  = pygame.font.SysFont("Arial", 60, bold=True)
        self.map_font_cache = {}
        
        # Palettes exactes Territorial.io (d'après screenshots)
        self.WATER_COLOR   = (30, 45, 100)      # Bleu marine foncé
        self.NEUTRAL_COLOR = (185, 170, 140)    # Beige/sable
        self.BORDER_COLOR  = (255, 255, 255)    # Bordures blanches
        self.UI_BG         = (18, 18, 26)       # Fond UI très foncé
        self.UI_LINE       = (50, 55, 80)
        
        # Couleurs des joueurs
        self.PLAYER_COLORS = {
            1:  (220, 220, 220),  # Blanc (Toi)
            2:  (160, 160, 160),  # Gris clair
            3:  (100, 100, 100),  # Gris moyen
            4:  (60,  60,  60),   # Gris foncé
            5:  (200, 200, 255),  # Bleu pâle
            6:  (180, 220, 180),  # Vert pâle
            7:  (255, 200, 180),  # Saumon
            8:  (255, 240, 180),  # Jaune pâle
            9:  (220, 180, 255),  # Violet pâle
            10: (180, 255, 230),  # Cyan pâle
        }
        
        # Surface carte (mise en cache pour éviter de tout recalculer)
        self._map_surface = None
        self._map_dirty = True
        
    def get_map_font(self, size):
        size = max(9, min(120, int(size)))
        if size not in self.map_font_cache:
            self.map_font_cache[size] = pygame.font.SysFont("Arial", size, bold=True)
        return self.map_font_cache[size]

    # ─── Texte avec contour ────────────────────────────────────────────────────
    def outlined_text(self, font, text, color, outline=(0,0,0)):
        txt = font.render(text, True, color)
        out = font.render(text, True, outline)
        w, h = txt.get_size()
        surf = pygame.Surface((w+4, h+4), pygame.SRCALPHA)
        for dx, dy in ((-2,-2),(2,-2),(-2,2),(2,2),(0,-2),(0,2),(-2,0),(2,0)):
            surf.blit(out, (dx+2, dy+2))
        surf.blit(txt, (2,2))
        return surf

    # ─── Espace monde ↔ Espace écran ──────────────────────────────────────────
    def world_to_screen(self, wx, wy):
        # Zone carte = toute la fenêtre sauf UI gauche/basse
        map_area_w = self.WINDOW_W - self.STATS_W
        map_area_h = self.WINDOW_H - self.UI_BOTTOM
        sx = self.UI_LEFT + (wx - self.cam_x) * self.zoom
        sy = (wy - self.cam_y) * self.zoom
        return int(sx), int(sy)

    def screen_to_world(self, sx, sy):
        wx = (sx - self.UI_LEFT) / self.zoom + self.cam_x
        wy = sy / self.zoom + self.cam_y
        return wx, wy

    def clamp_camera(self):
        # Limite la caméra aux bords du monde
        visible_w = (self.WINDOW_W - self.UI_LEFT - self.STATS_W) / self.zoom
        visible_h = (self.WINDOW_H - self.UI_BOTTOM) / self.zoom
        self.cam_x = max(0, min(self.base_width  - visible_w, self.cam_x))
        self.cam_y = max(0, min(self.base_height - visible_h, self.cam_y))

    # ─── Rendu de la carte ────────────────────────────────────────────────────
    def build_map_surface(self, game_state):
        """Construit la surface RGB de la carte entière (espace monde)."""
        rgb = np.zeros((self.base_width, self.base_height, 3), dtype=np.uint8)
        
        # Eau
        rgb[:, :] = self.WATER_COLOR
        
        # Terre neutre (grid == -1)
        neutral_mask = (game_state.grid.T == -1)
        rgb[neutral_mask] = self.NEUTRAL_COLOR
        
        # Territoires des joueurs
        for pid, color in self.PLAYER_COLORS.items():
            mask = (game_state.grid.T == pid)
            if not np.any(mask):
                continue
            rgb[mask] = color
            
            # Bordures en pointillés blancs : pixel de frontière si voisin différent
            # On détecte les bordures via np.roll
            border = mask & ~(
                np.roll(mask, 1, axis=0) &
                np.roll(mask, -1, axis=0) &
                np.roll(mask, 1, axis=1) &
                np.roll(mask, -1, axis=1)
            )
            # Motif "pointillé" : on garde 1 pixel sur 2 (checkerboard)
            ys_b, xs_b = np.where(border.T)
            for y_b, x_b in zip(ys_b, xs_b):
                if (x_b + y_b) % 2 == 0:
                    rgb[x_b, y_b] = self.BORDER_COLOR
                    
        return pygame.surfarray.make_surface(rgb)

    # ─── Rendu complet ────────────────────────────────────────────────────────
    def draw(self, game_state, clock):
        self.screen.fill(self.UI_BG)
        
        # 1. Zone de la carte (clipée)
        map_area_rect = pygame.Rect(self.UI_LEFT, 0,
                                    self.WINDOW_W - self.UI_LEFT - self.STATS_W,
                                    self.WINDOW_H - self.UI_BOTTOM)
        
        # Construire la surface monde
        world_surf = self.build_map_surface(game_state)
        
        # Mise à l'échelle selon le zoom
        zoom_w = int(self.base_width  * self.zoom)
        zoom_h = int(self.base_height * self.zoom)
        scaled_surf = pygame.transform.scale(world_surf, (zoom_w, zoom_h))
        
        # Décalage caméra
        blit_x = self.UI_LEFT - int(self.cam_x * self.zoom)
        blit_y = -int(self.cam_y * self.zoom)
        
        old_clip = self.screen.get_clip()
        self.screen.set_clip(map_area_rect)
        self.screen.blit(scaled_surf, (blit_x, blit_y))
        
        # 2. Textes sur les territoires
        sorted_players = sorted([p for p in game_state.players.values() if p.alive],
                                 key=lambda x: x.land, reverse=True)
        
        for p in sorted_players:
            if p.land < 30: continue
            
            cx, cy = self.world_to_screen(p.center_x, p.center_y)
            if not map_area_rect.collidepoint(cx, cy): continue
            
            # Taille de la police proportionnelle, mais plafonnée + zoom
            # On utilise une formule plus conservative : sqrt(land) * 0.3
            fsize = int(math.sqrt(p.land * self.zoom) * 0.30)
            fsize = max(9, min(50, fsize))
            
            if fsize < 10: continue
            
            if p.troops > 1_000_000:
                t_str = f"{p.troops/1_000_000:.1f}M"
            elif p.troops > 1_000:
                t_str = f"{p.troops/1000:.1f}k"
            else:
                t_str = str(int(p.troops))
                
            font = self.get_map_font(fsize)
            name_surf = self.outlined_text(font, p.name, (255,255,255))
            troop_surf = self.outlined_text(self.get_map_font(max(9, fsize-3)), t_str, (230,230,230))
            
            # Vérifier que le texte rentre dans le territoire (largeur approx)
            approx_diam = int(math.sqrt(p.land) * 1.4 * self.zoom)
            if name_surf.get_width() > approx_diam:
                continue  # Trop petit pour afficher le nom
            
            self.screen.blit(name_surf,  name_surf.get_rect(center=(cx, cy - fsize//2 - 1)))
            self.screen.blit(troop_surf, troop_surf.get_rect(center=(cx, cy + fsize//2 + 1)))
                
        self.screen.set_clip(old_clip)
        
        # 3. Panneau LEADERBOARD (gauche)
        self._draw_leaderboard(sorted_players[:10])
        
        # 4. Panneau STATS (droite)
        self._draw_stats(game_state, clock)
        
        # 5. Diagramme circulaire (bas-gauche)
        human = game_state.players.get(1)
        if human:
            self._draw_pie(human)
        
        # 6. Barre de balance (haut-centre)
        if human:
            self._draw_balance_bar(human)
        
        # 7. Barre inférieure - Slider
        if human:
            self._draw_bottom_ui(human)
            
        # 8. FPS
        fps = clock.get_fps()
        fps_surf = self.font_small.render(f"FPS: {int(fps)}", True, (200, 255, 200))
        self.screen.blit(fps_surf, (self.UI_LEFT + 5, 5))
        
        pygame.display.flip()

    # ─── UI Leaderboard ───────────────────────────────────────────────────────
    def _draw_leaderboard(self, players):
        lb_rect = pygame.Rect(0, 0, self.UI_LEFT, len(players)*26 + 36)
        # Fond semi-transparent
        bg = pygame.Surface((lb_rect.w, lb_rect.h), pygame.SRCALPHA)
        bg.fill((10, 12, 20, 210))
        self.screen.blit(bg, (0,0))
        
        # Titre
        title = self.font_mid.render("LEADERBOARD", True, (255,255,255))
        pygame.draw.rect(self.screen, (30,35,60), (0,0, self.UI_LEFT, 28))
        self.screen.blit(title, title.get_rect(center=(self.UI_LEFT//2, 14)))
        
        for i, p in enumerate(players):
            y = 30 + i * 26
            # Ligne de fond alternée
            row_color = (20,25,45,180) if i % 2 == 0 else (12,15,30,180)
            
            # Mise en évidence du joueur humain
            if p.id == 1:
                pygame.draw.rect(self.screen, (0, 100, 30), (0, y, self.UI_LEFT, 25))
            
            # Rang
            crown = "👑" if i == 0 else f"{i+1}."
            rank_c = (255, 210, 0) if i == 0 else (200, 200, 200)
            rank_s = self.font_small.render(crown, True, rank_c)
            self.screen.blit(rank_s, (5, y + 5))
            
            # Nom
            name_s = self.font_small.render(p.name[:18], True, p.color)
            self.screen.blit(name_s, (30, y + 5))
            
            # Score (taille du territoire)
            score_s = self.font_small.render(str(p.land), True, (220,220,220))
            self.screen.blit(score_s, (self.UI_LEFT - score_s.get_width() - 6, y+5))

    # ─── UI Stats (droite) ────────────────────────────────────────────────────
    def _draw_stats(self, game_state, clock):
        x0 = self.WINDOW_W - self.STATS_W
        bg = pygame.Surface((self.STATS_W, 160), pygame.SRCALPHA)
        bg.fill((10, 12, 20, 220))
        self.screen.blit(bg, (x0, 0))
        
        human = game_state.players.get(1)
        alive_count = sum(1 for p in game_state.players.values() if p.alive)
        
        rows = [
            ("Humans",      "1",   (200,200,200)),
            ("Bots",        str(alive_count - 1), (200,200,200)),
            ("Percentage",  f"{(human.land / max(1, game_state.width*game_state.height)) * 100:.2f}%"
                              if human else "0%", (200,200,200)),
        ]
        
        if human:
            max_troops = human.land * 150
            ratio = human.troops / max(1, max_troops)
            interest = max(0.0, 0.007 * (1 - ratio**2)) * 100
            interest_color = (255,80,80) if interest < 1.0 else (255,220,0)
            rows.append(("Interest", f"{interest:.2f}%", interest_color))
            rows.append(("Income",   str(int(human.land * 1.5)), (200,200,200)))
            
        ticks = game_state.tick_count
        mins, secs = divmod(ticks // 60, 60)
        rows.append(("Time", f"{mins}:{secs:02d}", (200,200,200)))
        
        for i, (label, value, color) in enumerate(rows):
            y = 5 + i * 22
            lbl_s = self.font_small.render(label, True, (160,160,180))
            val_s = self.font_small.render(value, True, color)
            self.screen.blit(lbl_s, (x0 + 6, y + 2))
            self.screen.blit(val_s, (x0 + self.STATS_W - val_s.get_width() - 6, y + 2))

    # ─── Diagramme circulaire ─────────────────────────────────────────────────
    def _draw_pie(self, human):
        cx, cy = 55, self.WINDOW_H - self.UI_BOTTOM - 70
        radius = 48
        
        bg = pygame.Surface((radius*2+20, radius*2+20), pygame.SRCALPHA)
        bg.fill((10,12,20,200))
        self.screen.blit(bg, (cx - radius - 10, cy - radius - 10))
        
        pct = human.attack_percentage
        # Arc de cercle pour représenter le pourcentage utilisé
        pygame.draw.circle(self.screen, (40,40,60), (cx, cy), radius)
        
        # Arc rempli (angle de 0 à pct*360°)
        angle_start = -90  # Commence en haut
        angle_end = angle_start + int(pct * 360)
        
        # Dessin de l'arc rempli pixel par pixel (via polygone)
        if pct > 0:
            pts = [(cx, cy)]
            for a in range(angle_start, angle_end + 1, 2):
                rad = math.radians(a)
                pts.append((cx + radius * math.cos(rad), cy + radius * math.sin(rad)))
            if len(pts) >= 3:
                # Petite portion = gris sombre, grande portion = couleur vive
                fill_color = (180, 60, 60) if pct > 0.8 else (100, 140, 200)
                pygame.draw.polygon(self.screen, fill_color, pts)
        
        pygame.draw.circle(self.screen, (200,200,200), (cx, cy), radius, 2)
        
        pct_surf = self.font_mid.render(f"{int(pct*100)}%", True, (255,255,255))
        self.screen.blit(pct_surf, pct_surf.get_rect(center=(cx, cy)))

    # ─── Barre de balance (haut-centre) ───────────────────────────────────────
    def _draw_balance_bar(self, human):
        bar_w = 300
        bar_h = 28
        bx = self.WINDOW_W//2 - bar_w//2
        by = 5
        
        # Fond
        pygame.draw.rect(self.screen, (20,20,40), (bx, by, bar_w, bar_h), border_radius=4)
        
        max_troops = human.land * 150
        ratio = human.troops / max(1, max_troops)
        
        # Partie remplie : rouge si pleine, vert si petit ratio
        fill_col = (200, 50, 50) if ratio > 0.8 else (50, 180, 80)
        fill_w = int(bar_w * min(1.0, ratio))
        pygame.draw.rect(self.screen, fill_col, (bx, by, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, (80, 90, 120), (bx, by, bar_w, bar_h), 2, border_radius=4)
        
        # Texte balance
        if human.troops > 1_000_000:
            t_str = f"{human.troops/1_000_000:.2f}M"
        elif human.troops > 1_000:
            t_str = f"{human.troops/1000:.1f}k"
        else:
            t_str = str(int(human.troops))
            
        # Variation (income)
        income = int(human.land * 1.5)
        bal_surf = self.font_mid.render(f"{t_str}  +{income}", True, (255,255,255))
        self.screen.blit(bal_surf, bal_surf.get_rect(center=(bx + bar_w//2, by + bar_h//2)))

    # ─── Barre inférieure ─────────────────────────────────────────────────────
    def _draw_bottom_ui(self, human):
        by = self.WINDOW_H - self.UI_BOTTOM
        pygame.draw.rect(self.screen, (15, 16, 28), (0, by, self.WINDOW_W, self.UI_BOTTOM))
        pygame.draw.line(self.screen, self.UI_LINE, (0, by), (self.WINDOW_W, by), 2)
        
        pct = human.attack_percentage
        
        # Bouton "-"
        btn_size = 36
        minus_rect = pygame.Rect(self.WINDOW_W//2 - 220, by + 12, btn_size, btn_size)
        plus_rect  = pygame.Rect(self.WINDOW_W//2 + 184, by + 12, btn_size, btn_size)
        
        pygame.draw.rect(self.screen, (180,40,40), minus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (40,180,40), plus_rect,  border_radius=6)
        
        m_surf = self.font_big.render("-", True, (255,255,255))
        p_surf = self.font_big.render("+", True, (255,255,255))
        self.screen.blit(m_surf, m_surf.get_rect(center=minus_rect.center))
        self.screen.blit(p_surf, p_surf.get_rect(center=plus_rect.center))
        
        # Slider violette (comme Territorial.io)
        slider_w = 370
        slider_h = 30
        slider_x = self.WINDOW_W//2 - slider_w//2
        slider_y = by + (self.UI_BOTTOM - slider_h)//2
        
        pygame.draw.rect(self.screen, (60,30,90), (slider_x, slider_y, slider_w, slider_h), border_radius=6)
        filled_w = int(slider_w * pct)
        if filled_w > 4:
            pygame.draw.rect(self.screen, (130, 60, 200),
                             (slider_x, slider_y, filled_w, slider_h), border_radius=6)
            # Reflet (effet premium)
            pygame.draw.rect(self.screen, (180, 100, 240),
                             (slider_x+2, slider_y+2, filled_w-4, slider_h//2 - 2), border_radius=4)
                             
        pygame.draw.rect(self.screen, (100,60,140), (slider_x, slider_y, slider_w, slider_h), 2, border_radius=6)
        
        # Repères
        for mark in [0.25, 0.5, 0.75]:
            mx = slider_x + int(slider_w * mark)
            pygame.draw.line(self.screen, (90,50,130), (mx, slider_y+4), (mx, slider_y+slider_h-4), 1)
        
        # Texte
        if human.troops > 1_000_000:
            t_str = f"{human.troops/1_000_000:.1f}M"
        elif human.troops > 1_000:
            t_str = f"{human.troops/1000:.1f}k"
        else:
            t_str = str(int(human.troops))
            
        pct_surf = self.font_mid.render(f"{t_str}  ({int(pct*100)}%)", True, (255,255,255))
        self.screen.blit(pct_surf, pct_surf.get_rect(center=(slider_x + slider_w//2, slider_y + slider_h//2)))
        
        # Zoom buttons (droite de l'UI)
        zoom_plus_rect  = pygame.Rect(self.WINDOW_W - self.STATS_W - 45, self.WINDOW_H//2 - 50, 36, 36)
        zoom_minus_rect = pygame.Rect(self.WINDOW_W - self.STATS_W - 45, self.WINDOW_H//2, 36, 36)
        pygame.draw.circle(self.screen, (40,45,70), zoom_plus_rect.center, 18)
        pygame.draw.circle(self.screen, (40,45,70), zoom_minus_rect.center, 18)
        pygame.draw.circle(self.screen, (100,110,160), zoom_plus_rect.center, 18, 2)
        pygame.draw.circle(self.screen, (100,110,160), zoom_minus_rect.center, 18, 2)
        zp_s = self.font_big.render("+", True, (255,255,255))
        zm_s = self.font_big.render("-", True, (255,255,255))
        self.screen.blit(zp_s, zp_s.get_rect(center=zoom_plus_rect.center))
        self.screen.blit(zm_s, zm_s.get_rect(center=zoom_minus_rect.center))
        
        # Retourner les rects pour les collisions dans human_player
        human._minus_rect = minus_rect
        human._plus_rect  = plus_rect
        human._slider_rect = pygame.Rect(slider_x, slider_y, slider_w, slider_h)
        human._slider_x    = slider_x
        human._slider_w    = slider_w
        human._zoom_plus_rect  = zoom_plus_rect
        human._zoom_minus_rect = zoom_minus_rect
