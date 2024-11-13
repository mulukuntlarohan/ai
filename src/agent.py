from knowledge_base import ResolutionEngine, KBInitializer, KBUpdater

class Agent:
    def __init__(self, wumpus_world, resolution_engine):
        # Initialization of agent with Wumpus world, resolution engine, etc.
        self.wumpus_world = wumpus_world
        self.resolution_engine = resolution_engine
        self.position = (0, 0)  # Initial position
        self.has_gold = False
        self.is_alive = True
        self.visited = set()  # Track visited cells
        self.safe_cells = set()  # Track safe cells

    def move_to_gold(self, gold_position):
        """Move the agent towards the gold's position."""
        if self.position == gold_position:
            print("Agent has reached the gold!")
            return
        
        gold_x, gold_y = gold_position
        agent_x, agent_y = self.position
        
        if agent_x < gold_x:
            self.position = (agent_x + 1, agent_y)
        elif agent_x > gold_x:
            self.position = (agent_x - 1, agent_y)
        
        if agent_y < gold_y:
            self.position = (agent_x, agent_y + 1)
        elif agent_y > gold_y:
            self.position = (agent_x, agent_y - 1)
        
        print(f"Agent moved to {self.position}")

    def perceive(self):
        """Get percepts based on the current position."""
        return self.wumpus_world.get_percepts(self.position)

    def update_knowledge(self, percepts):
        """Update the knowledge base based on percepts."""
        kb_updater = KBUpdater(self.resolution_engine)
        kb_updater.update_kb(percepts)

        self.visited.add(self.position)
        if not percepts['stench'] and not percepts['breeze']:
            self.safe_cells.add(self.position)

    def decide_action(self, percepts):
        """Decide the next action based on percepts."""
        if self.has_gold:
            return "climb"

        if percepts['glitter']:
            print("Gold detected! Grabbing the gold.")
            self.has_gold = True
            return "grab"

        if percepts['stench']:
            print("Stench detected! Avoiding Wumpus.")
            return "avoid wumpus"

        if percepts['breeze']:
            print("Breeze detected! Avoiding pit.")
            return "avoid pit"

        return self.explore_safe_area()

    def explore_safe_area(self):
        """Explore the closest safe, unvisited cell."""
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next_position = (self.position[0] + dx, self.position[1] + dy)
            if next_position not in self.visited and next_position in self.safe_cells:
                return "move", next_position

        return "move", (self.position[0] + 1, self.position[1])

    def move(self, action):
        """Perform the move action."""
        if action == "climb":
            print("Climbing out of the cave with the gold!")
            self.is_alive = False

        elif action == "grab":
            print("Gold grabbed!")

        elif isinstance(action, tuple) and action[0] == "move":
            next_position = action[1]
            print(f"Moving to {next_position}")
            self.position = next_position
            self.wumpus_world.agent_pos = self.position

    def act(self):
        """Main loop for agent actions."""
        while self.is_alive:
            percepts = self.perceive()
            self.update_knowledge(percepts)
            action = self.decide_action(percepts)
            print(f"Decided action: {action}")
            self.move(action)
