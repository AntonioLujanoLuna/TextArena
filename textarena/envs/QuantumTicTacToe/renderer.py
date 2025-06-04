from typing import List

def create_board_str(game_state: dict) -> str:
    """
    Create a visual representation of the Quantum Tic Tac Toe board.
    
    Shows:
    - 3x3 grid with cell indices
    - Quantum superposition marks (e.g., "X1/X1")  
    - Classical collapsed marks (e.g., "X", "O")
    - Visual distinction between quantum and classical states
    
    Args:
        game_state (dict): The current game state
        
    Returns:
        str: Formatted string representing the quantum board state
    """
    board = game_state.get("board", [['' for _ in range(3)] for _ in range(3)])
    superpositions = game_state.get("superpositions", {})
    move_log = game_state.get("move_log", [])
    
    # Build a mapping from cell position to marks
    cell_marks = {}
    for r in range(3):
        for c in range(3):
            cell_marks[(r, c)] = {
                "classical": board[r][c],  # Classical mark (X, O, or '')
                "quantum": []              # List of quantum marks
            }
    
    # Add quantum superposition marks
    for move_id, (player_id, pos_a, pos_b) in superpositions.items():
        symbol = 'X' if player_id == 1 else 'O'
        mark = f"{symbol}{move_id}"
        
        # Add quantum mark to both positions
        cell_marks[pos_a]["quantum"].append(mark)
        cell_marks[pos_b]["quantum"].append(mark)
    
    def render_cell(r: int, c: int) -> List[str]:
        """Render a single cell, returning multiple lines for complex states."""
        cell_idx = r * 3 + c
        marks = cell_marks[(r, c)]
        
        if marks["classical"]:
            # Classical mark - show large and prominent
            classical_mark = marks["classical"]
            return [
                f"     [{cell_idx}]     ",
                f"               ",
                f"      {classical_mark}      ",  # Classical mark in center
                f"   (SOLID)    "
            ]
        elif marks["quantum"]:
            # Quantum superposition marks
            quantum_marks = marks["quantum"]
            if len(quantum_marks) == 1:
                mark = quantum_marks[0]
                return [
                    f"     [{cell_idx}]     ",
                    f"               ",
                    f"    {mark}/{mark}    ",  # Show as superposition
                    f"   (quantum)   "
                ]
            else:
                # Multiple quantum marks in same cell
                marks_str = " ".join(quantum_marks)
                return [
                    f"     [{cell_idx}]     ",
                    f" {marks_str:<13} ",
                    f"   (multiple)  ",
                    f"   (quantum)   "
                ]
        else:
            # Empty cell - just show index
            return [
                f"     [{cell_idx}]     ",
                f"               ",
                f"     EMPTY     ",
                f"               "
            ]
    
    # Build the full grid
    lines = []
    
    # Header
    lines.append("┌─ QUANTUM TIC TAC TOE ────────────────────────────────────────────────┐")
    lines.append("│                                                                       │")
    
    # Render each row
    for row in range(3):
        # Get all cell renderings for this row
        cell_renders = [render_cell(row, col) for col in range(3)]
        
        # Combine cells horizontally for each line
        for line_idx in range(4):  # 4 lines per cell
            line = "│ "
            for col in range(3):
                line += cell_renders[col][line_idx]
                if col < 2:
                    line += " │ "
            line += " │"
            lines.append(line)
        
        # Add horizontal separator between rows (except after last row)
        if row < 2:
            lines.append("├" + "─" * 15 + "┼" + "─" * 15 + "┼" + "─" * 15 + "┤")
    
    lines.append("│                                                                       │")
    lines.append("└───────────────────────────────────────────────────────────────────────┘")
    
    # Add legend and status
    lines.append("")
    lines.append("Legend:")
    lines.append("• [n] = Cell index (0-8)")
    lines.append("• X1/X1, O2/O2 = Quantum superposition marks")  
    lines.append("• X, O = Classical collapsed marks (SOLID)")
    lines.append("• Multiple marks in one cell = Entangled superpositions")
    
    # Game status
    lines.append("")
    num_superpositions = len(superpositions)
    num_classical = sum(1 for row in board for cell in row if cell)
    
    lines.append(f"Game Status:")
    lines.append(f"• Active superpositions: {num_superpositions}")
    lines.append(f"• Collapsed marks: {num_classical}")
    lines.append(f"• Total moves made: {len(move_log)}")
    
    return "\n".join(lines)
