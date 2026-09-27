class Economy:
    @staticmethod
    def step(game_state):
        game_state.tick_count += 1
        
        # Le cycle de revenu (La jauge verticale dans Territorial.io)
        # La vitesse dépend de la taille de la map, disons 100 frames pour un cycle
        game_state.cycle_step += 1
        cycle_complete = False
        if game_state.cycle_step >= 100:
            game_state.cycle_step = 0
            cycle_complete = True
            
        for player in game_state.players.values():
            if not player.alive:
                continue
                
            # 1. REVENU DES TERRES (Seulement quand le cycle est complet)
            if cycle_complete:
                player.troops += player.land * 1.5 # Le revenu brut
                
            # 2. INTÉRÊTS COMPOSÉS (À chaque tick)
            # Dans Territorial.io, l'argent génère de l'argent (jusqu'à une limite)
            max_troops = player.land * 150
            
            if player.troops < max_troops:
                ratio = player.troops / max(1, player.land)
                
                # Modèle simplifié des intérêts de Territorial.io
                if ratio < 50:
                    interest_rate = 0.005 # Intérêt fort
                elif ratio < 100:
                    interest_rate = 0.002 # Intérêt moyen
                else:
                    interest_rate = 0.0005 # INTÉRÊT ROUGE (très faible)
                    
                player.troops += player.troops * interest_rate
                
            # Cap maximal absolu
            if player.troops > max_troops:
                player.troops = max_troops
