#!/usr/bin/env python3
import time
import sys
import os
import json
import random
from pathlib import Path

SAVE_FILE = Path.home() / ".buddy_save.json"

BUDDY_FRAMES = {
    "happy": [
        r"""
    / \__
   (    @\___
   /         O
  /   (_____/
 /_____/   U
""",
        r"""
    / \__
   (    @\___
   /         O
  /   (_____/
 /_____/   U  ~
""",
    ],
    "sleeping": [
        r"""
    / \__
   (    -\___
   /         O
  /   (_____/
 /_____/   U  zzz
""",
    ],
    "hungry": [
        r"""
    / \__
   (    >\___
   /         O
  /   (_____/
 /_____/   U  ...
""",
    ],
    "excited": [
        r"""
    / \__
   (    ^o^\___
   /           O
  /   (_______/
 /_____/   U  !!!
""",
        r"""
   \__ /
___/^o^    )
O           \
 \_______/   \
          U___\  !!!
""",
    ],
    "sad": [
        r"""
    / \__
   (    T\___
   /         O
  /   (_____/
 /_____/   U  ...
""",
    ],
}

COLORS = {
    "reset": "\033[0m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "green": "\033[92m",
    "red": "\033[91m",
    "magenta": "\033[95m",
    "blue": "\033[94m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}

def color(text, *codes):
    return "".join(COLORS[c] for c in codes) + text + COLORS["reset"]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def load_state():
    if SAVE_FILE.exists():
        try:
            return json.loads(SAVE_FILE.read_text())
        except Exception:
            pass
    return {
        "name": "Buddy",
        "hunger": 80,
        "happiness": 80,
        "energy": 80,
        "age_days": 0,
        "tricks": [],
        "last_seen": time.time(),
    }

def save_state(state):
    SAVE_FILE.write_text(json.dumps(state, indent=2))

def apply_time_decay(state):
    elapsed = time.time() - state.get("last_seen", time.time())
    hours = elapsed / 3600
    state["hunger"] = max(0, state["hunger"] - hours * 5)
    state["happiness"] = max(0, state["happiness"] - hours * 3)
    state["energy"] = min(100, state["energy"] + hours * 4)
    state["age_days"] = state.get("age_days", 0) + elapsed / 86400
    state["last_seen"] = time.time()
    return state

def get_mood(state):
    if state["energy"] < 20:
        return "sleeping"
    if state["hunger"] < 30:
        return "hungry"
    if state["happiness"] > 85:
        return "excited"
    if state["happiness"] < 40:
        return "sad"
    return "happy"

def stat_bar(value, width=20):
    filled = int(value / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    if value > 60:
        return color(bar, "green")
    elif value > 30:
        return color(bar, "yellow")
    else:
        return color(bar, "red")

def draw_buddy(state, message=""):
    clear()
    mood = get_mood(state)
    frames = BUDDY_FRAMES[mood]
    frame = frames[int(time.time() * 2) % len(frames)]

    age = state["age_days"]
    age_str = f"{age:.1f} days old"

    print(color("╔══════════════════════════════════════╗", "cyan"))
    print(color(f"║  🐾  {state['name'].center(28)}  🐾  ║", "cyan", "bold"))
    print(color("╚══════════════════════════════════════╝", "cyan"))
    print()
    print(color(frame, "yellow"))
    print()
    print(color(f"  Mood: {mood.upper():<12}", "magenta", "bold") +
          color(f"  Age: {age_str}", "dim"))
    print()
    print(f"  🍖 Hunger    {stat_bar(state['hunger'])} {state['hunger']:.0f}%")
    print(f"  💛 Happiness {stat_bar(state['happiness'])} {state['happiness']:.0f}%")
    print(f"  ⚡ Energy    {stat_bar(state['energy'])} {state['energy']:.0f}%")
    print()

    if state["tricks"]:
        print(color(f"  🎓 Tricks: ", "blue") + ", ".join(state["tricks"]))
        print()

    if message:
        print(color(f"  💬 {message}", "green", "bold"))
        print()

    print(color("  Commands: ", "bold") +
          "[f]eed  [p]lay  [s]leep  [t]rain  [r]ename  [q]uit")
    print()

def feed(state):
    if state["hunger"] >= 95:
        return "Buddy is already full and turns away the food!"
    state["hunger"] = min(100, state["hunger"] + 30)
    state["happiness"] = min(100, state["happiness"] + 5)
    sounds = ["Woof! Nom nom nom!", "Chomp chomp! Delicious!", "Tail wagging intensifies!"]
    return random.choice(sounds)

def play(state):
    if state["energy"] < 20:
        return "Buddy is too tired to play right now. Let them sleep!"
    state["happiness"] = min(100, state["happiness"] + 25)
    state["energy"] = max(0, state["energy"] - 20)
    state["hunger"] = max(0, state["hunger"] - 10)
    sounds = ["WOOF WOOF! FETCH!", "Buddy zooms around the room!", "Belly rubs accepted!"]
    return random.choice(sounds)

def sleep(state):
    state["energy"] = min(100, state["energy"] + 40)
    state["happiness"] = min(100, state["happiness"] + 5)
    return "Buddy curls up and snoozes... zzz"

def train(state):
    known = set(state.get("tricks", []))
    all_tricks = ["sit", "shake", "roll over", "speak", "fetch", "spin", "high five", "play dead"]
    unknown = [t for t in all_tricks if t not in known]
    if not unknown:
        return "Buddy already knows every trick! What a genius dog!"
    if state["energy"] < 30:
        return "Buddy is too tired to learn right now."
    trick = random.choice(unknown)
    state["tricks"] = list(known | {trick})
    state["energy"] = max(0, state["energy"] - 15)
    state["happiness"] = min(100, state["happiness"] + 10)
    return f'Buddy learned "{trick}"! 🎉'

def rename(state):
    print(color(f"\n  Current name: {state['name']}", "cyan"))
    new_name = input(color("  New name: ", "bold")).strip()
    if new_name:
        old = state["name"]
        state["name"] = new_name
        return f"{old} is now called {new_name}!"
    return "Name unchanged."

def intro_animation():
    clear()
    print()
    lines = [
        color("  ✨ You discovered the Easter Egg! ✨", "yellow", "bold"),
        "",
        color("  Meet your virtual pet...", "cyan"),
    ]
    for line in lines:
        print(line)
        time.sleep(0.4)

    time.sleep(0.3)
    for i, char in enumerate("  🐾 B U D D Y 🐾"):
        print(f"\r  🐾 {'B U D D Y 🐾'[:i+1]}", end="", flush=True)
        time.sleep(0.07)
    print()
    time.sleep(0.8)

def main():
    intro_animation()
    state = load_state()
    state = apply_time_decay(state)
    message = f"Woof! {state['name']} is happy to see you!"

    while True:
        draw_buddy(state, message)
        message = ""
        try:
            cmd = input("  > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(color("\n\n  Goodbye! Buddy will miss you! 🐾\n", "yellow", "bold"))
            save_state(state)
            break

        if cmd in ("f", "feed"):
            message = feed(state)
        elif cmd in ("p", "play"):
            message = play(state)
        elif cmd in ("s", "sleep"):
            message = sleep(state)
        elif cmd in ("t", "train"):
            message = train(state)
        elif cmd in ("r", "rename"):
            message = rename(state)
        elif cmd in ("q", "quit", "exit"):
            print(color("\n  Goodbye! Buddy will miss you! 🐾\n", "yellow", "bold"))
            save_state(state)
            break
        else:
            message = "Buddy tilts his head... (unknown command)"

        save_state(state)

if __name__ == "__main__":
    main()
