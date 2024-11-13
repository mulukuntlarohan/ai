import pygame
import json
import random
from knowledge_base import ResolutionEngine, KBInitializer, KBUpdater
from agent import Agent
from wumpus_world import WumpusWorld
from utils import Button

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_CELL_SIZE = 100
FPS = 30

# Load assets
WUMPUS_IMG = pygame.image.load('assets/images/wumpus.png')
AGENT_IMG = pygame.image.load('assets/images/agent.png')
GOLD_IMG = pygame.image.load('assets/images/gold.png')
PIT_IMG = pygame.image.load('assets/images/pit.png')

class Game:
    def __init__(self, config):
        self.grid_size = config['grid_size']
        self.num_pits = config['num_pits']
        self.wumpus_position = tuple(config['wumpus_position'])
        self.agent_position = tuple(config['agent_start_position'])
        self.gold_position = tuple(config['gold_position'])
        self.pits = self.generate_pits()

        # Initialize Wumpus World and Agent
        self.wumpus_world = WumpusWorld(self.grid_size, self.num_pits, self.wumpus_position, self.gold_position)
        self.resolution_engine = ResolutionEngine()
        self.knowledge_base = KBInitializer(self.resolution_engine)
        self.agent = Agent(self.wumpus_world, self.resolution_engine)
        self.kb_updater = KBUpdater(self.resolution_engine)

        # Pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wumpus World AI")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False

        # Initialize buttons
        self.ai_button = Button(650, 50, 100, 40, "AI")
        self.place_pits_button = Button(650, 150, 100, 40, "Place Pits")

    def generate_pits(self):
        pits = set()
        while len(pits) < self.num_pits:
            pit_position = (random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))
            if pit_position not in {self.agent_position, self.gold_position, self.wumpus_position}:
                pits.add(pit_position)
        return pits

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.ai_button.is_clicked(event.pos):
                    self.run_ai()
                elif self.place_pits_button.is_clicked(event.pos):
                    self.place_pits_mode = True
            elif event.type == pygame.KEYDOWN and not self.game_over:
                if event.key == pygame.K_UP:
                    self.move_agent("up")
                elif event.key == pygame.K_DOWN:
                    self.move_agent("down")
                elif event.key == pygame.K_LEFT:
                    self.move_agent("left")
                elif event.key == pygame.K_RIGHT:
                    self.move_agent("right")

    def run_ai(self):
        """Run AI loop for agent until it finds the gold or encounters a hazard."""
        while not self.agent.has_gold and self.agent.is_alive:
            percepts = self.agent.perceive()
            self.agent.update_knowledge(percepts)
            action = self.agent.decide_action(percepts)

            print(f"Decided action: {action}")

            # Perform the action
            if action == "climb":
                self.agent.move(action)
                self.game_over = True
                print("The agent climbed out with the gold!")

            elif action == "grab":
                self.agent.move(action)
                self.game_over = True
                print("The agent grabbed the gold!")

            elif isinstance(action, tuple) and action[0] == "move":
                next_position = action[1]
                self.agent.move(("move", next_position))
                self.agent_position = next_position
                self.check_game_state()

    def check_game_state(self):
        """Check if the game should end due to gold, Wumpus, or pit."""
        if self.agent_position == self.gold_position:
            self.game_over = True
            print("The agent found the gold and won!")
        elif self.agent_position == self.wumpus_position:
            self.game_over = True
            print("The agent was eaten by the Wumpus!")
        elif self.agent_position in self.pits:
            self.game_over = True
            print("The agent fell into a pit!")

    def update(self):
        """Update the game state."""
        if self.game_over:
            self.running = False

    def draw(self):
        """Draw the game screen."""
        self.screen.fill((255, 255, 255))

        # Draw grid
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                pygame.draw.rect(self.screen, (200, 200, 200), (x * GRID_CELL_SIZE, y * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE), 1)

        # Draw agents, gold, pits, and Wumpus
        self.draw_agent()
        self.draw_gold()
        self.draw_pits()
        self.draw_wumpus()

        # Draw buttons
        self.ai_button.draw(self.screen)
        self.place_pits_button.draw(self.screen)

        pygame.display.update()

    def draw_agent(self):
        """Draw the agent."""
        pygame.draw.rect(self.screen, (0, 0, 255), (self.agent_position[0] * GRID_CELL_SIZE, self.agent_position[1] * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE))

    def draw_gold(self):
        """Draw the gold."""
        pygame.draw.rect(self.screen, (255, 255, 0), (self.gold_position[0] * GRID_CELL_SIZE, self.gold_position[1] * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE))

    def draw_pits(self):
        """Draw the pits."""
        for pit in self.pits:
            pygame.draw.rect(self.screen, (0, 0, 0), (pit[0] * GRID_CELL_SIZE, pit[1] * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE))

    def draw_wumpus(self):
        """Draw the Wumpus."""
        pygame.draw.rect(self.screen, (255, 0, 0), (self.wumpus_position[0] * GRID_CELL_SIZE, self.wumpus_position[1] * GRID_CELL_SIZE, GRID_CELL_SIZE, GRID_CELL_SIZE))

if __name__ == "__main__":
    # Game configuration
    config = {
        "grid_size": 4,
        "num_pits": 2,
        "wumpus_position": [1, 1],
        "agent_start_position": [0, 0],
        "gold_position": [3, 3],
    }

    # Start the game
    game = Game(config)
    game.run()
