import pygame
import random
import json
import os
from collections import deque

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_CELL_SIZE = 100
FPS = 30
BUTTON_HEIGHT = 40
BUTTON_WIDTH = 120

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE_TEXT = (255, 255, 255)

# Asset loading
WUMPUS_IMG = pygame.image.load('assets/images/wumpus.png')
AGENT_IMG = pygame.image.load('assets/images/agent.png')
GOLD_IMG = pygame.image.load('assets/images/gold.png')
PIT_IMG = pygame.image.load('assets/images/pit.png')

# Load configuration from JSON file
def load_config(filename):
    """Load game configuration from a JSON file."""
    base_path = os.path.dirname(__file__)  # Directory of the current script
    file_path = os.path.join(base_path, '../assets/config', filename)
    with open(file_path, 'r') as f:
        return json.load(f)

# Helper functions
def get_grid_position(mouse_pos):
    """Convert mouse position to grid coordinates."""
    x, y = mouse_pos
    return x // GRID_CELL_SIZE, y // GRID_CELL_SIZE

def is_within_bounds(x, y, grid_size):
    """Check if a position is within the grid boundaries."""
    return 0 <= x < grid_size and 0 <= y < grid_size

# Game class
class WumpusWorld:
    def __init__(self, config):
        self.grid_size = config['grid_size']
        self.agent_start_position = tuple(config['agent_start_position'])
        self.agent_position = self.agent_start_position
        self.wumpus_position = tuple(config['wumpus_position'])
        self.gold_position = self.random_empty_cell(
            exclude={self.agent_position, self.wumpus_position, *[tuple(p) for p in config['pits']]}
        )
        self.pits = {tuple(p) for p in config['pits']}
        self.running = True
        self.game_over = False
        self.mode = "play"  # Modes: play, add_wumpus, add_pit, add_gold, clear_grid

        # Pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wumpus World")
        self.clock = pygame.time.Clock()

        # Buttons
        self.ai_button = pygame.Rect(650, 100, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.wumpus_button = pygame.Rect(650, 160, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.pit_button = pygame.Rect(650, 220, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.gold_button = pygame.Rect(650, 280, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.reset_button = pygame.Rect(650, 340, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.clear_button = pygame.Rect(650, 400, BUTTON_WIDTH, BUTTON_HEIGHT)

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

    def random_empty_cell(self, exclude):
        """Find a random empty cell not in the exclude set."""
        while True:
            x, y = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            if (x, y) not in exclude:
                return (x, y)

    def reset_game(self):
        """Reset the game state, placing the agent back and generating a new gold position."""
        self.agent_position = self.agent_start_position
        self.gold_position = self.random_empty_cell(
            exclude={self.agent_position, self.wumpus_position, *self.pits}
        )
        self.game_over = False
        self.mode = "play"

    def clear_grid(self):
        """Clear the grid entirely, allowing manual placement."""
        self.agent_position = None
        self.wumpus_position = None
        self.gold_position = None
        self.pits.clear()
        self.mode = "play"

    def is_safe(self, position):
        """Determine if a position is safe based on the Wumpus and pit locations."""
        return position != self.wumpus_position and position not in self.pits

    def handle_events(self):
        """Handle user inputs and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and not self.game_over:
                if event.key == pygame.K_UP and self.agent_position:
                    self.move_agent(0, -1)
                elif event.key == pygame.K_DOWN and self.agent_position:
                    self.move_agent(0, 1)
                elif event.key == pygame.K_LEFT and self.agent_position:
                    self.move_agent(-1, 0)
                elif event.key == pygame.K_RIGHT and self.agent_position:
                    self.move_agent(1, 0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if self.ai_button.collidepoint(mouse_pos):
                    self.run_ai()
                elif self.wumpus_button.collidepoint(mouse_pos):
                    self.mode = "add_wumpus"
                elif self.pit_button.collidepoint(mouse_pos):
                    self.mode = "add_pit"
                elif self.gold_button.collidepoint(mouse_pos):
                    self.mode = "add_gold"
                elif self.reset_button.collidepoint(mouse_pos):
                    self.reset_game()
                elif self.clear_button.collidepoint(mouse_pos):
                    self.clear_grid()
                elif self.mode == "add_wumpus":
                    self.wumpus_position = get_grid_position(mouse_pos)
                    self.mode = "play"
                elif self.mode == "add_pit":
                    pit_pos = get_grid_position(mouse_pos)
                    self.pits.add(pit_pos)
                    self.mode = "play"
                elif self.mode == "add_gold":
                    self.gold_position = get_grid_position(mouse_pos)
                    self.mode = "play"

    def move_agent(self, dx, dy):
        """Move the agent in the specified direction, only if safe."""
        x, y = self.agent_position
        new_x, new_y = x + dx, y + dy
        if is_within_bounds(new_x, new_y, self.grid_size):
            new_position = (new_x, new_y)
            if self.is_safe(new_position):
                self.agent_position = new_position
                self.check_game_state()
            else:
                self.show_popup(f"Position {new_position} is unsafe!")

    def check_game_state(self):
        """Check if the game is over or if the agent wins."""
        if self.agent_position == self.wumpus_position:
            self.show_popup("You encountered the Wumpus! Game Over.")
            self.game_over = True
        elif self.agent_position in self.pits:
            self.show_popup("You fell into a pit! Game Over.")
            self.game_over = True
        elif self.agent_position == self.gold_position:
            self.show_popup("You collected the gold! You win!")
            self.game_over = True

    def run_ai(self):
        """Run the AI to find a safe path to the gold."""
        if not self.agent_position:
            self.show_popup("Place the agent first!")
            return
        queue = deque([(self.agent_position, [])])
        visited = set()

        while queue:
            current_pos, path = queue.popleft()
            if current_pos in visited:
                continue
            visited.add(current_pos)

            if current_pos == self.gold_position:
                for step in path:
                    self.agent_position = step
                    self.draw()
                    pygame.time.delay(100)
                return

            x, y = current_pos
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                new_pos = (new_x, new_y)
                if is_within_bounds(new_x, new_y, self.grid_size) and self.is_safe(new_pos):
                    queue.append((new_pos, path + [new_pos]))

        self.show_popup("No safe path to the gold!")

    def show_popup(self, message):
        """Display a popup message."""
        font = pygame.font.Font(None, 48)
        text = font.render(message, True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return

            self.screen.fill(WHITE)
            self.screen.blit(text, text_rect)
            pygame.display.flip()

    def draw(self):
        """Render the game elements."""
        self.screen.fill(WHITE)
        self.draw_grid()

        # Draw agent
        if self.agent_position:
            self.screen.blit(AGENT_IMG, (self.agent_position[0] * GRID_CELL_SIZE, self.agent_position[1] * GRID_CELL_SIZE))

        # Draw gold
        if self.gold_position:
            self.screen.blit(GOLD_IMG, (self.gold_position[0] * GRID_CELL_SIZE, self.gold_position[1] * GRID_CELL_SIZE))

        # Draw Wumpus
        if self.wumpus_position:
            self.screen.blit(WUMPUS_IMG, (self.wumpus_position[0] * GRID_CELL_SIZE, self.wumpus_position[1] * GRID_CELL_SIZE))

        # Draw pits
        for pit in self.pits:
            self.screen.blit(PIT_IMG, (pit[0] * GRID_CELL_SIZE, pit[1] * GRID_CELL_SIZE))

        # Draw buttons
        self.draw_buttons()
        pygame.display.flip()

    def draw_grid(self):
        """Draw the game grid."""
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                rect = pygame.Rect(x * GRID_CELL_SIZE, y * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE)
                pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw_buttons(self):
        """Draw the buttons."""
        pygame.draw.rect(self.screen, GREEN, self.ai_button)
        pygame.draw.rect(self.screen, RED, self.wumpus_button)
        pygame.draw.rect(self.screen, BLUE, self.pit_button)
        pygame.draw.rect(self.screen, GRAY, self.gold_button)
        pygame.draw.rect(self.screen, GRAY, self.reset_button)
        pygame.draw.rect(self.screen, GRAY, self.clear_button)

        font = pygame.font.Font(None, 36)
        self.screen.blit(font.render("Run AI", True, WHITE_TEXT), (self.ai_button.x + 15, self.ai_button.y + 5))
        self.screen.blit(font.render("Add Wumpus", True, WHITE_TEXT), (self.wumpus_button.x + 5, self.wumpus_button.y + 5))
        self.screen.blit(font.render("Add Pit", True, WHITE_TEXT), (self.pit_button.x + 15, self.pit_button.y + 5))
        self.screen.blit(font.render("Add Gold", True, WHITE_TEXT), (self.gold_button.x + 15, self.gold_button.y + 5))
        self.screen.blit(font.render("Reset", True, WHITE_TEXT), (self.reset_button.x + 30, self.reset_button.y + 5))
        self.screen.blit(font.render("Clear Grid", True, WHITE_TEXT), (self.clear_button.x + 15, self.clear_button.y + 5))


def main():
    """Initialize and run the game."""
    config = load_config('game_config.json')
    game = WumpusWorld(config)
    game.run()


if __name__ == "__main__":
    main()
