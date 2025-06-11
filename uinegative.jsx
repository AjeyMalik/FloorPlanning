import React, { useState, useEffect, useRef } from 'react';
import { Trash2, Plus, Download, Eye, ChevronUp, ChevronDown, Maximize2, Save, Play, Home, ArrowRightCircle } from 'lucide-react';

// Mock Python functions for demo purposes
const mockPythonFunctions = {
  createFloorPlan: (regions) => {
    // In a real implementation, this would call the Python code
    console.log("Creating floor plan with regions:", regions);
    return { success: true };
  },
  addRoom: (name, width, height, maxExpansion) => {
    console.log(`Adding room: ${name} (${width}x${height}), max expansion: ${maxExpansion}`);
    return { success: true };
  },
  addAdjacency: (room1, room2) => {
    console.log(`Adding adjacency between ${room1} and ${room2}`);
    return { success: true };
  },
  placeRooms: (maxAttempts, enableExpansion) => {
    console.log(`Placing rooms with ${maxAttempts} attempts, expansion: ${enableExpansion}`);
    return {
      success: true,
      statistics: {
        floorArea: 300,
        roomArea: 240,
        spaceUtilization: 0.8,
        adjacencyScore: 5,
        totalAdjacencies: 7,
        adjacentPairs: [["Living Room", "Kitchen"], ["Kitchen", "Dining"], ["Bedroom", "Bathroom"], ["Living Room", "Bedroom"], ["Bathroom", "Kitchen"]]
      }
    };
  }
};

// Mock image for visualization
const mockFloorPlanImage = "/api/placeholder/600/450";

function FloorPlanGenerator() {
  // State for regions (floor shape)
  const [regions, setRegions] = useState([
    { x: 0, y: 0, width: 5, height: 15 },
    { x: 5, y: 0, width: 10, height: 5 },
    { x: 15, y: 0, width: 5, height: 15 }
  ]);

  // State for rooms
  const [rooms, setRooms] = useState([
    { name: "Living Room", width: 6, height: 4, maxExpansion: 10 },
    { name: "Kitchen", width: 5, height: 4, maxExpansion: 8 },
    { name: "Dining", width: 4, height: 4, maxExpansion: 6 },
    { name: "Bedroom", width: 5, height: 5, maxExpansion: 5 },
    { name: "Bathroom", width: 3, height: 3, maxExpansion: 2 }
  ]);

  // State for adjacencies
  const [adjacencies, setAdjacencies] = useState([
    { room1: "Living Room", room2: "Kitchen" },
    { room1: "Kitchen", room2: "Dining" },
    { room1: "Living Room", room2: "Bedroom" },
    { room1: "Bedroom", room2: "Bathroom" },
    { room1: "Bathroom", room2: "Kitchen" }
  ]);

  // State for algorithm settings
  const [settings, setSettings] = useState({
    maxAttempts: 5000,
    enableExpansion: true
  });

  // State for results
  const [results, setResults] = useState(null);

  // State for active tab
  const [activeTab, setActiveTab] = useState("floorPlan");

  // State for new region/room/adjacency
  const [newRegion, setNewRegion] = useState({ x: 0, y: 0, width: 5, height: 5 });
  const [newRoom, setNewRoom] = useState({ name: "", width: 4, height: 4, maxExpansion: 5 });
  const [newAdjacency, setNewAdjacency] = useState({ room1: "", room2: "" });

  // Reference for the visualization container
  const visualizationRef = useRef(null);

  // Function to add a new region
  const addRegion = () => {
    if (newRegion.width > 0 && newRegion.height > 0) {
      setRegions([...regions, { ...newRegion }]);
      setNewRegion({ x: 0, y: 0, width: 5, height: 5 });
    }
  };

  // Function to remove a region
  const removeRegion = (index) => {
    const updatedRegions = [...regions];
    updatedRegions.splice(index, 1);
    setRegions(updatedRegions);
  };

  // Function to add a new room
  const addRoom = () => {
    if (newRoom.name && newRoom.width > 0 && newRoom.height > 0) {
      setRooms([...rooms, { ...newRoom }]);
      setNewRoom({ name: "", width: 4, height: 4, maxExpansion: 5 });
    }
  };

  // Function to remove a room
  const removeRoom = (index) => {
    const roomName = rooms[index].name;

    // Remove adjacencies that include this room
    const updatedAdjacencies = adjacencies.filter(
      adj => adj.room1 !== roomName && adj.room2 !== roomName
    );

    // Remove the room
    const updatedRooms = [...rooms];
    updatedRooms.splice(index, 1);

    setRooms(updatedRooms);
    setAdjacencies(updatedAdjacencies);
  };

  // Function to add a new adjacency
  const addAdjacency = () => {
    if (newAdjacency.room1 && newAdjacency.room2 && newAdjacency.room1 !== newAdjacency.room2) {
      // Check if this adjacency already exists
      const exists = adjacencies.some(
        adj => (adj.room1 === newAdjacency.room1 && adj.room2 === newAdjacency.room2) ||
              (adj.room1 === newAdjacency.room2 && adj.room2 === newAdjacency.room1)
      );

      if (!exists) {
        setAdjacencies([...adjacencies, { ...newAdjacency }]);
        setNewAdjacency({ room1: "", room2: "" });
      }
    }
  };

  // Function to remove an adjacency
  const removeAdjacency = (index) => {
    const updatedAdjacencies = [...adjacencies];
    updatedAdjacencies.splice(index, 1);
    setAdjacencies(updatedAdjacencies);
  };

  // Function to generate the floor plan
  const generateFloorPlan = () => {
    // In a real application, this would call the Python code through a backend API
    mockPythonFunctions.createFloorPlan(regions);

    // Add rooms
    rooms.forEach(room => {
      mockPythonFunctions.addRoom(room.name, room.width, room.height, room.maxExpansion);
    });

    // Add adjacencies
    adjacencies.forEach(adj => {
      mockPythonFunctions.addAdjacency(adj.room1, adj.room2);
    });

    // Place rooms
    const result = mockPythonFunctions.placeRooms(settings.maxAttempts, settings.enableExpansion);

    if (result.success) {
      setResults(result.statistics);
    }
  };

  // Section components for organization
  const FloorPlanSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Floor Regions</h3>
      <p className="text-sm text-gray-600">Define the shape of your floor by adding rectangular regions</p>

      <div className="grid grid-cols-5 gap-2 items-center bg-gray-100 p-2 rounded">
        <div>X</div>
        <div>Y</div>
        <div>Width</div>
        <div>Height</div>
        <div></div>
      </div>

      {regions.map((region, index) => (
        <div key={index} className="grid grid-cols-5 gap-2 items-center">
          <input
            type="number"
            value={region.x}
            onChange={(e) => {
              const updated = [...regions];
              updated[index].x = parseInt(e.target.value) || 0;
              setRegions(updated);
            }}
            className="border rounded p-2"
          />
          <input
            type="number"
            value={region.y}
            onChange={(e) => {
              const updated = [...regions];
              updated[index].y = parseInt(e.target.value) || 0;
              setRegions(updated);
            }}
            className="border rounded p-2"
          />
          <input
            type="number"
            value={region.width}
            onChange={(e) => {
              const updated = [...regions];
              updated[index].width = parseInt(e.target.value) || 1;
              setRegions(updated);
            }}
            className="border rounded p-2"
          />
          <input
            type="number"
            value={region.height}
            onChange={(e) => {
              const updated = [...regions];
              updated[index].height = parseInt(e.target.value) || 1;
              setRegions(updated);
            }}
            className="border rounded p-2"
          />
          <button
            onClick={() => removeRegion(index)}
            className="p-2 text-red-600 hover:bg-red-100 rounded"
          >
            <Trash2 size={18} />
          </button>
        </div>
      ))}

      <div className="grid grid-cols-5 gap-2 items-center mt-4">
        <input
          type="number"
          value={newRegion.x}
          onChange={(e) => setNewRegion({ ...newRegion, x: parseInt(e.target.value) || 0 })}
          className="border rounded p-2"
          placeholder="X"
        />
        <input
          type="number"
          value={newRegion.y}
          onChange={(e) => setNewRegion({ ...newRegion, y: parseInt(e.target.value) || 0 })}
          className="border rounded p-2"
          placeholder="Y"
        />
        <input
          type="number"
          value={newRegion.width}
          onChange={(e) => setNewRegion({ ...newRegion, width: parseInt(e.target.value) || 1 })}
          className="border rounded p-2"
          placeholder="Width"
        />
        <input
          type="number"
          value={newRegion.height}
          onChange={(e) => setNewRegion({ ...newRegion, height: parseInt(e.target.value) || 1 })}
          className="border rounded p-2"
          placeholder="Height"
        />
        <button
          onClick={addRegion}
          className="flex items-center justify-center p-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );

  const RoomsSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Rooms</h3>
      <p className="text-sm text-gray-600">Add rooms with dimensions and expansion limits</p>

      <div className="grid grid-cols-5 gap-2 items-center bg-gray-100 p-2 rounded">
        <div>Name</div>
        <div>Width</div>
        <div>Height</div>
        <div>Max Expansion</div>
        <div></div>
      </div>

      {rooms.map((room, index) => (
        <div key={index} className="grid grid-cols-5 gap-2 items-center">
          <input
            type="text"
            value={room.name}
            onChange={(e) => {
              const oldName = room.name;
              const newName = e.target.value;

              // Update room name
              const updatedRooms = [...rooms];
              updatedRooms[index].name = newName;
              setRooms(updatedRooms);

              // Update adjacencies that reference this room
              if (oldName) {
                const updatedAdjacencies = adjacencies.map(adj => {
                  if (adj.room1 === oldName) return { ...adj, room1: newName };
                  if (adj.room2 === oldName) return { ...adj, room2: newName };
                  return adj;
                });
                setAdjacencies(updatedAdjacencies);
              }
            }}
            className="border rounded p-2"
          />
          <input
            type="number"
            value={room.width}
            onChange={(e) => {
              const updated = [...rooms];
              updated[index].width = parseInt(e.target.value) || 1;
              setRooms(updated);
            }}
            className="border rounded p-2"
          />
          <input
            type="number"
            value={room.height}
            onChange={(e) => {
              const updated = [...rooms];
              updated[index].height = parseInt(e.target.value) || 1;
              setRooms(updated);
            }}
            className="border rounded p-2"
          />
          <input
            type="number"
            value={room.maxExpansion}
            onChange={(e) => {
              const updated = [...rooms];
              updated[index].maxExpansion = parseInt(e.target.value) || 0;
              setRooms(updated);
            }}
            className="border rounded p-2"
          />
          <button
            onClick={() => removeRoom(index)}
            className="p-2 text-red-600 hover:bg-red-100 rounded"
          >
            <Trash2 size={18} />
          </button>
        </div>
      ))}

      <div className="grid grid-cols-5 gap-2 items-center mt-4">
        <input
          type="text"
          value={newRoom.name}
          onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
          className="border rounded p-2"
          placeholder="Room name"
        />
        <input
          type="number"
          value={newRoom.width}
          onChange={(e) => setNewRoom({ ...newRoom, width: parseInt(e.target.value) || 1 })}
          className="border rounded p-2"
          placeholder="Width"
        />
        <input
          type="number"
          value={newRoom.height}
          onChange={(e) => setNewRoom({ ...newRoom, height: parseInt(e.target.value) || 1 })}
          className="border rounded p-2"
          placeholder="Height"
        />
        <input
          type="number"
          value={newRoom.maxExpansion}
          onChange={(e) => setNewRoom({ ...newRoom, maxExpansion: parseInt(e.target.value) || 0 })}
          className="border rounded p-2"
          placeholder="Max Expansion"
        />
        <button
          onClick={addRoom}
          className="flex items-center justify-center p-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );

  const AdjacencySection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Adjacency Requirements</h3>
      <p className="text-sm text-gray-600">Define which rooms should share walls</p>

      <div className="grid grid-cols-3 gap-2 items-center bg-gray-100 p-2 rounded">
        <div>Room 1</div>
        <div>Room 2</div>
        <div></div>
      </div>

      {adjacencies.map((adj, index) => (
        <div key={index} className="grid grid-cols-3 gap-2 items-center">
          <select
            value={adj.room1}
            onChange={(e) => {
              const updated = [...adjacencies];
              updated[index].room1 = e.target.value;
              setAdjacencies(updated);
            }}
            className="border rounded p-2"
          >
            {rooms.map(room => (
              <option key={room.name} value={room.name}>{room.name}</option>
            ))}
          </select>
          <select
            value={adj.room2}
            onChange={(e) => {
              const updated = [...adjacencies];
              updated[index].room2 = e.target.value;
              setAdjacencies(updated);
            }}
            className="border rounded p-2"
          >
            {rooms.map(room => (
              <option key={room.name} value={room.name}>{room.name}</option>
            ))}
          </select>
          <button
            onClick={() => removeAdjacency(index)}
            className="p-2 text-red-600 hover:bg-red-100 rounded"
          >
            <Trash2 size={18} />
          </button>
        </div>
      ))}

      <div className="grid grid-cols-3 gap-2 items-center mt-4">
        <select
          value={newAdjacency.room1}
          onChange={(e) => setNewAdjacency({ ...newAdjacency, room1: e.target.value })}
          className="border rounded p-2"
        >
          <option value="">Select Room 1</option>
          {rooms.map(room => (
            <option key={room.name} value={room.name}>{room.name}</option>
          ))}
        </select>
        <select
          value={newAdjacency.room2}
          onChange={(e) => setNewAdjacency({ ...newAdjacency, room2: e.target.value })}
          className="border rounded p-2"
        >
          <option value="">Select Room 2</option>
          {rooms.map(room => (
            <option key={room.name} value={room.name}>{room.name}</option>
          ))}
        </select>
        <button
          onClick={addAdjacency}
          className="flex items-center justify-center p-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );

  const SettingsSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Algorithm Settings</h3>
      <p className="text-sm text-gray-600">Configure the floor plan generation algorithm</p>

      <div className="flex items-center space-x-2">
        <label className="min-w-40">Maximum Attempts:</label>
        <input
          type="number"
          value={settings.maxAttempts}
          onChange={(e) => setSettings({ ...settings, maxAttempts: parseInt(e.target.value) || 1000 })}
          className="border rounded p-2 flex-grow"
        />
      </div>

      <div className="flex items-center space-x-2">
        <label className="min-w-40">Enable Room Expansion:</label>
        <input
          type="checkbox"
          checked={settings.enableExpansion}
          onChange={(e) => setSettings({ ...settings, enableExpansion: e.target.checked })}
          className="h-5 w-5"
        />
      </div>
    </div>
  );

  const ResultsSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Results</h3>

      {results ? (
        <div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <h4 className="font-medium">Space Utilization</h4>
              <div className="text-2xl font-bold">{(results.spaceUtilization * 100).toFixed(1)}%</div>
              <div className="text-sm text-gray-600">
                Floor Area: {results.floorArea} square units<br />
                Room Area: {results.roomArea} square units
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded">
              <h4 className="font-medium">Adjacency Score</h4>
              <div className="text-2xl font-bold">{results.adjacencyScore}/{results.totalAdjacencies}</div>
              <div className="text-sm text-gray-600">
                {((results.adjacencyScore / results.totalAdjacencies) * 100).toFixed(1)}% of requirements met
              </div>
            </div>
          </div>

          <div className="mt-4">
            <h4 className="font-medium">Adjacent Pairs</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {results.adjacentPairs.map((pair, index) => (
                <div key={index} className="bg-blue-100 px-3 py-1 rounded-full text-sm">
                  {pair[0]} ⟷ {pair[1]}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6" ref={visualizationRef}>
            <h4 className="font-medium">Visualization</h4>
            <div className="mt-2 border rounded bg-white flex justify-center">
              <img src={mockFloorPlanImage} alt="Floor Plan Visualization" className="max-w-full" />
            </div>
            <div className="flex justify-end mt-2">
              <button className="flex items-center bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded">
                <Download size={16} className="mr-1" /> Save Image
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 bg-gray-50 rounded">
          <Eye size={48} className="text-gray-400 mb-4" />
          <p className="text-gray-500">Generate a floor plan to see results</p>
          <button
            onClick={generateFloorPlan}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded flex items-center"
          >
            <Play size={16} className="mr-2" /> Generate Floor Plan
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-4">
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Home size={24} className="text-blue-600 mr-2" />
          <h1 className="text-2xl font-bold">Floor Plan Generator</h1>
        </div>
        <div>
          <button
            onClick={generateFloorPlan}
            className="bg-blue-600 text-white px-4 py-2 rounded flex items-center"
          >
            <Play size={16} className="mr-2" /> Generate Floor Plan
          </button>
        </div>
      </header>

      <div className="flex gap-6">
        <div className="w-64 bg-gray-50 p-4 rounded-lg h-fit">
          <nav>
            <ul className="space-y-2">
              <li>
                <button
                  onClick={() => setActiveTab("floorPlan")}
                  className={`w-full text-left px-4 py-2 rounded flex items-center ${activeTab === "floorPlan" ? "bg-blue-600 text-white" : "hover:bg-gray-200"}`}
                >
                  <Maximize2 size={16} className="mr-2" /> Floor Regions
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab("rooms")}
                  className={`w-full text-left px-4 py-2 rounded flex items-center ${activeTab === "rooms" ? "bg-blue-600 text-white" : "hover:bg-gray-200"}`}
                >
                  <Home size={16} className="mr-2" /> Rooms
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab("adjacency")}
                  className={`w-full text-left px-4 py-2 rounded flex items-center ${activeTab === "adjacency" ? "bg-blue-600 text-white" : "hover:bg-gray-200"}`}
                >
                  <ArrowRightCircle size={16} className="mr-2" /> Adjacency
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab("settings")}
                  className={`w-full text-left px-4 py-2 rounded flex items-center ${activeTab === "settings" ? "bg-blue-600 text-white" : "hover:bg-gray-200"}`}
                >
                  <Save size={16} className="mr-2" /> Settings
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab("results")}
                  className={`w-full text-left px-4 py-2 rounded flex items-center ${activeTab === "results" ? "bg-blue-600 text-white" : "hover:bg-gray-200"}`}
                >
                  <Eye size={16} className="mr-2" /> Results
                </button>
              </li>
            </ul>
          </nav>
        </div>

        <div className="flex-1 bg-white border rounded-lg p-6">
          {activeTab === "floorPlan" && <FloorPlanSection />}
          {activeTab === "rooms" && <RoomsSection />}
          {activeTab === "adjacency" && <AdjacencySection />}
          {activeTab === "settings" && <SettingsSection />}
          {activeTab === "results" && <ResultsSection />}
        </div>
      </div>
    </div>
  );
}

export default FloorPlanGenerator;