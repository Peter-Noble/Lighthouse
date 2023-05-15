import pyspacemouse
import time


def button_0(state, buttons, pressed_buttons):
    print("Button:", pressed_buttons)


def button_0_1(state, buttons, pressed_buttons):
    print("Buttons:", pressed_buttons)


def someButton(state, buttons):
    print("Some button")


def print_state(state):
    """Simple default DoF callback
    Print all axis to output
    """
    if state:
        print(" ".join(["%4s %+.2f" % (k, getattr(state, k)) for k in ["x", "y", "z", "roll", "pitch", "yaw", "t"]]))


def callback():
    button_arr = [
        pyspacemouse.ButtonCallback(0, button_0),
        pyspacemouse.ButtonCallback([1], lambda state, buttons, pressed_buttons: print("Button: 1")),
        pyspacemouse.ButtonCallback([0, 1], button_0_1),
    ]

    success = pyspacemouse.open(dof_callback=print_state, button_callback=someButton, button_callback_arr=button_arr)
    if success:
        while True:
            pyspacemouse.read()
            time.sleep(0.01)


if __name__ == "__main__":
    callback()
