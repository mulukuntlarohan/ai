from wumpus_world import WumpusWorld
from knowledge_base import ResolutionEngine
from knowledge_base import KBInitializer
from knowledge_base import KBUpdater
from agent import Agent

def main():
    # Initialize the Wumpus World with random object placement
    wumpus_world = WumpusWorld(size=4)  # Randomly places Wumpus, gold, and pits

    # Initialize the knowledge base and resolution engine
    resolution_engine = ResolutionEngine() # Using the existing resolution engine
    kb_initializer = KBInitializer(resolution_engine)
    kb_updater = KBUpdater(resolution_engine)
   

    # Create the agent
    agent = Agent(wumpus_world, resolution_engine)  # This uses the existing Agent class

    # Start the agent's actions (the agent's main loop)
    agent.act()  # This method uses perception, updates knowledge, and makes decisions

if __name__ == "__main__":
    main()
