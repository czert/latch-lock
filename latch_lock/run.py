from latch_lock.keyboard import Keyboard
from latch_lock.load import CommandNode, Load, ModeNode
from latch_lock.show import Client


class State:
    path = []
    expect = {}

    def __init__(self, client, keyboard, root):
        self.client = client
        self.keyboard = keyboard
        self.root = root
        self.reset()

    def reset(self):
        self.path.clear()
        self.mode(self.root)

    def mode(self, node):
        self.keyboard.flush()
        self.expect.clear()
        self.path.append(node)

        show = {}

        for node in self.path[-1].children:
            self.expect[node.key] = node
            if type(node) is ModeNode:
                show[node.key] = f"+{node.name} ({len(node.children)})"
            elif type(node) is CommandNode:
                show[node.key] = f"{node.command} ({node.flags})"

        if self.path[-1] is self.root:
            self.client.send("hide")
        else:
            self.client.send("show", show)

        self.keyboard.grab(self.expect.keys())


def main():
    client = Client()
    keyboard = Keyboard()
    root = Load("./actions.yml").root
    state = State(client, keyboard, root)

    def handler(name, event):
        # print("Handling: ", name, event)

        if event.type == 3:
            return

        if name not in state.expect:
            return

        node = state.expect[name]
        if type(node) is ModeNode:
            state.mode(node)
        elif type(node) is CommandNode:
            print(node.command)
            state.reset()

    keyboard.loop(handler)

    client.send("hide")


if __name__ == "__main__":
    main()
