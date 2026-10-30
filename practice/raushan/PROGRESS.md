# Learning progress — Raushan

- Part: 3 — World
- Python comfort: New to Python

## Topics learned
- World module orientation: Identified the roles of the arena, walls, power-ups, and their contracts with the game engine.
- Classes: Wrote a `Square` class that stores a side length and created an instance to read that value.
- Screen coordinates: Represented a position as an `(x, y)` pair; x is horizontal and y is vertical, with the screen origin at top-left.
- RGB colours: Represented colours as `(red, green, blue)` tuples with channel values from 0 to 255.
- Pygame surfaces: Understood the window surface as a digital canvas where game objects are drawn.
- Rectangles: Used `pygame.Rect(x, y, width, height)` to store a rectangle’s position and size.
- Drawing rectangles: Used `pygame.draw.rect(surface, color, rectangle)` to draw a coloured rectangle.
- Grid indexing: Read a two-dimensional list using `grid[row][column]`; Python indexes start at zero.
- Nested loops: Used one loop for rows and an inner loop for each row's cells.
- enumerate: Looped over a list while getting each item's zero-based index and value.
- Grid-to-pixel conversion: Converted columns to x pixels and rows to y pixels by multiplying by tile size, then built a tile-sized `pygame.Rect`.
- Map rows and columns: Counted text-map lines as rows and characters in each line as columns; identified unequal row lengths.
- Map-to-window dimensions: Multiplied column count by tile size for width and row count by tile size for height.
- pathlib paths: Used `Path(__file__).parent` to build a path relative to the current Python file's folder, then read text with `read_text()`.
- Wall class data: Wrote a `Wall` class that stores its rectangle, destructible flag, alive state, and health value.
- Wall damage: Added `hit(damage)` so destructible walls lose health and become not alive when health reaches zero or below.
- Wall drawing: Used `pygame.draw.rect` with different temporary RGB colors for solid and destructible walls.
- Hiding broken walls: Used an early `return` in `draw()` to skip walls whose `alive` flag is false.
- Wall verification: Ran checks confirming syntax, damage behavior, hidden broken walls, and solid-wall drawing.
- Hard-coded arena grid: Added a three-row, three-column list of strings with equal row lengths in `arena.py`.
- Grid scanning: Used nested `enumerate` loops to find and print the row/column coordinates of each `#` tile; verified the six expected positions.
- Arena grid-to-pixel conversion: Calculated a `pygame.Rect` for each `#` using the 40-pixel temporary tile size; ran the script and verified all six rectangles have correct coordinates and size.
- Project environment: Ran `arena.py` with the project `.venv` interpreter to access installed Pygame-CE.
