import pygame
import sys
from engine.game_state import GameState
from engine.economy import Economy
from engine.combat import CombatEngine
from graphics.renderer import Renderer, PLAYER_COLORS
from players.human_player import HumanPlayer
from players.bot_player import BotPlayer


def process_action(state, renderer, player_obj, action):
    atype = action[0]
    
    if atype == "set_pct":
        state.players[player_obj.id].attack_percentage = action[1]
        
    elif atype == "attack":
        tx, ty = action[1], action[2]
        pct = state.players[player_obj.id].attack_percentage
        renderer.add_attack_marker(tx, ty)
        CombatEngine.start_attack(state, player_obj.id, tx, ty, pct)

    # "zoom" est géré directement par la caméra dans HumanPlayer
    # "idle" ne fait rien


if __name__ == "__main__":
    MAP_W, MAP_H = 900, 700

    renderer = Renderer(MAP_W, MAP_H)
    state    = GameState(MAP_W, MAP_H)

    # Joueur humain
    p1_color = PLAYER_COLORS[1]
    state.add_player(1, p1_color, "Toi", None, None)
    human = HumanPlayer(1)
    players = [human]

    # 9 Bots avec de vrais noms d'empires
    bot_names = ["Ottoman Empire", "British Empire", "Zulu Empire",
                 "Kaabu Empire", "Austria-Hungary", "Qin Dynasty",
                 "Joseon", "Maratha Empire", "Mughal Empire"]
    for i in range(2, 11):
        color = PLAYER_COLORS.get(i, (128,128,128))
        state.add_player(i, color, bot_names[i-2], None, None)
        players.append(BotPlayer(i))

    # Centrer la caméra sur le joueur humain dès le départ
    p1 = state.players[1]
    renderer.camera.center_on(p1.center_x, p1.center_y)
    renderer.camera.zoom = 4.0  # Zoom de départ proche du joueur

    clock  = pygame.time.Clock()
    print("Territorial.io Clone v3 - Pret!")
    print("Controles: Clic Gauche=Attaque | Molette=Zoom | Clic Droit=Deplacer | Espace=Expansion")

    # Pour détecter les morts et afficher des messages
    alive_set = set(state.players.keys())

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        # 1. Economie
        Economy.step(state)
        state.recalculate_land_and_centers()

        # 2. Messages de mort
        current_alive = set(p.id for p in state.players.values() if p.alive)
        for pid in alive_set - current_alive:
            name = state.players[pid].name
            renderer.add_message(f"{name} left the game.")
        alive_set = current_alive

        # 3. Attaques asynchrones
        CombatEngine.step(state)

        # 4. Actions des joueurs
        for p in players:
            if not state.players[p.id].alive:
                continue
                
            if isinstance(p, HumanPlayer):
                action = p.get_action(state, events, renderer)
                if action[0] != "idle":
                    process_action(state, renderer, p, action)
            else:
                raw = p.get_action(state, events)
                tx, ty, atype_bot, new_pct = raw
                if atype_bot == 1:
                    process_action(state, renderer, p, ("set_pct", new_pct))
                elif atype_bot == 2:
                    pct = state.players[p.id].attack_percentage
                    CombatEngine.start_attack(state, p.id, tx, ty, pct)

        # 5. Rendu
        renderer.draw(state, clock)
        clock.tick(60)
