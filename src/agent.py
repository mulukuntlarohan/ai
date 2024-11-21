import pygame
import random
import json
import os

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
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, '../assets/config', filename)
    with open(file_path, 'r') as f:
        return json.load(f)

# Helper functions
def get_grid_position(mouse_pos):
    x, y = mouse_pos
    return x // GRID_CELL_SIZE, y // GRID_CELL_SIZE

def is_within_bounds(x, y, grid_size):
    return 0 <= x < grid_size and 0 <= y < grid_size

# Knowledge Base Class
class KnowledgeBase:
    def __init__(self):
        self.clauses = []

    def add_clause(self, clause):
        """Add a propositional clause to the KB."""
        self.clauses.append(clause)

    def pl_resolution(self, query):
        """Apply PL-Resolution to check if the query can be inferred."""
        new = set()
        while True:
            pairs = [(ci, cj) for ci in self.clauses for cj in self.clauses if ci != cj]
            for (ci, cj) in pairs:
                resolvent = self.resolve(ci, cj)
                if resolvent is False:
                    return True
                if resolvent and resolvent not in new:
                    new.add(resolvent)
            if new.issubset(set(self.clauses)):
                return False
            for clause in new:
                if clause not in self.clauses:
                    self.clauses.append(clause)

    def resolve(self, ci, cj):
        """Resolve two clauses."""
        ci_literals = set(ci.split())
        cj_literals = set(cj.split())
        for literal in ci_literals:
            if f"~{literal}" in cj_literals:
                combined_literals = (ci_literals | cj_literals) - {literal, f"~{literal}"}
                return " ".join(combined_literals) if combined_literals else False
        return None

# Game class
class WumpusWorld:
    def __init__(self, config):
        self.grid_size = config['grid_size']
        self.agent_start_position = tuple(config['agent_start_position'])
        self.agent_position = self.agent_start_position
        self.wumpus_position = None
        self.gold_position = None
        self.pits = set()
        self.running = True
        self.game_over = False
        self.mode = "play"

        self.kb = KnowledgeBase()
        self.initialize_kb()

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
        self.random_button = pygame.Rect(650, 460, BUTTON_WIDTH, BUTTON_HEIGHT)

    def initialize_kb(self):
        """Initialize KB with the basic rules of Wumpus World."""
        self.kb.add_clause("~Breeze(x, y) OR Pit(adj_x, adj_y)")
        self.kb.add_clause("~Stench(x, y) OR Wumpus(adj_x, adj_y)")
        self.kb.add_clause("Gold(x, y) -> Reachable(x, y)")
        self.kb.add_clause("Agent(x, y) -> Safe(x, y)")
        self.kb.add_clause("~Pit(x, y) AND ~Wumpus(x, y) -> Safe(x, y)")

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

    def randomize_world(self):
        """Randomly place exactly 1 Wumpus, 1 gold, and 2 pits."""
        self.clear_grid()  # Clear existing placements

        # Place the Wumpus in a random unoccupied cell
        self.wumpus_position = self.random_empty_cell(exclude={self.agent_position})

        # Place the Gold in another random unoccupied cell
        self.gold_position = self.random_empty_cell(exclude={self.agent_position, self.wumpus_position})

        # Place exactly 2 pits in random unoccupied cells
        self.pits = set()
        for _ in range(2):  # Ensure exactly 2 pits
          pit = self.random_empty_cell(exclude={self.agent_position, self.wumpus_position, self.gold_position} | self.pits)
          if pit:
            self.pits.add(pit)

        # Update the Knowledge Base with new placements
        self.update_kb_with_world()

        # Re-draw the grid to reflect the updated world
        self.draw()


    def random_empty_cell(self, exclude=set()):
        """Find a random unoccupied cell, excluding certain positions."""
        available_cells = [
        (x, y)
        for x in range(self.grid_size)
        for y in range(self.grid_size)
        if (x, y) not in exclude
        ]
        return random.choice(available_cells) if available_cells else None

    def clear_grid(self):
        """Clear the grid except for the agent's position."""
        self.wumpus_position = None
        self.gold_position = None
        self.pits.clear()
        self.agent_position = self.agent_start_position

    def update_kb_with_world(self):
        """Update KB with initial placements."""
        if self.wumpus_position:
            self.kb.add_clause(f"Wumpus({self.wumpus_position[0]}, {self.wumpus_position[1]})")
        if self.gold_position:
            self.kb.add_clause(f"Gold({self.gold_position[0]}, {self.gold_position[1]})")
        for pit in self.pits:
            self.kb.add_clause(f"Pit({pit[0]}, {pit[1]})")

    def handle_events(self):
        """Handle user inputs and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if self.ai_button.collidepoint(mouse_pos):
                    self.run_ai()
                elif self.random_button.collidepoint(mouse_pos):
                    self.randomize_world()
                elif self.clear_button.collidepoint(mouse_pos):
                    self.clear_grid()
                elif self.wumpus_button.collidepoint(mouse_pos):
                    self.mode = "add_wumpus"
                elif self.pit_button.collidepoint(mouse_pos):
                    self.mode = "add_pit"
                elif self.gold_button.collidepoint(mouse_pos):
                    self.mode = "add_gold"
                else:
                    grid_pos = get_grid_position(mouse_pos)
                    if self.mode == "add_wumpus":
                        self.wumpus_position = grid_pos
                        self.kb.add_clause(f"Wumpus({grid_pos[0]}, {grid_pos[1]})")
                        self.mode = "play"
                    elif self.mode == "add_pit":
                        self.pits.add(grid_pos)
                        self.kb.add_clause(f"Pit({grid_pos[0]}, {grid_pos[1]})")
                        self.mode = "play"
                    elif self.mode == "add_gold":
                        self.gold_position = grid_pos
                        self.kb.add_clause(f"Gold({grid_pos[0]}, {grid_pos[1]})")
                        self.mode = "play"

    def run_ai(self):
        """Run the AI to find a safe path to the gold using KB and PL-Resolution."""
        if not self.gold_position:
            self.show_popup("Gold not placed!")
            return

        query = f"Reachable({self.gold_position[0]}, {self.gold_position[1]})"
        if self.kb.pl_resolution(query):
            self.agent_position = self.gold_position
            self.show_popup("Agent grabbed the gold!")
        else:
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
                    exit()
                elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
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
        pygame.draw.rect(self.screen, GRAY, self.clear_button)
        pygame.draw.rect(self.screen, GRAY, self.random_button)

        font = pygame.font.Font(None, 36)
        self.screen.blit(font.render("Run AI", True, WHITE_TEXT), (self.ai_button.x + 15, self.ai_button.y + 5))
        self.screen.blit(font.render("Add Wumpus", True, WHITE_TEXT), (self.wumpus_button.x + 5, self.wumpus_button.y + 5))
        self.screen.blit(font.render("Add Pit", True, WHITE_TEXT), (self.pit_button.x + 15, self.pit_button.y + 5))
        self.screen.blit(font.render("Add Gold", True, WHITE_TEXT), (self.gold_button.x + 15, self.gold_button.y + 5))
        self.screen.blit(font.render("Clear Grid", True, WHITE_TEXT), (self.clear_button.x + 15, self.clear_button.y + 5))
        self.screen.blit(font.render("Randomize", True, WHITE_TEXT), (self.random_button.x + 15, self.random_button.y + 5))


def main():
    """Initialize and run the game."""
    config = load_config('game_config.json')
    game = WumpusWorld(config)
    game.run()


if __name__ == "__main__":
    main()
 
