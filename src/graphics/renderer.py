import pygame
import numpy as np
import math

# ─── Couleurs de la palette exacte de Territorial.io ─────────────────────────
WATER_COLOR   = (28, 40, 95)       # Bleu marine foncé (exactement comme dans les screenshots)
NEUTRAL_COLOR = (175, 160, 130)    # Beige/sable pour la terre neutre
BORDER_WHITE  = (255, 255, 255)    # Bordures blanches en pointillés
UI_DARK       = (10, 12, 22)       # Fond UI très sombre
UI_MID        = (20, 25, 45)       # Fond panneaux

# Couleurs VIVES des joueurs (exactement comme dans le vrai jeu)
PLAYER_COLORS = {
    1:  (180,  50, 220),  # Violet/Magenta (Toi - couleur vive)
    2:  (50,  200, 160),  # Teal/Cyan vif
    3:  ( 80, 180,  50),  # Vert vif
    4:  (230,  60,  60),  # Rouge vif
    5:  ( 50, 130, 230),  # Bleu vif
    6:  (230, 180,  40),  # Jaune/Or
    7:  (230, 100,  40),  # Orange
    8:  (160,  60, 200),  # Violet foncé
    9:  ( 40, 200, 220),  # Cyan clair
    10: (200, 200, 200),  # Gris clair
}

class Camera:
    """Gestion du zoom et du déplacement caméra."""
    def __init__(self, world_w, world_h, view_x, view_y, view_w, view_h):
        self.world_w = world_w
        self.world_h = world_h
        self.view_x  = view_x   # Position X de la zone de vue (pixels écran)
        self.view_y  = view_y
        self.view_w  = view_w   # Largeur de la zone de vue (pixels écran)
        self.view_h  = view_h
        
        self.zoom    = 2.0       # Zoom de départ (on voit ~50% de la carte)
        self.cam_x   = 0.0       # Coin haut-gauche de la vue en coords monde
        self.cam_y   = 0.0
        self._dragging = False
        self._drag_start_screen = (0, 0)
        self._drag_start_cam = (0.0, 0.0)

    def center_on(self, wx, wy):
        """Centre la caméra sur un point du monde (coords monde)."""
        visible_w = self.view_w / self.zoom
        visible_h = self.view_h / self.zoom
        self.cam_x = wx - visible_w / 2
        self.cam_y = wy - visible_h / 2
        self.clamp()

    def clamp(self):
        visible_w = self.view_w / self.zoom
        visible_h = self.view_h / self.zoom
        self.cam_x = max(0.0, min(self.world_w - visible_w, self.cam_x))
        self.cam_y = max(0.0, min(self.world_h - visible_h, self.cam_y))

    def world_to_screen(self, wx, wy):
        sx = self.view_x + (wx - self.cam_x) * self.zoom
        sy = self.view_y + (wy - self.cam_y) * self.zoom
        return int(sx), int(sy)

    def screen_to_world(self, sx, sy):
        wx = (sx - self.view_x) / self.zoom + self.cam_x
        wy = (sy - self.view_y) / self.zoom + self.cam_y
        return wx, wy

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            # Zoom centré sur la position de la souris
            mx, my = pygame.mouse.get_pos()
            if not (self.view_x <= mx <= self.view_x + self.view_w and
                    self.view_y <= my <= self.view_y + self.view_h):
                return
            wx_before, wy_before = self.screen_to_world(mx, my)
            self.zoom = max(0.5, min(8.0, self.zoom * (1.15 ** event.y)))
            wx_after, wy_after = self.screen_to_world(mx, my)
            self.cam_x += wx_before - wx_after
            self.cam_y += wy_before - wy_after
            self.clamp()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (2, 3):
            # Clic droit ou milieu : début du drag
            self._dragging = True
            self._drag_start_screen = pygame.mouse.get_pos()
            self._drag_start_cam = (self.cam_x, self.cam_y)

        elif event.type == pygame.MOUSEBUTTONUP and event.button in (2, 3):
            self._dragging = False

        elif event.type == pygame.MOUSEMOTION and self._dragging:
            mx, my = pygame.mouse.get_pos()
            dx = (self._drag_start_screen[0] - mx) / self.zoom
            dy = (self._drag_start_screen[1] - my) / self.zoom
            self.cam_x = self._drag_start_cam[0] + dx
            self.cam_y = self._drag_start_cam[1] + dy
            self.clamp()

    def zoom_by(self, delta):
        mx, my = pygame.mouse.get_pos()
        wx_before, wy_before = self.screen_to_world(mx, my)
        self.zoom = max(0.5, min(8.0, self.zoom + delta))
        wx_after, wy_after = self.screen_to_world(mx, my)
        self.cam_x += wx_before - wx_after
        self.cam_y += wy_before - wy_after
        self.clamp()


class Renderer:
    """
    Renderer pixel-perfect basé sur les screenshots de Territorial.io.
    Structure de l'UI :
      - Zone carte : toute la fenêtre (les panneaux UI sont superposés)
      - Leaderboard : coin haut-gauche (220x~300, fond sombre)
      - Stats :       coin haut-droit  (170x~150, fond sombre)
      - Pie chart :   bas-gauche       (120x120, fond gris foncé)
      - Balance bar : haut-centre      (300x28, vert/rouge)
      - Bottom bar :  toute la largeur (60px hauteur, fond très sombre)
      - Zoom +/- :    droite milieu    (boutons ronds)
      - Info panel :  bas-droit        (messages flottants)
    """
    LB_W  = 222    # Leaderboard largeur
    ST_W  = 175    # Stats largeur
    BAR_H = 60     # Hauteur barre inférieure
    
    def __init__(self, world_w, world_h):
        self.world_w = world_w
        self.world_h = world_h
        
        pygame.init()
        pygame.font.init()
        
        # Plein écran
        info = pygame.display.Info()
        self.WIN_W = info.current_w
        self.WIN_H = info.current_h
        self.screen = pygame.display.set_mode((self.WIN_W, self.WIN_H))
        pygame.display.set_caption("Territorial.io Clone")
        
        # Zone de la carte = toute la fenêtre
        self.camera = Camera(world_w, world_h, 0, 0, self.WIN_W, self.WIN_H)
        
        # Fonts (style proche du jeu original)
        self.f_tiny   = pygame.font.SysFont("Arial", 11)
        self.f_small  = pygame.font.SysFont("Arial", 14, bold=True)
        self.f_mid    = pygame.font.SysFont("Arial", 17, bold=True)
        self.f_large  = pygame.font.SysFont("Arial", 22, bold=True)
        self.f_xl     = pygame.font.SysFont("Arial", 30, bold=True)
        self._map_font_cache = {}
        
        # Rect des boutons pour la détection de clic
        self.zoom_plus_rect  = pygame.Rect(self.WIN_W - self.ST_W - 55, self.WIN_H//2 - 55, 40, 40)
        self.zoom_minus_rect = pygame.Rect(self.WIN_W - self.ST_W - 55, self.WIN_H//2 + 5, 40, 40)
        self.slider_rect = None
        self.slider_x = 0
        self.slider_w = 0
        self.minus_btn_rect = None
        self.plus_btn_rect  = None
        
        # Messages flottants (bas-droit)
        self._messages = []
        
        # Marqueurs d'attaque (x_monde, y_monde, temps)
        self._attack_markers = []
        
    def add_message(self, msg):
        self._messages.append((msg, pygame.time.get_ticks()))

    def add_attack_marker(self, wx, wy):
        if wx is not None and wy is not None:
            self._attack_markers.append((wx, wy, pygame.time.get_ticks()))

    def get_map_font(self, size):
        size = max(9, min(80, size))
        if size not in self._map_font_cache:
            self._map_font_cache[size] = pygame.font.SysFont("Arial", size, bold=True)
        return self._map_font_cache[size]

    def outlined(self, font, text, color, outline=(0,0,0), thick=2):
        base = font.render(text, True, color)
        out  = font.render(text, True, outline)
        w, h = base.get_size()
        surf = pygame.Surface((w + thick*2+2, h + thick*2+2), pygame.SRCALPHA)
        for dx in range(-thick, thick+1):
            for dy in range(-thick, thick+1):
                if dx == 0 and dy == 0: continue
                surf.blit(out, (dx + thick + 1, dy + thick + 1))
        surf.blit(base, (thick + 1, thick + 1))
        return surf

    # ─── Carte ────────────────────────────────────────────────────────────────
    def _build_map_surface(self, game_state):
        """Construit la surface monde (non zoomée)."""
        # Base : eau partout
        rgb = np.full((self.world_w, self.world_h, 3), WATER_COLOR, dtype=np.uint8)
        
        # Terre neutre
        neutral = (game_state.grid.T == -1)
        rgb[neutral] = NEUTRAL_COLOR
        
        for pid, color in PLAYER_COLORS.items():
            if pid not in game_state.players: continue
            mask = (game_state.grid.T == pid)
            if not np.any(mask): continue
            
            rgb[mask] = color
            
            # Bordures blanches en pointillés (checkerboard)
            # On détecte les pixels frontières dans l'espace (height, width) = grid space
            border = mask & ~(
                np.roll(mask, 1, axis=0) & np.roll(mask, -1, axis=0) &
                np.roll(mask, 1, axis=1) & np.roll(mask, -1, axis=1)
            )
            # border shape: (width, height)
            # rgb shape: (width, height)
            xs_grid, ys_grid = np.where(border)
            
            # Filtrer les indices hors-limites (bords de carte)
            valid = (xs_grid < self.world_w) & (ys_grid < self.world_h)
            xs_grid = xs_grid[valid]
            ys_grid = ys_grid[valid]
            
            # Motif checkerboard
            checker = (xs_grid + ys_grid) % 2 == 0
            
            rgb[xs_grid[checker], ys_grid[checker]] = BORDER_WHITE
            
        return pygame.surfarray.make_surface(rgb)

    def _render_map(self, game_state):
        cam = self.camera
        map_area = pygame.Rect(0, 0, self.WIN_W, self.WIN_H)
        
        world_surf = self._build_map_surface(game_state)
        
        zoom_w = max(1, int(self.world_w * cam.zoom))
        zoom_h = max(1, int(self.world_h * cam.zoom))
        scaled  = pygame.transform.scale(world_surf, (zoom_w, zoom_h))
        
        blit_x = -int(cam.cam_x * cam.zoom)
        blit_y = -int(cam.cam_y * cam.zoom)
        
        old_clip = self.screen.get_clip()
        self.screen.set_clip(map_area)
        self.screen.blit(scaled, (blit_x, blit_y))
        self.screen.set_clip(old_clip)

    def _render_labels(self, game_state):
        cam = self.camera
        map_area = pygame.Rect(0, 0, self.WIN_W, self.WIN_H)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(map_area)
        
        sorted_p = sorted([p for p in game_state.players.values() if p.alive],
                          key=lambda x: x.land, reverse=True)
        
        for p in sorted_p:
            if p.land < 30: continue
            cx, cy = cam.world_to_screen(p.center_x, p.center_y)
            if not map_area.collidepoint(cx, cy): continue
            
            # Taille police en fonction du territoire et du zoom
            fsize = int(math.sqrt(p.land * cam.zoom) * 0.28)
            fsize = max(9, min(60, fsize))
            
            # Estimation de la taille du diamant pour éviter d'afficher un texte trop grand
            approx_radius = int(math.sqrt(p.land) * cam.zoom * 0.7)
            
            if p.troops > 1_000_000:
                t_str = f"{p.troops/1_000_000:.1f}M"
            elif p.troops > 1_000:
                t_str = f"{p.troops/1000:.1f}k"
            else:
                t_str = str(int(p.troops))
            
            font = self.get_map_font(fsize)
            n_surf = self.outlined(font, p.name, (255,255,255), thick=1)
            t_surf = self.outlined(self.get_map_font(max(9, fsize-3)), t_str, (230,230,230), thick=1)
            
            if n_surf.get_width() > approx_radius * 2:
                continue
            
            self.screen.blit(n_surf, n_surf.get_rect(center=(cx, cy - fsize//2)))
            self.screen.blit(t_surf, t_surf.get_rect(center=(cx, cy + fsize//2 + 2)))
            
        self.screen.set_clip(old_clip)

    # ─── Leaderboard ──────────────────────────────────────────────────────────
    def _render_leaderboard(self, game_state):
        players = sorted([p for p in game_state.players.values() if p.alive],
                          key=lambda x: x.land, reverse=True)[:10]
        
        row_h = 22
        h = 30 + len(players) * row_h
        
        # Panel
        bx, by = 15, 15
        bg = pygame.Surface((self.LB_W, h), pygame.SRCALPHA)
        bg.fill((30, 30, 30, 200))
        self.screen.blit(bg, (bx, by))
        
        # Titre "LEADERBOARD"
        pygame.draw.rect(self.screen, (25, 55, 110), (bx, by, self.LB_W, 26))
        pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, self.LB_W, h), 2)
        title = self.f_small.render("LEADERBOARD", True, (255,255,255))
        self.screen.blit(title, title.get_rect(center=(bx + self.LB_W//2, by + 13)))
        
        for i, p in enumerate(players):
            y = by + 28 + i * row_h
            
            # Highlight du joueur humain
            if p.id == 1:
                pygame.draw.rect(self.screen, (20, 100, 15), (bx+2, y, self.LB_W-4, row_h))
            elif i % 2 == 0:
                pygame.draw.rect(self.screen, (40, 40, 40), (bx+2, y, self.LB_W-4, row_h))
                
            # Rang
            if i == 0:
                rank_s = self.f_small.render("1.", True, (255, 220, 50))
            else:
                rank_s = self.f_small.render(f"{i+1}.", True, (200,200,200))
            self.screen.blit(rank_s, (bx + 8, y + 3))
            
            # Nom
            name_s = self.f_small.render(p.name[:20], True, p.color)
            self.screen.blit(name_s, (bx + 30, y + 3))
            
            # Score
            score_s = self.f_small.render(str(p.land), True, (220,220,220))
            self.screen.blit(score_s, (bx + self.LB_W - score_s.get_width() - 8, y + 3))

    # ─── Stats panel ──────────────────────────────────────────────────────────
    def _render_stats(self, game_state):
        x0 = self.WIN_W - self.ST_W - 15
        y0 = 15
        h  = 145
        
        bg = pygame.Surface((self.ST_W, h), pygame.SRCALPHA)
        bg.fill((30, 30, 30, 200))
        self.screen.blit(bg, (x0, y0))
        pygame.draw.rect(self.screen, (255, 255, 255), (x0, y0, self.ST_W, h), 1)
        
        human = game_state.players.get(1)
        alive_count = sum(1 for p in game_state.players.values() if p.alive)
        total_px = game_state.width * game_state.height
        
        pct_str = f"{(human.land / max(1, total_px)) * 100:.2f}%" if human else "0.00%"
        
        if human:
            max_troops = human.land * 150
            ratio = human.troops / max(1, max_troops)
            interest_rate = max(0.0, 0.007 * (1.0 - ratio**2)) * 100
            interest_color = (255, 80, 80) if interest_rate < 1.0 else (255, 220, 50)
            interest_str = f"{interest_rate:.2f}%"
            income_str = str(int(human.land * 1.5))
        else:
            interest_color = (255, 220, 50)
            interest_str = "7.00%"
            income_str = "0"
        
        ticks = game_state.tick_count
        mins, secs = divmod(ticks // 60, 60)
        time_str = f"{mins}:{secs:02d}"
        
        rows = [
            ("Humans",      "1",          (255, 255, 255)),
            ("Bots",        str(alive_count - 1), (255,255,255)),
            ("Spectators",  "0",          (255, 255, 255)),
            ("Percentage",  pct_str,      (255, 255, 255)),
            ("Interest",    interest_str, interest_color),
            ("Income",      income_str,   (255, 255, 255)),
            ("Time",        time_str,     (100, 255, 100)),
        ]
        
        for i, (label, value, color) in enumerate(rows):
            y = y0 + 4 + i * 20
            lbl = self.f_tiny.render(label, True, (240,240,240))
            val = self.f_tiny.render(value, True, color)
            self.screen.blit(lbl, (x0 + 8, y + 2))
            self.screen.blit(val, (x0 + self.ST_W - val.get_width() - 8, y + 2))

    # ─── Jauge circulaire (% territoire neutre restant) ───────────────────────
    def _render_pie(self, game_state):
        """
        La jauge circulaire dans Territorial.io montre combien de territoire
        est encore NEUTRE (non capturé). Le % affiché = 100% - (% capturé total).
        Les segments colorés montrent la distribution entre joueurs.
        """
        cx, cy = 70, self.WIN_H - 70
        R = 55
        
        # Fond gris foncé
        pygame.draw.circle(self.screen, (25, 28, 50), (cx, cy), R + 4)
        pygame.draw.circle(self.screen, (50, 55, 80), (cx, cy), R + 4, 2)
        
        total_px = game_state.width * game_state.height
        ids, counts = np.unique(game_state.grid, return_counts=True)
        land_dict = dict(zip(ids.tolist(), counts.tolist()))
        
        neutral_px = land_dict.get(-1, 0)
        water_px   = land_dict.get(0, 0)
        land_total = total_px - water_px
        
        # Fond gris = territoire neutre
        pygame.draw.circle(self.screen, (140, 130, 110), (cx, cy), R)
        
        # Secteurs colorés pour chaque joueur
        angle_start = -math.pi / 2  # Commence en haut
        for pid, color in PLAYER_COLORS.items():
            px_count = land_dict.get(pid, 0)
            if px_count == 0: continue
            frac = px_count / max(1, land_total)
            angle_end = angle_start + frac * 2 * math.pi
            
            # Dessin d'un secteur
            pts = [(cx, cy)]
            steps = max(4, int(frac * 60))
            for k in range(steps + 1):
                a = angle_start + k / steps * (angle_end - angle_start)
                pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
            if len(pts) >= 3:
                pygame.draw.polygon(self.screen, color, pts)
            angle_start = angle_end
        
        # Cercle de bord
        pygame.draw.circle(self.screen, (200, 200, 200), (cx, cy), R, 2)
        
        # Pourcentage de territoire neutre restant
        neutral_pct = int((neutral_px / max(1, land_total)) * 100)
        pct_surf = self.f_mid.render(f"{neutral_pct}%", True, (255, 255, 255))
        # Ombre
        shadow = self.f_mid.render(f"{neutral_pct}%", True, (0,0,0))
        self.screen.blit(shadow, shadow.get_rect(center=(cx+1, cy+1)))
        self.screen.blit(pct_surf, pct_surf.get_rect(center=(cx, cy)))

    # ─── Balance bar (haut-centre) ────────────────────────────────────────────
    def _render_balance_bar(self, human):
        bw, bh = 300, 26
        bx = self.WIN_W // 2 - bw // 2
        by = 5
        
        pygame.draw.rect(self.screen, (15, 18, 35), (bx, by, bw, bh), border_radius=3)
        
        max_troops = human.land * 150
        ratio = min(1.0, human.troops / max(1, max_troops))
        fill_color = (50, 200, 60) if ratio < 0.8 else (200, 50, 50)
        fill_w = int(bw * ratio)
        if fill_w > 2:
            pygame.draw.rect(self.screen, fill_color, (bx, by, fill_w, bh), border_radius=3)
        
        pygame.draw.rect(self.screen, (60, 70, 120), (bx, by, bw, bh), 1, border_radius=3)
        
        # Texte : "balance +income"
        if human.troops > 1_000_000:
            bal_str = f"{human.troops/1_000_000:.2f}M"
        elif human.troops > 1_000:
            bal_str = f"{int(human.troops/1000)}k"
        else:
            bal_str = str(int(human.troops))
        
        income = int(human.land * 1.5)
        txt = self.f_mid.render(f"{bal_str}  +{income}", True, (255,255,255))
        shadow = self.f_mid.render(f"{bal_str}  +{income}", True, (0,0,0))
        self.screen.blit(shadow, shadow.get_rect(center=(self.WIN_W//2+1, by+bh//2+1)))
        self.screen.blit(txt, txt.get_rect(center=(self.WIN_W//2, by+bh//2)))

    # ─── Barre inférieure ─────────────────────────────────────────────────────
    def _render_bottom_bar(self, human):
        pct = human.attack_percentage
        
        btn_w, btn_h = 36, 32
        sl_w, sl_h = 340, 32
        
        total_w = btn_w * 2 + sl_w + 10
        start_x = self.WIN_W // 2 - total_w // 2
        y_pos = self.WIN_H - sl_h - 20
        
        minus_x = start_x
        sl_x    = start_x + btn_w + 5
        plus_x  = sl_x + sl_w + 5
        
        self.minus_btn_rect = pygame.Rect(minus_x, y_pos, btn_w, btn_h)
        self.plus_btn_rect  = pygame.Rect(plus_x,  y_pos,  btn_w, btn_h)
        self.slider_rect = pygame.Rect(sl_x, y_pos, sl_w, sl_h)
        self.slider_x = sl_x
        self.slider_w = sl_w
        
        # Slider : fond gris-noir, remplissage violet vif
        pygame.draw.rect(self.screen, (20, 20, 20), self.slider_rect)
        filled_w = int(sl_w * pct)
        if filled_w > 0:
            pygame.draw.rect(self.screen, (160, 30, 210), (sl_x, y_pos, filled_w, sl_h))
        pygame.draw.rect(self.screen, (255, 255, 255), self.slider_rect, 2)
        
        # Bouton "-" (Gris sombre)
        pygame.draw.rect(self.screen, (30, 30, 30), self.minus_btn_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.minus_btn_rect, 2)
        m = self.f_large.render("-", True, (255,255,255))
        self.screen.blit(m, m.get_rect(center=self.minus_btn_rect.center))
        
        # Bouton "+" (Gris sombre)
        pygame.draw.rect(self.screen, (30, 30, 30), self.plus_btn_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.plus_btn_rect, 2)
        p = self.f_large.render("+", True, (255,255,255))
        self.screen.blit(p, p.get_rect(center=self.plus_btn_rect.center))
        
        # Texte dans le slider : "balance (pct%)"
        if human.troops > 1_000_000:
            bal_str = f"{human.troops/1_000_000:.1f}M"
        elif human.troops > 1_000:
            bal_str = f"{int(human.troops/1000)}k"
        else:
            bal_str = str(int(human.troops))
            
        sl_txt = self.f_mid.render(f"{bal_str}  ({int(pct*100)}%)", True, (255,255,255))
        self.screen.blit(sl_txt, sl_txt.get_rect(center=(sl_x + sl_w//2, y_pos + sl_h//2)))

    # ─── Boutons Zoom (droite, milieu de l'écran) ─────────────────────────────
    def _render_zoom_buttons(self):
        for rect, lbl in [(self.zoom_plus_rect, "+"), (self.zoom_minus_rect, "-")]:
            pygame.draw.circle(self.screen, (30, 35, 60), rect.center, 20)
            pygame.draw.circle(self.screen, (80, 90, 140), rect.center, 20, 2)
            s = self.f_large.render(lbl, True, (220,220,220))
            self.screen.blit(s, s.get_rect(center=rect.center))

    # ─── Messages bas-droite ──────────────────────────────────────────────────
    def _render_messages(self):
        now = pygame.time.get_ticks()
        self._messages = [(m, t) for m, t in self._messages if now - t < 5000]
        
        y = self.WIN_H - 100
        for msg, _ in reversed(self._messages[-5:]):
            s = self.f_tiny.render(msg, True, (230, 230, 200))
            bg = pygame.Surface((s.get_width()+8, s.get_height()+4), pygame.SRCALPHA)
            bg.fill((0,0,0,160))
            self.screen.blit(bg, (self.WIN_W - s.get_width() - 24, y - s.get_height() - 3))
            self.screen.blit(s, (self.WIN_W - s.get_width() - 20, y - s.get_height() - 1))
            y -= s.get_height() + 6

    def _render_attack_markers(self):
        """Dessine une confirmation d'attaque : cercle vert avec une épée basique."""
        now = pygame.time.get_ticks()
        self._attack_markers = [(wx, wy, t) for wx, wy, t in self._attack_markers if now - t < 500] # Disparaît après 500ms
        
        for wx, wy, _ in self._attack_markers:
            cx, cy = self.camera.world_to_screen(wx, wy)
            # Cercle vert
            pygame.draw.circle(self.screen, (60, 200, 60), (cx, cy), 16)
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 16, 2)
            # Epée basique (une ligne en diagonale)
            pygame.draw.line(self.screen, (255, 255, 255), (cx-6, cy+6), (cx+6, cy-6), 3)
            pygame.draw.line(self.screen, (255, 255, 255), (cx-8, cy+4), (cx-4, cy+8), 3)

    # ─── Frame complète ───────────────────────────────────────────────────────
    def draw(self, game_state, clock):
        self.screen.fill(WATER_COLOR)
        
        # 1. Carte
        self._render_map(game_state)
        
        # 2. Labels sur la carte
        self._render_labels(game_state)
        
        # 3. Leaderboard (overlay)
        self._render_leaderboard(game_state)
        
        # 4. Stats panel (overlay)
        self._render_stats(game_state)
        
        # 5. Pie chart
        self._render_pie(game_state)
        
        # 6. Barre de balance
        human = game_state.players.get(1)
        if human and human.alive:
            self._render_balance_bar(human)
        
        # 7. Barre inférieure
        if human and human.alive:
            self._render_bottom_bar(human)
        
        # 8. Boutons zoom
        self._render_zoom_buttons()
        
        # 9. Markers d'attaque (clics)
        self._render_attack_markers()
        
        # 10. Messages
        self._render_messages()
        
        # 11. FPS
        fps = int(clock.get_fps())
        fps_s = self.f_tiny.render(f"FPS: {fps}", True, (150,255,150) if fps >= 50 else (255,150,50))
        self.screen.blit(fps_s, (self.LB_W + 20, 15))
        
        pygame.display.flip()
