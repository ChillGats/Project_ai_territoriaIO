import pygame
import sys
from engine.game_state import GameState
from engine.economy import Economy
from engine.combat import CombatEngine
from graphics.renderer import Renderer
from players.human_player import HumanPlayer
from players.bot_player import BotPlayer

def process_action(state, renderer, player_obj, action):
    """Interprète l'action retournée par un joueur et l'applique au moteur."""
    atype = action[0]

    if atype == "set_pct":
        state.players[player_obj.id].attack_percentage = action[1]

    elif atype == "attack":
        tx, ty = action[1], action[2]
        pct = state.players[player_obj.id].attack_percentage
        CombatEngine.start_attack(state, player_obj.id, tx, ty, pct)

    elif atype == "zoom":
        delta = action[1]
        renderer.zoom = max(0.5, min(6.0, renderer.zoom + delta))
        renderer.clamp_camera()

    # "idle" ne fait rien


if __name__ == "__main__":
    MAP_W, MAP_H = 900, 700   # Résolution de la carte (espace monde)
    
    renderer = Renderer(MAP_W, MAP_H)
    state    = GameState(MAP_W, MAP_H)

    # ── Joueur humain (ID 1) ──────────────────────────────────────────────────
    p_color = renderer.PLAYER_COLORS[1]
    state.add_player(1, p_color, "Toi", None, None)
    human = HumanPlayer(1)
    players = [human]

    # ── 9 Bots ───────────────────────────────────────────────────────────────
    bot_names = ["Empire Rouge", "Royaume Vert", "Sultanat", "Duché Violet",
                 "République Cyan", "Khalifat", "Gris Corp", "Sombre Nation", "Alliance Rose"]
    for i in range(2, 11):
        color = renderer.PLAYER_COLORS.get(i, (128, 128, 128))
        state.add_player(i, color, bot_names[i-2], None, None)
        players.append(BotPlayer(i))

    # ── Boucle principale ─────────────────────────────────────────────────────
    clock = pygame.time.Clock()
    print("Territorial.io Clone — Moteur Asynchrone v2 Prêt !")
    print("Commandes : Clic Gauche = Attaque | Molette = % troupes | +/- = Zoom | Espace = Expansion globale")

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 1. Économie (intérêts + revenus)
        Economy.step(state)
        state.recalculate_land_and_centers()

        # 2. Propagation des attaques asynchrones
        CombatEngine.step(state)

        # 3. Actions des joueurs
        for p in players:
            if not state.players[p.id].alive:
                continue
            if isinstance(p, HumanPlayer):
                action = p.get_action(state, events, renderer)
            else:
                # Les bots renvoient une action au format bot (tuple 4)
                raw = p.get_action(state, events)
                # Convertir le format bot → format moteur
                tx, ty, atype_bot, new_pct = raw
                if atype_bot == 1:
                    action = ("set_pct", new_pct)
                elif atype_bot == 2:
                    pct_bot = state.players[p.id].attack_percentage
                    action = ("attack", tx, ty)
                else:
                    action = ("idle",)

            process_action(state, renderer, p, action)

        # 4. Rendu
        renderer.draw(state, clock)
        clock.tick(60)
