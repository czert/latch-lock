import signal
import sys

from Xlib import XK, X
from Xlib.display import Display


class Keyboard:
    def __init__(self, alarm=None):
        self.display = Display()
        self.root = self.display.screen().root
        self.root.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
        self.keys = {}

        if alarm:
            signal.signal(signal.SIGALRM, lambda a, b: sys.exit(1))
            signal.alarm(alarm)

    def grab(self, keys):
        for key in keys:
            keysym = XK.string_to_keysym(key)
            if not keysym:
                # print(f'Bad keyname: "{key}"')
                continue
            keycode = self.display.keysym_to_keycode(keysym)
            self.keys[keycode] = key
            # print("Grabbing ", key, keysym, keycode)
            self.root.grab_key(keycode, 0, False, X.GrabModeSync, X.GrabModeAsync)

    def flush(self):
        for keycode in self.keys.keys():
            # print("Releasing ", self.keys[keycode])
            self.root.ungrab_key(keycode, X.AnyModifier)
        self.keys.clear()

    def loop(self, handle_press, handle_release):
        keys_pressed = 0  # https://stackoverflow.com/questions/18160792/python-xlib-xgrabkey-keyrelease-events-not-firing

        while True:
            event = self.display.next_event()
            if event.type == X.MappingNotify:
                continue

            if event.type == X.KeyPress:
                keys_pressed += 1
            elif event.type == X.KeyRelease:
                if keys_pressed == 0:
                    # print("Unexpected key release: ", event)
                    continue  # ignore a superfluous key release
                keys_pressed -= 1

            if keys_pressed == 0:
                self.display.flush()
                self.display.ungrab_keyboard(X.CurrentTime)
            else:
                self.root.grab_keyboard(
                    False, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime
                )

            if event.detail not in self.keys:
                # print("Unexpected key event: ", event)
                continue

            if event.type == X.KeyPress:
                handle_release(self.keys[event.detail])
            elif event.type == X.KeyRelease:
                handle_press(self.keys[event.detail])
