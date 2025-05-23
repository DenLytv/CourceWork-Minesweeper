# Minesweeper Game

A classic Minesweeper game implemented in Python using the Tkinter GUI library. This version includes all the familiar gameplay elements along with additional features like leaderboards and customizable difficulty levels.

## Features

- 🎮 Classic Minesweeper gameplay
- 🏆 Leaderboards for different difficulty levels
- ⚙️ Customizable game settings (grid size and mine count)
- ⏱️ Game timer and mine counter
- 😊 Interactive smiley button
- 📊 Three preset difficulty levels:
  - Beginner (9×9 grid, 15 mines)
  - Intermediate (16×16 grid, 40 mines)
  - Expert (16×30 grid, 99 mines)
- 📝 Game rules and about information

## Requirements

- Python 3.x
- Tkinter (usually included with Python)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/minesweeper.git
   ```
2. Navigate to the project directory:
   ```bash
   cd minesweeper
   ```
3. Run the game:
   ```bash
   python minesweeper.py
   ```

## How to Play

- Left-click to reveal a cell
- Right-click to place/remove a flag
- Reveal all non-mine cells to win
- Avoid clicking on mines!

## Controls

| Action | Key |
|--------|-----|
| New game | F2 |
| Show rules | F1 |
| Reset game | Click smiley button |

## Leaderboards

The game maintains separate leaderboards for each difficulty level, recording the fastest completion times. Player names are saved along with the scores.

## Customization

You can customize:
- Grid height (1-23 rows)
- Grid width (1-50 columns)
- Number of mines

## Files

- `minesweeper.py` - Main game file
- `*_leaderboard.csv` - Leaderboard data files (automatically created)
