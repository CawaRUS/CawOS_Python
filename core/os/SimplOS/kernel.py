
class Kernel:
    def __init__(self):
        self.root = {"type": "dir", "children": {}}
        self.current_dir = self.root
        self.path_stack = []

    def run(self):
        print("Welcome to SimplOS! Type 'help' for commands.")
        while True:
            path = "/" + "/".join(self.path_stack)
            cmd = input(f"SimplOS:{path if path != '/' else '/'}> ").strip()
            if not cmd:
                continue
            self.handle_command(cmd)

    def handle_command(self, cmd):
        parts = cmd.split()
        if not parts:
            return
        command = parts[0]
        args = parts[1:]

        if command == "help":
            self.help()
        elif command == "ls":
            self.ls()
        elif command == "cd":
            self.cd(args)
        elif command == "mkdir":
            self.mkdir(args)
        elif command == "touch":
            self.touch(args)
        elif command == "cat":
            self.cat(args)
        elif command == "exit":
            print("Exiting SimplOS...")
            exit()
        else:
            print(f"Unknown command: {command}")

    def help(self):
        print("Commands: ls, cd <dir>, mkdir <dir>, touch <file>, cat <file>, exit")

    def ls(self):
        for name in self.current_dir["children"]:
            print(name)

    def cd(self, args):
        if not args:
            print("cd: missing argument")
            return
        dir_name = args[0]
        if dir_name == "..":
            if self.path_stack:
                self.path_stack.pop()
                self.current_dir = self.root
                for p in self.path_stack:
                    self.current_dir = self.current_dir["children"][p]
        elif dir_name in self.current_dir["children"]:
            if self.current_dir["children"][dir_name]["type"] == "dir":
                self.current_dir = self.current_dir["children"][dir_name]
                self.path_stack.append(dir_name)
            else:
                print(f"cd: {dir_name} is not a directory")
        else:
            print(f"cd: {dir_name} not found")

    def mkdir(self, args):
        if not args:
            print("mkdir: missing argument")
            return
        name = args[0]
        if name in self.current_dir["children"]:
            print(f"mkdir: {name} already exists")
        else:
            self.current_dir["children"][name] = {"type": "dir", "children": {}}

    def touch(self, args):
        if not args:
            print("touch: missing argument")
            return
        name = args[0]
        if name in self.current_dir["children"]:
            print(f"touch: {name} already exists")
        else:
            self.current_dir["children"][name] = {"type": "file", "content": ""}

    def cat(self, args):
        if not args:
            print("cat: missing argument")
            return
        name = args[0]
        if name in self.current_dir["children"]:
            node = self.current_dir["children"][name]
            if node["type"] == "file":
                print(node["content"])
            else:
                print(f"cat: {name} is a directory")
        else:
            print(f"cat: {name} not found")

# Функция, которую твоя загрузка вызывает
def start(*args, **kwargs):
    os_sim = Kernel()
    os_sim.run()
