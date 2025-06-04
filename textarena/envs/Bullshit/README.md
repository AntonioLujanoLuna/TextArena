# Bullshit Environment Documentation

## Overview
**Bullshit** (also known as Cheat or I Doubt It) is a classic multi-player card game where players attempt to get rid of all their cards by playing them face-down while claiming they are of a specific rank. Other players can challenge these claims by calling "Bullshit" if they suspect the player is lying. The first player to successfully discard all their cards wins the game.

## Action Space

- **Format:** Actions are strings representing the player's choice during different game phases.

### Playing Phase Actions:
- **Format:** `[rank card_indices]` where rank is the claimed rank and card_indices are space-separated indexes
- **Examples:**
  - Play cards at indexes 0 and 2, claiming they are Aces: `[A 0 2]`
  - Play cards at indexes 1, 3, and 5, claiming they are Kings: `[K 1 3 5]`
  - Play single card at index 0, claiming it's a 7: `[7 0]`

### Bullshit Calling Phase Actions:
- **Call Bullshit:** `[BULLSHIT]` - Challenge the previous player's claim
- **Pass:** `[PASS]` - Decline to challenge the previous play

- **Notes:** Players can include additional text before or after the action tokens. Card indices correspond to the numbered positions shown in the player's hand.

## Observation Space

### Reset Observations
On reset, each player receives a prompt containing the game rules and their initial hand:

```plaintext
Welcome to Bullshit! You are Player 0.

OBJECTIVE:
  Be the first to get rid of all your cards.

GAME FLOW:
  1. Players take turns playing 1 or more cards face down.
  2. You must CLAIM these cards are of the current rank.
  3. The current rank starts at A (Ace) and increments: A, 2, 3, ..., K, then back to A.
  4. After a player plays, others may call [BULLSHIT] if they think you're lying.
  5. If you lied, you pick up the whole pile.
  6. If you told the truth, the accuser picks up the pile.
  7. The first player to have no cards left wins!

ACTIONS:
  [A 0 2]        => 'I claim these 2 cards are Aces', using card indexes 0 and 2 from my hand.
  [BULLSHIT]     => Call bullshit on the previous play.
  [PASS]         => Decline to call bullshit.

Your hand will be shown as numbered cards. Use the indexes to specify which cards to play.
Good luck!
```

### Step Observations
During gameplay, players receive updates about:
- Their current hand with card indices
- Other players' card counts
- Current rank to claim
- Pile size
- Game phase (playing vs. bullshit calling)

Example observation:
```plaintext
--- BULLSHIT GAME STATUS ---
Phase: Playing Cards
Your Hand (7 cards): 0: A♠, 1: 3♥, 2: 7♦, 3: K♣, 4: 2♠, 5: Q♥, 6: 9♦
Opponents: Player 1: 6 cards, Player 2: 8 cards
Pile: 12 cards
Current Rank to Claim: 5
```

## Gameplay

- **Players:** 2-8 players
- **Initial Setup:** Standard 52-card deck is shuffled and dealt evenly among players
- **Turn Structure:** Players take turns in order, with each turn consisting of:
  1. **Playing Phase:** Current player plays 1+ cards claiming they match the current rank
  2. **Bullshit Phase:** Other players may call bullshit or pass
- **Rank Progression:** Current rank starts at Ace and progresses: A → 2 → 3 → ... → K → A (cyclical)
- **Objective:** Be the first player to discard all cards

## Key Rules

1. **Playing Cards:**
   - Players must play at least 1 card on their turn
   - Cards are played face-down and claimed to be of the current rank
   - Players can play any cards from their hand regardless of actual rank
   - After playing, the current rank advances to the next rank

2. **Bullshit Calling:**
   - After any play, other players can call "Bullshit" if they suspect lying
   - If called and the player was lying: the player who played picks up the entire pile
   - If called and the player was honest: the caller picks up the entire pile
   - If no one calls bullshit, play continues normally

3. **Valid Moves:**
   - During playing phase: `[rank card_indices]` where rank matches current rank
   - During bullshit phase: `[BULLSHIT]` to call or `[PASS]` to decline
   - Card indices must be valid positions in the player's hand

4. **Winning Conditions:**
   - **Win:** First player to have zero cards remaining
   - **Invalid Move:** Player makes an incorrectly formatted action or uses invalid card indices

5. **Game Termination:**
   - Game ends immediately when any player discards their last card(s)
   - Maximum turn limit prevents infinite games

## Rewards

| Outcome          | Reward for Winner | Reward for Others |
|------------------|:-----------------:|:-----------------:|
| **Win**          | `+1`              | `-1`              |
| **Invalid Move** | `-1`              | `0`               |
| **Turn Limit**   | `0`               | `0`               |

## Parameters

- `max_turns` (`int`):
    - **Description:** Maximum number of turns before the game ends in a draw
    - **Default:** 200
    - **Impact:** Prevents games from running indefinitely; higher values allow longer games

## Variants

| Env-id                | max_turns |
|-----------------------|:---------:|
| `Bullshit-v0`         | `200`     |
| `Bullshit-v0-long`    | `500`     |
| `Bullshit-v0-short`   | `100`     |

## Strategic Considerations

1. **Bluffing vs. Truth:** Players must balance between lying to get rid of unwanted cards and telling the truth to avoid being caught
2. **Observation:** Tracking what ranks have been played can help identify likely lies
3. **Risk Assessment:** Calling bullshit carries risk - wrong calls result in taking the pile
4. **Card Management:** Strategic timing of when to play multiple cards vs. single cards
5. **Pile Size:** Larger piles make the penalty for being caught more severe

## Example Usage

```python
import textarena as ta

# Initialize agents
agents = {
    0: ta.agents.OpenRouterAgent(model_name="gpt-4o"),
    1: ta.agents.OpenRouterAgent(model_name="anthropic/claude-3.5-sonnet"),
    2: ta.agents.OpenRouterAgent(model_name="meta-llama/llama-3.3-70b-instruct"),
}

# Initialize environment
env = ta.make("Bullshit-v0")
env = ta.wrappers.LLMObservationWrapper(env=env)
env = ta.wrappers.SimpleRenderWrapper(
    env=env,
    player_names={0: "GPT-4o", 1: "Claude", 2: "Llama"},
)

# Reset and play
env.reset(num_players=3)
done = False
while not done:
    player_id, observation = env.get_observation()
    action = agents[player_id](observation)
    done, info = env.step(action=action)

rewards = env.close()
```

## Troubleshooting

- **Invalid Card Index:** Ensure card indices correspond to positions shown in your hand (0-based indexing)
- **Wrong Rank:** During playing phase, you must claim cards match the current rank exactly
- **Phase Confusion:** Pay attention to whether you're in playing phase or bullshit calling phase
- **Multiple Actions:** Only one action per turn - either play cards OR call bullshit/pass

### Contact
If you have questions or face issues with this specific environment, please reach out directly to the TextArena team or to `a00lujano@gmail.com`.