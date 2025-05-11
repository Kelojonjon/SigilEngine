# 🎨 SigilEngine

## Foreword

This is a hobby project that can be used to build various ASCII based "projects"

The architechture is built in a way that should allow, easy expansion, and adding of new features, with minimal changes.

Chaining, and global registry allow for flexible queueing of commands, and rendering of different canvases.

Individual cells host their own metadata, this allows creating fun stuff like game of life, only by sending packets and reading the buffers, while the internals themselves stay untouched.

Some of the feartures like "visible" metadata, are in the code, but dont yet do anything.

Possible future plans (depending on motivation of the hobbyist :D):

- Sockets and servers for fully async usage and rendering
- Input handling
- Scrollable canvases (although this could already be done manually via origin, or content handling)
- Proper logging
- Styling options for terminal rendering
- Handle visibility, and possibly "writable" metadata for individual cells
- Rendering via pygame for simulations

Things currently brewing / Upcoming (also depending on the motivation :D):

- Centralized logging system with batching, prebuffers, and metadata
- Event-based timer module for scheduled triggers
- Refactoring of the code (especially the canva_thread parser :D)

The below readme is generated using AI, if something is  unclear, you should find the answer from the codebase!

Feel free to contribute & fork && have fun! 
---

# Welcome to SigilEngine

A modular, threaded system for dynamic ASCII canvas rendering, chaining, and message forwarding.

This engine is built for fun, creativity, and hacking systems together — while giving you tight control over individual canvas states.

## 🌌 Core Components

- **CANVA_THREAD** - Active canvas thread with its own queue, state, and loop. All cells on the grid can host various metadata making the cells more than just simple characters.
- **PACKET_CREATOR** - Helper to build ready-to-send command packets
- **ASCII_SCREEN** - Reusable tools for grid rendering and manipulation
- **SPACE** - Global registry of active canvases, dimensions, and queues

## 📦 Examples

The engine comes with a set of demo examples to showcase functionality:

```python
__init__()
# Sets up 7 canvas threads (5 demo + 2 Game of Life specific) and a PACKET_CREATOR

game_of_life()
# Conway's Game of Life implementation with random meteorite impacts
# Demonstrates the power of cellular automata using SigilEngine's metadata capabilities

test_loop()
# Randomly moves canvases, forwards messages, clears/redraws
# Shows how canvases can be repositioned with real-time updates

chaining_test()
# Shows message forwarding between multiple nested canvases
# Demonstrates the hierarchical canvas structure

kill_test()
# Sends !kill commands, monitors cleanup, prints SPACE state
# Shows the graceful thread termination process

resize_and_fillvalue_test()
# Randomly resizes and updates fill characters
# Demonstrates dynamic canvas manipulation

run_random_test()
# Stress test: sends random packets, monitors queues
# Shows the engine's robustness under load

shutdown()
# Gracefully stops all threads, confirms shutdown
# Proper cleanup of all system resources
```

## ✉️ Command Packet System

### Structure

```python
{
  "command": {
    "cmd": "command_name",
    "args": {...}
  },
  "chart": [...],
  "metadata": [...]
}
```

**Example:**

```python
{
  "command": { "cmd": "write", "args": {} },
  "chart": [ (4,10), (4,11) ],
  "metadata": [ {"char": "@"}, {"char": "#"} ]
}
```

### 🔧 Supported Commands

|Command|Description|
|---|---|
|`write`|Local write to canvas|
|`auto_forward`|Local write + forward until no hosts left|
|`resize`|Change canvas size|
|`set_origin`|Reposition on host|
|`set_host`|Change host canvas|
|`set_fillvalue`|Set default fill character|
|`!kill`|Remove canvas, stop thread|
|`forward_to`|Local write + forward until target canvas|
|`clear`|Regenerate canvas using current state|

### 🔍 Command Details

**write**

- Writes locally using chart + metadata
- Engine stays passive; logic layer controls placement
- Maintains any existing metadata not updated by the write

**auto_forward**

- Writes locally, then forwards automatically to the next host
- Enables chaining small canvases into a final buffer
- Perfect for creating complex visual hierarchies from simpler components

**resize**

- Updates canvas size, recreates buffer, resyncs host, and draws debug borders
- Maintains current fillvalue character and other settings
- Automatically updates the global SPACE registry

**set_origin**

- Updates canvas origin on host, regenerates chart, refreshes host reference
- Does NOT auto-write canvas content to host
- Use after repositioning to refresh any debug reference borders

**set_host**

- Sets a new host if it exists in SPACE, resyncs canvas with host dimensions
- Enables dynamic re-parenting of canvases during runtime
- Automatically verifies host existence in SPACE registry

**set_fillvalue**

- Updates fill character for empty cells
- Multi-character fills can break visual grid; use with care
- Instantly regenerates canvas with new fill character

**!kill**

- Removes canvas from SPACE, stops its thread loop
- Gracefully terminates thread execution
- Automatically cleans up all references

**forward_to**

- Writes locally using chart + metadata
- Forwards the same data up the host chain
- Stops forwarding once the specified target canvas is reached
- Useful for targeted updates in complex canvas hierarchies

**clear**

- Wipes canvas by regenerating it from current state
- Maintains current dimensions, fill character, and other settings
- Useful for resetting a canvas without changing configuration

### 📝 PACKET_CREATOR Methods

**set_content_origin(origin)**
- Sets starting (y, x) coordinate for content placement on target canvas
- Default origin is (1,1), but can be placed outside canvas bounds
- Out-of-bounds content is automatically skipped during writing
- Example: `packet_creator.set_content_origin((10, 15))`

**set_target_width(width)**
- Sets target width for chart generation and text wrapping
- Content will wrap around at this width when using write commands
- No Y limit, so long texts might overflow vertically
- Can be used with newlines (\n) for more control
- Example: `packet_creator.set_target_width(50)`

**write_to_canvas(message)**
- Generates a chart matching message length, applying current target_width for wrapping
- All characters injected onto template as 'char' type
- Used for writing to a single canvas (no forwarding)
- Example: `packet = packet_creator.write_to_canvas("Hello World!")`

**auto_forward(message)**
- Same as write_to_canvas but includes auto_forward command
- Allows chaining write operations from first canvas to last in chain
- Example: `packet = packet_creator.auto_forward("Hello World!")`

**forward_to(target_id, message)**
- Writes through canvas chain but stops at specified target_id
- Perfect for partial chain forwarding
- Example: `packet = packet_creator.forward_to("canvas_1", "Hello World!")`

**set_template(template)**
- Sets a template dictionary where additional metadata will be injected
- Currently only 'char' is fully supported
- Example: `packet_creator.set_template({'char': '@', 'visible': True})`


## 🌌 SPACE

The global registry that coordinates all canvas threads:

```python
SPACE
# Global dictionary storing CANVA_THREAD instances
# Tracks canvas ID, dimensions, queues, thread objects
# Key-based access to all active canvases in the system

SPACE_LOCK
# Global Lock for thread-safe access to SPACE
# Always wrap SPACE reads/writes in:
with SPACE_LOCK:
    # Your code here
```

Each canvas registers itself in SPACE with:
- Canvas ID (used as dictionary key)
- Owner identifier
- Current dimensions (height & width)
- Visibility flag
- Queue reference (for sending commands)
- Thread object reference

This registry enables canvas discovery, hierarchical relationships, and thread management without tightly coupling components.

## 🖥️ ASCII_SCREEN

Utility functions for ASCII canvas operations:

```python
clear_screen()
# Cross-platform terminal clear (works on Windows and Unix)

create_canvas(canvas_id, owner, height, width, fillvalue, visible)
# Builds full canvas with metadata for each cell
# Each cell contains 'char', 'owner', 'visible', and 'canvas_id'

create_ref_canvas(height, width)
# Lightweight debug/reference canvas for visualization
# Uses predefined values: fillvalue='·', owner='ref', visible=True

render(buffer, ignore=None)
# Converts canvas buffer to printable string
# Optional 'ignore' parameter to treat specific characters as transparent

write_cell(buffer, y, x, metadata)
# Safely updates a single cell's metadata
# Returns True if update succeeded, False if coordinates invalid

zip_and_write(buffer, chart, metadata_list)
# Bulk-write metadata across coordinates
# Returns count of successfully written cells

box_borders(buffer, yx_corner, height, width, char="#")
# Draws visual borders around canvas regions
# Useful for debugging canvas placement

generate_wrapped_chart(origin_yx, string, width)
# Creates wrapped text coordinates with automatic line breaks
# Handles explicit newlines (\n) as well as width-based wrapping

generate_coords(yx_corner, height, width)
# Generates coordinate grid for a rectangular region
# Returns list of (y, x) tuples in row-major order
```

## ⚙️ CANVA_THREAD

The **CANVA_THREAD** is the heart of the engine — an independent, threaded canvas instance that:

- Listens on its queue for command packets
- Manages its state: size, fill, position, visibility
- Communicates with other canvases by forwarding data
- Registers itself in the global SPACE registry

### 🎮 Core Methods

```python
run()
# Main thread loop: registers in SPACE, waits on queue, processes packets
# Entry point for all canvas threads

parse_packet(packet)
# Parses incoming packets, executes commands
# Handles all supported commands: write, resize, auto_forward, etc.

clear_canvas()
# Resets local buffer with current state
# Maintains all current configuration

check_host()
# Verifies if assigned host exists in SPACE
# Returns boolean indicating host availability

sync_host()
# Syncs local canvas with host dimensions
# Builds host_ref_canvas (debug overlay) + conversion chart
# Essential for proper canvas chaining and visualization

sync_to_space()
# Updates height, width, visibility in global SPACE registry
# Ensures other canvases have accurate information

kill()
# Marks self dead, removes from SPACE
# Allows thread to exit gracefully
```

### 🌊 Thread Life Cycle

1. Registers itself into SPACE with metadata and queue reference
2. Builds its local canvas + optional host debug canvas
3. Enters a loop:
    - Waits for packets (`queue.get()`)
    - Processes commands via parse_packet
    - Forwards to host if needed
4. Exits cleanly when `alive = False` or on `!kill`
5. Removes itself from SPACE during cleanup

### 📡 Communication Flow

**Local → Host → Host's Host → … → Top Canvas**

With `auto_forward` or `forward_to`, CANVA_THREAD can pass its rendered data up the chain — all controlled with simple packet headers.

#### Host Resolution Process
1. Canvas checks if host exists in SPACE
2. If found, gets host dimensions and creates reference canvas
3. Generates coordinate conversion chart for proper placement
4. Draws debug borders for visualization
5. When forwarding, recalculates coordinates based on origin

### 🔥 Debugging Tips

- Check `thread.is_alive()` to monitor thread health
- Print `queue.qsize()` to spot clogged threads
- Print `SPACE` (with lock!) to inspect canvas states
- Enable `host_ref_canvas` renders for placement debugging
- Use `time.sleep()` in test loops to slow down operations
- Examine the canvas chaining with step-by-step rendering
- Use different fill characters to easily identify canvases

## 🎮 Advanced Examples

### Game of Life with Meteorites
The included Game of Life example demonstrates:
- Cellular automaton implementation using canvas metadata
- Dynamic rule processing based on neighbor states
- Random meteorite impacts that interact with the simulation
- Full screen rendering with animation

### Multi-Canvas Chaining
The chaining test shows:
- Nested canvas hierarchies up to 3 levels deep
- Coordinated message passing between canvases
- Dynamic repositioning of child canvases
- Automatic coordinate translation between hosts

## 🚀 Getting Started

1. Create CANVA_THREAD instances with desired dimensions and hosts
2. Wrap each CANVA_THREAD in a threading.Thread targeting its run()
3. Start all threads
4. Create a PACKET_CREATOR for generating command packets
5. Send packets to canvas queues
6. Use ASCII_SCREEN.render() to visualize results

## 🎯 Best Practices

- Use a consistent fill character that's visually distinct
- Set appropriate target_width for your content
- Always check host existence before setting
- Use thread-safe SPACE access with SPACE_LOCK
- Small sleep times (0.001s) can prevent race conditions
- Clear canvases before new content to avoid artifacts
- Consider canvas hierarchies carefully for proper chaining