import shlex
import subprocess

from latch_lock.keyboard import Keyboard
from latch_lock.load import CommandNode, Load, ModeNode
from latch_lock.mode import Mode
from latch_lock.show import Client


def aliases(key):
    if key == "Shift":
        return ["Shift_L", "Shift_R"]
    return [key]


def unalias(key):
    if key == "Shift_L":
        return "Shift"
    if key == "Shift_R":
        return "Shift"
    return key


class State:
    END = "Escape"
    BACK = "BackSpace"
    path = []
    expect = {}

    def __init__(self, client, keyboard, root, mode):
        self.client = client
        self.keyboard = keyboard
        self.root = root
        self.mode = mode
        self.reset()

    def reset(self):
        self.mode.clear()
        self.grab_keys()

    def active_node(self):
        node = self.root
        for key, state in self.mode.stack:
            for child in node.children:
                if type(child) is ModeNode and child.key == key:
                    node = child
        return node

    def grab_keys(self):
        self.keyboard.flush()
        self.expect.clear()
        if self.mode.stack:
            self.expect[self.END] = None
            self.expect[self.BACK] = None

        active = self.active_node()

        # add active node's children to expected keys
        for node in active.children:
            for key in aliases(node.key):
                self.expect[key] = node

        # add active node and it's ancestors to expected keys
        while True:
            for key in aliases(active.key):
                self.expect[key] = active
            if not active.parent:
                break
            active = active.parent

        # grab expected keys
        self.keyboard.grab(self.expect.keys())

    def show_menu(self):
        show = {}
        for node in self.active_node().children:
            if type(node) is ModeNode:
                show[node.key] = f"+{node.name} ({len(node.children)})"
            elif type(node) is CommandNode:
                show[node.key] = f"{node.command} ({node.flags})"

        if self.mode.stack:
            self.client.send("show", show)
        else:
            self.client.send("hide")

    def press(self, key):
        self.mode.press(unalias(key))
        print(self.mode.stack)
        self.grab_keys()
        self.show_menu()

    def release(self, key):
        self.mode.release(unalias(key))
        print(self.mode.stack)
        self.grab_keys()
        self.show_menu()

    def special(self, key):
        if key == self.END:
            self.mode.clear()
        elif key == self.BACK:
            self.mode.pop()
        print(self.mode.stack)
        self.grab_keys()
        self.show_menu()

    def command(self, key):
        for child in self.active_node().children:
            if type(child) is CommandNode and child.key == key:
                self.mode.command()
                print(self.mode.stack)
                self.grab_keys()
                self.show_menu()
                if child.command:
                    cmd = shlex.split(child.command)
                    try:
                        subprocess.Popen(cmd, close_fds=True, start_new_session=True)
                    except Exception as e:
                        print(e)
                break


def main():
    client = Client()
    keyboard = Keyboard()
    root = Load("/home/pedro/fun/latch-lock/actions.yml").root
    mode = Mode()
    state = State(client, keyboard, root, mode)

    def press(name):
        print("press", name)
        node = state.expect[name]
        if type(node) is ModeNode:
            state.press(name)
        elif type(node) is CommandNode:
            state.command(name)
        elif node is None:
            state.special(name)

    def release(name):
        print("release", name)
        node = state.expect[name]
        if type(node) is ModeNode:
            state.release(name)

    keyboard.loop(press, release)

    client.send("hide")


if __name__ == "__main__":
    main()
