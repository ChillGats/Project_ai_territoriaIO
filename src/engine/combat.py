import numpy as np
from collections import deque

class ActiveAttack:
    def __init__(self, player_id, attack_force, start_queue, visited):
        self.player_id = player_id
        self.attack_force = attack_force
        self.queue = start_queue
        self.visited = visited
        self.speed = max(1.0, attack_force * 0.05) 

class CombatEngine:
    @staticmethod
    def start_attack(game_state, player_id, target_x, target_y, percentage):
        player = game_state.players.get(player_id)
        if not player or not player.alive or player.troops < 2:
            return
            
        # War Tax : Attaquer coûte une pénalité immédiate de 5% de la balance pour éviter le spam
        war_tax = player.troops * 0.05
        available_for_attack = player.troops - war_tax
        
        attack_force = available_for_attack * percentage
        player.troops -= (attack_force + war_tax)
        
        ys, xs = np.where(game_state.grid == player_id)
        if len(ys) == 0: 
            player.troops += attack_force 
            return
            
        if target_x is None or target_y is None:
            if len(ys) > 1000:
                indices = np.random.choice(len(ys), 1000, replace=False)
                start_queue = deque(zip(xs[indices], ys[indices]))
                visited = set(zip(xs[indices], ys[indices]))
            else:
                start_queue = deque(zip(xs, ys))
                visited = set(zip(xs, ys))
        else:
            distances = (xs - target_x)**2 + (ys - target_y)**2
            closest_idx = np.argmin(distances)
            front_x, front_y = xs[closest_idx], ys[closest_idx]
            start_queue = deque([(front_x, front_y)])
            visited = set([(front_x, front_y)])
            
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
                continue
                
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
                                # Eau (Navigation) : Naviguer coûte cher (bateaux)
                                water_cost = 4.0
                                if attack.attack_force >= water_cost:
                                    attack.attack_force -= water_cost
                                    budget_for_frame -= water_cost
                                    # L'eau reste de l'eau, mais on propage l'onde à travers !
                                    # Cela simulera l'envoi de bateaux sans changer la couleur de la carte.
                                    attack.queue.append((nx, ny))
                                    
                            elif target_cell == -1:
                                # Terre neutre
                                cost = 1.5
                                if attack.attack_force >= cost:
                                    attack.attack_force -= cost
                                    budget_for_frame -= cost
                                    game_state.grid[ny, nx] = attack.player_id
                                    attack.queue.append((nx, ny))
                            else:
                                # Joueur Ennemi (Ratio 2:1 strict)
                                enemy_id = target_cell
                                enemy = game_state.players.get(enemy_id)
                                if not enemy or not enemy.alive: continue
                                
                                defense_power = enemy.troops / max(1, enemy.land)
                                
                                # RATIO 2:1 STRICT (L'attaquant doit payer 2x la défense)
                                attack_cost = defense_power * 2.0 
                                
                                if attack.attack_force >= attack_cost:
                                    attack.attack_force -= attack_cost
                                    budget_for_frame -= attack_cost
                                    enemy.troops -= defense_power
                                    game_state.grid[ny, nx] = attack.player_id
                                    attack.queue.append((nx, ny))
                                else:
                                    # Défaite locale : l'attaquant perd sa force, l'ennemi perd la moitié de la force attaquante
                                    enemy.troops -= (attack.attack_force / 2.0)
                                    attack.attack_force = 0
                                    break
                                    
            if attack.queue and attack.attack_force > 0:
                remaining_attacks.append(attack)
            else:
                player.troops += attack.attack_force
                
        game_state.active_attacks = remaining_attacks
