# Pokémon Auto-Trainer

A Python bot that plays Pokémon Unbound by reading the screen and pressing keys, with no access to the game's memory.

**Status:** In progress

## What it does

1. **Navigates** from the Pokémon Center, through town, and into the Gym using timed keyboard inputs, waiting out map-loading transitions.
2. **Finds a moving trainer** by capturing the emulator screen and running OpenCV template matching against his four directional sprites.
3. **Chases him on the tile grid**, converting pixel offsets into tile moves one step at a time.
4. **Starts the battle** only after re-checking fresh frames that the trainer is adjacent and facing the player.

## Setup

```
pip install opencv-python pyautogui numpy
```

## Usage

1. Open Pokémon Unbound in an emulator and stand at the Pokémon Center nurse, facing up.
2. Run:
   ```
   python find_trainer.py
   ```
3. Click inside the emulator window during the 5-second countdown.

To stop the bot at any time, move your mouse to the top-left corner of the screen.

## Files

- `find_trainer.py`: main bot (navigation, detection, chase, interaction)
- `test_control.py`: early movement test
- `bald_trainer_*.png`: sprite templates used for detection

## Next steps

- [add what you're working on next]
