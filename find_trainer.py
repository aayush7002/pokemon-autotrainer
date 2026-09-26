import cv2
import numpy as np
import pyautogui
import time

pyautogui.FAILSAFE = True


# =========================================================
# SETTINGS
# =========================================================

TILE_X = 57
TILE_Y = 57

# Allows some error in the detected sprite center.
TOLERANCE = 15

STEP_TIME = 0.02
STEP_PAUSE = 0.15

# Start here.
# If real bald-trainer matches are below this,
# we can lower it after looking at terminal output.
MATCH_THRESHOLD = 0.50

MAX_CHASE_ATTEMPTS = 20

# How long we wait if we are beside the trainer
# but he is facing the wrong direction.
ADJACENT_WAIT_ATTEMPTS = 30

GAME_ROI = (335, 480, 1710, 853)

game_x, game_y, game_width, game_height = GAME_ROI

player_x = game_width // 2
player_y = game_height // 2

# Known initial direction at Pokemon Center nurse.
facing = "up"


# =========================================================
# BALD TRAINER TEMPLATE FILES
# =========================================================

trainer_template_files = [
    "bald_trainer_front.png",
    "bald_trainer_back.png",
    "bald_trainer_left.png",
    "bald_trainer_right.png"
]


# =========================================================
# KEYBOARD CONTROL
# =========================================================

def press_a():
    pyautogui.keyDown("z")
    time.sleep(0.02)
    pyautogui.keyUp("z")
    time.sleep(0.40)


def press_direction(direction):
    pyautogui.keyDown(direction)
    time.sleep(STEP_TIME)
    pyautogui.keyUp(direction)
    time.sleep(STEP_PAUSE)


def move(direction, steps):
    global facing

    # If changing direction, first input turns the player.
    if direction != facing:
        press_direction(direction)
        facing = direction

    # Move requested number of tiles.
    for _ in range(steps):
        press_direction(direction)


def force_face(direction):
    global facing

    # Always send the direction.
    #
    # When an NPC occupies that adjacent tile,
    # player cannot walk into the NPC and will face them.
    press_direction(direction)

    facing = direction


# =========================================================
# FIXED NAVIGATION
# KEEPING YOUR CURRENT WORKING ROUTE
# =========================================================

def center_to_gym():
    global facing

    # Known start:
    # Pokemon Center nurse desk, facing UP.
    facing = "up"

    print("Leaving Pokemon Center...")

    move("down", 8)

    # Outside map transition.
    time.sleep(2.0)

    print("Walking toward Gym...")

    # KEEPING YOUR CURRENT VALUE OF 5.
    move("left", 5)

    move("up", 1)


def enter_gym():

    print("Entering Gym...")

    move("up", 1)

    # Allow Gym map to load.
    time.sleep(2.5)


def gym_entrance_to_search_area():
    global facing

    # Expected facing direction after Gym entry.
    facing = "up"

    print("Moving through Gym...")

    move("up", 1)

    move("right", 6)

    move("up", 3)

    print("Expected search area reached.")


# =========================================================
# SCREEN CAPTURE
# =========================================================

def get_game_screen():

    screenshot = pyautogui.screenshot()

    screen = np.array(screenshot)

    screen = cv2.cvtColor(
        screen,
        cv2.COLOR_RGB2BGR
    )

    game_screen = screen[
        game_y:game_y + game_height,
        game_x:game_x + game_width
    ]

    return game_screen


# =========================================================
# LOAD TRAINER TEMPLATES ONCE
# =========================================================

def load_template(filename):

    image = cv2.imread(filename)

    if image is None:
        print(f"WARNING: Could not load {filename}")

    return image


templates = {}

for filename in trainer_template_files:

    image = load_template(filename)

    if image is not None:
        templates[filename] = image


# =========================================================
# FIND BEST BALD-TRAINER MATCH
# =========================================================

def find_best_match(game_screen):

    best_confidence = 0.0
    best_location = None
    best_template = None
    best_width = None
    best_height = None


    for filename in trainer_template_files:

        trainer = templates.get(filename)

        if trainer is None:
            continue


        height, width = trainer.shape[:2]


        result = cv2.matchTemplate(
            game_screen,
            trainer,
            cv2.TM_CCOEFF_NORMED
        )


        _, max_val, _, max_loc = cv2.minMaxLoc(result)


        print(
            f"{filename}: "
            f"{max_val:.3f} at {max_loc}"
        )


        if max_val > best_confidence:

            best_confidence = max_val
            best_location = max_loc
            best_template = filename
            best_width = width
            best_height = height


    return (
        best_confidence,
        best_location,
        best_template,
        best_width,
        best_height
    )


# =========================================================
# DETECT BALD TRAINER
# =========================================================

def detect_trainer():

    game_screen = get_game_screen()


    (
        confidence,
        location,
        trainer_template,
        width,
        height
    ) = find_best_match(game_screen)


    if (
        confidence < MATCH_THRESHOLD
        or location is None
        or trainer_template is None
    ):

        return None


    x, y = location


    # Template match gives TOP-LEFT.
    # Convert it to sprite CENTER.
    center_x = x + width // 2
    center_y = y + height // 2


    dx = center_x - player_x
    dy = center_y - player_y


    return {
        "confidence": confidence,
        "template": trainer_template,
        "center_x": center_x,
        "center_y": center_y,
        "dx": dx,
        "dy": dy
    }


# =========================================================
# ADJACENCY
# =========================================================

def adjacent_direction(dx, dy):

    # -----------------------------------------
    # Trainer directly ABOVE or BELOW
    # -----------------------------------------

    if (
        abs(dx) < TOLERANCE
        and
        abs(abs(dy) - TILE_Y) < TOLERANCE
    ):

        if dy < 0:
            return "up"

        return "down"


    # -----------------------------------------
    # Trainer directly LEFT or RIGHT
    # -----------------------------------------

    if (
        abs(dy) < TOLERANCE
        and
        abs(abs(dx) - TILE_X) < TOLERANCE
    ):

        if dx < 0:
            return "left"

        return "right"


    return None


# =========================================================
# IS TRAINER FACING PLAYER?
# =========================================================

def trainer_faces_player(
    trainer_template,
    player_direction_to_trainer
):

    # Example:
    #
    # Trainer is LEFT of player.
    #
    # Player needs to face LEFT.
    # Trainer needs to face RIGHT.
    #
    # Therefore:
    #
    # "left" -> bald_trainer_right.png


    required_template = {

        # Trainer is ABOVE player.
        # Trainer must face DOWN.
        "up": "bald_trainer_front.png",

        # Trainer is BELOW player.
        # Trainer must face UP.
        "down": "bald_trainer_back.png",

        # Trainer is LEFT of player.
        # Trainer must face RIGHT.
        "left": "bald_trainer_right.png",

        # Trainer is RIGHT of player.
        # Trainer must face LEFT.
        "right": "bald_trainer_left.png"
    }


    return (
        trainer_template
        ==
        required_template[player_direction_to_trainer]
    )


# =========================================================
# SPECIAL MOVEMENT FOR BALD TRAINER
# =========================================================

def movement_direction(dx, dy):

    # =====================================================
    # IMPORTANT DIFFERENCE FROM BLOND TRAINER:
    #
    # Bald trainer mainly patrols vertically.
    #
    # We want our player to stay approximately
    # ONE TILE TO THE RIGHT of him.
    #
    # Therefore our preferred relationship is:
    #
    # dx = trainer_x - player_x
    #
    # dx ≈ -57
    #
    # Trainer:
    #       T   P
    #
    # After horizontal alignment is correct,
    # we chase him vertically.
    # =====================================================


    target_dx = -TILE_X


    horizontal_error = dx - target_dx


    # -----------------------------------------
    # First establish correct horizontal column.
    # -----------------------------------------

    if horizontal_error < -TOLERANCE:

        # Trainer is too far LEFT of us.
        # Player should move LEFT.
        return "left"


    if horizontal_error > TOLERANCE:

        # Trainer is not far enough LEFT.
        # Player should move RIGHT.
        return "right"


    # -----------------------------------------
    # Horizontal relationship is good.
    #
    # Now follow trainer vertically.
    # -----------------------------------------

    if dy < 0:
        return "up"

    return "down"


# =========================================================
# WAIT FOR ADJACENT TRAINER TO FACE US
# =========================================================

def wait_for_trainer_to_face_us():

    print(
        "\nPlayer is adjacent."
    )

    print(
        "Staying still while waiting "
        "for bald trainer to face player..."
    )


    for check in range(ADJACENT_WAIT_ATTEMPTS):

        time.sleep(0.10)


        detection = detect_trainer()


        if detection is None:

            print(
                "Lost trainer while waiting."
            )

            return False


        dx = detection["dx"]
        dy = detection["dy"]


        direction = adjacent_direction(
            dx,
            dy
        )


        # -----------------------------------------
        # Trainer moved away.
        # Resume chase.
        # -----------------------------------------

        if direction is None:

            print(
                "Trainer moved away. "
                "Resuming chase."
            )

            return False


        print(
            f"Wait {check + 1}: "
            f"adjacent {direction.upper()} | "
            f"{detection['template']} | "
            f"dx={dx}, dy={dy}"
        )


        # -----------------------------------------
        # Did trainer turn toward us?
        # -----------------------------------------

        if trainer_faces_player(
            detection["template"],
            direction
        ):

            print(
                "Trainer is now facing player!"
            )


            # Ensure player is also facing trainer.
            force_face(direction)


            # Tiny pause.
            time.sleep(0.10)


            # -------------------------------------
            # One final confirmation.
            # -------------------------------------

            final_detection = detect_trainer()


            if final_detection is None:

                print(
                    "Trainer disappeared before Z."
                )

                return False


            final_direction = adjacent_direction(
                final_detection["dx"],
                final_detection["dy"]
            )


            if final_direction is None:

                print(
                    "Trainer moved before interaction."
                )

                return False


            if not trainer_faces_player(
                final_detection["template"],
                final_direction
            ):

                print(
                    "Trainer turned away before interaction."
                )

                return False


            print(
                "Both are facing each other."
            )

            print(
                "Pressing Z..."
            )


            press_a()


            return True


    print(
        "Trainer stayed adjacent but did not "
        "face player in time."
    )


    return False


# =========================================================
# HANDLE ADJACENT TRAINER
# =========================================================

def handle_adjacent_trainer(detection):

    dx = detection["dx"]
    dy = detection["dy"]


    direction = adjacent_direction(
        dx,
        dy
    )


    if direction is None:
        return False


    print(
        f"\nTrainer appears adjacent "
        f"{direction.upper()}."
    )


    # -----------------------------------------------------
    # FIRST take another screenshot.
    #
    # Do not act based on stale trainer position.
    # -----------------------------------------------------

    time.sleep(0.05)


    confirmation = detect_trainer()


    if confirmation is None:

        print(
            "Trainer disappeared during confirmation."
        )

        return False


    confirmed_direction = adjacent_direction(
        confirmation["dx"],
        confirmation["dy"]
    )


    if confirmed_direction is None:

        print(
            "Trainer moved before adjacency confirmation."
        )

        return False


    # -----------------------------------------------------
    # Ensure player faces trainer.
    # -----------------------------------------------------

    force_face(confirmed_direction)


    time.sleep(0.10)


    # -----------------------------------------------------
    # Check trainer again.
    # -----------------------------------------------------

    confirmation = detect_trainer()


    if confirmation is None:

        return False


    confirmed_direction = adjacent_direction(
        confirmation["dx"],
        confirmation["dy"]
    )


    if confirmed_direction is None:

        print(
            "Trainer moved away after player turned."
        )

        return False


    # -----------------------------------------------------
    # Trainer already facing us?
    # -----------------------------------------------------

    if trainer_faces_player(
        confirmation["template"],
        confirmed_direction
    ):

        print(
            "Trainer is already facing player!"
        )


        # Final tiny confirmation.
        time.sleep(0.05)


        final_detection = detect_trainer()


        if final_detection is None:

            return False


        final_direction = adjacent_direction(
            final_detection["dx"],
            final_detection["dy"]
        )


        if (
            final_direction is not None
            and trainer_faces_player(
                final_detection["template"],
                final_direction
            )
        ):

            print(
                "Both players aligned."
            )

            print(
                "Pressing Z..."
            )

            press_a()

            return True


        return False


    # -----------------------------------------------------
    # Trainer is adjacent but looking elsewhere.
    #
    # PLAYER SHOULD NOT MOVE.
    # -----------------------------------------------------

    return wait_for_trainer_to_face_us()


# =========================================================
# CHASE BALD TRAINER
# =========================================================

def chase_trainer():

    for attempt in range(
        MAX_CHASE_ATTEMPTS
    ):

        print(
            f"\n"
            f"===================================="
        )

        print(
            f"CHASE ATTEMPT {attempt + 1}"
        )

        print(
            f"===================================="
        )


        detection = detect_trainer()


        # -------------------------------------------------
        # TRAINER NOT FOUND
        # -------------------------------------------------

        if detection is None:

            print(
                "Bald trainer not found."
            )

            # Don't immediately quit.
            #
            # He may currently be moving between
            # animation frames.
            time.sleep(0.25)

            continue


        dx = detection["dx"]
        dy = detection["dy"]


        print(
            f"Confidence: "
            f"{detection['confidence']:.3f}"
        )


        print(
            f"Trainer sprite: "
            f"{detection['template']}"
        )


        print(
            f"Player: "
            f"({player_x}, {player_y})"
        )


        print(
            f"Trainer: "
            f"({detection['center_x']}, "
            f"{detection['center_y']})"
        )


        print(
            f"dx = {dx}, dy = {dy}"
        )


        # -------------------------------------------------
        # FIRST: CHECK ADJACENCY
        # -------------------------------------------------

        direction = adjacent_direction(
            dx,
            dy
        )


        if direction is not None:

            if handle_adjacent_trainer(
                detection
            ):

                return True


            # Trainer moved/turned/etc.
            #
            # Go back to top and take
            # a completely fresh screenshot.
            continue


        # -------------------------------------------------
        # NOT ADJACENT:
        # MOVE EXACTLY ONE TILE
        # -------------------------------------------------

        direction = movement_direction(
            dx,
            dy
        )


        print(
            f"Moving one tile "
            f"{direction.upper()}"
        )


        move(
            direction,
            1
        )


        # Allow player movement to complete.
        time.sleep(0.30)


    return False


# =========================================================
# MAIN PROGRAM
# =========================================================

print(
    "Starting in 5 seconds..."
)

print(
    "Click inside the Pokemon emulator "
    "during the countdown."
)

print(
    "Move mouse to the TOP-LEFT corner "
    "for emergency stop."
)

time.sleep(5)


# =========================================================
# 1. POKEMON CENTER -> GYM
# =========================================================

center_to_gym()


# =========================================================
# 2. ENTER GYM
# =========================================================

enter_gym()


# =========================================================
# 3. GYM -> SEARCH AREA
# =========================================================

gym_entrance_to_search_area()


print(
    f"Player screen position: "
    f"({player_x}, {player_y})"
)


# =========================================================
# 4. CHASE BALD TRAINER
# =========================================================

interaction_attempted = chase_trainer()


# =========================================================
# 5. RESULT
# =========================================================

if interaction_attempted:

    print(
        "\nTrainer interaction completed."
    )


else:

    print(
        "\nCould not interact with bald trainer "
        "within chase limit."
    )
