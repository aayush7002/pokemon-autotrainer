import pyautogui
import time

step_time = 0.02
step_pause = 0.15
facing = "down"

def press_a():
    pyautogui.keyDown("z")
    time.sleep(0.02)
    pyautogui.keyUp("z")
    time.sleep(0.3)

def press_direction(direction):
    pyautogui.keyDown(direction)
    time.sleep(step_time)
    pyautogui.keyUp(direction)
    time.sleep(step_pause)

def move(direction, steps):
    global facing

    if direction != facing:
        press_direction(direction)
        facing = direction

    for step in range(steps):
        press_direction(direction)

def center_to_gym():
	global facing
	facing = "up"

	move("down", 8)
	time.sleep(1)
	move("left", 7)
	move("up", 1)

def gym_entrance_to_trainer():
	global facing
	facing = "up"

	move("up", 1)
	time.sleep(2)
	move("up", 1)
	move("left", 3)
	move("up", 2)
	press_a()
	move("up", 7)

print("Starting in 5 seconds...")
time.sleep(5)
center_to_gym()		
gym_entrance_to_trainer()	


