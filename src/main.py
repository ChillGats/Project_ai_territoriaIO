import pygame
import sys
from engine.game_state import GameState
from engine.economy import Economy
from engine.combat import CombatEngine
from graphics.renderer import Renderer
from players.human_player import HumanPlayer
from players.bot_player import BotPlayer

def process_action(state, player_obj, action):
    target_x, target_y, action_type, new_pct = action
    
    if action_type == 1:
        state.players[player_obj.id].attack_percentage = new_pct
        
    elif action_type == 2:
        pct = state.players[player_obj.id].attack_percentage
        CombatEngine.start_attack(state, player_obj.id, target_x, target_y, pct)

if __name__ == "__main__":
    MAP_W, MAP_H = 600, 600
    SCALE = 1
    
    renderer = Renderer(MAP_W, MAP_H, scale=SCALE)
    state = GameState(MAP_W, MAP_H)
    
    # 1 Humain vs 9 Bots
    state.add_player(1, (50, 150, 250), "Toi", None, None) 
    players = [HumanPlayer(1, scale=SCALE)]
    
    bot_names = ["Rouge", "Vert", "Jaune", "Violet", "Cyan", "Orange", "Gris", "Noir", "Rose"]
    for i in range(2, 11):
        color = renderer.colors[i]
        state.add_player(i, color, f"Bot {bot_names[i-2]}", None, None)
        players.append(BotPlayer(i))
        
    clock = pygame.time.Clock()
    print("Moteur Asynchrone Prêt !")
    
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        # 1. Économie
        Economy.step(state)
        state.recalculate_land_and_centers()
        
        # 2. Gestion des attaques asynchrones (La vague de pixels)
        CombatEngine.step(state)
        
        # 3. Actions
        for p in players:
            if state.players[p.id].alive:
                action = p.get_action(state, events)
                process_action(state, p, action)
                
        # 4. Rendu
        renderer.draw(state)
        clock.tick(60) 
