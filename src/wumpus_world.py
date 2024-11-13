import random

class WumpusWorld:
    def __init__(self, size=4, num_pits=2, wumpus_pos=None, gold_pos=None):
        self.size = size
        self.grid = [[' ' for _ in range(size)] for _ in range(size)]
        self.agent_pos = (0, 0)  # Starting position of the agent
        self.wumpus_pos = wumpus_pos
        self.gold_pos = gold_pos
        self.pits = set()  # Set to store pit positions
        self.breeze_cells = set()  # Cells with breeze
        self.stench_cells = set()   # Cells with stench
        self.visited = set()  # Track visited cells

        # Place elements randomly if no positions are provided
        if not self.wumpus_pos:
            self.place_wumpus()
        if not self.gold_pos:
            self.place_gold()
        for _ in range(num_pits):  # Random number of pits
            self.place_pit()

    def place_wumpus(self, x=None, y=None):
        """Place the Wumpus at specified or random coordinates."""
        if x is None or y is None:
            x, y = self.get_random_position()
        if self.is_valid_position(x, y):
            self.wumpus_pos = (x, y)
            self.grid[x][y] = 'W'
            self.update_stench(x, y)

    def place_gold(self, x=None, y=None):
        """Place the gold at specified or random coordinates."""
        if x is None or y is None:
            x, y = self.get_random_position()
        if self.is_valid_position(x, y):
            self.gold_pos = (x, y)
            self.grid[x][y] = 'G'

    def place_pit(self, x=None, y=None):
        """Place a pit at specified or random coordinates."""
        if x is None or y is None:
            x, y = self.get_random_position()
        if self.is_valid_position(x, y):
            self.pits.add((x, y))
            self.grid[x][y] = 'P'
            self.update_breeze(x, y)

    def get_random_position(self):
        """Get a random position in the grid that is not occupied."""
        while True:
            x, y = random.randint(0, self.size - 1), random.randint(0, self.size - 1)
            if self.grid[x][y] == ' ' and (x, y) != self.agent_pos and (x, y) != self.wumpus_pos and (x, y) not in self.pits:
                return x, y

    def update_breeze(self, x, y):
        """Update breeze in neighboring cells of the pit."""
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                self.breeze_cells.add((nx, ny))

    def update_stench(self, x, y):
        """Update stench in neighboring cells of the Wumpus."""
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                self.stench_cells.add((nx, ny))

    def is_valid_position(self, x, y):
        """Check if the position is within the grid bounds."""
        return 0 <= x < self.size and 0 <= y < self.size

    def get_percepts(self):
        """Return percepts based on the agent's position."""
        position = self.agent_pos  # Get the agent's position from self
        percepts = {
            'stench': position in [(self.wumpus_pos[0] + dx, self.wumpus_pos[1] + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]],
            'breeze': any(position in [(pit[0] + dx, pit[1] + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]] for pit in self.pits),
            'glitter': position == self.gold_pos,
        }
        return percepts

    def move_agent(self, direction):
        """Move the agent in the specified direction if possible."""
        x, y = self.agent_pos
        if direction == 'UP':
            new_pos = (x - 1, y)
        elif direction == 'DOWN':
            new_pos = (x + 1, y)
        elif direction == 'LEFT':
            new_pos = (x, y - 1)
        elif direction == 'RIGHT':
            new_pos = (x, y + 1)
        else:
            return {"error": "Invalid direction"}

        if self.is_valid_position(*new_pos):
            self.agent_pos = new_pos
            self.visited.add(self.agent_pos)
            percepts = self.get_percepts()
            percepts['bump'] = False
        else:
            percepts = self.get_percepts()
            percepts['bump'] = True  # Bump percept if hitting wall

        return percepts

    def reset_world(self):
        """Reset the world with new random positions for objects."""
        self.grid = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.agent_pos = (0, 0)
        self.wumpus_pos = None
        self.gold_pos = None
        self.pits = set()
        self.breeze_cells.clear()
        self.stench_cells.clear()
        self.visited.clear()
        # Place elements randomly
        self.place_wumpus()
        self.place_gold()
        for _ in range(2):  # Example: Place two pits
            self.place_pit()

    def display(self):
        """Display the current state of the Wumpus World."""
        for i, row in enumerate(self.grid):
            row_display = ""
            for j, cell in enumerate(row):
                if (i, j) == self.agent_pos:
                    row_display += "A "  # Agent position
                elif (i, j) == self.wumpus_pos:
                    row_display += "W "
                elif (i, j) == self.gold_pos:
                    row_display += "G "
                elif (i, j) in self.pits:
                    row_display += "P "
                else:
                    row_display += ". "
            print(row_display)
        print(f"Agent Position: {self.agent_pos}")
        print(f"Wumpus Position: {self.wumpus_pos}")
        print(f"Gold Position: {self.gold_pos}")
        print(f"Pits: {self.pits}")


# Example usage
if __name__ == "__main__":
    wumpus_world = WumpusWorld(num_pits=3)  # Specify the number of pits
    wumpus_world.display()
    print("Percepts at Start:", wumpus_world.get_percepts())

    # Move the agent
    print("Move Right:", wumpus_world.move_agent("RIGHT"))
    print("Move Down:", wumpus_world.move_agent("DOWN"))
    wumpus_world.display()
