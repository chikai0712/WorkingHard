"""
Pokemon Battle Game - Main Program
Ash vs Computer: Epic Pokemon Battle

Author: CK Chiu
Date: 2026-02-07
"""
import pygame
import sys
from pokemon import Pokemon
from battle import Battle
from ui import GameUI


def main():
    """Main program"""
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    
    # Window settings
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ash vs Computer: Pokemon Battle")
    clock = pygame.time.Clock()
    FPS = 30
    
    # Load music
    try:
        pygame.mixer.music.load("assets/audio/bgm.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # -1 means infinite loop
        print("Background music loaded successfully")
    except Exception as e:
        print(f"Warning: Music loading failed - {e}")
    
    # Create Ash's team
    ash_team = [
        Pokemon("Charizard", 186, 45, "assets/images/charizard.png"),
        Pokemon("Blastoise", 188, 38, "assets/images/blastoise.png"),
        Pokemon("Venusaur", 190, 42, "assets/images/venusaur.png")
    ]
    
    # Create Computer's team
    comp_team = [
        Pokemon("Garchomp", 239, 42, "assets/images/garchomp.png"),
        Pokemon("Kingdra", 181, 40, "assets/images/kingdra.png"),
        Pokemon("Persian", 163, 35, "assets/images/persian.png")
    ]
    
    # Create battle and UI manager
    battle = Battle(ash_team, comp_team)
    ui = GameUI(screen)
    
    print("=" * 50)
    print("Pokemon Battle Game Started!")
    print("=" * 50)
    print("\nAsh's Team:")
    for i, pkmn in enumerate(ash_team, 1):
        print(f"  {i}. {pkmn}")
    print("\nComputer's Team:")
    for i, pkmn in enumerate(comp_team, 1):
        print(f"  {i}. {pkmn}")
    print("\n" + "=" * 50)
    
    # Main game loop
    running = True
    while running:
        # Draw screen
        ui.draw_background()
        
        # Get current Pokemon in battle
        player_pkmn, comp_pkmn = battle.get_current_pokemon()
        
        # Draw Pokemon
        ui.draw_pokemon(player_pkmn, 50, 250)
        ui.draw_pokemon(comp_pkmn, 500, 50)
        
        # Draw HP bars
        ui.draw_hp_bar(player_pkmn, 50, 220)
        ui.draw_hp_bar(comp_pkmn, 500, 310)
        
        # Draw switch buttons
        ui.draw_switch_buttons(ash_team, battle.ash_idx)
        
        # Draw instructions
        ui.draw_instructions()
        
        # Draw battle message
        if battle.message:
            ui.draw_battle_message(battle.message)
        
        # Display game state messages
        if battle.game_state == "FORCE_SWITCH":
            ui.draw_message("Choose your next Pokemon!", (255, 0, 0))
        elif battle.game_state == "WIN":
            ui.draw_message("Ash Wins!", (0, 255, 0))
        elif battle.game_state == "LOSE":
            ui.draw_message("Computer Wins!", (255, 0, 0))
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # Check if switch button clicked (Y coordinate between 500-550)
                if 500 <= my <= 550:
                    button_width = 130
                    button_spacing = 20
                    start_x = 50
                    
                    for i in range(len(ash_team)):
                        button_x = start_x + i * (button_width + button_spacing)
                        if button_x <= mx <= button_x + button_width:
                            if battle.switch_pokemon(i):
                                print(f"\n>>> Ash sent out {ash_team[i].name}!")
                            break
                
                # Click elsewhere to attack (only in battle state)
                elif battle.game_state == "BATTLE":
                    print("\n>>> Attack!")
                    battle.attack()
            
            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                # ESC to quit
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                # Number keys 1-3 for quick switch
                if battle.game_state in ["BATTLE", "FORCE_SWITCH"]:
                    if event.key == pygame.K_1:
                        battle.switch_pokemon(0)
                    elif event.key == pygame.K_2:
                        battle.switch_pokemon(1)
                    elif event.key == pygame.K_3:
                        battle.switch_pokemon(2)
                
                # Spacebar to attack
                if event.key == pygame.K_SPACE and battle.game_state == "BATTLE":
                    print("\n>>> Attack!")
                    battle.attack()
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    # Game over
    print("\n" + "=" * 50)
    print("Game Over! Thanks for playing!")
    print("=" * 50)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

