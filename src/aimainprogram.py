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
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
WHITE_TEXT = (255, 255, 255)

# Asset loading
def load_image(filename):
    try:
        return pygame.image.load(filename)
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        return None

WUMPUS_IMG = load_image('assets/images/wumpus.png')
AGENT_IMG = load_image('assets/images/agent.png')
GOLD_IMG = load_image('assets/images/gold.png')
PIT_IMG = load_image('assets/images/pit.png')

# Load configuration from JSON file
def load_config(filename):
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, '../assets/config', filename)
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {file_path}")
        return {
            "grid_size": 5,
            "agent_start_position": [0, 0]
        }

# Helper functions
def is_within_bounds(x, y, grid_size):
    return 0 <= x < grid_size and 0 <= y < grid_size

def get_adjacent_cells(x, y, grid_size):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return [(x + dx, y + dy) for dx, dy in directions if is_within_bounds(x + dx, y + dy, grid_size)]

# Knowledge Base Class
class KnowledgeBase:
    def __init__(self):
        self.clauses = []

    def add_clause(self, clause):
        formatted_clause = clause.replace("->", "=>").replace("  ", " ").strip()
        if formatted_clause not in self.clauses:
            self.clauses.append(formatted_clause)
            print(f"Added Clause: {formatted_clause}")

    def pl_resolution(self, query):
        clauses = self.clauses + [f"~{query}"]
        print(f"Resolving for query: {query}")
        new = set()
        while True:
            pairs = [(ci, cj) for ci in clauses for cj in clauses if ci != cj]
            for (ci, cj) in pairs:
                resolvent = self.resolve(ci, cj)
                if resolvent is False:
                    print(f"Contradiction found: {ci} and {cj}")
                    return True
                if resolvent and resolvent not in new:
                    new.add(resolvent)
            if new.issubset(set(clauses)):
                print("No new clauses inferred. Resolution failed.")
                return False
            clauses += list(new)

    def resolve(self, ci, cj):
        ci_literals = set(ci.split(" AND "))
        cj_literals = set(cj.split(" AND "))
        for literal in ci_literals:
            if f"~{literal}" in cj_literals:
                combined_literals = (ci_literals | cj_literals) - {literal, f"~{literal}"}
                return " AND ".join(sorted(combined_literals)) if combined_literals else False
        return None

# Game Class
class WumpusWorld:
    def __init__(self, config):
        self.grid_size = config['grid_size']
        self.agent_start_position = tuple(config['agent_start_position'])
        self.agent_position = self.agent_start_position
        self.wumpus_position = None
        self.gold_position = None
        self.pits = set()
        self.running = True
        self.mode = "play"
        self.kb = KnowledgeBase()

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wumpus World")
        self.clock = pygame.time.Clock()

        # Buttons
        self.ai_button = pygame.Rect(650, 100, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.random_button = pygame.Rect(650, 160, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.wumpus_button = pygame.Rect(650, 220, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.pit_button = pygame.Rect(650, 280, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.gold_button = pygame.Rect(650, 340, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.clear_button = pygame.Rect(650, 400, BUTTON_WIDTH, BUTTON_HEIGHT)

        self.initialize_kb()

    def initialize_kb(self):
        self.kb.add_clause("Agent(x, y) => Safe(x, y)")
        self.kb.add_clause("~Pit(x, y) AND ~Wumpus(x, y) => Safe(x, y)")
        self.kb.add_clause("Gold(x, y) => Reachable(x, y)")
        self.kb.add_clause("Stench(x, y) => Wumpus(x±1, y) OR Wumpus(x, y±1)")
        self.kb.add_clause("Breeze(x, y) => Pit(x±1, y) OR Pit(x, y±1)")

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)
    def randomize_world(self):
        self.clear_world()
        self.wumpus_position = self.random_empty_cell(exclude={self.agent_position})
        self.gold_position = self.random_empty_cell(exclude={self.agent_position, self.wumpus_position})
        self.pits = {self.random_empty_cell(exclude={self.agent_position, self.wumpus_position, self.gold_position}) for _ in range(2)}
        self.update_kb_with_world()
        print(f"Randomized World - Wumpus: {self.wumpus_position}, Gold: {self.gold_position}, Pits: {self.pits}")

    def random_empty_cell(self, exclude):
        cells = [(x, y) for x in range(self.grid_size) for y in range(self.grid_size) if (x, y) not in exclude]
        return random.choice(cells) if cells else None

    def clear_world(self):
        self.wumpus_position = None
        self.gold_position = None
        self.pits.clear()
        self.agent_position = self.agent_start_position
        print("World cleared.")

    def update_kb_with_world(self):
        if self.wumpus_position:
            self.kb.add_clause(f"Wumpus({self.wumpus_position[0]}, {self.wumpus_position[1]})")
        if self.gold_position:
            self.kb.add_clause(f"Gold({self.gold_position[0]}, {self.gold_position[1]})")
        for pit in self.pits:
            self.kb.add_clause(f"Pit({pit[0]}, {pit[1]})")
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                adj_cells = get_adjacent_cells(x, y, self.grid_size)
                for nx, ny in adj_cells:
                    self.kb.add_clause(f"(Safe({x}, {y}) AND Adjacent({x}, {y}, {nx}, {ny})) => Reachable({nx}, {ny})")

    def explore_and_update(self):
        queue = deque([self.agent_position])
        visited = set()

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Simulate percepts and add logical clauses
            if (x, y) in get_adjacent_cells(*self.wumpus_position, self.grid_size):
                self.kb.add_clause(f"Stench({x}, {y})")
            if (x, y) in get_adjacent_cells(*next(iter(self.pits), (None, None)), self.grid_size):
                self.kb.add_clause(f"Breeze({x}, {y})")

            if (x, y) == self.gold_position:
                print("Gold found!")
                self.agent_position = (x, y)
                self.show_popup("Agent grabbed the gold!")
                return

            adj_cells = get_adjacent_cells(x, y, self.grid_size)
            for nx, ny in adj_cells:
                if (nx, ny) not in visited:
                    queue.append((nx, ny))
                    self.kb.add_clause(f"(Safe({x}, {y}) AND Adjacent({x}, {y}, {nx}, {ny})) => Reachable({nx}, {ny})")
                    if self.kb.pl_resolution(f"Reachable({nx}, {ny})"):
                        self.agent_position = (nx, ny)
                        print(f"Agent moved to: {self.agent_position}")

    def run_ai(self):
        print("Running AI...")
        self.explore_and_update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                grid_pos = mouse_pos[0] // GRID_CELL_SIZE, mouse_pos[1] // GRID_CELL_SIZE
                if self.ai_button.collidepoint(mouse_pos):
                    self.run_ai()
                elif self.random_button.collidepoint(mouse_pos):
                    self.randomize_world()
                elif self.clear_button.collidepoint(mouse_pos):
                    self.clear_world()
                elif self.wumpus_button.collidepoint(mouse_pos):
                    self.mode = "add_wumpus"
                elif self.pit_button.collidepoint(mouse_pos):
                    self.mode = "add_pit"
                elif self.gold_button.collidepoint(mouse_pos):
                    self.mode = "add_gold"
                elif is_within_bounds(*grid_pos, self.grid_size):
                    if self.mode == "add_wumpus":
                        self.wumpus_position = grid_pos
                        self.kb.add_clause(f"Wumpus({grid_pos[0]}, {grid_pos[1]})")
                        print(f"Wumpus placed at {grid_pos}.")
                    elif self.mode == "add_pit":
                        self.pits.add(grid_pos)
                        self.kb.add_clause(f"Pit({grid_pos[0]}, {grid_pos[1]})")
                        print(f"Pit added at {grid_pos}.")
                    elif self.mode == "add_gold":
                        self.gold_position = grid_pos
                        self.kb.add_clause(f"Gold({grid_pos[0]}, {grid_pos[1]})")
                        print(f"Gold placed at {grid_pos}.")
                    self.mode = "play"

    def show_popup(self, message):
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
        self.screen.fill(WHITE)
        self.draw_grid()
        if self.agent_position:
            self.screen.blit(AGENT_IMG, (self.agent_position[0] * GRID_CELL_SIZE, self.agent_position[1] * GRID_CELL_SIZE))
        if self.gold_position:
            self.screen.blit(GOLD_IMG, (self.gold_position[0] * GRID_CELL_SIZE, self.gold_position[1] * GRID_CELL_SIZE))
        if self.wumpus_position:
            self.screen.blit(WUMPUS_IMG, (self.wumpus_position[0] * GRID_CELL_SIZE, self.wumpus_position[1] * GRID_CELL_SIZE))
        for pit in self.pits:
            self.screen.blit(PIT_IMG, (pit[0] * GRID_CELL_SIZE, pit[1] * GRID_CELL_SIZE))
        self.draw_buttons()
        pygame.display.flip()

    def draw_grid(self):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                rect = pygame.Rect(x * GRID_CELL_SIZE, y * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE)
                pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw_buttons(self):
        font = pygame.font.Font(None, 36)
        buttons = [
            (self.ai_button, "Run AI", GREEN),
            (self.random_button, "Randomize", ORANGE),
            (self.wumpus_button, "Add Wumpus", RED),
            (self.pit_button, "Add Pit", BLUE),
            (self.gold_button, "Add Gold", YELLOW),
            (self.clear_button, "Clear Grid", GRAY),
        ]
        for button, text, color in buttons:
            pygame.draw.rect(self.screen, color, button)
            text_surface = font.render(text, True, WHITE_TEXT)
            text_rect = text_surface.get_rect(center=button.center)
            self.screen.blit(text_surface, text_rect)


def main():
    config = load_config('game_config.json')
    game = WumpusWorld(config)
    game.run()


if __name__ == "__main__":
    main()
