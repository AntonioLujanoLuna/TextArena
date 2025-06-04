import re, random
from typing import Optional, Dict, Any, Tuple

import textarena as ta

from textarena.envs.Bullshit.renderer import create_board_str

class BullshitEnv(ta.Env):
    """
    A text-based implementation of the Bullshit (Cheat) card game using textarena.

    In this game, players take turns playing cards face-down and declaring what rank
    they are. Other players can call "Bullshit" if they think the player is lying.
    The goal is to be the first player to get rid of all your cards.
    """

    # Regex patterns to detect user actions
    BULLSHIT_PATTERN = re.compile(r"\[\s*BULLSHIT\s*\]", re.IGNORECASE)
    PASS_PATTERN = re.compile(r"\[\s*PASS\s*\]", re.IGNORECASE)
    PLAY_PATTERN = re.compile(
        r"\[\s*(\w+)\s+((?:\d+\s*)+)\]",  # [rank card_indexes]
        re.IGNORECASE
    )

    # Card setup
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    def __init__(self, max_turns: int = 200):
        """
        Initialize the Bullshit game environment.
        
        Args:
            max_turns (int): Maximum number of turns before game ends in draw
        """
        super().__init__()
        self.max_turns = max_turns
        # rank_values: {"A": 1, "2": 2, ..., "K": 13}
        self.rank_values = {rank: i + 1 for i, rank in enumerate(self.ranks)}

    def get_board_str(self):
        return create_board_str(game_state=self.state.game_state)

    def reset(self, num_players: int, seed: Optional[int] = None) -> None:
        """Reset the environment for a new Bullshit game."""
        self.state = ta.State(
            num_players=num_players, 
            min_players=2, 
            max_players=8,
            max_turns=self.max_turns
        )

        # Create deck and shuffle
        deck = [{"rank": rank, "suit": suit} for suit in self.suits for rank in self.ranks]
        random.shuffle(deck)

        # Deal cards to all players
        hands = {pid: [] for pid in range(num_players)}
        current_player = 0
        while deck:
            hands[current_player].append(deck.pop())
            current_player = (current_player + 1) % num_players

        # Initialize game state
        game_state = {
            "hands": hands,
            "pile": [],
            "last_played_cards": [],
            "last_declared_rank": None,
            "last_player": None,
            "current_rank": 1,  # Start with Aces (1)
            "bullshit_phase": False,  # Are we in bullshit calling phase?
            "players_who_can_call": set(),  # Players who can call bullshit
        }

        # Reset state
        self.state.reset(
            seed=seed, 
            game_state=game_state, 
            player_prompt_function=self._generate_player_prompt
        )

        # Show initial state
        self._announce_game_state()

    def _generate_player_prompt(self, player_id: int, game_state: Dict[str, Any]) -> str:
        """Provide game instructions for each player at game start."""
        prompt = (
            f"Welcome to Bullshit! You are Player {player_id}.\n\n"
            "OBJECTIVE:\n"
            "  Be the first to get rid of all your cards.\n\n"
            "GAME FLOW:\n"
            "  1. Players take turns playing 1 or more cards face down.\n"
            "  2. You must CLAIM these cards are of the current rank.\n"
            "  3. The current rank starts at A (Ace) and increments: A, 2, 3, ..., K, then back to A.\n"
            "  4. After a player plays, others may call [BULLSHIT] if they think you're lying.\n"
            "  5. If you lied, you pick up the whole pile.\n"
            "  6. If you told the truth, the accuser picks up the pile.\n"
            "  7. The first player to have no cards left wins!\n\n"
            "ACTIONS:\n"
            "  [A 0 2]        => 'I claim these 2 cards are Aces', using card indexes 0 and 2 from my hand.\n"
            "  [BULLSHIT]     => Call bullshit on the previous play.\n"
            "  [PASS]         => Decline to call bullshit.\n\n"
            "Your hand will be shown as numbered cards. Use the indexes to specify which cards to play.\n"
            "Good luck!\n"
        )
        return prompt

    def step(self, action: str) -> Tuple[bool, ta.Info]:
        """Process a single step/action from the current player."""
        current_pid = self.state.current_player_id
        gs = self.state.game_state

        # Log the player's raw input
        self.state.add_observation(from_id=current_pid, to_id=-1, message=action)

        if gs["bullshit_phase"]:
            self._handle_bullshit_phase(action, current_pid)
        else:
            self._handle_play_phase(action, current_pid)

        # Check win condition after any action
        if len(gs["hands"][current_pid]) == 0:
            self.state.set_winners(
                player_ids=[current_pid],
                reason=f"Player {current_pid} has no cards left and wins!"
            )
        else:
            # Show updated state
            self._announce_game_state()

        return self.state.step(rotate_player=False)

    def _handle_play_phase(self, action: str, current_pid: int):
        """Handle actions during the normal play phase."""
        gs = self.state.game_state

        # Try to parse as a play action
        match = self.PLAY_PATTERN.search(action.strip())
        if match:
            declared_rank_str = match.group(1)
            indexes_str = match.group(2)
            self._process_play_action(current_pid, declared_rank_str, indexes_str)
        else:
            self.state.set_invalid_move(
                player_id=current_pid,
                reason="Invalid action. Use format [rank card_indexes], e.g., [A 0 2] or [K 1 3 5]."
            )

    def _handle_bullshit_phase(self, action: str, current_pid: int):
        """Handle actions during the bullshit calling phase."""
        gs = self.state.game_state

        if current_pid not in gs["players_who_can_call"]:
            self.state.set_invalid_move(
                player_id=current_pid,
                reason="You cannot call bullshit right now. Wait for your turn."
            )
            return

        if self.BULLSHIT_PATTERN.search(action):
            self._process_bullshit_call(current_pid)
        elif self.PASS_PATTERN.search(action):
            self._process_pass(current_pid)
        else:
            self.state.set_invalid_move(
                player_id=current_pid,
                reason="During bullshit phase, use [BULLSHIT] to call or [PASS] to decline."
            )

    def _process_play_action(self, current_pid: int, declared_rank_str: str, indexes_str: str):
        """Process a player's play action."""
        gs = self.state.game_state

        # Validate declared rank
        declared_rank = self._parse_declared_rank(declared_rank_str)
        if self.rank_values[declared_rank] != gs["current_rank"]:
            self.state.set_invalid_move(
                player_id=current_pid,
                reason=f"You must claim rank {self._int_to_rank(gs['current_rank'])}, not {declared_rank_str}."
            )
            return
        if declared_rank is None:
            self.state.set_invalid_move(
                player_id=current_pid,
                reason=f"Unrecognized rank: {declared_rank_str}. Must be A, 2-10, J, Q, K."
            )
            return

        # Parse card indexes
        try:
            card_indexes = [int(x) for x in indexes_str.split()]
        except ValueError:
            self.state.set_invalid_move(
                player_id=current_pid,
                reason=f"Could not parse card indexes: '{indexes_str}'"
            )
            return

        # Validate indexes
        hand = gs["hands"][current_pid]
        if any(i < 0 or i >= len(hand) for i in card_indexes):
            self.state.set_invalid_move(
                player_id=current_pid,
                reason="One or more card indexes are out of range for your hand."
            )
            return

        # Remove cards from hand (sort indexes in reverse to avoid index shifting)
        played_cards = []
        for i in sorted(card_indexes, reverse=True):
            played_cards.append(hand.pop(i))

        # Update game state
        gs["last_played_cards"] = played_cards
        gs["last_declared_rank"] = declared_rank
        gs["last_player"] = current_pid
        gs["pile"].extend(played_cards)

        # Announce the play
        rank_text = self._int_to_rank(declared_rank)
        self.state.add_observation(
            from_id=ta.GAME_ID,
            to_id=-1,
            message=f"Player {current_pid} plays {len(played_cards)} card(s), claiming they are {rank_text}."
        )

        # Enter bullshit phase
        gs["bullshit_phase"] = True
        gs["players_who_can_call"] = set(range(self.state.num_players)) - {current_pid}

        # Move to next player for bullshit calling
        next_player = (current_pid + 1) % self.state.num_players
        self.state.manually_update_current_player(new_player_id=next_player)

        # Announce bullshit opportunity
        self.state.add_observation(
            from_id=ta.GAME_ID,
            to_id=-1,
            message="Other players may now call [BULLSHIT] or [PASS]. Waiting for responses..."
        )

    def _process_bullshit_call(self, caller_pid: int):
        """Process a bullshit call."""
        gs = self.state.game_state
        last_player = gs["last_player"]
        last_declared_rank = gs["last_declared_rank"]
        last_played_cards = gs["last_played_cards"]

        # Check if the last play was honest
        honest = all(
            self.rank_values[card["rank"]] == last_declared_rank
            for card in last_played_cards
        )

        if honest:
            # The caller was wrong - they pick up the pile
            self.state.add_observation(
                from_id=ta.GAME_ID,
                to_id=-1,
                message=f"Player {caller_pid} calls Bullshit, but Player {last_player} was telling the truth! Player {caller_pid} picks up the pile."
            )
            self._give_pile_to_player(caller_pid)
        else:
            # The caller was right - the last player picks up the pile
            self.state.add_observation(
                from_id=ta.GAME_ID,
                to_id=-1,
                message=f"Player {caller_pid} calls Bullshit, and they're correct! Player {last_player} picks up the pile."
            )
            self._give_pile_to_player(last_player)

        self._end_bullshit_phase()

    def _process_pass(self, current_pid: int):
        """Process a pass during bullshit phase."""
        gs = self.state.game_state
        gs["players_who_can_call"].discard(current_pid)

        if not gs["players_who_can_call"]:
            # Everyone passed - continue normal play
            self.state.add_observation(
                from_id=ta.GAME_ID,
                to_id=-1,
                message="All players passed. Continuing play."
            )
            self._end_bullshit_phase()
        else:
            # Move to next player who can call
            next_player = self._get_next_player_who_can_call(current_pid)
            self.state.manually_update_current_player(new_player_id=next_player)

    def _end_bullshit_phase(self):
        """End the bullshit phase and return to normal play."""
        gs = self.state.game_state
        gs["bullshit_phase"] = False
        gs["players_who_can_call"] = set()

        # Advance rank for next play
        gs["current_rank"] = gs["current_rank"] + 1 if gs["current_rank"] < 13 else 1

        # Clear last play info
        gs["last_played_cards"] = []
        gs["last_declared_rank"] = None

        # Move to next player in normal turn order
        if gs["last_player"] is not None:
            next_player = (gs["last_player"] + 1) % self.state.num_players
        else:
            next_player = 0
        self.state.manually_update_current_player(new_player_id=next_player)

    def _give_pile_to_player(self, player_id: int):
        """Give all cards in the pile to the specified player."""
        gs = self.state.game_state
        pile_size = len(gs["pile"])
        if pile_size > 0:
            gs["hands"][player_id].extend(gs["pile"])
            gs["pile"].clear()

    def _get_next_player_who_can_call(self, current_player: int) -> int:
        """Find the next player who can still call bullshit."""
        gs = self.state.game_state
        candidates = list(gs["players_who_can_call"])
        if not candidates:
            return current_player

        # Find the next one in turn order
        for i in range(1, self.state.num_players):
            next_pid = (current_player + i) % self.state.num_players
            if next_pid in candidates:
                return next_pid
        return candidates[0]  # Fallback

    def _announce_game_state(self):
        """Send current game state to all players."""
        gs = self.state.game_state
        current_rank_text = self._int_to_rank(gs["current_rank"])

        for pid in range(self.state.num_players):
            hand = gs["hands"][pid]
            indexed_hand = [
                f"{idx}: {card['rank']}{card['suit']}" 
                for idx, card in enumerate(hand)
            ]
            hand_str = ", ".join(indexed_hand) if indexed_hand else "No cards!"

            # Opponent card counts
            opponents_info = []
            for opp_pid in range(self.state.num_players):
                if opp_pid != pid:
                    opponents_info.append(f"Player {opp_pid}: {len(gs['hands'][opp_pid])} cards")

            pile_size = len(gs["pile"])
            phase_text = "Bullshit Calling" if gs["bullshit_phase"] else "Playing Cards"

            message = (
                f"--- BULLSHIT GAME STATUS ---\n"
                f"Phase: {phase_text}\n"
                f"Your Hand ({len(hand)} cards): {hand_str}\n"
                f"Opponents: {', '.join(opponents_info)}\n"
                f"Pile: {pile_size} cards\n"
                f"Current Rank to Claim: {current_rank_text}\n"
            )

            if gs["bullshit_phase"]:
                if pid in gs["players_who_can_call"]:
                    message += "You can call [BULLSHIT] or [PASS].\n"
                else:
                    message += "Waiting for other players to call bullshit...\n"

            self.state.add_observation(
                from_id=ta.GAME_ID, 
                to_id=pid, 
                message=message, 
                for_logging=False
            )

    def _parse_declared_rank(self, rank_str: str) -> Optional[int]:
        """Convert rank string to integer (1-13). Return None if invalid."""
        rank_str = rank_str.upper()
        return self.rank_values.get(rank_str)

    def _int_to_rank(self, val: int) -> str:
        """Convert integer rank (1-13) back to string rank."""
        if 1 <= val <= 13:
            return self.ranks[val - 1]
        return str(val)