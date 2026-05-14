"""
Game UI Rendering
"""
import pygame


class GameUI:
    """Game UI Management"""
    
    def __init__(self, screen):
        """
        Initialize UI
        
        Args:
            screen: Pygame window object
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Font settings (using default font, no Chinese character issues)
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 64)
        self.small_font = pygame.font.Font(None, 24)
        print("✅ Using default font (English)")
        
        # Load background
        try:
            self.background = pygame.image.load("assets/images/background.png")
            self.background = pygame.transform.scale(self.background, (self.width, self.height))
        except:
            print("Warning: Cannot load background image, using default")
            self.background = None
    
    def draw_background(self):
        """Draw background"""
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            # Use gradient background
            for y in range(self.height):
                color = (50 + y // 10, 50 + y // 15, 100 + y // 8)
                pygame.draw.line(self.screen, color, (0, y), (self.width, y))
    
    def draw_pokemon(self, pokemon, x, y):
        """
        Draw Pokemon
        
        Args:
            pokemon: Pokemon object
            x: X coordinate
            y: Y coordinate
        """
        self.screen.blit(pokemon.image, (x, y))
    
    def draw_hp_bar(self, pokemon, x, y):
        """
        Draw HP bar
        
        Args:
            pokemon: Pokemon object
            x: X coordinate
            y: Y coordinate
        """
        bar_width = 200
        bar_height = 20
        
        # Background bar (red)
        pygame.draw.rect(self.screen, (100, 0, 0), (x, y, bar_width, bar_height))
        
        # Current HP (green to yellow to red)
        hp_ratio = pokemon.get_hp_ratio()
        hp_width = int(bar_width * hp_ratio)
        
        # Change color based on HP percentage
        if hp_ratio > 0.5:
            color = (0, 255, 0)  # Green
        elif hp_ratio > 0.2:
            color = (255, 255, 0)  # Yellow
        else:
            color = (255, 0, 0)  # Red
        
        pygame.draw.rect(self.screen, color, (x, y, hp_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, (0, 0, 0), (x, y, bar_width, bar_height), 2)
        
        # Display name and HP
        text = self.font.render(f"{pokemon.name} HP: {int(pokemon.hp)}/{pokemon.max_hp}", True, (255, 255, 255))
        # Add shadow effect
        shadow = self.font.render(f"{pokemon.name} HP: {int(pokemon.hp)}/{pokemon.max_hp}", True, (0, 0, 0))
        self.screen.blit(shadow, (x + 2, y - 28))
        self.screen.blit(text, (x, y - 30))
    
    def draw_switch_buttons(self, team, current_idx):
        """
        Draw switch buttons
        
        Args:
            team: Pokemon team list
            current_idx: Current Pokemon index
        """
        button_width = 130
        button_height = 50
        button_spacing = 20
        start_x = 50
        start_y = 500
        
        for i, pokemon in enumerate(team):
            x = start_x + i * (button_width + button_spacing)
            y = start_y
            
            # Button color
            if i == current_idx:
                color = (255, 255, 0)  # Current: Yellow
                border_color = (255, 200, 0)
            elif pokemon.is_alive():
                color = (200, 200, 200)  # Available: Gray
                border_color = (150, 150, 150)
            else:
                color = (100, 100, 100)  # Fainted: Dark gray
                border_color = (50, 50, 50)
            
            # Draw button (with shadow effect)
            pygame.draw.rect(self.screen, (0, 0, 0), (x + 3, y + 3, button_width, button_height), border_radius=5)
            pygame.draw.rect(self.screen, color, (x, y, button_width, button_height), border_radius=5)
            pygame.draw.rect(self.screen, border_color, (x, y, button_width, button_height), 3, border_radius=5)
            
            # Button text
            name_text = self.small_font.render(f"{pokemon.name}", True, (0, 0, 0))
            hp_text = self.small_font.render(f"HP: {int(pokemon.hp)}", True, (0, 0, 0))
            
            # Center display
            name_rect = name_text.get_rect(center=(x + button_width // 2, y + 15))
            hp_rect = hp_text.get_rect(center=(x + button_width // 2, y + 35))
            
            self.screen.blit(name_text, name_rect)
            self.screen.blit(hp_text, hp_rect)
    
    def draw_message(self, message, color=(255, 0, 0)):
        """
        Draw message
        
        Args:
            message: Message text
            color: Text color
        """
        text = self.title_font.render(message, True, color)
        # Add shadow
        shadow = self.title_font.render(message, True, (0, 0, 0))
        
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        shadow_rect = shadow.get_rect(center=(self.width // 2 + 3, self.height // 2 + 3))
        
        # Draw semi-transparent background
        bg_rect = pygame.Rect(text_rect.x - 20, text_rect.y - 10, text_rect.width + 40, text_rect.height + 20)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, bg_rect)
        
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(text, text_rect)
    
    def draw_battle_message(self, message):
        """
        Draw battle message (at bottom of screen)
        
        Args:
            message: Message text
        """
        text = self.font.render(message, True, (255, 255, 255))
        shadow = self.font.render(message, True, (0, 0, 0))
        
        # Draw at bottom of screen
        x = 50
        y = 450
        
        # Background box
        bg_rect = pygame.Rect(x - 10, y - 5, self.width - 80, 35)
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2, border_radius=5)
        
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(text, (x, y))
    
    def draw_instructions(self):
        """Draw instructions"""
        instructions = [
            "Controls:",
            "Click = Attack",
            "Click Button = Switch"
        ]
        
        y = 10
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (255, 255, 255))
            shadow = self.small_font.render(instruction, True, (0, 0, 0))
            self.screen.blit(shadow, (self.width - 152, y + 2))
            self.screen.blit(text, (self.width - 150, y))
            y += 25

