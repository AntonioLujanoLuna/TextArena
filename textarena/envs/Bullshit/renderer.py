def create_board_str(game_state: dict) -> str:
    """
    Create an ASCII representation of the Bullshit game state.
    
    Args:
        game_state (dict): The current game state containing hands, pile, etc.
        
    Returns:
        str: A formatted string representing the current game state.
    """
    hands = game_state.get("hands", {})
    pile = game_state.get("pile", [])
    current_rank = game_state.get("current_rank", 1)
    bullshit_phase = game_state.get("bullshit_phase", False)
    last_declared_rank = game_state.get("last_declared_rank", None)
    last_player = game_state.get("last_player", None)
    last_played_cards = game_state.get("last_played_cards", [])
    players_who_can_call = game_state.get("players_who_can_call", set())
    
    # Convert rank number to rank string
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    current_rank_str = ranks[current_rank - 1] if 1 <= current_rank <= 13 else "?"
    
    lines = []
    
    # Header
    lines.append("┌─ BULLSHIT CARD GAME ────────────────────────────────────────┐")
    
    # Game phase
    phase_text = "🔍 BULLSHIT CALLING PHASE" if bullshit_phase else "🎮 PLAYING PHASE"
    lines.append(f"│ {phase_text:<58} │")
    lines.append("├──────────────────────────────────────────────────────────────┤")
    
    # Current rank and pile info
    lines.append(f"│ Current Rank to Claim: {current_rank_str:<3} ({current_rank:>2})                       │")
    lines.append(f"│ Pile Size: {len(pile):>3} cards                                  │")
    
    # Last play information
    if bullshit_phase and last_player is not None and last_declared_rank is not None:
        last_rank_str = ranks[last_declared_rank - 1] if 1 <= last_declared_rank <= 13 else "?"
        num_cards = len(last_played_cards)
        lines.append("├──────────────────────────────────────────────────────────────┤")
        lines.append(f"│ Last Play: Player {last_player} claimed {num_cards} card(s) as {last_rank_str:<3}           │")
        
        if players_who_can_call:
            waiting_players = ", ".join(str(p) for p in sorted(players_who_can_call))
            lines.append(f"│ Waiting for: Player(s) {waiting_players:<30} │")
    
    lines.append("├──────────────────────────────────────────────────────────────┤")
    
    # Player information
    lines.append("│ PLAYER STATUS:                                               │")
    lines.append("├────┬─────────────┬──────────────────────────────────────────┤")
    lines.append("│ ID │ Card Count  │ Status                                   │")
    lines.append("├────┼─────────────┼──────────────────────────────────────────┤")
    
    num_players = len(hands)
    for pid in range(num_players):
        card_count = len(hands.get(pid, []))
        
        # Determine status
        if bullshit_phase:
            if pid == last_player:
                status = "🎯 Last Player"
            elif pid in players_who_can_call:
                status = "⏳ Can Call BS"
            else:
                status = "⏸️  Waiting"
        else:
            status = "🎮 Playing"
        
        # Special case for winner
        if card_count == 0:
            status = "🏆 WINNER!"
        
        lines.append(f"│ {pid:>2} │ {card_count:>8} cards │ {status:<40} │")
    
    lines.append("├────┴─────────────┴──────────────────────────────────────────┤")
    
    # Pile visualization (top few cards)
    if pile:
        lines.append("│ TOP CARDS IN PILE:                                           │")
        # Show last few cards added to pile (face down representation)
        recent_cards = pile[-min(5, len(pile)):]
        card_representations = []
        for card in recent_cards:
            card_representations.append("🎴")
        
        pile_display = " ".join(card_representations)
        if len(pile) > 5:
            pile_display = f"... {pile_display}"
            
        lines.append(f"│ {pile_display:<58} │")
    else:
        lines.append("│ PILE: Empty                                                  │")
    
    lines.append("└──────────────────────────────────────────────────────────────┘")
    
    # Instructions based on phase
    if bullshit_phase:
        lines.append("")
        lines.append("Actions: [BULLSHIT] to call, [PASS] to decline")
    else:
        lines.append("")
        lines.append("Actions: [rank card_indices] (e.g., [A 0 2] or [K 1 3 5])")
    
    return "\n".join(lines)
