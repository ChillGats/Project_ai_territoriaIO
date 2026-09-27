import numpy as np
from collections import deque

class ActiveAttack:
    def __init__(self, player_id, attack_force, start_queue, visited):
        self.player_id = player_id
        self.attack_force = attack_force
        self.queue = start_queue
        self.visited = visited
        # Vitesse : combien de "coût" on peut dépenser par frame. 
        # Plus on envoie de troupes, plus l'onde se propage vite !
        self.speed = max(1.0, attack_force * 0.05) 

class CombatEngine:
    @staticmethod
    def start_attack(game_state, player_id, target_x, target_y, percentage):
        player = game_state.players.get(player_id)
        if not player or not player.alive or player.troops < 2:
            return
            
        attack_force = player.troops * percentage
        player.troops -= attack_force
        
        ys, xs = np.where(game_state.grid == player_id)
        if len(ys) == 0: 
            player.troops += attack_force # Remboursement
            return
            
        if target_x is None or target_y is None:
            # Expansion Globale
            if len(ys) > 1000:
                indices = np.random.choice(len(ys), 1000, replace=False)
                start_queue = deque(zip(xs[indices], ys[indices]))
                visited = set(zip(xs[indices], ys[indices]))
            else:
                start_queue = deque(zip(xs, ys))
                visited = set(zip(xs, ys))
        else:
            # Expansion Dirigée
            distances = (xs - target_x)**2 + (ys - target_y)**2
            closest_idx = np.argmin(distances)
            front_x, front_y = xs[closest_idx], ys[closest_idx]
            start_queue = deque([(front_x, front_y)])
            visited = set([(front_x, front_y)])
            
        # On ajoute cette attaque à la liste des attaques en cours
        if not hasattr(game_state, 'active_attacks'):
            game_state.active_attacks = []
            
        game_state.active_attacks.append(ActiveAttack(player_id, attack_force, start_queue, visited))

    @staticmethod
    def step(game_state):
        if not hasattr(game_state, 'active_attacks'):
            game_state.active_attacks = []
            
        remaining_attacks = []
        
        for attack in game_state.active_attacks:
            player = game_state.players.get(attack.player_id)
            if not player or not player.alive:
                continue # L'attaque s'arrête si le joueur meurt
                
            # Budget de conquête pour cette frame
            budget_for_frame = attack.speed
            
            while attack.queue and attack.attack_force > 0 and budget_for_frame > 0:
                cx, cy = attack.queue.popleft()
                
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    
                    if 0 <= nx < game_state.width and 0 <= ny < game_state.height:
                        if (nx, ny) not in attack.visited:
                            attack.visited.add((nx, ny))
                            target_cell = game_state.grid[ny, nx]
                            
                            if target_cell == attack.player_id:
                                attack.queue.append((nx, ny))
                            elif target_cell == 0:
                                # Eau
                                continue
                            elif target_cell == -1:
                                # Terre neutre
                                cost = 1.5
                                if attack.attack_force >= cost:
                                    attack.attack_force -= cost
                                    budget_for_frame -= cost
                                    game_state.grid[ny, nx] = attack.player_id
                                    attack.queue.append((nx, ny))
                            else:
                                # Ennemi
                                enemy_id = target_cell
                                enemy = game_state.players.get(enemy_id)
                                if not enemy or not enemy.alive: continue
                                
                                defense_power = enemy.troops / max(1, enemy.land)
                                attack_cost = defense_power * 2.0 
                                
                                if attack.attack_force >= attack_cost:
                                    attack.attack_force -= attack_cost
                                    budget_for_frame -= attack_cost
                                    enemy.troops -= defense_power
                                    game_state.grid[ny, nx] = attack.player_id
                                    attack.queue.append((nx, ny))
                                else:
                                    enemy.troops -= (attack.attack_force / 2.0)
                                    attack.attack_force = 0
                                    break
                                    
            # Si l'attaque n'est pas finie, on la garde pour la prochaine frame
            if attack.queue and attack.attack_force > 0:
                remaining_attacks.append(attack)
            else:
                # L'attaque est finie, on rembourse les troupes non utilisées
                player.troops += attack.attack_force
                
        game_state.active_attacks = remaining_attacks
