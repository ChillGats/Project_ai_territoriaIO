import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
import math
from collections import deque
from .base_player import BasePlayer

class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_dim, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, output_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

class DQNAgent(BasePlayer):
    def __init__(self, player_id):
        super().__init__(player_id)
        
        # Actions discrètes : 
        # 0 = Attendre
        # Directions : 8 angles + 1 globale = 9 cibles
        # Pourcentages : 10%, 25%, 50%, 100% = 4 choix
        # Total : 1 + (9 * 4) = 37 actions possibles
        self.action_dim = 37
        
        # État (Features simples pour ne pas faire exploser le CPU) :
        # - Mes Troupes, Mon Territoire, Mon X, Mon Y
        # - Les mêmes stats pour 4 autres joueurs maximum (4 * 4 = 16)
        # Total = 20 dimensions
        self.state_dim = 20
        
        self.model = DQN(self.state_dim, self.action_dim)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.memory = deque(maxlen=5000)
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.999
        self.criterion = nn.MSELoss()
        
        self.last_state = None
        self.last_action = 0

    def _extract_state(self, game_state):
        state = np.zeros(self.state_dim, dtype=np.float32)
        me = game_state.players.get(self.id)
        if not me or not me.alive:
            return state
            
        state[0] = me.troops / 10000.0
        state[1] = me.land / 10000.0
        state[2] = me.center_x / game_state.width
        state[3] = me.center_y / game_state.height
        
        idx = 4
        for p in game_state.players.values():
            if p.id != self.id and p.alive and idx < 20:
                state[idx] = p.troops / 10000.0
                state[idx+1] = p.land / 10000.0
                state[idx+2] = p.center_x / game_state.width
                state[idx+3] = p.center_y / game_state.height
                idx += 4
                
        return state

    def get_action(self, game_state, events=None):
        state = self._extract_state(game_state)
        self.last_state = state
        
        if np.random.rand() <= self.epsilon:
            action_idx = random.randrange(self.action_dim)
        else:
            state_t = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                q_values = self.model(state_t)
            action_idx = torch.argmax(q_values[0]).item()
            
        self.last_action = action_idx
        
        if action_idx == 0:
            return (None, None, 0, None)
            
        # Décodage de l'action
        # L'index va de 1 à 36
        idx = action_idx - 1
        dir_idx = idx // 4 # 0 à 8
        pct_idx = idx % 4 # 0 à 3
        
        percentages = [0.1, 0.25, 0.5, 1.0]
        pct = percentages[pct_idx]
        
        if dir_idx == 8: # Globale
            target_x, target_y = None, None
        else:
            # 8 angles
            angle = dir_idx * (math.pi / 4)
            dist = min(game_state.width, game_state.height) // 2
            me = game_state.players[self.id]
            target_x = int(me.center_x + math.cos(angle) * dist)
            target_y = int(me.center_y + math.sin(angle) * dist)
            
            # Clamp
            target_x = max(0, min(game_state.width-1, target_x))
            target_y = max(0, min(game_state.height-1, target_y))
            
        # On définit le pourcentage du joueur
        game_state.players[self.id].attack_percentage = pct
        
        return (target_x, target_y, 2, None)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, batch_size):
        if len(self.memory) < batch_size: return
        
        minibatch = random.sample(self.memory, batch_size)
        
        for state, action, reward, next_state, done in minibatch:
            state_t = torch.FloatTensor(state).unsqueeze(0)
            next_state_t = torch.FloatTensor(next_state).unsqueeze(0)
            reward_t = torch.FloatTensor([reward])
            
            current_q = self.model(state_t)
            max_next_q = torch.max(self.model(next_state_t).detach())
            
            target_q = reward_t + (0.95 * max_next_q * (1 - int(done)))
            
            target_f = current_q.clone()
            target_f[0][action] = target_q
            
            loss = self.criterion(current_q, target_f)
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

