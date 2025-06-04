def create_board_str(game_state: dict) -> str:
    """
    Create a visual representation of the Codenames game board.
    
    Args:
        game_state (dict): The current game state containing board, guessed words, etc.
        
    Returns:
        str: A formatted string representing the current game state.
    """
    board = game_state.get("board", {})
    guessed_words = game_state.get("guessed_words", set())
    team_turn = game_state.get("team_turn", 0)
    phase = game_state.get("phase", "clue")
    last_clue = game_state.get("last_clue", None)
    last_number = game_state.get("last_number", 0)
    remaining_guesses = game_state.get("remaining_guesses", 0)
    red_words_left = game_state.get("red_words_left", 8)
    blue_words_left = game_state.get("blue_words_left", 8)
    
    # Color and symbol mapping
    color_symbols = {
        "R": "🔴",  # Red team
        "B": "🔵",  # Blue team  
        "N": "⚪",  # Neutral
        "A": "💀"   # Assassin
    }
    
    # Convert board dict to 5x5 grid
    words = list(board.keys())
    if len(words) != 25:
        return "Error: Board should contain exactly 25 words"
    
    # Create 5x5 grid
    grid = []
    for i in range(5):
        row = words[i*5:(i+1)*5]
        grid.append(row)
    
    lines = []
    
    # Header with game status
    lines.append("┌─ CODENAMES GAME ─────────────────────────────────────────────────────┐")
    
    # Team status
    current_team = "🔴 RED" if team_turn == 0 else "🔵 BLUE"
    current_phase = "GIVING CLUE" if phase == "clue" else "GUESSING"
    lines.append(f"│ Current Turn: {current_team} TEAM - {current_phase:<20}           │")
    
    # Clue information
    if last_clue and phase == "guess":
        lines.append(f"│ Active Clue: [{last_clue.upper()} {last_number}] - {remaining_guesses} guesses remaining{' ' * (20 - len(str(remaining_guesses)))}│")
    else:
        lines.append(f"│ Active Clue: None{' ' * 50}                  │")
    
    # Team progress
    lines.append(f"│ 🔴 Red: {red_words_left}/8 words left    🔵 Blue: {blue_words_left}/8 words left{' ' * 15}│")
    lines.append("├" + "─" * 70 + "┤")
    
    # Column headers (optional spacing for alignment)
    lines.append("│     " + "    ".join([f"{i+1:^12}" for i in range(5)]) + "     │")
    lines.append("├" + "─" * 70 + "┤")
    
    # Word grid
    for row_idx, row in enumerate(grid):
        # Word row
        word_line = "│ "
        for word in row:
            # Determine display format
            if word in guessed_words:
                # Revealed word - show color symbol
                team = board[word]
                symbol = color_symbols[team]
                word_display = f"{symbol} {word:<9}"
            else:
                # Hidden word - just show the word
                word_display = f"   {word:<9}"
            
            word_line += word_display
            if word != row[-1]:  # Not the last word in row
                word_line += " "
        word_line += " │"
        lines.append(word_line)
        
        # Add separator between rows (except after last row)
        if row_idx < 4:
            lines.append("├" + "─" * 70 + "┤")
    
    lines.append("└" + "─" * 70 + "┘")
    
    # Legend
    lines.append("")
    lines.append("Legend:")
    lines.append("🔴 Red Team Word    🔵 Blue Team Word    ⚪ Neutral Word    💀 Assassin Word")
    lines.append("(Colors shown only after words are guessed)")
    
    # Game instructions based on current phase
    lines.append("")
    if phase == "clue":
        role = "Spymaster"
        instruction = "Give a one-word clue and number: [clue number]"
    else:
        role = "Operative" 
        instruction = f"Guess a word: [word] ({remaining_guesses} guesses remaining)"
    
    lines.append(f"Next action ({current_team} {role}): {instruction}")
    
    return "\n".join(lines)
