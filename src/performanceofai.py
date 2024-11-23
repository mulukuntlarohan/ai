import time
from WumpusWorld import WumpusWorld, load_config, get_adjacent_cells

class WumpusWorldTester:
    def __init__(self, config_file, num_tests=10):
        self.config_file = config_file
        self.num_tests = num_tests
        self.results = []

    def run_tests(self):
        for i in range(self.num_tests):
            print(f"Running Test {i + 1}...")
            start_time = time.time()

            # Load a fresh game configuration
            config = load_config(self.config_file)
            game = WumpusWorld(config)

            # Randomize the world and run the AI
            game.randomize_world()

            steps_taken = 0
            try:
                game.run_ai()
                steps_taken = len(self.track_agent_path(game))
            except Exception as e:
                print(f"Error during test {i + 1}: {e}")

            # Evaluate results
            end_time = time.time()
            result = {
                "Test Number": i + 1,
                "Success": game.agent_position == game.gold_position,
                "Time Taken": end_time - start_time,
                "Gold Found": game.agent_position == game.gold_position,
                "Logical Consistency": self.check_logical_consistency(game.kb),
                "Steps Taken": steps_taken,
                "Hazards Avoided": self.count_hazards_avoided(game),
            }
            self.results.append(result)
            print(f"Test {i + 1} Completed - Result: {result}")

        self.display_results()

    def track_agent_path(self, game):
        # Simulate the agent's path (steps taken)
        path = []
        queue = [(game.agent_start_position, [])]
        visited = set()

        while queue:
            position, current_path = queue.pop(0)
            if position in visited:
                continue
            visited.add(position)
            current_path = current_path + [position]
            path = current_path

            if position == game.gold_position:
                break
            adjacent_cells = get_adjacent_cells(position[0], position[1], game.grid_size)
            for cell in adjacent_cells:
                if cell not in visited:
                    queue.append((cell, current_path))

        return path

    def count_hazards_avoided(self, game):
        # Count the number of hazardous cells avoided by the agent
        hazards = game.pits.union({game.wumpus_position}) if game.wumpus_position else game.pits
        agent_path = self.track_agent_path(game)
        avoided_hazards = [cell for cell in hazards if cell not in agent_path]
        return len(avoided_hazards)

    def check_logical_consistency(self, kb):
        # Check for redundant or contradictory clauses
        clauses = kb.clauses
        for clause in clauses:
            if f"~{clause}" in clauses:
                return False
        return True

    def display_results(self):
        # Display a summary of results
        print("\nTesting Summary:")
        for result in self.results:
            print(f"Test {result['Test Number']} - Success: {result['Success']}, "
                  f"Time Taken: {result['Time Taken']:.2f}s, Steps Taken: {result['Steps Taken']}, "
                  f"Hazards Avoided: {result['Hazards Avoided']}, Logical Consistency: {result['Logical Consistency']}")

        success_rate = sum(1 for result in self.results if result["Success"]) / self.num_tests
        avg_time = sum(result["Time Taken"] for result in self.results) / self.num_tests
        avg_steps = sum(result["Steps Taken"] for result in self.results) / self.num_tests
        avg_hazards_avoided = sum(result["Hazards Avoided"] for result in self.results) / self.num_tests

        print(f"\nPerformance Metrics:")
        print(f"Success Rate: {success_rate * 100:.2f}%")
        print(f"Average Time Taken: {avg_time:.2f} seconds")
        print(f"Average Steps Taken: {avg_steps:.2f}")
        print(f"Average Hazards Avoided: {avg_hazards_avoided:.2f}")

# Main Function for Testing
if __name__ == "__main__":
    tester = WumpusWorldTester('game_config.json', num_tests=10)
    tester.run_tests()
