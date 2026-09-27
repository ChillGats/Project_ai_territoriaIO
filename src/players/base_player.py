class BasePlayer:
    def __init__(self, player_id):
        self.id = player_id

    def get_action(self, game_state, events=None):
        """
        Doit retourner une action sous la forme : 
        (target_x, target_y, action_type)
        
        action_type : 
        0 = Attendre / Ne rien faire
        1 = Changer le pourcentage d'attaque
        2 = Lancer une attaque sur (target_x, target_y)
        """
        raise NotImplementedError
