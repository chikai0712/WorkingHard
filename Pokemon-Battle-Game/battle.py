"""
Battle Logic Management
"""


class Battle:
    """Battle Management Class"""
    
    def __init__(self, ash_team, comp_team):
        """
        Initialize Battle
        
        Args:
            ash_team: Ash's Pokemon team list
            comp_team: Computer's Pokemon team list
        """
        self.ash_team = ash_team
        self.comp_team = comp_team
        self.ash_idx = 0  # Ash's current Pokemon index
        self.comp_idx = 0  # Computer's current Pokemon index
        self.game_state = "BATTLE"  # Game state: BATTLE, FORCE_SWITCH, WIN, LOSE
        self.message = ""  # Battle message
    
    def attack(self):
        """Execute attack turn"""
        if self.game_state != "BATTLE":
            return
        
        # Get current Pokemon
        player_pkmn = self.ash_team[self.ash_idx]
        comp_pkmn = self.comp_team[self.comp_idx]
        
        # Player attacks
        damage = player_pkmn.atk
        comp_pkmn.take_damage(damage)
        self.message = f"{player_pkmn.name} attacked {comp_pkmn.name}, dealt {damage} damage!"
        print(self.message)
        
        # Check if computer's Pokemon fainted
        if not comp_pkmn.is_alive():
            self.message = f"{comp_pkmn.name} fainted!"
            print(self.message)
            self.auto_switch_comp()
            if self.check_winner():
                return
        
        # Computer counterattacks
        comp_pkmn = self.comp_team[self.comp_idx]  # May have switched
        damage = comp_pkmn.atk
        player_pkmn.take_damage(damage)
        self.message = f"{comp_pkmn.name} counterattacked {player_pkmn.name}, dealt {damage} damage!"
        print(self.message)
        
        # Check if player's Pokemon fainted
        if not player_pkmn.is_alive():
            self.message = f"{player_pkmn.name} fainted!"
            print(self.message)
            if any(p.is_alive() for p in self.ash_team):
                self.game_state = "FORCE_SWITCH"
                self.message = "Choose your next Pokemon!"
            else:
                self.game_state = "LOSE"
                self.message = "Computer wins!"
    
    def switch_pokemon(self, new_idx):
        """
        Switch Pokemon
        
        Args:
            new_idx: Index of Pokemon to switch to
            
        Returns:
            bool: Whether switch was successful
        """
        if 0 <= new_idx < len(self.ash_team):
            if self.ash_team[new_idx].is_alive():
                old_name = self.ash_team[self.ash_idx].name
                self.ash_idx = new_idx
                new_name = self.ash_team[self.ash_idx].name
                self.game_state = "BATTLE"
                self.message = f"Ash sent out {new_name}!"
                print(self.message)
                return True
        return False
    
    def auto_switch_comp(self):
        """Computer auto-switch"""
        for i in range(len(self.comp_team)):
            if self.comp_team[i].is_alive() and i != self.comp_idx:
                old_name = self.comp_team[self.comp_idx].name
                self.comp_idx = i
                new_name = self.comp_team[self.comp_idx].name
                self.message = f"Computer sent out {new_name}!"
                print(self.message)
                return
        # No alive Pokemon left
        self.game_state = "WIN"
        self.message = "Ash wins!"
    
    def check_winner(self):
        """
        Check winner
        
        Returns:
            bool: Whether game is over
        """
        ash_alive = any(p.is_alive() for p in self.ash_team)
        comp_alive = any(p.is_alive() for p in self.comp_team)
        
        if not comp_alive:
            self.game_state = "WIN"
            self.message = "Ash wins!"
            print(self.message)
            return True
        elif not ash_alive:
            self.game_state = "LOSE"
            self.message = "Computer wins!"
            print(self.message)
            return True
        return False
    
    def get_current_pokemon(self):
        """
        Get current Pokemon in battle
        
        Returns:
            tuple: (player Pokemon, computer Pokemon)
        """
        return self.ash_team[self.ash_idx], self.comp_team[self.comp_idx]

