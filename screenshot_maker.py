import sys, os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, "src")

import pygame
pygame.init()

from engine.game_state import GameState
from engine.economy import Economy
from engine.combat import CombatEngine
from graphics.renderer import Renderer
from players.bot_player import BotPlayer

MAP_W, MAP_H = 900, 700
renderer = Renderer(MAP_W, MAP_H)
state = GameState(MAP_W, MAP_H)

bot_names = ["Empire Rouge", "Royaume Vert", "Sultanat", "Duche Violet",
             "Repub Cyan", "Khalifat", "Gris Corp", "Sombre Nation", "Alliance Rose"]
players = []
for i in range(1, 11):
    color = renderer.PLAYER_COLORS.get(i, (128,128,128))
    state.add_player(i, color, bot_names[i-1] if i <= len(bot_names) else f"Bot{i}", None, None)
    players.append(BotPlayer(i))

# Simuler 800 ticks
for tick in range(800):
    Economy.step(state)
    state.recalculate_land_and_centers()
    CombatEngine.step(state)
    for p in players:
        if state.players[p.id].alive:
            raw = p.get_action(state, [])
            tx, ty, atype, new_pct = raw
            if atype == 2:
                state.players[p.id].attack_percentage = 0.15
                CombatEngine.start_attack(state, p.id, tx, ty, 0.15)

clock = pygame.time.Clock()
renderer.draw(state, clock)

out = "C:\\Users\\gatsb\\.gemini\\antigravity-ide\\brain\\f257219c-f9a9-4552-8a5f-36b3bebeb715\\scratch\\screenshot_v2.png"
pygame.image.save(renderer.screen, out)
print(f"Saved: {out}")
