import yaml
from anytree import Node, NodeMixin, PreOrderIter, RenderTree, search


def transform(s):
    if len(s) == 1 and s.isupper():
        return ["Shift", s.lower()]
    else:
        return [s]


def flatten(l):
    return [item for sublist in l for item in sublist]


class Command:
    key: str
    command: str | None = None
    flags: str | None = None

    def setCommand(self, command):
        words = command.split()
        first_nonflag = words.index(
            next(filter(lambda x: not x.startswith("--"), words))
        )
        self.command = " ".join(words[first_nonflag:])
        self.flags = " ".join(words[:first_nonflag])

    def __repr__(self):
        return f"Command {self.key}: {self.flags} {self.command}"


class Mode:
    key: str
    name: str | None = None

    def __repr__(self):
        return f"Mode {self.key}: {self.name}"


class CommandNode(Command, NodeMixin):
    def __init__(self, key, command, parent=None, children=None):
        super().__init__()
        self.key = key
        self.setCommand(command)
        self.parent = parent
        if children:
            self.children = children


class ModeNode(Mode, NodeMixin):
    def __init__(self, key, name=None, parent=None, children=None):
        super().__init__()
        self.key = key
        self.name = name
        self.parent = parent
        if children:
            self.children = children


class Load:
    root = None

    def __init__(self, fn):
        self.root = ModeNode("default", "default")
        with open(fn) as f:
            commands = yaml.safe_load(f)
        self.load(commands)

    def load(self, commands):
        for path_str, cmd in reversed(commands.items()):
            path = flatten(map(transform, path_str.split()))
            # path = path_str.split()
            # print(path, cmd)
            parent = self.root
            for mode in path[:-1]:
                mnode = search.find_by_attr(parent, mode, "key", 2)
                if not mnode:
                    mnode = ModeNode(mode, parent=parent)
                parent = mnode

            node = search.find_by_attr(parent, path[-1], "key", 2)
            if node and type(node) is ModeNode:
                # set mode name
                node.name = cmd[6:-1]
            elif not node:
                node = CommandNode(path.pop(), cmd, parent=parent)
            else:
                # command already exists
                pass

        # print(RenderTree(self.root))
