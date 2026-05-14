"""
Pokemon Class Definition
"""
import pygame


class Pokemon:
    """Pokemon Class"""
    
    def __init__(self, name, hp, atk, img_path):
        """
        Initialize Pokemon
        
        Args:
            name: Pokemon name
            hp: Maximum HP
            atk: Attack power
            img_path: Image path
        """
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        
        # Load image
        try:
            self.image = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (250, 250))
        except Exception as e:
            print(f"Warning: Cannot load image {img_path}, using default")
            # If image loading fails, use gray square
            self.image = pygame.Surface((250, 250))
            self.image.fill((150, 150, 150))
    
    def is_alive(self):
        """Check if alive"""
        return self.hp > 0
    
    def take_damage(self, damage):
        """
        Take damage
        
        Args:
            damage: Damage amount
        """
        self.hp = max(0, self.hp - damage)
    
    def get_hp_ratio(self):
        """Get HP ratio (0.0 ~ 1.0)"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0
    
    def __str__(self):
        """String representation"""
        return f"{self.name} (HP: {self.hp}/{self.max_hp}, ATK: {self.atk})"

