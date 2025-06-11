import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import numpy as np
import random


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

    def place_rooms_with_constraints(self, max_attempts=1000, enable_expansion=True):
        """Place rooms respecting floor shape and trying to satisfy adjacencies"""
        # Sort rooms by area (largest first) for better packing
        sorted_rooms = sorted(self.rooms, key=lambda r: r.get_area(), reverse=True)

        best_score = -1
        best_placement = None

        # Attempt placements
        for attempt in range(max_attempts):
            # Reset placements and sizes
            for room in self.rooms:
                room.x = None
                room.y = None
                room.reset_to_original_size()
                # Randomly decide whether to rotate
                if random.random() > 0.5:
                    room.rotate()

            # Try to place all rooms
            all_placed = True
            for room in sorted_rooms:
                placed = False

                # Try different positions
                for region in self.floor_regions:
                    # Skip regions too small for this room
                    if region['width'] < room.width or region['height'] < room.height:
                        continue

                    # Try placing in this region
                    for _ in range(200):  # Try 200 random positions within this region
                        # Ensure we have valid ranges for random.randint
                        max_x = region['x'] + region['width'] - room.width
                        max_y = region['y'] + region['height'] - room.height

                        # Only try if we have valid ranges
                        if max_x >= region['x'] and max_y >= region['y']:
                            x = random.randint(region['x'], max_x)
                            y = random.randint(region['y'], max_y)

                            if not self.check_overlap(room, x, y, room.width, room.height):
                                room.x = x
                                room.y = y
                                placed = True
                                break

                    if placed:
                        break

                if not placed:
                    # Try rotating the room and placing again
                    room.rotate()
                    for region in self.floor_regions:
                        # Skip regions too small for this room after rotation
                        if region['width'] < room.width or region['height'] < room.height:
                            continue

                        # Try placing in this region
                        for _ in range(100):
                            max_x = region['x'] + region['width'] - room.width
                            max_y = region['y'] + region['height'] - room.height

                            if max_x >= region['x'] and max_y >= region['y']:
                                x = random.randint(region['x'], max_x)
                                y = random.randint(region['y'], max_y)

                                if not self.check_overlap(room, x, y, room.width, room.height):
                                    room.x = x
                                    room.y = y
                                    placed = True
                                    break

                        if placed:
                            break

                if not placed:
                    all_placed = False
                    break

            if all_placed:
                # Store the current placement
                current_placement = [
                    (room.name, room.x, room.y, room.width, room.height, room.rotated, room.max_expansion)
                    for room in self.rooms]

                # If expansion is enabled, try to expand rooms to fill space
                if enable_expansion:
                    self.expand_rooms()

                # Calculate adjacency score
                score, _ = self.evaluate_adjacency_score()

                # Keep track of the best placement
                if score > best_score:
                    best_score = score
                    best_placement = [
                        (room.name, room.x, room.y, room.width, room.height, room.rotated, room.max_expansion)
                        for room in self.rooms]

                # If all adjacency requirements are met, we can stop
                if score == len(self.adjacency_graph.edges):
                    break

        # Restore best placement if found
        if best_placement:
            for room_data in best_placement:
                name, x, y, width, height, rotated, max_expansion = room_data
                room = next(r for r in self.rooms if r.name == name)
                room.x = x
                room.y = y
                room.width = width
                room.height = height
                room.rotated = rotated
                room.max_expansion = max_expansion
            return True

        return all_placed  # Return True if at least we placed all rooms, even if adjacencies aren't perfect

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


# Example usage
if __name__ == "__main__":
    # Define floor shape with explicit x and y coordinates for each region
    # This example creates an L-shaped floor plan
    region_specs = [
        {'x': 0, 'y': 0, 'width': 10, 'height': 10},  # Main square part
        {'x': 10, 'y': 0, 'width': 8, 'height': 5},  # Right extension
        {'x': 0, 'y': 10, 'width': 5, 'height': 8},  # Top extension
        {'x': 10,'y':5,'width': 6,'height':6}
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
    floor_plan.add_room("secretRoom",3,3,3)

    # Add adjacency requirements
    floor_plan.add_adjacency("Living Room", "Kitchen")
    floor_plan.add_adjacency("Living Room", "Bathroom")
    floor_plan.add_adjacency("Kitchen", "Bedroom 1")
    floor_plan.add_adjacency("Bedroom 2", "Hallway")
    floor_plan.add_adjacency("Hallway", "Bathroom")
    floor_plan.add_adjacency("Office", "Bedroom 2")
    floor_plan.add_adjacency("secretRoom","Kitchen")

    # Try to place rooms with expansion enabled
    success = floor_plan.place_rooms_with_constraints(max_attempts=50000, enable_expansion=True)
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
