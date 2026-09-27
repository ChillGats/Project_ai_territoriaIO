class Economy:
    @staticmethod
    def step(game_state):
        game_state.tick_count += 1
        
        # Le cycle de revenu
        game_state.cycle_step += 1
        cycle_complete = False
        if game_state.cycle_step >= 100:
            game_state.cycle_step = 0
            cycle_complete = True
            
        for player in game_state.players.values():
            if not player.alive:
                continue
                
            # 1. REVENU DES TERRES
            if cycle_complete:
                player.troops += player.land * 1.5 
                
            # 2. INTÉRÊTS COMPOSÉS (Équation continue)
            max_troops = player.land * 150
            
            if player.troops < max_troops and player.land > 0:
                ratio = player.troops / max_troops
                
                # Équation parabolique inversée : 
                # L'intérêt est maximum à 0 troupes, et décroît jusqu'à 0 quand ratio = 1.0 (cap max).
                # Cela reproduit la courbe lisse de Territorial.io.
                base_interest = 0.007
                interest_rate = base_interest * (1.0 - (ratio ** 2))
                
                # On s'assure que l'intérêt n'est jamais négatif
                interest_rate = max(0.0, interest_rate)
                
                player.troops += player.troops * interest_rate
                
            # Cap maximal absolu
            if player.troops > max_troops:
                player.troops = max_troops
