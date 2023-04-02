from lark import Lark, Transformer
import getch
import enum
import types


class Flags(enum.Enum):
    outp_flag = enum.auto()
    inp_flag = enum.auto()
    struct_sep = enum.auto()


class Node:
    def __init__(self, name, outp_flag=False, count=1, cycle=None):
        self.name = name
        self.outp_flag = outp_flag
        self._count = count
        self.cycle = cycle or []

        self.resolved = False
        self.pos = -1
        self.parent = None

    def __repr__(self):
        return f"Node({self.name}, {self.outp_flag}, {self._repr_count}, {self.cycle})"

    def __str__(self):
        return f"{self.name}"

    @property
    def _repr_count(self):
        if self._count is Flags.inp_flag:
            return "inp_flag"
        else:
            return self._count

    @property
    def count(self):
        if self._count is Flags.inp_flag:
            return ord(getch.getch())
        else:
            return self._count

    @property
    def is_terminal(self):
        return not self.cycle

    def step(self, n):
        if self.outp_flag:
            print(chr(n), end="", flush=True)

        self.pos = (self.pos + n) % len(self.cycle)
        return self.cycle[self.pos], self.count


class Structure:
    def __init__(self, name, nodes, instances):
        self.name = name
        self.nodes = nodes
        self.instances = instances

    def __repr__(self):
        return f"Structure({self.name}, {self.nodes})"

    def __str__(self):
        return f"{self.name}"

    def __getattr__(self, key):
        if key in self.nodes:
            return self.nodes[key]

        if key in self.instances:
            return self.instances[key]

        raise AttributeError(f"Structure {self.name} has no attribute {key}")


def traverse(node, n):
    while True:
        if node is None or node.is_terminal:
            return node

        if n is Flags.inp_flag:
            n = ord(getch.getch())

        node, n = node.step(n)


with open("grammar.lark") as f:
    grammar = f.read()
    parser = Lark(grammar, parser="lalr")


class Preprocessor(Transformer):
    def __init__(self):
        super().__init__()
        self.structs = {}

    def outp_flag(self, tree):
        return Flags.outp_flag

    def inp_flag(self, tree):
        return Flags.inp_flag

    def struct_sep(self, tree):
        return Flags.struct_sep

    def count(self, tree):
        v = tree[0]

        if v is Flags.inp_flag:
            return v

        return int(v)

    def name(self, tree):
        return ".".join(x for x in tree if x is not Flags.struct_sep)

    def cycle(self, tree):
        return tree

    def counter_def(self, tree):
        outp_flag = False
        match tree:
            case [Flags.outp_flag, *tree]:
                outp_flag = True

        match tree:
            case [str(name), count, list(cycle)]:
                pass

            case [str(name), list(cycle)]:
                count = 1

            case [str(name)]:
                count = 1
                cycle = []

            case _:
                raise Exception("Invalid counter definition")

        def create(parent_name=None):
            if parent_name:
                new_name = f"{parent_name}.{name}"
            else:
                new_name = name
            return name, Node(new_name, outp_flag, count, cycle)

        return "counter", (name, create, cycle)

    def trigger(self, tree):
        match tree:
            case [str(name)]:
                return "trigger", (name, 1)

            case [str(name), count]:
                return "trigger", (name, count)

    def struct_def(self, tree):
        name, *lines = tree

        def create(parent_name=None):
            nodes = {}
            instances = {}

            for line in lines:
                match line:
                    case ("counter", (str(cname), creator, cycle)):
                        node = resolve(cname.split("."), nodes, instances)
                        if not node:
                            cname, node = creator(parent_name)
                        else:
                            node.cycle = cycle
                        nodes[cname] = node

                    case ("struct_set", (str(cname), str(struct_name))):
                        if parent_name:
                            new_name = f"{parent_name}.{cname}"
                        else:
                            new_name = cname
                        _, instance = self.structs[struct_name](new_name)
                        instances[cname] = instance

            for node in nodes.values():
                node.cycle = [
                    resolve(x.split("."), nodes, instances) for x in node.cycle
                ]

            return name, Structure(parent_name, nodes, instances)

        self.structs[name] = create
        return "struct", (name, create)

    def struct_set(self, tree):
        return "struct_set", tree


def resolve(name_split, nodes, instances):
    match name_split:
        case [str(name)]:
            return nodes.get(name, None)

        case [str(instance), *remaining]:
            instance = instances[instance]
            node = resolve(remaining, instance.nodes, instance.instances)
            return node


def read_tree(filename):
    with open(filename) as f:
        code = f.read()
        tree = parser.parse(code)
    return tree


def preprocess(tree):
    preprocessor = Preprocessor()
    return preprocessor.transform(tree)


def import_structs(filename):
    tree = read_tree(filename)
    tree = preprocess(tree)

    structs = types.SimpleNamespace()
    for x in tree.children:
        match x:
            case ("struct", (str(name), creator)):
                structs.__dict__[name] = creator
                continue
    return structs


def execute(tree):
    nodes = {}
    structs = {}
    instances = {}

    processed = False

    term_nodes = []

    for x in tree.children:
        match x:
            case ("counter", (str(name), creator, cycle)):
                node = resolve(name.split("."), nodes, instances)
                if not node:
                    name, node = creator()
                else:
                    node.cycle = cycle
                nodes[name] = node
                continue

            case ("struct", (str(name), creator)):
                structs[name] = creator
                continue

            case ("struct_set", (str(name), str(struct_name))):
                _, struct = structs[struct_name](name)
                instances[name] = struct
                continue

            case ("trigger", (str(name), count)):
                if not processed:
                    processed = True
                    for node in nodes.values():
                        node.cycle = [
                            resolve(x.split("."), nodes, instances) for x in node.cycle
                        ]

                node = resolve(name.split("."), nodes, instances)

                term = traverse(node, count)
                term_nodes.append(term)

    return term_nodes

def extract_graph(*inital_nodes):
    seen = {}

    def bfs(start):
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node.name in seen:
                continue
            
            cycle = [n.name for n in node.cycle]

            if len(cycle) != 0:
                offset = (node.pos - 1) % len(cycle)
            else:
                offset = 0
            cycle = cycle[offset:] + cycle[:offset]

            seen[node.name] = "?" if node._count is Flags.inp_flag else node._count, cycle, node.outp_flag

            queue.extend(node.cycle)

    for node in inital_nodes:
        bfs(node)

    return seen

def dump_graph(graph, filename):
    with open(filename, "w") as f:
        for name, (count, cycle, outp) in graph.items():
            name = name.replace(".", "_")
            cycle = [x.replace(".", "_") for x in cycle]
            outp_flag = "!" if outp else ""

            if len(cycle) == 0:
                f.write(f"{outp_flag}{name};\n")
            else:
                f.write(f"{outp_flag}{name} {count}: {' '.join(cycle)};\n")