import pygame
import sys
import os
from src.engine.game_state import GameState
from src.engine.economy import Economy
from src.engine.combat import CombatEngine
from src.graphics.renderer import Renderer
from src.players.bot_player import BotPlayer

MAP_W, MAP_H = 1200, 800
SCALE = 1

renderer = Renderer(MAP_W, MAP_H, scale=SCALE)
state = GameState(MAP_W, MAP_H)

bot_names = ["Rouge", "Vert", "Jaune", "Violet", "Cyan", "Orange", "Gris", "Noir", "Rose", "Bleu"]
players = []
for i in range(1, 11):
    color = renderer.colors[i]
    state.add_player(i, color, f"Bot {bot_names[i-1]}", None, None)
    players.append(BotPlayer(i))

# Simule 500 frames pour laisser les territoires grandir
for _ in range(500):
    Economy.step(state)
    state.recalculate_land_and_centers()
    CombatEngine.step(state)
    for p in players:
        if state.players[p.id].alive:
            action = p.get_action(state, [])
            if action[2] == 2:
                CombatEngine.start_attack(state, p.id, action[0], action[1], action[3] if action[3] else state.players[p.id].attack_percentage)

renderer.draw(state)
pygame.image.save(renderer.screen, "C:\\Users\\gatsb\\.gemini\\antigravity-ide\\brain\\f257219c-f9a9-4552-8a5f-36b3bebeb715\\scratch\\screenshot.png")
print("Screenshot saved!")
