# echo 'exit' | cat - tmp/payl | socat unix-connect:/tmp/.latch-lock.sock STDIO

import json
import os
import re
import socket
import sys
import tkinter as tk

from columnify import columnify

TICK = 50  # socket update interfal [ms]
CHUNK = 4096  # socket read bytes
SOCKET_PATH = "/tmp/.latch-lock.sock"


class Show:
    def __init__(self):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(SOCKET_PATH)
        self.socket.listen(1)
        self.buffer = ""

    def start(self):
        self.root = tk.Tk()
        self.root.title("latch-lock show")
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        self.labelvar = tk.StringVar()
        # self.labelvar.set("\n[startup]\n")
        label = tk.Label(
            self.root,
            textvariable=self.labelvar,
            **{
                "justify": "left",
                "font": ("Droid Sans Mono Slashed for Powerline", 16),
                "bg": "black",
                "fg": "white",
            },
        )
        label.grid(sticky=tk.NW, column=0, row=0, padx=0, pady=0)

        self.update()
        self.root.withdraw()

        self.root.after(TICK, self.receive)
        self.root.mainloop()

    def parse_message(self, msg):
        m = re.match(r"\s*(\w+)", msg)
        if not m:
            return None, None
        command = m.groups()[0]
        payload = msg[m.end() :]
        if not payload:
            return command, None
        return command, json.loads(payload)

    def columns(self, data, width):
        items = [f"{key: <10}  {value}" for key, value in data.items()]
        return columnify(items, width)

    def dispatch(self, msg):
        # print(">>>", msg, "<<<")
        cmd, payload = self.parse_message(msg)
        # print("!!!", cmd, payload, "!!!")
        if cmd == "exit":
            self.root.quit()
            self.root.deletefilehandler(self.socket)
            sys.exit(0)
        elif cmd == "hide":
            self.root.withdraw()
        elif cmd == "show":
            self.root.deiconify()
            if payload:
                self.labelvar.set(self.columns(payload, 300))
                self.update()
        else:
            self.root.deiconify()
            self.labelvar.set("Unknown command: " + repr(cmd))
            self.update()

    def receive(self):
        self.conn, _ = self.socket.accept()
        # self.conn.setblocking(0)

        while True:
            try:
                data = self.conn.recv(CHUNK).decode("utf-8")
            except:  # BlockingIOError, but this is system-dependent
                break
            if not data:
                break
            self.buffer += data
            # print(repr(self.buffer))

            while "\n\n" in self.buffer:
                pos = self.buffer.find("\n\n")
                msg = self.buffer[:pos]
                self.buffer = self.buffer[pos + 2 :]
                self.dispatch(msg)

        self.root.after(TICK, self.receive)

    def update(self):
        self.root.update()
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_reqheight()
        b = 30
        self.root.geometry(f"{w}x{h}+0-{b}")
        self.root.update()


class Client:
    def __init__(self, socket_path=None):
        if socket_path is None:
            socket_path = SOCKET_PATH
        self.client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.client.connect(socket_path)

    def send(self, cmd, payload=None):
        if payload:
            self.client.sendall(f"{cmd} {json.dumps(payload)}\n\n".encode())
        else:
            self.client.sendall(f"{cmd}\n\n".encode())


def main():
    try:
        os.unlink(SOCKET_PATH)
    except OSError:
        if os.path.exists(SOCKET_PATH):
            raise

    show = Show()
    show.start()



if __name__ == "__main__":
    main()
