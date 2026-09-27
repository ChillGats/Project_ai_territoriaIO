import numpy as np
from collections import deque

# ─────────────────────────────────────────────────────────────────────────────
# Territorial.io utilise une expansion en DIAMANT (distance de Manhattan).
# Contrairement à un cercle (distance Euclidienne), la distance de Manhattan
# donne cette forme caractéristique de carré tourné à 45°.
# Exemple : un pixel est "proche" si |dx| + |dy| <= rayon (pas dx²+dy²)
# ─────────────────────────────────────────────────────────────────────────────

class ActiveAttack:
    def __init__(self, player_id, attack_force, start_queue, visited):
        self.player_id   = player_id
        self.attack_force = attack_force
        self.queue       = start_queue  # deque de (x, y) : le front de l'onde
        self.visited     = visited      # set de (x, y) : pixels déjà évalués
        # Vitesse = pixels conquis par frame, proportionnel aux troupes allouées
        self.speed       = max(2, int(attack_force * 0.08))


class CombatEngine:
    @staticmethod
    def start_attack(game_state, player_id, target_x, target_y, percentage):
        """Lance une vague d'attaque depuis les frontières du joueur."""
        player = game_state.players.get(player_id)
        if not player or not player.alive or player.troops < 2:
            return

        # War Tax (5%) : évite le spam de micro-attaques
        war_tax    = player.troops * 0.05
        available  = player.troops - war_tax
        force      = available * percentage
        player.troops -= (force + war_tax)

        # Trouver les pixels frontières du joueur (bord de son territoire)
        ys, xs = np.where(game_state.grid == player_id)
        if len(ys) == 0:
            player.troops += force
            return

        if target_x is None or target_y is None:
            # Expansion Globale → On démarre depuis toutes les frontières
            # On détecte les frontières : pixels qui ont un voisin non-joueur
            g = game_state.grid
            pid = player_id
            h, w = g.shape

            # Masque joueur
            p_mask = (g == pid)
            # Voisins (roll 4-dirs)
            frontier_mask = p_mask & (
                (np.roll(g, 1, axis=0) != pid) |
                (np.roll(g, -1, axis=0) != pid) |
                (np.roll(g, 1, axis=1) != pid) |
                (np.roll(g, -1, axis=1) != pid)
            )
            fy, fx = np.where(frontier_mask)
            
            if len(fy) == 0:
                player.troops += force
                return

            # On échantillonne les frontières pour limiter la mémoire
            max_pts = 600
            if len(fy) > max_pts:
                idx = np.random.choice(len(fy), max_pts, replace=False)
                pts = list(zip(fx[idx], fy[idx]))
            else:
                pts = list(zip(fx, fy))

            start_queue = deque(pts)
            visited     = set(pts)
        else:
            # Attaque Ciblée → On démarre depuis le pixel du joueur le plus proche de la cible
            dist = np.abs(xs - target_x) + np.abs(ys - target_y)  # Distance de Manhattan !
            idx  = np.argmin(dist)
            fx, fy = xs[idx], ys[idx]
            start_queue = deque([(fx, fy)])
            visited     = {(fx, fy)}

        if not hasattr(game_state, 'active_attacks'):
            game_state.active_attacks = []

        game_state.active_attacks.append(
            ActiveAttack(player_id, force, start_queue, visited)
        )

    @staticmethod
    def step(game_state):
        """Fait avancer toutes les vagues d'attaque en cours d'une frame."""
        if not hasattr(game_state, 'active_attacks'):
            game_state.active_attacks = []

        remaining = []

        for attack in game_state.active_attacks:
            player = game_state.players.get(attack.player_id)
            if not player or not player.alive:
                continue  # Le joueur est mort, l'attaque s'arrête

            budget = attack.speed  # Pixels que l'on peut conquérir ce tick

            while attack.queue and attack.attack_force > 0 and budget > 0:
                cx, cy = attack.queue.popleft()

                # 4-voisins : carré de Manhattan → forme diamant !
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = cx + dx, cy + dy

                    if not (0 <= nx < game_state.width and 0 <= ny < game_state.height):
                        continue
                    if (nx, ny) in attack.visited:
                        continue

                    attack.visited.add((nx, ny))
                    cell = game_state.grid[ny, nx]

                    # ── Pixel du joueur lui-même → continuer de propager ──────
                    if cell == attack.player_id:
                        attack.queue.append((nx, ny))

                    # ── Eau → coût de navigation élevé ────────────────────────
                    elif cell == 0:
                        cost = 4.0
                        if attack.attack_force >= cost:
                            attack.attack_force -= cost
                            budget -= cost
                            attack.queue.append((nx, ny))

                    # ── Terre neutre → conquête facile ─────────────────────────
                    elif cell == -1:
                        cost = 1.0
                        if attack.attack_force >= cost:
                            attack.attack_force -= cost
                            budget -= cost
                            game_state.grid[ny, nx] = attack.player_id
                            attack.queue.append((nx, ny))

                    # ── Ennemi → Ratio 2:1 strict ──────────────────────────────
                    else:
                        enemy = game_state.players.get(cell)
                        if not enemy or not enemy.alive:
                            # Case morte → conquête libre
                            game_state.grid[ny, nx] = attack.player_id
                            attack.queue.append((nx, ny))
                            continue

                        # Défense par pixel = densité de troupes de l'ennemi
                        defense = enemy.troops / max(1, enemy.land)
                        cost    = defense * 2.0  # Ratio 2:1

                        if attack.attack_force >= cost:
                            attack.attack_force -= cost
                            budget -= cost
                            enemy.troops       -= defense
                            game_state.grid[ny, nx] = attack.player_id
                            attack.queue.append((nx, ny))
                        else:
                            # L'attaquant s'épuise : l'ennemi absorbe le reste
                            enemy.troops -= attack.attack_force / 2.0
                            attack.attack_force = 0
                            break

            # Attaque encore active ?
            if attack.queue and attack.attack_force > 0:
                remaining.append(attack)
            else:
                # Remboursement des troupes non utilisées
                player.troops += max(0, attack.attack_force)

        game_state.active_attacks = remaining
