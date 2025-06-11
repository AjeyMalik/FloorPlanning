import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import numpy as np
import random
import heapq
from collections import defaultdict, deque


class Room:
    def __init__(self, name, width, height, max_expansion=20):
        self.name = name
        self.original_width = width
        self.original_height = height
        self.width = width
        self.height = height
        self.x = None
        self.y = None
        self.rotated = False
        # Add max_expansion parameter to control how much a room can expand
        self.max_expansion = max_expansion

    def rotate(self):
        self.width, self.height = self.height, self.width
        self.rotated = not self.rotated

    def reset_to_original_size(self):
        """Reset room to its original dimensions"""
        if self.rotated:
            self.width = self.original_height
            self.height = self.original_width
        else:
            self.width = self.original_width
            self.height = self.original_height

    def get_area(self):
        return self.width * self.height

    def __repr__(self):
        position = f"at ({self.x}, {self.y})" if self.x is not None else "unplaced"
        size_info = f"[{self.width}x{self.height}]"
        if self.width != self.original_width or self.height != self.original_height:
            if not self.rotated:
                size_info += f" (expanded from {self.original_width}x{self.original_height})"
            else:
                size_info += f" (expanded from {self.original_height}x{self.original_width} and rotated)"
        elif self.rotated:
            size_info += f" (rotated from {self.original_height}x{self.original_width})"

        return f"Room {self.name} {size_info} {position} (max expansion: {self.max_expansion})"

    def get_boundaries(self):
        """Return room boundaries as (left, right, bottom, top)"""
        if self.x is None or self.y is None:
            return None
        return (self.x, self.x + self.width, self.y, self.y + self.height)

    def has_shared_wall_with(self, other_room):
        """Check if this room shares a wall with another room"""
        if self.x is None or self.y is None or other_room.x is None or other_room.y is None:
            return False

        left1, right1, bottom1, top1 = self.get_boundaries()
        left2, right2, bottom2, top2 = other_room.get_boundaries()

        # Check for vertical walls (left or right side)
        if right1 == left2:  # This room's right wall is other room's left wall
            # Check if there's a vertical overlap
            return max(bottom1, bottom2) < min(top1, top2)

        if right2 == left1:  # Other room's right wall is this room's left wall
            # Check if there's a vertical overlap
            return max(bottom1, bottom2) < min(top1, top2)

        # Check for horizontal walls (top or bottom)
        if top1 == bottom2:  # This room's top wall is other room's bottom wall
            # Check if there's a horizontal overlap
            return max(left1, left2) < min(right1, right2)

        if top2 == bottom1:  # Other room's top wall is this room's bottom wall
            # Check if there's a horizontal overlap
            return max(left1, left2) < min(right1, right2)

        return False


class FloorPlan:
    def __init__(self, region_specs):
        """
        region_specs: list of dictionaries with the following keys:
        - 'width': width of the rectangular region
        - 'height': height of the rectangular region
        - 'x': starting x-coordinate of the region (default 0)
        - 'y': starting y-coordinate of the region (default based on previous regions)

        Example: [
            {'x': 0, 'y': 0, 'width': 12, 'height': 4},
            {'x': 0, 'y': 4, 'width': 18, 'height': 6},
            {'x': 0, 'y': 10, 'width': 22, 'height': 6}
        ]
        """
        self.rooms = []
        self.adjacency_graph = nx.Graph()

        # Process floor regions
        self.floor_regions = []

        # Support both the new format and the old format for backward compatibility
        if isinstance(region_specs[0], tuple):
            # Old format: [(width1, height1), (width2, height2), ...]
            y_offset = 0
            for width, height in region_specs:
                self.floor_regions.append({
                    'x': 0,
                    'y': y_offset,
                    'width': width,
                    'height': height
                })
                y_offset += height
        else:
            # New format: List of dictionaries
            for region in region_specs:
                self.floor_regions.append({
                    'x': region.get('x', 0),
                    'y': region.get('y', 0),
                    'width': region['width'],
                    'height': region['height']
                })

        # Calculate floor dimensions
        self.floor_width = max(region['x'] + region['width'] for region in self.floor_regions)
        self.floor_height = max(region['y'] + region['height'] for region in self.floor_regions)

        # Add spatial indexing for faster overlap detection
        self.spatial_grid = {}
        self.grid_size = 2  # Grid cell size for spatial indexing

    def _get_grid_cells(self, x, y, width, height):
        """Get all grid cells that a rectangle occupies"""
        cells = []
        start_x = x // self.grid_size
        end_x = (x + width - 1) // self.grid_size
        start_y = y // self.grid_size
        end_y = (y + height - 1) // self.grid_size

        for gx in range(start_x, end_x + 1):
            for gy in range(start_y, end_y + 1):
                cells.append((gx, gy))
        return cells

    def _add_to_spatial_grid(self, room):
        """Add room to spatial grid for fast overlap detection"""
        if room.x is None or room.y is None:
            return

        cells = self._get_grid_cells(room.x, room.y, room.width, room.height)
        for cell in cells:
            if cell not in self.spatial_grid:
                self.spatial_grid[cell] = []
            self.spatial_grid[cell].append(room)

    def _remove_from_spatial_grid(self, room):
        """Remove room from spatial grid"""
        if room.x is None or room.y is None:
            return

        cells = self._get_grid_cells(room.x, room.y, room.width, room.height)
        for cell in cells:
            if cell in self.spatial_grid and room in self.spatial_grid[cell]:
                self.spatial_grid[cell].remove(room)
                if not self.spatial_grid[cell]:
                    del self.spatial_grid[cell]

    def check_overlap_optimized(self, room, x, y, width, height):
        """Optimized overlap detection using spatial grid"""
        cells = self._get_grid_cells(x, y, width, height)
        checked_rooms = set()

        for cell in cells:
            if cell in self.spatial_grid:
                for existing_room in self.spatial_grid[cell]:
                    if existing_room != room and existing_room not in checked_rooms:
                        checked_rooms.add(existing_room)
                        # Check actual overlap
                        if (x < existing_room.x + existing_room.width and
                                x + width > existing_room.x and
                                y < existing_room.y + existing_room.height and
                                y + height > existing_room.y):
                            return True
        return False

    def get_valid_positions(self, room, max_positions=100):
        """Get valid positions for a room, prioritizing adjacency requirements"""
        valid_positions = []

        # Get rooms that should be adjacent to this room
        adjacent_rooms = []
        for neighbor in self.adjacency_graph.neighbors(room.name):
            neighbor_room = next((r for r in self.rooms if r.name == neighbor), None)
            if neighbor_room and neighbor_room.x is not None:
                adjacent_rooms.append(neighbor_room)

        # If we have adjacent rooms, prioritize positions near them
        if adjacent_rooms:
            for adj_room in adjacent_rooms:
                # Try positions around the adjacent room
                positions = [
                    (adj_room.x + adj_room.width, adj_room.y),  # Right
                    (adj_room.x - room.width, adj_room.y),  # Left
                    (adj_room.x, adj_room.y + adj_room.height),  # Above
                    (adj_room.x, adj_room.y - room.height),  # Below
                ]

                for x, y in positions:
                    if (self.is_within_floor(x, y, room.width, room.height) and
                            not self.check_overlap_optimized(room, x, y, room.width, room.height)):
                        valid_positions.append((x, y))
                        if len(valid_positions) >= max_positions:
                            return valid_positions

        # If no adjacent rooms or need more positions, try random positions
        attempts = 0
        while len(valid_positions) < max_positions and attempts < 200:
            attempts += 1

            # Choose a random region
            region = random.choice(self.floor_regions)

            if region['width'] < room.width or region['height'] < room.height:
                continue

            max_x = region['x'] + region['width'] - room.width
            max_y = region['y'] + region['height'] - room.height

            if max_x >= region['x'] and max_y >= region['y']:
                x = random.randint(region['x'], max_x)
                y = random.randint(region['y'], max_y)

                if (not self.check_overlap_optimized(room, x, y, room.width, room.height) and
                        (x, y) not in valid_positions):
                    valid_positions.append((x, y))

        return valid_positions

    def get_adjacency_clusters(self):
        """
        Group rooms into connected components based on adjacency requirements
        Returns clusters ordered by size (largest first)
        """
        visited = set()
        clusters = []

        for room in self.rooms:
            if room.name not in visited:
                # BFS to find connected component
                cluster = []
                queue = deque([room.name])
                visited.add(room.name)

                while queue:
                    current_room = queue.popleft()
                    cluster.append(current_room)

                    # Add all unvisited neighbors
                    for neighbor in self.adjacency_graph.neighbors(current_room):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

                clusters.append(cluster)

        # Sort clusters by size (largest first) and then by total area
        def cluster_priority(cluster):
            total_area = sum(next(r for r in self.rooms if r.name == name).get_area()
                             for name in cluster)
            return (len(cluster), total_area)

        clusters.sort(key=cluster_priority, reverse=True)
        return clusters

    def place_cluster_bfs(self, cluster, placed_rooms):
        """
        Place a cluster of rooms using BFS to maximize adjacency satisfaction
        """
        if not cluster:
            return True

        cluster_rooms = [next(r for r in self.rooms if r.name == name) for name in cluster]

        # If this is the first cluster or no rooms are placed yet
        if not placed_rooms:
            # Start with the largest room in the cluster
            start_room = max(cluster_rooms, key=lambda r: r.get_area())

            # Try to place the start room in the center of the largest region
            best_region = max(self.floor_regions, key=lambda r: r['width'] * r['height'])
            center_x = best_region['x'] + (best_region['width'] - start_room.width) // 2
            center_y = best_region['y'] + (best_region['height'] - start_room.height) // 2

            # Ensure it's within bounds
            center_x = max(best_region['x'], min(center_x, best_region['x'] + best_region['width'] - start_room.width))
            center_y = max(best_region['y'],
                           min(center_y, best_region['y'] + best_region['height'] - start_room.height))

            if (self.is_within_floor(center_x, center_y, start_room.width, start_room.height) and
                    not self.check_overlap_optimized(start_room, center_x, center_y, start_room.width,
                                                     start_room.height)):
                start_room.x = center_x
                start_room.y = center_y
                self._add_to_spatial_grid(start_room)
                placed_rooms.add(start_room.name)
            else:
                # Fallback to any valid position
                valid_positions = self.get_valid_positions(start_room, max_positions=50)
                if valid_positions:
                    x, y = valid_positions[0]
                    start_room.x = x
                    start_room.y = y
                    self._add_to_spatial_grid(start_room)
                    placed_rooms.add(start_room.name)
                else:
                    return False

        # BFS placement starting from already placed rooms
        queue = deque()
        remaining_rooms = set(cluster) - placed_rooms

        # Initialize queue with rooms that should be adjacent to already placed rooms
        for room_name in remaining_rooms:
            for neighbor in self.adjacency_graph.neighbors(room_name):
                if neighbor in placed_rooms:
                    queue.append(room_name)
                    break

        # If no connections to placed rooms, start with largest remaining room
        if not queue and remaining_rooms:
            largest_remaining = max([r for r in cluster_rooms if r.name in remaining_rooms],
                                    key=lambda r: r.get_area())
            queue.append(largest_remaining.name)

        # BFS placement
        while queue and remaining_rooms:
            current_room_name = queue.popleft()

            if current_room_name not in remaining_rooms:
                continue

            current_room = next(r for r in self.rooms if r.name == current_room_name)

            # Get positions prioritizing adjacency to already placed neighbors
            placed_neighbors = [neighbor for neighbor in self.adjacency_graph.neighbors(current_room_name)
                                if neighbor in placed_rooms]

            valid_positions = self.get_valid_positions_for_adjacency(current_room, placed_neighbors)

            # Try both orientations
            placed = False
            for try_rotation in [False, True]:
                if try_rotation:
                    current_room.rotate()

                valid_positions = self.get_valid_positions_for_adjacency(current_room, placed_neighbors)

                if valid_positions:
                    # Sort positions by adjacency score
                    position_scores = []
                    for x, y in valid_positions:
                        temp_x, temp_y = current_room.x, current_room.y
                        current_room.x, current_room.y = x, y

                        # Count how many required adjacencies this position satisfies
                        adjacency_score = 0
                        for neighbor_name in placed_neighbors:
                            neighbor_room = next(r for r in self.rooms if r.name == neighbor_name)
                            if current_room.has_shared_wall_with(neighbor_room):
                                adjacency_score += 1

                        position_scores.append(((x, y), adjacency_score))
                        current_room.x, current_room.y = temp_x, temp_y

                    # Sort by adjacency score (highest first)
                    position_scores.sort(key=lambda x: x[1], reverse=True)

                    # Try the best positions
                    for (x, y), score in position_scores[:5]:  # Try top 5 positions
                        current_room.x = x
                        current_room.y = y
                        self._add_to_spatial_grid(current_room)
                        placed_rooms.add(current_room_name)
                        remaining_rooms.remove(current_room_name)
                        placed = True

                        # Add unplaced neighbors to queue
                        for neighbor in self.adjacency_graph.neighbors(current_room_name):
                            if neighbor in remaining_rooms and neighbor not in [item for item in queue]:
                                queue.append(neighbor)

                        break

                if placed:
                    break

            if not placed:
                return False

        return len(remaining_rooms) == 0

    def get_valid_positions_for_adjacency(self, room, placed_neighbors, max_positions=30):
        """
        Get valid positions prioritizing adjacency to specific placed neighbors
        """
        valid_positions = []

        # Get neighbor rooms
        neighbor_rooms = []
        for neighbor_name in placed_neighbors:
            neighbor_room = next(r for r in self.rooms if r.name == neighbor_name)
            if neighbor_room.x is not None:
                neighbor_rooms.append(neighbor_room)

        # Generate positions adjacent to neighbors
        for neighbor_room in neighbor_rooms:
            # Try all four sides of the neighbor
            potential_positions = [
                (neighbor_room.x + neighbor_room.width, neighbor_room.y),  # Right
                (neighbor_room.x - room.width, neighbor_room.y),  # Left
                (neighbor_room.x, neighbor_room.y + neighbor_room.height),  # Above
                (neighbor_room.x, neighbor_room.y - room.height),  # Below
            ]

            # Also try positions that share partial walls
            for offset in range(1, min(neighbor_room.width, neighbor_room.height)):
                potential_positions.extend([
                    (neighbor_room.x + neighbor_room.width, neighbor_room.y + offset),
                    (neighbor_room.x + neighbor_room.width, neighbor_room.y - offset),
                    (neighbor_room.x - room.width, neighbor_room.y + offset),
                    (neighbor_room.x - room.width, neighbor_room.y - offset),
                    (neighbor_room.x + offset, neighbor_room.y + neighbor_room.height),
                    (neighbor_room.x - offset, neighbor_room.y + neighbor_room.height),
                    (neighbor_room.x + offset, neighbor_room.y - room.height),
                    (neighbor_room.x - offset, neighbor_room.y - room.height),
                ])

            for x, y in potential_positions:
                if (self.is_within_floor(x, y, room.width, room.height) and
                        not self.check_overlap_optimized(room, x, y, room.width, room.height) and
                        (x, y) not in valid_positions):
                    valid_positions.append((x, y))

                    if len(valid_positions) >= max_positions:
                        return valid_positions

        # If we need more positions, add some random ones
        if len(valid_positions) < max_positions:
            additional_positions = self.get_valid_positions(room, max_positions - len(valid_positions))
            for pos in additional_positions:
                if pos not in valid_positions:
                    valid_positions.append(pos)

        return valid_positions

    def add_room(self, name, width, height, max_expansion=20):
        """Add a room with specified dimensions and maximum expansion limit"""
        room = Room(name, width, height, max_expansion)
        self.rooms.append(room)
        self.adjacency_graph.add_node(name)
        return room

    def add_adjacency(self, room1_name, room2_name):
        if room1_name in self.adjacency_graph.nodes and room2_name in self.adjacency_graph.nodes:
            self.adjacency_graph.add_edge(room1_name, room2_name)

    def is_within_floor(self, x, y, width, height):
        """Check if a rectangle fits within the entire composite floor shape"""
        for dx in range(width):
            for dy in range(height):
                px = x + dx
                py = y + dy

                if not self.point_in_floor(px, py):
                    return False
        return True

    def point_in_floor(self, x, y):
        """Check if a point is within any of the defined floor regions"""
        for region in self.floor_regions:
            if (region['x'] <= x < region['x'] + region['width'] and
                    region['y'] <= y < region['y'] + region['height']):
                return True
        return False

    def check_overlap(self, room, x, y, width, height):
        """Check if placing a room at (x,y) with given width/height would overlap with existing rooms"""
        for existing_room in self.rooms:
            if existing_room.x is not None and existing_room != room:
                # Check for overlap - two rectangles overlap if they overlap in both x and y directions
                if (x < existing_room.x + existing_room.width and
                        x + width > existing_room.x and
                        y < existing_room.y + existing_room.height and
                        y + height > existing_room.y):
                    return True
        return False

    def evaluate_adjacency_score(self):
        """Calculate how well adjacency requirements are met"""
        score = 0
        adjacent_pairs = []

        for room1_name, room2_name in self.adjacency_graph.edges:
            room1 = next(r for r in self.rooms if r.name == room1_name)
            room2 = next(r for r in self.rooms if r.name == room2_name)

            if room1.x is None or room2.x is None:
                continue

            # Check if rooms share a wall
            if room1.has_shared_wall_with(room2):
                score += 1
                adjacent_pairs.append((room1_name, room2_name))

        return score, adjacent_pairs

    def can_expand_room(self, room, direction, amount):
        """Check if a room can be expanded in the given direction by the specified amount"""
        if room.x is None or room.y is None:
            return False

        # Calculate total expansion so far
        current_expansion = 0
        if not room.rotated:
            current_expansion += room.width - room.original_width
            current_expansion += room.height - room.original_height
        else:
            current_expansion += room.width - room.original_height
            current_expansion += room.height - room.original_width

        # Check if we've reached the maximum expansion for this room
        if current_expansion + amount > room.max_expansion:
            return False

        # Calculate new dimensions and position after expansion
        new_x, new_y = room.x, room.y
        new_width, new_height = room.width, room.height

        if direction == 'right':
            new_width += amount
        elif direction == 'left':
            new_x -= amount
            new_width += amount
        elif direction == 'up':
            new_height += amount
        elif direction == 'down':
            new_y -= amount
            new_height += amount
        else:
            return False

        # Check if new position is within floor and doesn't overlap other rooms
        if not self.is_within_floor(new_x, new_y, new_width, new_height):
            return False

        if self.check_overlap(room, new_x, new_y, new_width, new_height):
            return False

        return True

    def expand_rooms(self):
        """
        Expand rooms to fill available space while maintaining adjacency constraints
        and ensuring no overlaps, respecting each room's max_expansion limit
        """
        # For each room, attempt expansion in each direction
        for room in self.rooms:
            if room.x is None or room.y is None:
                continue

            # Try to expand in all four directions
            directions = ['right', 'down', 'left', 'up']
            random.shuffle(directions)  # Randomize direction order for more varied results

            for direction in directions:
                # Try expanding 1 unit at a time up to max expansion
                expanded = True
                total_expansion = 0

                while expanded:
                    if self.can_expand_room(room, direction, 1):
                        # Apply 1 unit expansion
                        if direction == 'right':
                            room.width += 1
                        elif direction == 'left':
                            room.x -= 1
                            room.width += 1
                        elif direction == 'up':
                            room.height += 1
                        elif direction == 'down':
                            room.y -= 1
                            room.height += 1

                        total_expansion += 1
                    else:
                        expanded = False

    def place_rooms_bfs_with_backtracking(self, max_depth=None, max_positions_per_room=25, enable_expansion=True,
                                          timeout_seconds=30):
        """
        True BFS approach with backtracking for room placement
        """
        import time
        from collections import deque

        start_time = time.time()

        # Clear spatial grid and reset rooms
        self.spatial_grid = {}
        for room in self.rooms:
            room.x = None
            room.y = None
            room.reset_to_original_size()

        # Sort rooms by constraint priority (most constrained first)
        room_constraints = {}
        for room in self.rooms:
            room_constraints[room.name] = len(list(self.adjacency_graph.neighbors(room.name)))

        sorted_rooms = sorted(self.rooms,
                              key=lambda r: (room_constraints[r.name], r.get_area()),
                              reverse=True)

        if max_depth is None:
            max_depth = len(sorted_rooms)

        # BFS queue: (room_index, placement_state)
        initial_state = PlacementState()
        queue = deque([(0, initial_state)])

        best_score = -1
        best_placement = None
        nodes_explored = 0

        while queue and (time.time() - start_time) < timeout_seconds:
            room_idx, current_state = queue.popleft()
            nodes_explored += 1

            # Check if we've placed all rooms
            if room_idx >= len(sorted_rooms):
                # Apply current state and evaluate
                self._apply_placement_state(current_state)

                if enable_expansion:
                    self.expand_rooms_optimized()

                score, _ = self.evaluate_adjacency_score()

                if score > best_score:
                    best_score = score
                    best_placement = self._capture_current_placement()

                # If perfect score, we can stop
                if score == len(self.adjacency_graph.edges):
                    print(f"Perfect solution found! Explored {nodes_explored} nodes")
                    return True

                continue

            # Skip if we've exceeded max depth
            if room_idx >= max_depth:
                continue

            current_room = sorted_rooms[room_idx]

            # Try both orientations (original and rotated)
            orientations = [False, True]

            for rotated in orientations:
                # Apply rotation if needed
                if rotated:
                    current_room.rotate()

                # Get valid positions for current room considering already placed rooms
                valid_positions = self._get_valid_positions_with_state(current_room, current_state,
                                                                       max_positions_per_room)

                for x, y in valid_positions:
                    # Check if this position is valid with current state
                    if self._is_position_valid_with_state(current_room, x, y, current_state):
                        # Create new state with this room placed
                        new_state = current_state.copy()
                        new_state.add_room(current_room, x, y, current_room.width, current_room.height, rotated)

                        # Add to queue for next room
                        queue.append((room_idx + 1, new_state))

                # Reset rotation
                if rotated:
                    current_room.rotate()

        print(f"BFS completed. Explored {nodes_explored} nodes in {time.time() - start_time:.2f} seconds")

        # Apply best placement found
        if best_placement:
            self._apply_placement_data(best_placement)
            print(f"Best adjacency score: {best_score}/{len(self.adjacency_graph.edges)}")
            return True

        return False

    def _get_valid_positions_with_state(self, room, current_state, max_positions):
        """Get valid positions considering current placement state"""
        valid_positions = []

        # Get rooms that should be adjacent and are already placed
        adjacent_rooms = []
        for neighbor_name in self.adjacency_graph.neighbors(room.name):
            for placement in current_state.placements:
                if placement[0] == neighbor_name:  # room_name matches
                    adjacent_rooms.append(placement)
                    break

        # Prioritize positions near already placed adjacent rooms
        if adjacent_rooms:
            for adj_name, adj_x, adj_y, adj_w, adj_h, adj_rot in adjacent_rooms:
                positions = [
                    (adj_x + adj_w, adj_y),  # Right
                    (adj_x - room.width, adj_y),  # Left
                    (adj_x, adj_y + adj_h),  # Above
                    (adj_x, adj_y - room.height),  # Below
                ]

                for x, y in positions:
                    if (self.is_within_floor(x, y, room.width, room.height) and
                            self._is_position_valid_with_state(room, x, y, current_state) and
                            (x, y) not in valid_positions):
                        valid_positions.append((x, y))

                        if len(valid_positions) >= max_positions:
                            return valid_positions

        # Add random positions if needed
        attempts = 0
        while len(valid_positions) < max_positions and attempts < 100:
            attempts += 1

            region = random.choice(self.floor_regions)

            if region['width'] < room.width or region['height'] < room.height:
                continue

            max_x = region['x'] + region['width'] - room.width
            max_y = region['y'] + region['height'] - room.height

            if max_x >= region['x'] and max_y >= region['y']:
                x = random.randint(region['x'], max_x)
                y = random.randint(region['y'], max_y)

                if (self._is_position_valid_with_state(room, x, y, current_state) and
                        (x, y) not in valid_positions):
                    valid_positions.append((x, y))

        return valid_positions

    def _is_position_valid_with_state(self, room, x, y, current_state):
        """Check if position is valid given current placement state"""
        # Check floor boundaries
        if not self.is_within_floor(x, y, room.width, room.height):
            return False

        # Check overlap with already placed rooms using grid cells
        room_cells = set(current_state._get_grid_cells(x, y, room.width, room.height))

        if room_cells.intersection(current_state.occupied_cells):
            return False

        return True

    def _apply_placement_state(self, placement_state):
        """Apply a placement state to the actual rooms"""
        self.spatial_grid = {}

        for room_name, x, y, width, height, rotated in placement_state.placements:
            room = next(r for r in self.rooms if r.name == room_name)
            room.x = x
            room.y = y
            room.width = width
            room.height = height
            room.rotated = rotated
            self._add_to_spatial_grid(room)

    def _capture_current_placement(self):
        """Capture current room placements"""
        return [
            (room.name, room.x, room.y, room.width, room.height, room.rotated, room.max_expansion)
            for room in self.rooms if room.x is not None
        ]

    def _apply_placement_data(self, placement_data):
        """Apply captured placement data"""
        self.spatial_grid = {}
        for room_data in placement_data:
            name, x, y, width, height, rotated, max_expansion = room_data
            room = next(r for r in self.rooms if r.name == name)
            room.x = x
            room.y = y
            room.width = width
            room.height = height
            room.rotated = rotated
            room.max_expansion = max_expansion
            self._add_to_spatial_grid(room)

    def place_rooms_with_constraints_optimized(self, max_attempts=100, enable_expansion=True):
        """
        Optimized room placement using constraint satisfaction and spatial indexing
        """
        # Clear spatial grid
        self.spatial_grid = {}

        # Reset all rooms
        for room in self.rooms:
            room.x = None
            room.y = None
            room.reset_to_original_size()

        # Sort rooms by constraint priority (rooms with more adjacency requirements first)
        room_constraints = {}
        for room in self.rooms:
            room_constraints[room.name] = len(list(self.adjacency_graph.neighbors(room.name)))

        sorted_rooms = sorted(self.rooms,
                              key=lambda r: (room_constraints[r.name], r.get_area()),
                              reverse=True)

        best_score = -1
        best_placement = None

        for attempt in range(max_attempts):
            # Reset placements
            self.spatial_grid = {}
            for room in self.rooms:
                room.x = None
                room.y = None
                room.reset_to_original_size()
                if random.random() > 0.5:
                    room.rotate()

            # Use constraint satisfaction approach
            placement_successful = True

            for room in sorted_rooms:
                placed = False

                # Get valid positions for this room
                valid_positions = self.get_valid_positions(room, max_positions=30)

                # Try original orientation
                for x, y in valid_positions:
                    room.x = x
                    room.y = y
                    self._add_to_spatial_grid(room)
                    placed = True
                    break

                # If not placed, try rotated
                if not placed:
                    room.rotate()
                    valid_positions = self.get_valid_positions(room, max_positions=30)

                    for x, y in valid_positions:
                        room.x = x
                        room.y = y
                        self._add_to_spatial_grid(room)
                        placed = True
                        break

                if not placed:
                    placement_successful = False
                    break

            if placement_successful:
                # Apply expansion if enabled
                if enable_expansion:
                    self.expand_rooms_optimized()

                # Evaluate this placement
                score, _ = self.evaluate_adjacency_score()

                if score > best_score:
                    best_score = score
                    best_placement = [
                        (room.name, room.x, room.y, room.width, room.height, room.rotated, room.max_expansion)
                        for room in self.rooms
                    ]

                # Early exit if all constraints satisfied
                if score == len(self.adjacency_graph.edges):
                    break

        # Restore best placement
        if best_placement:
            self.spatial_grid = {}
            for room_data in best_placement:
                name, x, y, width, height, rotated, max_expansion = room_data
                room = next(r for r in self.rooms if r.name == name)
                room.x = x
                room.y = y
                room.width = width
                room.height = height
                room.rotated = rotated
                room.max_expansion = max_expansion
                self._add_to_spatial_grid(room)
            return True

        return False


    def expand_rooms_optimized(self):
        """Optimized room expansion using spatial grid"""
        for room in self.rooms:
            if room.x is None or room.y is None:
                continue

            # Remove from spatial grid temporarily
            self._remove_from_spatial_grid(room)

            # Try expansion in each direction
            directions = ['right', 'down', 'left', 'up']
            random.shuffle(directions)

            for direction in directions:
                # Try expanding in larger increments first, then smaller
                for increment in [5, 3, 2, 1]:
                    while self.can_expand_room_optimized(room, direction, increment):
                        # Apply expansion
                        if direction == 'right':
                            room.width += increment
                        elif direction == 'left':
                            room.x -= increment
                            room.width += increment
                        elif direction == 'up':
                            room.height += increment
                        elif direction == 'down':
                            room.y -= increment
                            room.height += increment

            # Add back to spatial grid
            self._add_to_spatial_grid(room)

    def can_expand_room_optimized(self, room, direction, amount):
        """Optimized room expansion check"""
        if room.x is None or room.y is None:
            return False

        # Check expansion limits
        current_expansion = 0
        if not room.rotated:
            current_expansion += room.width - room.original_width
            current_expansion += room.height - room.original_height
        else:
            current_expansion += room.width - room.original_height
            current_expansion += room.height - room.original_width

        if current_expansion + amount > room.max_expansion:
            return False

        # Calculate new dimensions
        new_x, new_y = room.x, room.y
        new_width, new_height = room.width, room.height

        if direction == 'right':
            new_width += amount
        elif direction == 'left':
            new_x -= amount
            new_width += amount
        elif direction == 'up':
            new_height += amount
        elif direction == 'down':
            new_y -= amount
            new_height += amount
        else:
            return False

        # Quick bounds check
        if not self.is_within_floor(new_x, new_y, new_width, new_height):
            return False

        # Use optimized overlap check
        return not self.check_overlap_optimized(room, new_x, new_y, new_width, new_height)



    def visualize(self):
        """Visualize the floor plan using matplotlib"""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Draw floor shape
        for region in self.floor_regions:
            rect = patches.Rectangle(
                (region['x'], region['y']),
                region['width'],
                region['height'],
                linewidth=2,
                edgecolor='black',
                facecolor='none',
                linestyle='--'
            )
            ax.add_patch(rect)

        # Draw rooms
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.rooms)))
        for i, room in enumerate(self.rooms):
            if room.x is not None and room.y is not None:
                rect = patches.Rectangle(
                    (room.x, room.y),
                    room.width,
                    room.height,
                    linewidth=1,
                    edgecolor='black',
                    facecolor=colors[i],
                    alpha=0.7
                )
                ax.add_patch(rect)

                # Add room name, size, and expansion info
                original_size = f"{room.original_width}x{room.original_height}"
                current_size = f"{room.width}x{room.height}"
                display_text = f"{room.name}\n{current_size}"

                # Add expansion info if expanded
                if room.width != room.original_width or room.height != room.original_height:
                    if room.rotated:
                        display_text += f"\n(from {room.original_height}x{room.original_width})"
                    else:
                        display_text += f"\n(from {original_size})"

                ax.text(
                    room.x + room.width / 2,
                    room.y + room.height / 2,
                    display_text,
                    ha='center',
                    va='center',
                    fontsize=8
                )

        # Add adjacency relationships as dotted lines between room centers
        for room1_name, room2_name in self.adjacency_graph.edges:
            room1 = next(r for r in self.rooms if r.name == room1_name)
            room2 = next(r for r in self.rooms if r.name == room2_name)

            if room1.x is not None and room2.x is not None:
                center1 = (room1.x + room1.width / 2, room1.y + room1.height / 2)
                center2 = (room2.x + room2.width / 2, room2.y + room2.height / 2)

                # Check if rooms share a wall
                if room1.has_shared_wall_with(room2):
                    ax.plot([center1[0], center2[0]], [center1[1], center2[1]], 'g-', linewidth=1.5)
                else:
                    ax.plot([center1[0], center2[0]], [center1[1], center2[1]], 'r:', linewidth=0.8)

        # Set limits and labels
        max_width = self.floor_width
        max_height = self.floor_height
        ax.set_xlim(-1, max_width + 1)
        ax.set_ylim(-1, max_height + 1)
        ax.set_aspect('equal')
        ax.set_title('Floor Plan')
        ax.set_xlabel('Width')
        ax.set_ylabel('Height')

        plt.tight_layout()
        plt.show()

    def print_statistics(self):
        """Print statistics about the floor plan"""
        total_area = sum(region['width'] * region['height'] for region in self.floor_regions)
        used_area = sum(room.width * room.height for room in self.rooms if room.x is not None)

        print(f"Floor area: {total_area} square units")
        print(f"Room area: {used_area} square units")
        print(f"Space utilization: {used_area / total_area:.2%}")

        score, adjacent_pairs = self.evaluate_adjacency_score()
        print(f"Adjacency score: {score}/{len(self.adjacency_graph.edges)}")
        print(f"Adjacent pairs: {adjacent_pairs}")

        # Print expansion statistics
        print("\nRoom Expansion Statistics:")
        for room in self.rooms:
            if room.x is not None:
                original_area = room.original_width * room.original_height
                current_area = room.width * room.height
                expansion_pct = (current_area - original_area) / original_area * 100 if original_area > 0 else 0

                # Calculate how much of the max expansion was used
                if not room.rotated:
                    total_expansion = (room.width - room.original_width) + (room.height - room.original_height)
                else:
                    total_expansion = (room.width - room.original_height) + (room.height - room.original_width)

                expansion_usage = f"{total_expansion}/{room.max_expansion}"

                print(f"{room.name}: {room.original_width}x{room.original_height} → {room.width}x{room.height} " +
                      f"({expansion_pct:.1f}% increase, expansion used: {expansion_usage})")


class PlacementState:
    """Represents the state of room placements during BFS"""

    def __init__(self):
        self.placements = []  # List of (room_name, x, y, width, height, rotated)
        self.occupied_cells = set()  # Set of occupied grid cells

    def add_room(self, room, x, y, width, height, rotated):
        """Add a room placement to this state"""
        self.placements.append((room.name, x, y, width, height, rotated))

        # Add occupied cells (using same grid logic as spatial_grid)
        cells = self._get_grid_cells(x, y, width, height)
        self.occupied_cells.update(cells)

    def copy(self):
        """Create a deep copy of this state"""
        new_state = PlacementState()
        new_state.placements = self.placements.copy()
        new_state.occupied_cells = self.occupied_cells.copy()
        return new_state

    def _get_grid_cells(self, x, y, width, height):
        """Get grid cells occupied by a rectangle (matches main class logic)"""
        cells = []
        grid_size = 2

        start_x = x // grid_size
        end_x = (x + width - 1) // grid_size
        start_y = y // grid_size
        end_y = (y + height - 1) // grid_size

        for gx in range(start_x, end_x + 1):
            for gy in range(start_y, end_y + 1):
                cells.append((gx, gy))

        return cells


# Example usage
if __name__ == "__main__":
    # Define floor shape with explicit x and y coordinates for each region
    # This example creates an L-shaped floor plan
    region_specs = [
        {'x': 0, 'y': 0, 'width': 10, 'height': 10},  # Main square part
        {'x': 10, 'y': 0, 'width': 8, 'height': 5},  # Right extension
        {'x': 0, 'y': 10, 'width': 5, 'height': 8},  # Top extension
        {'x': 10, 'y': 5, 'width': 6, 'height': 6}
    ]

    floor_plan = FloorPlan(region_specs)

    # Add rooms with dimensions and custom max expansion limits
    floor_plan.add_room("Living Room", 8, 4, max_expansion=15)
    floor_plan.add_room("Kitchen", 6, 4, max_expansion=8)
    floor_plan.add_room("Bedroom 1", 5, 4, max_expansion=10)
    floor_plan.add_room("Bedroom 2", 5, 4, max_expansion=6)
    floor_plan.add_room("Bathroom", 3, 4, max_expansion=2)  # Limited expansion for bathroom
    floor_plan.add_room("Hallway", 2, 4, max_expansion=5)
    floor_plan.add_room("Office", 3, 3, max_expansion=0)  # No expansion allowed for office
    floor_plan.add_room("secretRoom", 3, 3, 3)

    # Add adjacency requirements
    floor_plan.add_adjacency("Living Room", "Kitchen")
    floor_plan.add_adjacency("Living Room", "Bathroom")
    floor_plan.add_adjacency("Kitchen", "Bedroom 1")
    floor_plan.add_adjacency("Bedroom 2", "Hallway")
    floor_plan.add_adjacency("Hallway", "Bathroom")
    floor_plan.add_adjacency("Office", "Bedroom 2")
    floor_plan.add_adjacency("secretRoom", "Kitchen")

    # Try to place rooms with expansion enabled
    success = floor_plan.place_rooms_bfs_with_backtracking(10,25,True,30)
    if success:
        print("Successfully placed all rooms!")
        floor_plan.print_statistics()
    else:
        print("Failed to place all rooms. You may need to adjust room or floor dimensions.")

    # Print room placements and sizes
    for room in floor_plan.rooms:
        print(room)

    # Visualize the floor plan
    floor_plan.visualize()
