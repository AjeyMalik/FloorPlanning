import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from bfs import FloorPlan  # Import from your original file
import json
from tkinter import filedialog

class FloorPlanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Floor Plan Designer")
        self.root.geometry("1200x800")

        # Initialize floor plan with example data
        self.floor_plan = None
        self.current_screen = "regions"

        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create navigation frame
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(fill=tk.X, pady=(0, 10))

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("Region Specs", "regions"),
            ("Rooms", "rooms"),
            ("Adjacency", "adjacency"),
            ("Output", "output")
        ]

        for i, (text, screen) in enumerate(nav_items):
            btn = ttk.Button(self.nav_frame, text=text,
                             command=lambda s=screen: self.show_screen(s))
            btn.pack(side=tk.LEFT, padx=5)
            self.nav_buttons[screen] = btn

        # Generate button
        ttk.Button(self.nav_frame, text="Generate Floor Plan",
                   command=self.generate_floor_plan,
                   style="Accent.TButton").pack(side=tk.RIGHT, padx=5)

        # Create content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize screens
        self.screens = {}
        self.init_screens()

        # Load example data
        self.load_example_data()

        # Show initial screen
        self.show_screen("regions")

    def init_screens(self):
        """Initialize all screen frames"""
        # Region Specs Screen
        self.init_regions_screen()

        # Rooms Screen
        self.init_rooms_screen()

        # Adjacency Screen
        self.init_adjacency_screen()

        # Output Screen
        self.init_output_screen()

    def init_regions_screen(self):
        """Initialize the region specifications screen"""
        frame = ttk.Frame(self.content_frame)
        self.screens["regions"] = frame

        # Title
        ttk.Label(frame, text="Floor Region Specifications",
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # Instructions
        instructions = ttk.Label(frame,
                                 text="Define rectangular regions that make up your floor plan. Each region has x, y coordinates, width, and height.",
                                 wraplength=800)
        instructions.pack(pady=(0, 10))

        # Regions list frame
        regions_frame = ttk.LabelFrame(frame, text="Regions", padding=10)
        regions_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Regions treeview
        columns = ("X", "Y", "Width", "Height")
        self.regions_tree = ttk.Treeview(regions_frame, columns=columns, show="tree headings", height=8)

        # Configure columns
        self.regions_tree.heading("#0", text="Region")
        self.regions_tree.column("#0", width=80)
        for col in columns:
            self.regions_tree.heading(col, text=col)
            self.regions_tree.column(col, width=80)

        self.regions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for regions
        regions_scrollbar = ttk.Scrollbar(regions_frame, orient=tk.VERTICAL, command=self.regions_tree.yview)
        regions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.regions_tree.config(yscrollcommand=regions_scrollbar.set)

        # Region input frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=10)

        # Input fields
        ttk.Label(input_frame, text="X:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.region_x_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.region_x_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Y:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.region_y_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.region_y_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Label(input_frame, text="Width:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.region_width_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.region_width_var, width=10).grid(row=0, column=5, padx=5)

        ttk.Label(input_frame, text="Height:").grid(row=0, column=6, padx=5, sticky=tk.W)
        self.region_height_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.region_height_var, width=10).grid(row=0, column=7, padx=5)

        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=8, padx=20)

        ttk.Button(button_frame, text="Add Region", command=self.add_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_region).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear All", command=self.clear_regions).pack(side=tk.LEFT, padx=2)

    def init_rooms_screen(self):
        """Initialize the rooms screen"""
        frame = ttk.Frame(self.content_frame)
        self.screens["rooms"] = frame

        # Title
        ttk.Label(frame, text="Room Specifications",
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # Instructions
        instructions = ttk.Label(frame,
                                 text="Define rooms with their dimensions and maximum expansion limits.",
                                 wraplength=800)
        instructions.pack(pady=(0, 10))

        # Rooms list frame
        rooms_frame = ttk.LabelFrame(frame, text="Rooms", padding=10)
        rooms_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Rooms treeview
        columns = ("Width", "Height", "Max Expansion")
        self.rooms_tree = ttk.Treeview(rooms_frame, columns=columns, show="tree headings", height=8)

        # Configure columns
        self.rooms_tree.heading("#0", text="Room Name")
        self.rooms_tree.column("#0", width=120)
        for col in columns:
            self.rooms_tree.heading(col, text=col)
            self.rooms_tree.column(col, width=100)

        self.rooms_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for rooms
        rooms_scrollbar = ttk.Scrollbar(rooms_frame, orient=tk.VERTICAL, command=self.rooms_tree.yview)
        rooms_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rooms_tree.config(yscrollcommand=rooms_scrollbar.set)

        # Room input frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=10)

        # Input fields
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.room_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.room_name_var, width=15).grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Width:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.room_width_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.room_width_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Label(input_frame, text="Height:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.room_height_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.room_height_var, width=10).grid(row=0, column=5, padx=5)

        ttk.Label(input_frame, text="Max Expansion:").grid(row=0, column=6, padx=5, sticky=tk.W)
        self.room_max_exp_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.room_max_exp_var, width=10).grid(row=0, column=7, padx=5)

        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=8, padx=20)

        ttk.Button(button_frame, text="Add Room", command=self.add_room).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_room).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear All", command=self.clear_rooms).pack(side=tk.LEFT, padx=2)

    def init_adjacency_screen(self):
        """Initialize the adjacency screen"""
        frame = ttk.Frame(self.content_frame)
        self.screens["adjacency"] = frame

        # Title
        ttk.Label(frame, text="Room Adjacency Requirements",
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # Instructions
        instructions = ttk.Label(frame,
                                 text="Define which rooms should be adjacent to each other (share a wall).",
                                 wraplength=800)
        instructions.pack(pady=(0, 10))

        # Main container
        main_container = ttk.Frame(frame)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left side - Add adjacencies
        left_frame = ttk.LabelFrame(main_container, text="Add Adjacency", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Room selection
        ttk.Label(left_frame, text="Room 1:").pack(anchor=tk.W)
        self.room1_combo = ttk.Combobox(left_frame, state="readonly", width=20)
        self.room1_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(left_frame, text="Room 2:").pack(anchor=tk.W)
        self.room2_combo = ttk.Combobox(left_frame, state="readonly", width=20)
        self.room2_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(left_frame, text="Add Adjacency", command=self.add_adjacency).pack(pady=10)

        # Right side - Current adjacencies
        right_frame = ttk.LabelFrame(main_container, text="Current Adjacencies", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Adjacencies listbox
        self.adjacencies_listbox = tk.Listbox(right_frame, height=15)
        self.adjacencies_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for adjacencies
        adj_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.adjacencies_listbox.yview)
        adj_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.adjacencies_listbox.config(yscrollcommand=adj_scrollbar.set)

        # Buttons for adjacencies
        adj_button_frame = ttk.Frame(right_frame)
        adj_button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(adj_button_frame, text="Remove Selected",
                   command=self.remove_adjacency).pack(side=tk.LEFT, padx=2)
        ttk.Button(adj_button_frame, text="Clear All",
                   command=self.clear_adjacencies).pack(side=tk.LEFT, padx=2)

    def init_output_screen(self):
        """Initialize the output screen"""
        frame = ttk.Frame(self.content_frame)
        self.screens["output"] = frame

        # Title
        ttk.Label(frame, text="Floor Plan Output",
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))

        # Create paned window for split view
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left side - Statistics and controls
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        # Controls frame
        controls_frame = ttk.LabelFrame(left_panel, text="Generation Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # First row - generation controls
        gen_controls_row = ttk.Frame(controls_frame)
        gen_controls_row.pack(fill=tk.X, pady=(0, 10))

        # Max attempts
        ttk.Label(gen_controls_row, text="Max Attempts:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.max_attempts_var = tk.StringVar(value="1000")
        ttk.Entry(gen_controls_row, textvariable=self.max_attempts_var, width=10).grid(row=0, column=1, padx=5)

        # Enable expansion
        self.enable_expansion_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(gen_controls_row, text="Enable Room Expansion",
                        variable=self.enable_expansion_var).grid(row=0, column=2, padx=20)

        # Second row - save controls
        save_controls_row = ttk.Frame(controls_frame)
        save_controls_row.pack(fill=tk.X)

        ttk.Button(save_controls_row, text="Save as JSON",
                   command=self.save_floor_plan_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_controls_row, text="Load from JSON",
                   command=self.load_floor_plan_json).pack(side=tk.LEFT, padx=5)

        # Statistics frame
        stats_frame = ttk.LabelFrame(left_panel, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        # Statistics text
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, width=40)
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Right side - Visualization
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=2)

        # Visualization frame
        viz_frame = ttk.LabelFrame(right_panel, text="Floor Plan Visualization", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True)

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def save_floor_plan_json(self):
        """Save the current floor plan configuration and results to JSON"""
        try:
            # Get file path from user
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Floor Plan"
            )

            if not file_path:
                return  # User cancelled

            # Collect all data
            data = {
                "metadata": {
                    "version": "1.0",
                    "created_at": self.get_current_timestamp(),
                    "description": "Floor plan configuration and results"
                },
                "regions": self.get_regions_data(),
                "rooms": self.get_rooms_data(),
                "adjacencies": self.get_adjacencies_data(),
                "generation_settings": {
                    "max_attempts": int(self.max_attempts_var.get()),
                    "enable_expansion": self.enable_expansion_var.get()
                }
            }

            # Add floor plan results if generated
            if self.floor_plan:
                data["results"] = self.get_floor_plan_results()

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Success", f"Floor plan saved to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save floor plan:\n{str(e)}")

    def load_floor_plan_json(self):
        """Load floor plan configuration from JSON and automatically generate if results exist"""
        try:
            # Get file path from user
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Floor Plan"
            )

            if not file_path:
                return  # User cancelled

            # Load from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Clear existing data
            self.clear_all_data()

            # Load regions
            if "regions" in data:
                for i, region in enumerate(data["regions"]):
                    item = self.regions_tree.insert("", "end", text=f"Region {i + 1}")
                    self.regions_tree.set(item, "X", region['x'])
                    self.regions_tree.set(item, "Y", region['y'])
                    self.regions_tree.set(item, "Width", region['width'])
                    self.regions_tree.set(item, "Height", region['height'])

            # Load rooms
            if "rooms" in data:
                for room in data["rooms"]:
                    item = self.rooms_tree.insert("", "end", text=room['name'])
                    self.rooms_tree.set(item, "Width", room['width'])
                    self.rooms_tree.set(item, "Height", room['height'])
                    self.rooms_tree.set(item, "Max Expansion", room['max_expansion'])

            # Load adjacencies
            if "adjacencies" in data:
                for adj in data["adjacencies"]:
                    self.adjacencies_listbox.insert(tk.END, f"{adj['room1']} ↔ {adj['room2']}")

            # Load generation settings
            if "generation_settings" in data:
                settings = data["generation_settings"]
                self.max_attempts_var.set(str(settings.get("max_attempts", 1000)))
                self.enable_expansion_var.set(settings.get("enable_expansion", True))

            # Check if the loaded JSON has results and ask user if they want to restore them
            has_results = "results" in data and data["results"] is not None

            if has_results:
                response = messagebox.askyesno(
                    "Restore Results",
                    "This file contains previous floor plan results.\n\n"
                    "Do you want to:\n"
                    "• YES: Restore the exact previous layout\n"
                    "• NO: Generate a new layout with current settings"
                )

                if response:  # User chose YES - restore exact layout
                    self.restore_floor_plan_from_results(data["results"])
                    messagebox.showinfo("Success", f"Floor plan and results restored from:\n{file_path}")
                else:  # User chose NO - generate new layout
                    self.generate_floor_plan()
                    messagebox.showinfo("Success",
                                        f"Floor plan configuration loaded from:\n{file_path}\nNew layout generated.")
            else:
                # No results in file, ask if user wants to generate now
                response = messagebox.askyesno(
                    "Generate Floor Plan",
                    "Floor plan configuration loaded successfully.\n\n"
                    "Do you want to generate the floor plan now?"
                )

                if response:
                    self.generate_floor_plan()
                    messagebox.showinfo("Success", f"Floor plan loaded and generated from:\n{file_path}")
                else:
                    messagebox.showinfo("Success", f"Floor plan configuration loaded from:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load floor plan:\n{str(e)}")

    def restore_floor_plan_from_results(self, results_data):
        """Restore floor plan from saved results data"""
        try:
            # Create floor plan with current regions
            regions = self.get_regions_data()
            if not regions:
                raise ValueError("No regions defined")

            self.floor_plan = FloorPlan(regions)

            # Add rooms with original specifications
            room_names = []
            for item in self.rooms_tree.get_children():
                name = self.rooms_tree.item(item)['text']
                width = int(self.rooms_tree.set(item, "Width"))
                height = int(self.rooms_tree.set(item, "Height"))
                max_exp = int(self.rooms_tree.set(item, "Max Expansion"))

                self.floor_plan.add_room(name, width, height, max_exp)
                room_names.append(name)

            # Add adjacencies
            for i in range(self.adjacencies_listbox.size()):
                adjacency = self.adjacencies_listbox.get(i)
                room1, room2 = adjacency.split(" ↔ ")
                self.floor_plan.add_adjacency(room1, room2)

            # Restore room placements from saved results
            if "room_placements" in results_data:
                for placement in results_data["room_placements"]:
                    # Find the room object
                    room = next((r for r in self.floor_plan.rooms if r.name == placement["name"]), None)
                    if room:
                        # Restore the placement
                        room.x = placement["x"]
                        room.y = placement["y"]
                        room.width = placement["width"]
                        room.height = placement["height"]
                        room.rotated = placement.get("rotated", False)

                        # Ensure original dimensions are preserved
                        if not hasattr(room, 'original_width'):
                            room.original_width = placement.get("original_width", placement["width"])
                            room.original_height = placement.get("original_height", placement["height"])

            # Update the display
            self.update_output_display()

        except Exception as e:
            # If restoration fails, fall back to generating new layout
            messagebox.showwarning("Restoration Failed",
                                   f"Could not restore exact layout: {str(e)}\n"
                                   "Generating new layout instead...")
            self.generate_floor_plan()

    def get_regions_data(self):
        """Get regions data as list of dictionaries"""
        regions = []
        for item in self.regions_tree.get_children():
            region = {
                "x": int(self.regions_tree.set(item, "X")),
                "y": int(self.regions_tree.set(item, "Y")),
                "width": int(self.regions_tree.set(item, "Width")),
                "height": int(self.regions_tree.set(item, "Height"))
            }
            regions.append(region)
        return regions

    def get_rooms_data(self):
        """Get rooms data as list of dictionaries"""
        rooms = []
        for item in self.rooms_tree.get_children():
            room = {
                "name": self.rooms_tree.item(item)['text'],
                "width": int(self.rooms_tree.set(item, "Width")),
                "height": int(self.rooms_tree.set(item, "Height")),
                "max_expansion": int(self.rooms_tree.set(item, "Max Expansion"))
            }
            rooms.append(room)
        return rooms

    def get_adjacencies_data(self):
        """Get adjacencies data as list of dictionaries"""
        adjacencies = []
        for i in range(self.adjacencies_listbox.size()):
            adjacency_text = self.adjacencies_listbox.get(i)
            room1, room2 = adjacency_text.split(" ↔ ")
            adjacencies.append({"room1": room1, "room2": room2})
        return adjacencies

    def get_floor_plan_results(self):
        """Get floor plan generation results"""
        if not self.floor_plan:
            return None

        # Calculate statistics
        total_area = sum(region['width'] * region['height'] for region in self.floor_plan.floor_regions)
        used_area = sum(room.width * room.height for room in self.floor_plan.rooms if room.x is not None)
        score, adjacent_pairs = self.floor_plan.evaluate_adjacency_score()

        # Get room placements
        room_placements = []
        for room in self.floor_plan.rooms:
            if room.x is not None:
                placement = {
                    "name": room.name,
                    "x": room.x,
                    "y": room.y,
                    "width": room.width,
                    "height": room.height,
                    "original_width": room.original_width,
                    "original_height": room.original_height,
                    "rotated": room.rotated,
                    "max_expansion": room.max_expansion
                }
                room_placements.append(placement)

        return {
            "statistics": {
                "total_floor_area": total_area,
                "used_area": used_area,
                "space_utilization": used_area / total_area if total_area > 0 else 0,
                "adjacency_score": score,
                "total_adjacency_requirements": len(self.floor_plan.adjacency_graph.edges),
                "satisfied_adjacencies": len(adjacent_pairs)
            },
            "room_placements": room_placements,
            "satisfied_adjacencies": [{"room1": pair[0], "room2": pair[1]} for pair in adjacent_pairs]
        }

    def get_current_timestamp(self):
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def show_screen(self, screen_name):
        """Show the specified screen and hide others"""
        # Hide all screens
        for screen in self.screens.values():
            screen.pack_forget()

        # Show selected screen
        if screen_name in self.screens:
            self.screens[screen_name].pack(fill=tk.BOTH, expand=True)
            self.current_screen = screen_name

            # Update button states (optional visual feedback)
            for name, btn in self.nav_buttons.items():
                if name == screen_name:
                    btn.state(['pressed'])
                else:
                    btn.state(['!pressed'])

            # Refresh data if switching to certain screens
            if screen_name == "adjacency":
                self.refresh_room_combos()

    def load_example_data(self):
        """Load the example data from the original code"""
        # Clear existing data
        self.clear_all_data()

        # Load example regions
        example_regions = [
            {'x': 0, 'y': 0, 'width': 10, 'height': 10},
            {'x': 10, 'y': 0, 'width': 8, 'height': 5},
            {'x': 0, 'y': 10, 'width': 5, 'height': 8},
            {'x': 10, 'y': 5, 'width': 6, 'height': 6}
        ]

        for i, region in enumerate(example_regions):
            item = self.regions_tree.insert("", "end", text=f"Region {i + 1}")
            self.regions_tree.set(item, "X", region['x'])
            self.regions_tree.set(item, "Y", region['y'])
            self.regions_tree.set(item, "Width", region['width'])
            self.regions_tree.set(item, "Height", region['height'])

        # Load example rooms
        example_rooms = [
            ("Living Room", 8, 4, 15),
            ("Kitchen", 6, 4, 8),
            ("Bedroom 1", 5, 4, 10),
            ("Bedroom 2", 5, 4, 6),
            ("Bathroom", 3, 4, 2),
            ("Hallway", 2, 4, 5),
            ("Office", 3, 3, 0),
            ("secretRoom", 3, 3, 3)
        ]

        for room_data in example_rooms:
            name, width, height, max_exp = room_data
            item = self.rooms_tree.insert("", "end", text=name)
            self.rooms_tree.set(item, "Width", width)
            self.rooms_tree.set(item, "Height", height)
            self.rooms_tree.set(item, "Max Expansion", max_exp)

        # Load example adjacencies
        example_adjacencies = [
            ("Living Room", "Kitchen"),
            ("Living Room", "Bathroom"),
            ("Kitchen", "Bedroom 1"),
            ("Bedroom 2", "Hallway"),
            ("Hallway", "Bathroom"),
            ("Office", "Bedroom 2"),
            ("secretRoom", "Kitchen")
        ]

        for room1, room2 in example_adjacencies:
            self.adjacencies_listbox.insert(tk.END, f"{room1} ↔ {room2}")

    def clear_all_data(self):
        """Clear all data from the GUI"""
        # Clear regions
        for item in self.regions_tree.get_children():
            self.regions_tree.delete(item)

        # Clear rooms
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)

        # Clear adjacencies
        self.adjacencies_listbox.delete(0, tk.END)

    def add_region(self):
        """Add a new region"""
        try:
            x = int(self.region_x_var.get())
            y = int(self.region_y_var.get())
            width = int(self.region_width_var.get())
            height = int(self.region_height_var.get())

            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Width and height must be positive")
                return

            # Add to tree
            region_count = len(self.regions_tree.get_children()) + 1
            item = self.regions_tree.insert("", "end", text=f"Region {region_count}")
            self.regions_tree.set(item, "X", x)
            self.regions_tree.set(item, "Y", y)
            self.regions_tree.set(item, "Width", width)
            self.regions_tree.set(item, "Height", height)

            # Clear input fields
            self.region_x_var.set("")
            self.region_y_var.set("")
            self.region_width_var.set("")
            self.region_height_var.set("")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def remove_region(self):
        """Remove selected region"""
        selected = self.regions_tree.selection()
        if selected:
            self.regions_tree.delete(selected[0])

    def edit_region(self):
        """Edit the selected region"""
        selected = self.regions_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a region to edit")
            return

        # Get current values from the selected region
        item = selected[0]
        current_x = self.regions_tree.set(item, "X")
        current_y = self.regions_tree.set(item, "Y")
        current_width = self.regions_tree.set(item, "Width")
        current_height = self.regions_tree.set(item, "Height")

        # Populate input fields with current values
        self.region_x_var.set(current_x)
        self.region_y_var.set(current_y)
        self.region_width_var.set(current_width)
        self.region_height_var.set(current_height)

        # Remove the selected region (it will be re-added with new values when user clicks Add)
        region_name = self.regions_tree.item(item)['text']
        self.regions_tree.delete(item)

        # Show message to user
        messagebox.showinfo("Edit Mode",
                            f"Region values loaded into input fields.\nModify the values and click 'Add Region' to save changes.\n\nNote: {region_name} has been temporarily removed.")

    def clear_regions(self):
        """Clear all regions"""
        for item in self.regions_tree.get_children():
            self.regions_tree.delete(item)

    def add_room(self):
        """Add a new room"""
        try:
            name = self.room_name_var.get().strip()
            width = int(self.room_width_var.get())
            height = int(self.room_height_var.get())
            max_exp = int(self.room_max_exp_var.get())

            if not name:
                messagebox.showerror("Error", "Please enter a room name")
                return

            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Width and height must be positive")
                return

            if max_exp < 0:
                messagebox.showerror("Error", "Max expansion cannot be negative")
                return

            # Check if room name already exists
            for item in self.rooms_tree.get_children():
                if self.rooms_tree.item(item)['text'] == name:
                    messagebox.showerror("Error", "Room name already exists")
                    return

            # Add to tree
            item = self.rooms_tree.insert("", "end", text=name)
            self.rooms_tree.set(item, "Width", width)
            self.rooms_tree.set(item, "Height", height)
            self.rooms_tree.set(item, "Max Expansion", max_exp)

            # Clear input fields
            self.room_name_var.set("")
            self.room_width_var.set("")
            self.room_height_var.set("")
            self.room_max_exp_var.set("")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def remove_room(self):
        """Remove selected room"""
        selected = self.rooms_tree.selection()
        if selected:
            room_name = self.rooms_tree.item(selected[0])['text']
            self.rooms_tree.delete(selected[0])

            # Remove any adjacencies involving this room
            items_to_remove = []
            for i in range(self.adjacencies_listbox.size()):
                adjacency = self.adjacencies_listbox.get(i)
                if room_name in adjacency:
                    items_to_remove.append(i)

            # Remove from bottom to top to maintain indices
            for i in reversed(items_to_remove):
                self.adjacencies_listbox.delete(i)

    def clear_rooms(self):
        """Clear all rooms"""
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
        self.adjacencies_listbox.delete(0, tk.END)  # Clear adjacencies too

    def refresh_room_combos(self):
        """Refresh the room combo boxes with current room names"""
        room_names = [self.rooms_tree.item(item)['text'] for item in self.rooms_tree.get_children()]
        self.room1_combo['values'] = room_names
        self.room2_combo['values'] = room_names

    def add_adjacency(self):
        """Add a new adjacency"""
        room1 = self.room1_combo.get()
        room2 = self.room2_combo.get()

        if not room1 or not room2:
            messagebox.showerror("Error", "Please select both rooms")
            return

        if room1 == room2:
            messagebox.showerror("Error", "A room cannot be adjacent to itself")
            return

        # Check if adjacency already exists (in either direction)
        adjacency1 = f"{room1} ↔ {room2}"
        adjacency2 = f"{room2} ↔ {room1}"

        for i in range(self.adjacencies_listbox.size()):
            existing = self.adjacencies_listbox.get(i)
            if existing == adjacency1 or existing == adjacency2:
                messagebox.showerror("Error", "This adjacency already exists")
                return

        # Add adjacency
        self.adjacencies_listbox.insert(tk.END, adjacency1)

        # Clear selections
        self.room1_combo.set("")
        self.room2_combo.set("")

    def remove_adjacency(self):
        """Remove selected adjacency"""
        selection = self.adjacencies_listbox.curselection()
        if selection:
            self.adjacencies_listbox.delete(selection[0])

    def clear_adjacencies(self):
        """Clear all adjacencies"""
        self.adjacencies_listbox.delete(0, tk.END)

    def generate_floor_plan(self):
        """Generate the floor plan based on current data"""
        try:
            # Collect regions
            regions = []
            for item in self.regions_tree.get_children():
                x = int(self.regions_tree.set(item, "X"))
                y = int(self.regions_tree.set(item, "Y"))
                width = int(self.regions_tree.set(item, "Width"))
                height = int(self.regions_tree.set(item, "Height"))
                regions.append({'x': x, 'y': y, 'width': width, 'height': height})

            if not regions:
                messagebox.showerror("Error", "Please define at least one region")
                return

            # Create floor plan
            self.floor_plan = FloorPlan(regions)

            # Add rooms
            room_names = []
            for item in self.rooms_tree.get_children():
                name = self.rooms_tree.item(item)['text']
                width = int(self.rooms_tree.set(item, "Width"))
                height = int(self.rooms_tree.set(item, "Height"))
                max_exp = int(self.rooms_tree.set(item, "Max Expansion"))

                self.floor_plan.add_room(name, width, height, max_exp)
                room_names.append(name)

            if not room_names:
                messagebox.showerror("Error", "Please define at least one room")
                return

            # Add adjacencies
            for i in range(self.adjacencies_listbox.size()):
                adjacency = self.adjacencies_listbox.get(i)
                room1, room2 = adjacency.split(" ↔ ")
                self.floor_plan.add_adjacency(room1, room2)

            # Generate floor plan
            max_attempts = int(self.max_attempts_var.get())
            enable_expansion = self.enable_expansion_var.get()

            success = self.floor_plan.place_rooms_with_constraints_optimized(
                max_attempts=max_attempts,
                enable_expansion=enable_expansion
            )

            if success:
                messagebox.showinfo("Success", "Floor plan generated successfully!")
                self.update_output_display()
            else:
                messagebox.showwarning("Warning",
                                       "Failed to place all rooms optimally. You may need to adjust room sizes or floor dimensions.")
                self.update_output_display()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def update_output_display(self):
        """Update the output display with statistics and visualization"""
        if not self.floor_plan:
            return

        # Update statistics
        self.stats_text.delete('1.0', tk.END)

        # Calculate and display statistics
        total_area = sum(region['width'] * region['height'] for region in self.floor_plan.floor_regions)
        used_area = sum(room.width * room.height for room in self.floor_plan.rooms if room.x is not None)

        stats = f"FLOOR PLAN STATISTICS\n{'=' * 30}\n\n"
        stats += f"Floor area: {total_area} square units\n"
        stats += f"Room area: {used_area} square units\n"
        stats += f"Space utilization: {used_area / total_area:.2%}\n\n"

        score, adjacent_pairs = self.floor_plan.evaluate_adjacency_score()
        stats += f"Adjacency score: {score}/{len(self.floor_plan.adjacency_graph.edges)}\n"
        stats += f"Adjacent pairs: {adjacent_pairs}\n\n"

        stats += "ROOM EXPANSION STATISTICS:\n" + "-" * 30 + "\n"
        for room in self.floor_plan.rooms:
            if room.x is not None:
                original_area = room.original_width * room.original_height
                current_area = room.width * room.height
                expansion_pct = (current_area - original_area) / original_area * 100 if original_area > 0 else 0

                if not room.rotated:
                    total_expansion = (room.width - room.original_width) + (room.height - room.original_height)
                else:
                    total_expansion = (room.width - room.original_height) + (room.height - room.original_width)

                expansion_usage = f"{total_expansion}/{room.max_expansion}"

                stats += f"{room.name}: {room.original_width}x{room.original_height} → {room.width}x{room.height} "
                stats += f"({expansion_pct:.1f}% increase, expansion used: {expansion_usage})\n"

        stats += "\nROOM PLACEMENTS:\n" + "-" * 20 + "\n"
        for room in self.floor_plan.rooms:
            stats += f"{room}\n"

        self.stats_text.insert('1.0', stats)

        # Update visualization
        self.ax.clear()
        self.visualize_floor_plan()
        self.canvas.draw()

        # Switch to output screen
        self.show_screen("output")

    def visualize_floor_plan(self):
        """Create matplotlib visualization of the floor plan"""
        if not self.floor_plan:
            return

        # Draw floor shape
        for region in self.floor_plan.floor_regions:
            rect = plt.Rectangle(
                (region['x'], region['y']),
                region['width'],
                region['height'],
                linewidth=2,
                edgecolor='black',
                facecolor='none',
                linestyle='--'
            )
            self.ax.add_patch(rect)

        # Draw rooms
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.floor_plan.rooms)))
        for i, room in enumerate(self.floor_plan.rooms):
            if room.x is not None and room.y is not None:
                rect = plt.Rectangle(
                    (room.x, room.y),
                    room.width,
                    room.height,
                    linewidth=1,
                    edgecolor='black',
                    facecolor=colors[i],
                    alpha=0.7
                )
                self.ax.add_patch(rect)

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

                self.ax.text(
                    room.x + room.width / 2,
                    room.y + room.height / 2,
                    display_text,
                    ha='center',
                    va='center',
                    fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8)
                )

        # Add adjacency relationships as lines between room centers
        for room1_name, room2_name in self.floor_plan.adjacency_graph.edges:
            room1 = next(r for r in self.floor_plan.rooms if r.name == room1_name)
            room2 = next(r for r in self.floor_plan.rooms if r.name == room2_name)

            if room1.x is not None and room2.x is not None:
                center1 = (room1.x + room1.width / 2, room1.y + room1.height / 2)
                center2 = (room2.x + room2.width / 2, room2.y + room2.height / 2)

                # Check if rooms share a wall
                if room1.has_shared_wall_with(room2):
                    self.ax.plot([center1[0], center2[0]], [center1[1], center2[1]],
                                 'g-', linewidth=2, alpha=0.8, label='Adjacent (satisfied)')
                else:
                    self.ax.plot([center1[0], center2[0]], [center1[1], center2[1]],
                                 'r:', linewidth=1.5, alpha=0.8, label='Adjacent (unsatisfied)')

        # Set limits and labels
        max_width = self.floor_plan.floor_width
        max_height = self.floor_plan.floor_height
        self.ax.set_xlim(-1, max_width + 1)
        self.ax.set_ylim(-1, max_height + 1)
        self.ax.set_aspect('equal')
        self.ax.set_title('Floor Plan Layout')
        self.ax.set_xlabel('Width')
        self.ax.set_ylabel('Height')
        self.ax.grid(True, alpha=0.3)

        # Add legend for adjacency lines (avoid duplicates)
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if by_label:
            self.ax.legend(by_label.values(), by_label.keys(), loc='upper left',
                           bbox_to_anchor=(1.02, 1), borderaxespad=0)

        plt.tight_layout()


def main():
    """Main function to run the GUI"""
    root = tk.Tk()

    # Configure style
    style = ttk.Style()

    # Try to use a modern theme
    try:
        style.theme_use('clam')  # More modern than default
    except:
        pass  # Fall back to default theme

    # Configure some custom styles
    style.configure('Accent.TButton', foreground='white')

    # Create and run the application
    app = FloorPlanGUI(root)

    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()