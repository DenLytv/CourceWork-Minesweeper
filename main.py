import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.constants import RAISED, SUNKEN
from random import shuffle
import time
import csv
import os
from collections import namedtuple

# Numbers colors
COLORS = {
    1: "blue",
    2: "green",
    3: "red",
    4: "dark blue",
    5: "brown",
    6: "cyan",
    7: "black",
    8: "grey",
}

# Game difficulty presets (height, width, mines)
BEGINNER_OPTIONS = (9, 9, 15)
INTERMEDIATE_OPTIONS = (16, 16, 40)
EXPERT_OPTIONS = (16, 30, 99)

# Size constants
MIN_HEIGHT = MIN_WIDTH = 1
MAX_WIDTH = 50
MAX_HEIGHT = 23

# Leaderboard entry structure
LeaderboardEntry = namedtuple('LeaderboardEntry', ['name', 'time'])


class FieldButton(tk.Button):
    """Custom button class for each cell in the Minesweeper grid."""

    def __init__(self, master, row, col, number=0, *args, **kwargs):
        super().__init__(
            master,
            width=2,
            font=("Tahoma", 10, "bold"),
            relief=RAISED,
            bd=4,
            *args,
            **kwargs,
            activebackground="#d0d0d0"
        )
        self.row = row
        self.col = col
        self.number = number
        self.is_mine = False
        self.adjacent_mines = 0
        self.is_open = False

        def on_enter(event):
            """Changes the button color on hover"""
            if not self.is_open and self["state"] == "normal":
                self.config(background=self.highlight_bg)

        def on_leave(event):
            """Returns the button's normal color"""
            if not self.is_open and self["state"] == "normal":
                self.config(background=self.default_bg)

        # Event handlers for highlighting
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
        self.default_bg = self.cget("background")
        self.highlight_bg = "#e0e0e0"


class LeaderboardWindow(tk.Toplevel):
    """Window to display high scores for different difficulty levels."""

    def __init__(self, parent, leaderboards, minesweeper_instance):
        super().__init__(parent)
        self.title("Leaderboards")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self.minesweeper = minesweeper_instance
        self.trees = {}

        self.setup_ui(leaderboards)

    def setup_ui(self, leaderboards):
        """Initialize all UI components."""
        notebook = ttk.Notebook(self)

        # Create tabs for each difficulty
        difficulties = [
            ('beginner', "Beginner (9×9, 10 mines)"),
            ('intermediate', "Intermediate (16×16, 40 mines)"),
            ('expert', "Expert (16×30, 99 mines)")
        ]

        for difficulty, title in difficulties:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=difficulty.capitalize())
            self.trees[difficulty] = self.create_leaderboard_table(
                frame,
                leaderboards[difficulty],
                title
            )

        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        self.create_buttons()

    def create_leaderboard_table(self, parent, entries, title):
        """Create and populate a leaderboard table for one difficulty level."""
        title_label = ttk.Label(parent, text=title, font=("Arial", 10, "bold"))
        title_label.pack(pady=(5, 10))

        columns = ("Rank", "Name", "Time")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)

        # Configure columns
        tree.column("Rank", width=50, anchor="center")
        tree.column("Name", width=150, anchor="center")
        tree.column("Time", width=100, anchor="center")

        # Set headings
        for col in columns:
            tree.heading(col, text=col)

        self.update_treeview(tree, entries)
        tree.pack(padx=10, pady=5)
        return tree

    def create_buttons(self):
        """Create control buttons at the bottom of the window."""
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        # Configure button styles
        style = ttk.Style()
        style.configure('Danger.TButton', foreground='red')

        reset_button = ttk.Button(
            button_frame,
            text="Reset Scores",
            command=self.reset_leaderboards,
            style='Danger.TButton'
        )
        reset_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        )
        close_button.pack(side=tk.LEFT, padx=5)

    @staticmethod
    def update_treeview(tree, entries):
        """Update the contents of a Treeview widget."""
        tree.delete(*tree.get_children())
        for rank, entry in enumerate(entries, 1):
            tree.insert("", "end", values=(rank, entry.name, entry.time))

    def reset_leaderboards(self):
        """Reset all leaderboards after confirmation."""
        if not messagebox.askyesno(
                "Reset Scores",
                "Are you sure you want to reset all leaderboards?\nThis cannot be undone!",
                icon='warning'
        ):
            return

        # Clear in-memory data
        self.minesweeper.leaderboards = {
            'beginner': [],
            'intermediate': [],
            'expert': []
        }

        # Delete files
        for difficulty in self.minesweeper.leaderboards.keys():
            filename = f"{difficulty}_leaderboard.csv"
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

        # Update UI
        for difficulty, tree in self.trees.items():
            self.update_treeview(tree, [])

        messagebox.showinfo("Reset Scores", "All leaderboards have been reset.")

class MinesweeperGame:
    """Main game class with main game configuration and logic."""

    def __init__(self):
        # Root configuration
        self.root = tk.Tk()
        self.root.title("Minesweeper")
        self.root.resizable(width=False, height=False)

        def on_closing():
            self.save_leaderboards()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

        # Game state variables
        self.game_over = False
        self.is_first_click = True
        self.width = 9
        self.height = 9
        self.mines = 15
        self.flags_left = self.mines
        self.start_time = 0
        self.timer_running = False

        # UI elements
        self.flags_label = None
        self.restart_button = None
        self.timer_label = None
        self.buttons = []
        self.setup_ui()

        # Leaderboard data
        self.player_name = None
        self.leaderboards = {
            'beginner': [],
            'intermediate': [],
            'expert': []
        }

    def setup_ui(self):
        self.create_top_panel()
        self.create_game_grid()
        self.create_menu()

    def create_top_panel(self):
        """Create the top panel with flags counter, smiley button and timer."""
        top_frame = tk.Frame(self.root, bd=12, relief=SUNKEN)
        top_frame.pack(fill="x")
        top_frame.columnconfigure([0, 1, 2], weight=1)

        # Flags counter
        self.flags_label = tk.Label(
            top_frame,
            text=f"{self.flags_left:03d}",
            font=("Courier New", 15, "bold"),
            fg="red",
            bg="black",
            relief=SUNKEN,
            bd=3
        )
        self.flags_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Restart button
        self.restart_button = tk.Button(
            top_frame,
            text="🙂",
            font=("Segoe UI Emoji", 12, "normal"),
            relief=RAISED,
            bd=4,
            command=self.reset_game
        )
        self.restart_button.grid(row=0, column=1, pady=5)

        # Timer
        self.timer_label = tk.Label(
            top_frame,
            text="000",
            font=("Courier New", 15, "bold"),
            fg="red",
            bg="black",
            relief=SUNKEN,
            bd=3
        )
        self.timer_label.grid(row=0, column=2, sticky="e", padx=5, pady=5)

    def create_game_grid(self):
        """Create the grid of buttons for the game."""
        grid_frame = tk.Frame(self.root, bd=12, relief=SUNKEN)
        grid_frame.pack()

        for i in range(self.height + 2):
            temp = []
            for j in range(self.width + 2):
                btn = FieldButton(grid_frame, row=i, col=j)
                btn.config(command=lambda button=btn: self.handle_click(button))
                btn.bind("<Button-1>", self.update_smiley)
                btn.bind("<ButtonRelease-1>", self.update_smiley)
                btn.bind("<Button-3>", self.toggle_flag)
                temp.append(btn)
            self.buttons.append(temp)

    def create_menu(self):
        """Create the game menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New", accelerator="F2", command=self.reset_game)
        game_menu.add_separator()

        # Difficulty submenu
        difficulty_menu = tk.Menu(game_menu, tearoff=0)
        difficulty_menu.add_command(
            label="Beginner",
            command=lambda: self.set_difficulty(BEGINNER_OPTIONS)
        )
        difficulty_menu.add_command(
            label="Intermediate",
            command=lambda: self.set_difficulty(INTERMEDIATE_OPTIONS)
        )
        difficulty_menu.add_command(
            label="Expert",
            command=lambda: self.set_difficulty(EXPERT_OPTIONS)
        )
        difficulty_menu.add_command(
            label="Custom...",
            command=self.show_custom_difficulty_dialog
        )

        game_menu.add_cascade(label="Difficulty", menu=difficulty_menu)
        game_menu.add_separator()
        game_menu.add_command(label="Leaderboards...", command=self.show_leaderboards)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=lambda: self.root.destroy())

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Game Rules", command=self.show_game_rules, accelerator="F1")
        help_menu.add_command(label="About", command=self.show_about)

        menubar.add_cascade(label="Game", menu=game_menu)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.bind("<F1>", lambda e: self.show_game_rules())
        self.root.bind("<F2>", lambda e: self.reset_game())

        count = 1
        for i in range(1, self.height + 1):
            for j in range(1, self.width + 1):
                btn = self.buttons[i][j]
                btn.number = count
                btn.grid(row=i, column=j, sticky="nw")
                count += 1

        self.root.rowconfigure([i for i in range(0, self.height)], weight=1)
        self.root.columnconfigure([i for i in range(0, self.width)], weight=1)

    def show_game_rules(self):
        """Display game rules"""
        win = tk.Toplevel(self.root)
        win.title("Game Rules")
        win.resizable(False, False)

        win.grab_set()
        win.transient(self.root)

        # Header
        ttk.Label(win, text="Minesweeper Rules",
                  font=("Arial", 16, "bold")).pack(pady=10)

        # Rules text with scrollbar
        text_frame = tk.Frame(win)
        scrollbar = tk.Scrollbar(text_frame)
        text = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set,
                       padx=10, pady=10, font=("Arial", 11), width=50, height=15)

        rules = """1. The game board consists of hidden cells
2. Some cells contain mines (bombs)
3. Click on a cell to reveal it
4. If you reveal a mine, you lose
5. Numbers show how many mines are adjacent to that cell
6. Right-click to place/remove a flag where you think mines are
7. To win, reveal all cells without mines
8. The timer records your completion time

Controls:
- Left click: Reveal cell
- Right click: Place/remove flag
- F2: New game
- Smiley face: Reset game

Tips for beginners:
- Start from the corners
- Find all the obvious mines first
- Use numbers to make logical deductions
"""

        text.insert("1.0", rules.strip())
        text.config(state="disabled")
        scrollbar.config(command=text.yview)

        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Close button
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def show_about(self):
        """Display information about the program"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Minesweeper")
        about_window.resizable(False, False)

        about_window.grab_set()
        about_window.transient(self.root)

        # Header
        tk.Label(about_window,
                 text="Minesweeper Python Edition",
                 font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Version info
        info_frame = tk.Frame(about_window)
        info_frame.pack(padx=20, pady=10)

        infos = [
            ("Version:", "1.0"),
            ("Developer:", "Denys Lytvynenko"),
            ("GitHub:", "github.com/DenLytv"),
        ]

        for label, text in infos:
            tk.Label(info_frame, text=label, anchor="e", width=10).grid(sticky="e")
            tk.Label(info_frame, text=text, anchor="w").grid(row=infos.index((label, text)), column=1, sticky="w")

        # Credits
        tk.Label(about_window,
                 text="Credits: Tkinter, Python 3.13",
                 font=("Arial", 9)).pack(pady=10)

        # Close button
        ttk.Button(about_window,
                   text="Close",
                   command=about_window.destroy).pack(pady=10)

    def load_leaderboards(self):
        """Load leaderboard data from CSV files, skipping invalid entries."""
        for difficulty in self.leaderboards.keys():
            filename = f"{difficulty}_leaderboard.csv"
            entries = []

            if os.path.exists(filename):
                try:
                    with open(filename, 'r', newline='') as file:
                        reader = csv.reader(file)
                        for row in reader:
                            try:
                                # Skip empty lines or lines with wrong format
                                if len(row) == 2:
                                    name, time_str = row
                                    time_val = int(time_str)
                                    if time_val > 0:
                                        if time_val > 999:
                                            time_val = 999
                                        if name == "":
                                            name = "Anonymous"
                                        entries.append(LeaderboardEntry(name, time_val))
                            except (ValueError, IndexError):
                                # Skip malformed entries but continue processing
                                continue

                        # Sort and keep only top 5 valid entries
                        entries.sort(key=lambda x: x.time)
                        self.leaderboards[difficulty] = entries[:5]
                except Exception as e:
                    # If file is completely unreadable, keep empty leaderboard
                    print(f"Error reading {filename}: {e}")
                    self.leaderboards[difficulty] = []

    def save_leaderboards(self):
        """Save leaderboard data to CSV files."""
        for difficulty, entries in self.leaderboards.items():
            filename = f"{difficulty}_leaderboard.csv"
            try:
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    for entry in entries:
                        writer.writerow([entry.name, entry.time])
            except Exception as e:
                pass

    def update_timer(self):
        """Update the game timer display."""
        if self.timer_running and not self.game_over:
            elapsed = min(int(time.time() - self.start_time), 999)
            self.timer_label.config(text=f"{elapsed:03d}")
            self.root.after(1000, self.update_timer)

    def start_timer(self):
        """Start the game timer."""
        if not self.timer_running:
            self.start_time = time.time()
            self.timer_running = True
            self.update_timer()

    def stop_timer(self):
        """Stop the game timer."""
        self.timer_running = False

    def update_smiley(self, event):
        """Update the smiley button appearance based on mouse actions."""
        emoji = self.restart_button.cget("text")
        if emoji in ("😵", "😎"):
            return
        self.restart_button.config(text="😮" if event.type == tk.EventType.ButtonPress else "🙂")

    def toggle_flag(self, event):
        if self.game_over:
            return
        button = event.widget
        if button["state"] == "normal" and self.flags_left > 0:
            self.flags_left -= 1
            button.config(state="disabled", text="🚩", disabledforeground="red", bg=button.default_bg)
        elif button.cget("text") == "🚩":
            self.flags_left += 1
            button.config(state="normal", text="", bg=button.default_bg)
        self.flags_label.config(text=f"{self.flags_left:03d}")

    def handle_click(self, button: FieldButton):
        if self.game_over:
            return

        button.config(background=button.default_bg)

        if self.is_first_click:
            self.place_mines(button.number)
            self.calculate_adjacent_mines()
            self.is_first_click = False
            self.start_timer()

        if button.is_mine:
            self.game_lost(button)
        else:
            color = COLORS.get(button.adjacent_mines, "black")
            if button.adjacent_mines:
                button.config(text=button.adjacent_mines, disabledforeground=color)
                button.is_open = True
            else:
                self.reveal_empty_region(button)
            button.config(state="disabled", relief=tk.SUNKEN)
            self.check_win()

    def place_mines(self, number: int):
        """Randomly place mines on the grid, excluding the first clicked cell."""
        index_mines = self.get_mines_places(number)
        for i in range(1, self.height + 1):
            for j in range(1, self.width + 1):
                btn = self.buttons[i][j]
                if btn.number in index_mines:
                    btn.is_mine = True

    def get_mines_places(self, exclude_number: int):
        """Get mines places."""
        indexes = list(range(1, self.width * self.height + 1))
        indexes.remove(exclude_number)
        shuffle(indexes)
        return indexes[:self.mines]

    def calculate_adjacent_mines(self):
        """Calculate how many mines are adjacent to each cell."""
        for i in range(1, self.height + 1):
            for j in range(1, self.width + 1):
                btn = self.buttons[i][j]
                adjacent_mines = 0
                if not btn.is_mine:
                    for row_dx in [-1, 0, 1]:
                        for col_dx in [-1, 0, 1]:
                            neighbour = self.buttons[i + row_dx][j + col_dx]
                            if neighbour.is_mine:
                                adjacent_mines += 1
                btn.adjacent_mines = adjacent_mines

    def reveal_empty_region(self, btn: FieldButton):
        """Reveal a cell and its neighbors if it's empty."""
        queue = [btn]
        while queue:
            cur_btn = queue.pop()
            color = COLORS.get(cur_btn.adjacent_mines, "black")
            if not cur_btn.cget("text") == "🚩":
                if cur_btn.adjacent_mines:
                    cur_btn.config(text=cur_btn.adjacent_mines, disabledforeground=color)
                else:
                    cur_btn.config(text="", disabledforeground=color)
                cur_btn.config(state="disabled", relief=tk.SUNKEN)
            cur_btn.is_open = True

            if cur_btn.adjacent_mines == 0:
                row, col = cur_btn.row, cur_btn.col
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        next_btn = self.buttons[row + dx][col + dy]
                        if (not next_btn.is_open
                                and 1 <= next_btn.row <= self.height
                                and 1 <= next_btn.col <= self.width
                                and next_btn not in queue):
                            queue.append(next_btn)

    def game_lost(self, button: FieldButton):
        """Handle game over when a mine is clicked."""
        button.config(text="*", bg="red", disabledforeground="black")
        self.stop_timer()
        self.game_over = True
        self.restart_button.config(text="😵")

        # Reveal all mines
        for row in range(1, self.height + 1):
            for col in range(1, self.width + 1):
                btn = self.buttons[row][col]
                if btn.is_mine:
                    btn.config(text="*", state='disabled', disabledforeground="black")
                else:
                    btn.config(state='disabled')

        messagebox.showinfo("Game Over", "You clicked on a mine!")

    def check_win(self):
        """Checks win conditions"""
        for row in range(1, self.height + 1):
            for col in range(1, self.width + 1):
                btn = self.buttons[row][col]
                if (not btn.is_mine and not btn.is_open) or (btn.cget("text") == "🚩" and not btn.is_mine):
                    return False

        self.game_won()
        return True

    def game_won(self):
        """Handle game win condition."""
        self.stop_timer()
        self.game_over = True
        elapsed = int(time.time() - self.start_time)

        self.timer_label.config(text=f"{elapsed:03d}")
        self.restart_button.config(text="😎")

        # Determine current difficulty
        current_settings = (self.height, self.width, self.mines)
        difficulty = None

        if current_settings == BEGINNER_OPTIONS:
            difficulty = 'beginner'
        elif current_settings == INTERMEDIATE_OPTIONS:
            difficulty = 'intermediate'
        elif current_settings == EXPERT_OPTIONS:
            difficulty = 'expert'

        messagebox.showinfo("Congratulations!", f"You won in {elapsed} seconds!")

        # Update leaderboard if applicable
        if difficulty:
            self.update_leaderboard(difficulty, elapsed)


        # Disable all buttons
        for row in range(1, self.height + 1):
            for col in range(1, self.width + 1):
                self.buttons[row][col].config(state='disabled')

    def update_leaderboard(self, difficulty, time_elapsed):
        """Update leaderboard"""
        self.load_leaderboards()

        entries = self.leaderboards[difficulty].copy()

        # Check if the time qualifies for top 5
        if len(entries) < 5 or time_elapsed < entries[-1].time:
            self.prompt_player_name(difficulty)

            # Add new entry and sort
            entries.append(LeaderboardEntry(self.player_name, time_elapsed))
            entries.sort(key=lambda x: x.time)

            # Keep only top 5 entries
            self.leaderboards[difficulty] = entries[:5]
            self.save_leaderboards()

            # Show leaderboard with new record
            self.show_leaderboards()

    def prompt_player_name(self, difficulty):
        """Show dialog to get player name after first win."""
        win = tk.Toplevel(self.root)
        win.title("You Won!")
        win.grab_set()
        win.transient(self.root)
        win.resizable(False, False)

        tk.Label(win, text=f"You have one of the fastest times for {difficulty} level."
                           f"\n Please enter your name:", wraplength=180).pack(pady=10, padx=10)

        name_entry = tk.Entry(win, width=20)
        name_entry.pack(pady=5, padx=10)
        name_entry.focus_set()

        def save_name():
            name = name_entry.get()
            self.player_name = "Anonymous" if name == "" else name
            win.destroy()

        ttk.Button(win, text="OK", command=save_name).pack(pady=10)
        win.wait_window()

    def show_custom_difficulty_dialog(self):
        """Show dialog for custom game settings."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Field")
        dialog.grab_set()
        dialog.transient(self.root)
        dialog.resizable(False, False)

        # Input validation functions
        def validate_width(value):
            return (value.isdecimal() and
                    MIN_WIDTH <= int(value) <= MAX_WIDTH or
                    value == "")

        def validate_height(value):
            return (value.isdecimal()
                    and MIN_HEIGHT <= int(value) <= MAX_HEIGHT
                    or value == "")

        width_var = tk.StringVar(value=str(self.width))
        height_var = tk.StringVar(value=str(self.height))
        mines_var = tk.StringVar(value=str(self.mines))

        frame = tk.Frame(dialog)
        frame.pack(padx=5, pady=5)

        # Status label for validation errors
        status_label = tk.Label(frame, text="", fg="red",  font=("Arial", 8, "normal"))
        status_label.grid(row=3, column=0, sticky="w", padx=(10, 0), pady=5, columnspan=4)

        def show_invalid_custom_data():
            status_label.config(text="Please enter valid numbers!")

        # Height setting
        tk.Label(frame, text=f"Height ({MIN_HEIGHT}-{MAX_HEIGHT})").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        height_spinbox = tk.Spinbox(
            frame,
            from_=MIN_HEIGHT,
            to=MAX_HEIGHT,
            textvariable=height_var,
            width=10,
            validate="key",
            validatecommand=(dialog.register(validate_height), "%P"),
            invalidcommand=dialog.register(show_invalid_custom_data)
        )
        height_spinbox.grid(row=0, column=1, padx=10, pady=5)

        # Width setting
        tk.Label(frame, text=f"Width ({MIN_WIDTH}-{MAX_WIDTH})").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        width_spinbox = tk.Spinbox(
            frame,
            from_=MIN_WIDTH,
            to=MAX_WIDTH,
            textvariable=width_var,
            width=10,
            validate="key",
            validatecommand=(dialog.register(validate_width), "%P"),
            invalidcommand=dialog.register(show_invalid_custom_data)
        )
        width_spinbox.grid(row=1, column=1, padx=10, pady=5)

        # Mines setting
        tk.Label(frame, text="Mines").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        mines_spinbox = tk.Spinbox(
            frame,
            from_=1,
            to=self.width*self.height-1,
            textvariable=mines_var,
            width=10,
        )
        mines_spinbox.grid(row=2, column=1, padx=10, pady=5)

        # Update mines max when dimensions change
        def update_mines_max(*args):
            try:
                w, h = int(width_var.get()), int(height_var.get())
                mines_spinbox.config(to=w * h - 1)
            except (ValueError, tk.TclError):
                pass

        width_var.trace("w", update_mines_max)
        height_var.trace("w", update_mines_max)

        # Button frame
        button_frame = tk.Frame(frame)
        button_frame.grid(row=0, column=2, rowspan=3, pady=10)

        # OK button
        def apply_settings():
            try:
                width = int(width_var.get())
                height = int(height_var.get())
                mines = int(mines_var.get())
                if mines < 0:
                    status_label.config(text="Please enter valid value")
                    return
                elif mines >= width * height:
                    status_label.config(text="Too many mines for this grid size!")
                    return

                self.set_difficulty((height, width, mines))
                dialog.destroy()
            except ValueError:
                status_label.config(text="Please enter valid numbers!")

        ttk.Button(frame, text="OK", command=apply_settings, width=10).grid(row=0, column=2, padx=10, pady=5)

        # Cancel button
        ttk.Button(frame, text="Cancel", command=dialog.destroy).grid(row=2, column=2, padx=10, pady=5)

    def show_leaderboards(self):
        """Read and display the leaderboard window."""
        self.load_leaderboards()
        LeaderboardWindow(self.root, self.leaderboards, self)

    def set_difficulty(self, settings):
        """Set game difficulty with given (height, width, mines) tuple."""
        self.height, self.width, self.mines = settings
        self.reset_game()

    def reset_game(self):
        """Reset the game to initial state."""
        self.stop_timer()

        # Clear the current UI
        for child in self.root.winfo_children():
            child.destroy()

        # Reset game state
        self.is_first_click = True
        self.game_over = False
        self.flags_left = self.mines
        self.buttons = []

        # Rebuild UI
        self.setup_ui()

    def start(self):
        """Start the game main loop."""
        self.root.mainloop()


game = MinesweeperGame()
game.start()