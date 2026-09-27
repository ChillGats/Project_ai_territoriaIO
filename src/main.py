import numpy as np
import pygame
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
import sys

# ==========================================
# MODULE 1 : LE MOTEUR DE JEU (Game Engine)
# ==========================================
class TerritorialGame:
    def __init__(self, size=15):
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.troops = {1: 10, 2: 10} # Troupes de départ (Ressources)
        
        # Initialisation des positions de départ
        self.grid[1, 1] = 1 # IA (Joueur 1) en haut à gauche
        self.grid[size-2, size-2] = 2 # Bot ennemi (Joueur 2) en bas à droite
        
    def step_income(self):
        # Chaque case possédée rapporte 1 troupe à chaque "tick"
        p1_cells = np.sum(self.grid == 1)
        p2_cells = np.sum(self.grid == 2)
        self.troops[1] += p1_cells
        self.troops[2] += p2_cells
        
    def get_borders(self, player):
        # Trouve toutes les cases VIDES qui touchent le territoire du joueur.
        # Mathématiquement, c'est l'équivalent d'une "dilatation morphologique".
        borders = []
        for y in range(self.size):
            for x in range(self.size):
                if self.grid[y, x] == player:
                    # On regarde les 4 voisins (Haut, Bas, Gauche, Droite)
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        # Si on ne sort pas de la carte et que la case est vide
                        if 0 <= ny < self.size and 0 <= nx < self.size:
                            if self.grid[ny, nx] == 0: 
                                borders.append((ny, nx))
        return list(set(borders)) # 'set' enlève les doublons

    def expand(self, player, direction):
        # Direction: 0=Haut, 1=Droite, 2=Bas, 3=Gauche
        borders = self.get_borders(player)
        
        # Si aucune frontière n'est dispo ou pas assez d'argent (10 troupes le coût)
        if not borders or self.troops[player] < 10: 
            return False 
            
        # Trie les frontières pour trouver la case la plus extrême dans la direction voulue
        if direction == 0:   # Haut (Coordonnée Y la plus petite)
            borders.sort(key=lambda p: p[0])
        elif direction == 1: # Droite (Coordonnée X la plus grande)
            borders.sort(key=lambda p: -p[1])
        elif direction == 2: # Bas (Coordonnée Y la plus grande)
            borders.sort(key=lambda p: -p[0])
        elif direction == 3: # Gauche (Coordonnée X la plus petite)
            borders.sort(key=lambda p: p[1])
            
        # On conquiert la première case de la liste triée
        target_y, target_x = borders[0]
        self.grid[target_y, target_x] = player
        self.troops[player] -= 10
        return True

    def render(self, screen, cell_size):
        colors = {
            0: (30, 30, 30),      # Vide (Gris foncé)
            1: (50, 150, 250),    # IA (Bleu)
            2: (250, 50, 50)      # Bot Ennemi (Rouge)
        }
        for y in range(self.size):
            for x in range(self.size):
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, colors[self.grid[y, x]], rect)
                pygame.draw.rect(screen, (20, 20, 20), rect, 1) # Dessine les lignes de la grille

# ==========================================
# MODULE 2 : L'ENVIRONNEMENT IA (Interface)
# ==========================================
class TerritorialEnv:
    def __init__(self, size=15):
        self.size = size
        self.game = TerritorialGame(size)
        
        # ESPACE D'ACTION : Ce que l'IA a le droit de faire
        # 0=Économiser, 1=S'étendre en Haut, 2=Droite, 3=Bas, 4=Gauche
        self.action_space = 5 
        
        # ESPACE D'OBSERVATION : Ce que l'IA "voit"
        # La grille complète aplatie en 1D + les troupes des 2 joueurs
        self.observation_space = size * size + 2
        
    def reset(self):
        # Remet le jeu à zéro pour une nouvelle partie
        self.game = TerritorialGame(self.size)
        return self._get_state()
        
    def _get_state(self):
        # Normalisation : Les réseaux de neurones détestent les grands nombres.
        # On divise la grille par 2 (car max=2) pour que les valeurs soient entre 0 et 1.
        flat_grid = self.game.grid.flatten() / 2.0 
        # On divise les troupes par 100 pour la même raison
        troops = np.array([self.game.troops[1] / 100.0, self.game.troops[2] / 100.0])
        return np.concatenate((flat_grid, troops), axis=0).astype(np.float32)

    def step(self, action):
        # 1. Action de notre IA (Joueur 1)
        if action > 0: # Si l'action n'est pas "0" (Économiser)
            self.game.expand(1, action - 1)
            
        # 2. Action du Bot ennemi (Il joue de manière complètement aléatoire)
        if self.game.troops[2] >= 10:
            self.game.expand(2, random.randint(0, 3))
            
        # 3. Récolte des ressources
        self.game.step_income()
        
        # 4. RÉCOMPENSE (Reward) : C'est la carotte ! 
        # Comment dire à l'IA qu'elle fait du bon travail ? 
        # On lui donne un score équivalent à son avance sur l'ennemi.
        p1_cells = np.sum(self.game.grid == 1)
        p2_cells = np.sum(self.game.grid == 2)
        reward = p1_cells - p2_cells 
        
        # Le jeu se termine quand il n'y a plus de cases vides (0)
        done = np.sum(self.game.grid == 0) == 0
        
        if done: # Bonus final pour encourager la victoire globale
            if p1_cells > p2_cells:
                reward += 100 
            else:
                reward -= 100 
                
        return self._get_state(), reward, done

# ==========================================
# MODULE 3 : L'AGENT IA (Le Cerveau)
# ==========================================
class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        # Le réseau de neurones : 3 couches de neurones. 
        # Métaphore : C'est comme un comité d'experts.
        # La couche 1 regarde les pixels, la 2 cherche des motifs (formes du territoire), 
        # la 3 prend la décision finale.
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, output_dim)

    def forward(self, x):
        # Fonction d'activation ReLU (Rectified Linear Unit) :
        # Math : f(x) = max(0, x). 
        # Sens : Un neurone ne transmet l'information que si elle est positive (pertinente).
        # Ça permet de modéliser des comportements non-linéaires (complexes).
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        # La sortie donne un "Score d'intérêt" (Q-Value) pour CHACUNE des 5 actions possibles.
        return self.fc3(x)

class DQNAgent:
    def __init__(self, state_dim, action_dim):
        self.action_dim = action_dim
        # La "mémoire" : l'IA va se souvenir de ses 2000 dernières actions pour s'entraîner dessus.
        self.memory = deque(maxlen=2000) 
        
        self.model = DQN(state_dim, action_dim)
        
        # L'Optimiseur : C'est le professeur qui corrige le cerveau. 
        # lr (Learning Rate) = 0.001 : Vitesse de correction. S'il est trop grand, 
        # l'IA apprend trop vite et oublie le passé. Trop petit, elle est trop lente.
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        # Fonction de Perte (MSELoss) : On mesure l'erreur entre ce que l'IA prévoyait 
        # et ce qui s'est vraiment passé.
        self.criterion = nn.MSELoss() 
        
        # Epsilon : Probabilité de jouer au hasard (Exploration).
        # Au début (1.0 = 100%), l'IA fait n'importe quoi pour découvrir le monde.
        self.epsilon = 1.0 
        self.epsilon_decay = 0.995 # L'IA va doucement remplacer le hasard par la réflexion.
        self.epsilon_min = 0.01

    def act(self, state):
        # Métaphore : On lance un dé à 100 faces.
        # Si on fait moins que epsilon, on explore au hasard !
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
            
        # Sinon (Exploitation), on utilise le cerveau de l'IA.
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad(): # On bloque l'apprentissage, on veut juste lire la décision.
            q_values = self.model(state_tensor)
        
        # On choisit l'action qui a reçu le score maximum (argmax) par le réseau.
        return torch.argmax(q_values[0]).item()

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, batch_size):
        # L'IA "rêve" et apprend de ses expériences passées en piochant au hasard.
        # Cela empêche qu'elle apprenne des choses "trop logiques" à la suite et qu'elle tourne en rond.
        if len(self.memory) < batch_size: return
        
        minibatch = random.sample(self.memory, batch_size)
        
        # Note : On fait une boucle pour que les maths soient lisibles, 
        # en vrai on ferait ça d'un coup (vectorisation) pour la vitesse.
        for state, action, reward, next_state, done in minibatch:
            
            # Transformation en Tenseurs (Vecteurs pour PyTorch)
            state_t = torch.FloatTensor(state).unsqueeze(0)
            next_state_t = torch.FloatTensor(next_state).unsqueeze(0)
            reward_t = torch.FloatTensor([reward])
            
            # --- LE COEUR MATHÉMATIQUE DE L'APPRENTISSAGE (L'Équation de Bellman) ---
            
            # 1. Quelle est l'évaluation ACTUELLE du cerveau pour ce moment ?
            current_q = self.model(state_t)
            
            # 2. Quelle est l'évaluation de la MEILLEURE action possible au tour SUIVANT ?
            # .detach() coupe le gradient. On ne veut pas modifier le futur, on veut s'y ajuster.
            max_next_q = torch.max(self.model(next_state_t).detach())
            
            # 3. La cible idéale : Récompense Immédiate + (0.95 * Potentiel Futur)
            # 0.95 s'appelle le "Facteur d'Escompte" (Gamma). L'IA préfère une récompense 
            # aujourd'hui plutôt que demain, car le futur est incertain.
            target_q = reward_t + (0.95 * max_next_q * (1 - int(done)))
            
            # 4. On crée le corrigé de l'examen
            target_f = current_q.clone()
            target_f[0][action] = target_q # On ne corrige que l'action qui a été réellement jouée
            
            # 5. Calcul de l'erreur (Loss) 
            # Math : (Prédit - Cible)²
            loss = self.criterion(current_q, target_f)
            
            # 6. Rétropropagation (Backpropagation)
            self.optimizer.zero_grad() # Efface les brouillons de calcul précédents
            loss.backward()            # Calcule le Gradient: "Dans quel sens je dois tourner les boutons du cerveau pour réduire l'erreur ?"
            self.optimizer.step()      # Tourne effectivement les boutons (met à jour les poids)
            
        # On réduit doucement l'exploration (Epsilon)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# ==========================================
# MODULE 4 : LA BOUCLE PRINCIPALE (Main)
# ==========================================
if __name__ == "__main__":
    pygame.init()
    cell_size = 30
    grid_size = 15
    screen = pygame.display.set_mode((grid_size * cell_size, grid_size * cell_size))
    pygame.display.set_caption("Territorial.io - IA Training (DQN)")
    clock = pygame.time.Clock()

    env = TerritorialEnv(size=grid_size)
    agent = DQNAgent(env.observation_space, env.action_space)
    
    episodes = 500
    batch_size = 32
    
    for e in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            # Pour éviter que la fenêtre fige
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
            # 1. Obtenir l'action (Le cerveau réfléchit)
            action = agent.act(state)
            
            # 2. Jouer l'action (Le jeu avance d'un tick)
            next_state, reward, done = env.step(action)
            
            # 3. Sauvegarder dans la mémoire
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            
            # 4. Dessiner le jeu
            screen.fill((0, 0, 0))
            env.game.render(screen, cell_size)
            pygame.display.flip()
            # 30 FPS. Si tu veux que l'entraînement soit invisible et instantané, 
            # tu peux retirer clock.tick et les rendus.
            clock.tick(30) 
            
            # 5. Entraîner le cerveau sur les souvenirs passés
            agent.replay(batch_size)
            
        print(f"Épisode {e+1}/{episodes} | Score: {total_reward} | Hasard (Epsilon): {agent.epsilon:.2f}")

    pygame.quit()
