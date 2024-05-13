import pygame 
import sys 
from collections import deque
import heapq


class Button:
    def __init__(self, x, y, width, height, color, hover_color, text, text_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.text_color = text_color
        self.action = action
        self.hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)  # Add black border
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()


class TowerOfHanoiGame:
    def __init__(self):
        self.min_disks = 3
        
        self.num_disks = self.min_disks
        self.towers = [[i for i in range(self.num_disks, 0, -1)], [], []]
        self.selected_disk = None
        self.selected_tower = None
        self.width = 800
        self.height = 600
        self.disk_height = 20
        self.disk_width_factor = 20
        self.tower_width = 10
        self.base_height = 10  # Adjusted base height
        self.base_width = 170
        self.base_color = (0, 0, 0)
        self.tower_color = (0, 0, 0)
        self.disk_colors = [
            (255, 255, 255),  # White
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (128, 0, 128),  # Purple
            (128, 128, 0)   # Olive
        ]
        self.selected_color = (255, 255, 0)
        self.tower_positions = [(self.width // 4, 100), (self.width // 2, 100), (3 * self.width // 4, 100)]
        self.selected_tower_color = (255, 255, 0)
        self.moves = 0
        self.completed = False

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tower of Hanoi ")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 32)
        self.buttons = [
            Button(50, self.height - 100, 120, 40, (255, 255, 0), (128, 128, 128), "DFS", (0, 0, 0),
                   self.solve_with_dfs),
            Button(200, self.height - 100, 120, 40, (255, 255, 0), (128, 128, 128), "BFS", (0, 0, 0),
                   self.solve_with_bfs),
            Button(350, self.height - 100, 120, 40, (255, 255, 0), (128, 128, 128), "UCS", (0, 0, 0),
                   self.solve_with_ucs),
            Button(520, self.height - 100, 120, 40, (255, 255, 0), (128, 128, 128), "A*", (0, 0, 0),
                   self.solve_with_a_star),
            Button(670, self.height - 100, 120, 40, (255, 255, 0), (128, 128, 128), "Best-First", (0, 0, 0),
                   self.solve_with_best_first),
            Button(350, self.height - 50, 120, 40, (255, 255, 0), (128, 128, 128), "Restart", (0, 0, 0),
                   self.restart_game)
        ]


    def draw_towers(self):
        self.screen.fill((152, 251, 152))  # Light green background

        # Draw Tower of Hanoi title
        title_font = pygame.font.SysFont("IBM Plex", 50)
        title_text = title_font.render("Tower of Hanoi", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title_text, title_rect)

        # Draw colored rectangles for Disks, Minimum Moves, and Moves
        cyan_color = (0, 255, 255)
        pygame.draw.rect(self.screen, cyan_color, (15, 100, 220, 30))    # Cyan for Minimum Moves
        pygame.draw.rect(self.screen, cyan_color, (390, 100, 120, 30))   # Cyan for Moves
        pygame.draw.rect(self.screen, cyan_color, (690, 100, 100, 30))   # Cyan for Disks
        pygame.draw.rect(self.screen, (0, 0, 0), (15, 100, 220, 30), 2)  # Black border for Cyan rectangle
        pygame.draw.rect(self.screen, (0, 0, 0), (390, 100, 120, 30), 2)  # Black border for Cyan rectangle
        pygame.draw.rect(self.screen, (0, 0, 0), (690, 100, 100, 30), 2)  # Black border for Cyan rectangle

        # Render text for Disks, Minimum Moves, and Moves
        disks_text = self.font.render("Disks: " + str(self.num_disks), True, (0, 0, 0))
        moves_text = self.font.render("Moves: " + str(self.moves), True, (0, 0, 0))
        min_moves_text = self.font.render("Minimum Moves: " + str(self.minimum_moves()), True, (0, 0, 0))

        # Blit text onto the screen
        self.screen.blit(disks_text, (700, 105))
        self.screen.blit(min_moves_text, (20, 105))
        self.screen.blit(moves_text, (400, 105))

        for i, tower in enumerate(self.towers):
            x, y = self.tower_positions[i]

            # Draw the tower base
            pygame.draw.rect(self.screen, self.base_color,
                             (x - self.tower_width // 2 - (self.base_width - self.tower_width) // 2,
                              self.height - 120 - self.base_height, self.base_width,
                              self.base_height))  # Adjusted base position

            # Draw the disks
            for j, disk in enumerate(tower):
                disk_width = self.disk_width_factor * disk
                pygame.draw.rect(self.screen, (0, 0, 0),  # Black color for disks
                                 (x - disk_width // 2, self.height - (j + 1) * self.disk_height - 130,
                                  disk_width, self.disk_height))

            # Draw the tower
            pygame.draw.rect(self.screen, self.tower_color,
                             (x - self.tower_width // 2, y - (self.height - 670), self.tower_width,
                              self.height - 300))

    def draw_buttons(self):
        for button in self.buttons:
            button.draw(self.screen, self.font)
    def on_click(self, tower):
        if self.selected_disk is None:
            if self.towers[tower]:
                self.selected_disk = self.towers[tower].pop()
                self.selected_tower = tower
        else:
            if not self.towers[tower] or self.towers[tower][-1] > self.selected_disk:
                self.towers[tower].append(self.selected_disk)
                self.selected_disk = None
                self.moves += 1  # Increment moves after each move
                self.selected_tower = None
                if tower == 2 and len(self.towers[2]) == self.num_disks:
                    self.completed = True

    def reset_game(self):
        self.towers = [[i for i in range(self.num_disks, 0, -1)], [], []]
        self.moves = 0
        self.completed = False

    def minimum_moves(self):
        return 2 ** self.num_disks - 1

    def move_disk(self, source, target):
        disk = self.towers[source].pop()
        self.towers[target].append(disk)

    def dfs(self, source, target, auxiliary, num_disks):
        if num_disks == 1:
            # Move the top disk from source to target
            self.move_disk(source, target)
            self.draw_towers()
            pygame.display.flip()
            pygame.time.delay(500)
            self.moves += 1  # Increment moves after each move
            return

        # Move num_disks-1 disks from source to auxiliary
        self.dfs(source, auxiliary, target, num_disks - 1)

        # Move the bottom disk from source to target
        self.move_disk(source, target)
        self.draw_towers()
        pygame.display.flip()
        pygame.time.delay(500)
        self.moves += 1  # Increment moves after each move

        # Move num_disks-1 disks from auxiliary to target
        self.dfs(auxiliary, target, source, num_disks - 1)

    def solve_with_dfs(self):
        self.dfs(0, 2, 1, self.num_disks)

    def solve_with_bfs(self):
        # Initialize the BFS queue with the initial state
        initial_state = (tuple(tuple(tower) for tower in self.towers), [])
        queue = deque([initial_state])

        # Set to keep track of visited states
        visited = set()

        # Perform BFS until the queue is empty
        while queue:
            # Get the current state from the queue
            current_state, moves = queue.popleft()

            # Check if the current state is the goal state
            if len(current_state[2]) == self.num_disks:
                # Apply the moves to the game state
                for move in moves:
                    source, target = move
                    self.move_disk(source, target)
                    self.draw_towers()
                    pygame.display.flip()
                    pygame.time.delay(500)
                    self.moves += 1  # Increment moves after each move
                return

            # Generate possible moves from the current state
            for source in range(3):
                if not current_state[source]:
                    continue
                for target in range(3):
                    if source != target and (
                            not current_state[target] or current_state[source][-1] < current_state[target][-1]):
                        # Create a new state by making the move
                        new_state = [list(tower) for tower in current_state]
                        disk = new_state[source].pop()
                        new_state[target].append(disk)
                        new_state = tuple(tuple(tower) for tower in new_state)

                        # Check if the new state has been visited
                        if new_state not in visited:
                            # Add the new state and moves to the queue
                            new_moves = moves + [(source, target)]
                            queue.append((new_state, new_moves))
                            visited.add(new_state)

    def solve_with_ucs(self):
        # Initialize the UCS priority queue with the initial state
        initial_state = (tuple(tuple(tower) for tower in self.towers), [])
        queue = [(0, initial_state)]  # Priority queue using heapq
        heapq.heapify(queue)

        # Set to keep track of visited states
        visited = set()

        # Perform UCS until the queue is empty
        while queue:
            # Get the current state from the queue
            priority, (current_state, moves) = heapq.heappop(queue)

            # Check if the current state is the goal state
            if len(current_state[2]) == self.num_disks:
                # Apply the moves to the game state
                for move in moves:
                    source, target = move
                    self.move_disk(source, target)
                    self.draw_towers()
                    pygame.display.flip()
                    pygame.time.delay(500)
                    self.moves += 1  # Increment moves after each move
                return

            # Generate possible moves from the current state
            for source in range(3):
                if not current_state[source]:
                    continue
                for target in range(3):
                    if source != target and (
                            not current_state[target] or current_state[source][-1] < current_state[target][-1]):
                        # Create a new state by making the move
                        new_state = [list(tower) for tower in current_state]
                        disk = new_state[source].pop()
                        new_state[target].append(disk)
                        new_state = tuple(tuple(tower) for tower in new_state)

                        # Calculate the priority of the new state
                        new_priority = priority + 1

                        # Check if the new state has been visited
                        if new_state not in visited:
                            # Add the new state and moves to the queue
                            new_moves = moves + [(source, target)]
                            heapq.heappush(queue, (new_priority, (new_state, new_moves)))
                            visited.add(new_state)

    def heuristic(self, state):
        return sum(len(tower) for tower in state)

    def solve_with_a_star(self):
        # Initialize the A* priority queue with the initial state
        initial_state = (tuple(tuple(tower) for tower in self.towers), [])
        queue = [(self.heuristic(initial_state), initial_state)]  # Priority queue using heapq
        heapq.heapify(queue)

        # Set to keep track of visited states
        visited = set()

        # Perform A* until the queue is empty
        while queue:
            # Get the current state from the queue
            _, (current_state, moves) = heapq.heappop(queue)

            # Check if the current state is the goal state
            if len(current_state[2]) == self.num_disks:
                # Apply the moves to the game state
                for move in moves:
                    source, target = move
                    self.move_disk(source, target)
                    self.draw_towers()
                    pygame.display.flip()
                    pygame.time.delay(500)
                    self.moves += 1  # Increment moves after each move
                return

            # Generate possible moves from the current state
            for source in range(3):
                if not current_state[source]:
                    continue
                for target in range(3):
                    if source != target and (
                            not current_state[target] or current_state[source][-1] < current_state[target][-1]):
                        # Create a new state by making the move
                        new_state = [list(tower) for tower in current_state]
                        disk = new_state[source].pop()
                        new_state[target].append(disk)
                        new_state = tuple(tuple(tower) for tower in new_state)

                        # Calculate the priority of the new state
                        new_priority = self.heuristic(new_state) + len(moves) + 1

                        # Check if the new state has been visited
                        if new_state not in visited:
                            # Add the new state and moves to the queue
                            new_moves = moves + [(source, target)]
                            heapq.heappush(queue, (new_priority, (new_state, new_moves)))
                            visited.add(new_state)

    def solve_with_best_first(self):
        # Initialize the Best-First priority queue with the initial state
        initial_state = (tuple(tuple(tower) for tower in self.towers), [])
        queue = [(self.heuristic(initial_state), initial_state)]  # Priority queue using heapq
        heapq.heapify(queue)

        # Set to keep track of visited states
        visited = set()

        # Perform Best-First until the queue is empty
        while queue:
            # Get the current state from the queue
            _, (current_state, moves) = heapq.heappop(queue)

            # Check if the current state is the goal state
            if len(current_state[2]) == self.num_disks:
                # Apply the moves to the game state
                for move in moves:
                    source, target = move
                    self.move_disk(source, target)
                    self.draw_towers()
                    pygame.display.flip()
                    pygame.time.delay(500)
                    self.moves += 1  # Increment moves after each move
                return

            # Generate possible moves from the current state
            for source in range(3):
                if not current_state[source]:
                    continue
                for target in range(3):
                    if source != target and (
                            not current_state[target] or current_state[source][-1] < current_state[target][-1]):
                        # Create a new state by making the move
                        new_state = [list(tower) for tower in current_state]
                        disk = new_state[source].pop()
                        new_state[target].append(disk)
                        new_state = tuple(tuple(tower) for tower in new_state)

                        # Calculate the priority of the new state
                        new_priority = self.heuristic(new_state)

                        # Check if the new state has been visited
                        if new_state not in visited:
                            # Add the new state and moves to the queue
                            new_moves = moves + [(source, target)]
                            heapq.heappush(queue, (new_priority, (new_state, new_moves)))
                            visited.add(new_state)

    def restart_game(self):
        self.num_disks = self.min_disks
        self.reset_game()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.completed:
                    for i, tower_position in enumerate(self.tower_positions):
                        if pygame.Rect(tower_position[0] - self.tower_width // 2, 100,
                                       self.tower_width, self.height - 300).collidepoint(
                                pygame.mouse.get_pos()):
                            self.on_click(i)

            for button in self.buttons:
                button.handle_event(event)

    def run(self):
        while True:
            self.handle_events()
            self.draw_towers()
            self.draw_buttons()
            pygame.display.flip()
            self.clock.tick(30)


if __name__ == "__main__":
    game = TowerOfHanoiGame()
    game.run()
