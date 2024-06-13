import os
from z3 import *

class Interval:
    def __init__(self, tmin, tmax):
        if not (isinstance(tmax, int) or tmax == float('inf')):
            raise ValueError(f"Invalid tmax '{tmax}'. tmax must be an integer or 'inf'.")
        if tmax == 'inf':
            tmax = float('inf')
        if not isinstance(tmin, int) or tmin > tmax:
            raise ValueError(f"Invalid interval with tmin {tmin} and tmax {tmax}. tmin must be an integer and tmin <= tmax.")
        self.tmin = tmin
        self.tmax = tmax

    def add(self, i):
        new_tmin = self.tmin + i
        if self.tmax == float('inf'):
            new_tmax = float('inf')
        else:
            new_tmax = self.tmax + i
        return Interval(new_tmin, new_tmax)

    def __repr__(self):
        tmax_display = '∞' if self.tmax == float('inf') else self.tmax
        return f"[{self.tmin}, {tmax_display}]"

class Leaf:
    def __init__(self, idt, duration, cost):
        if not isinstance(idt, str):
            raise TypeError("idt must be a string")
        self.name = idt
        self.duration = duration
        self.cost = cost
        self.interval = Interval(0, 0)  # Initialize with a default interval, can be updated later

    def __str__(self):
        return f"Node(idt={self.name}, duration={self.duration}, cost={self.cost})"

    def __repr__(self):
        return self.__str__()

class Node:
    def __init__(self, operator, interval, idt, left=None, right=None):
        self.operator = operator
        self.interval = interval
        self.name = idt
        self.left = left
        self.right = right

    def __str__(self):
        return f"Node(idt={self.name}, duration={self.operator}, cost={self.interval})"

    def __repr__(self):
        return self.__str__()

class Attack_tree:
    def __init__(self, root, left, right):
        if root.operator not in {'||', '&', ';'}:
            raise ValueError(f"Invalid operator '{root.operator}'. Operator must be '&', '||', or ';'.")
        self.root = root
        self.left = left
        self.right = right

    def add(self, i):
        new_left = self.left.add(i) if hasattr(self.left, 'add') else self.left + i
        new_right = self.right.add(i) if hasattr(self.right, 'add') else self.right + i
        return Attack_tree(self.root, new_left, new_right)

    def is_valid_tree(self, node):
        if isinstance(node, Leaf):
            return True
        elif isinstance(node, Attack_tree):
            return self.is_valid_tree(node.left) and self.is_valid_tree(node.right)
        else:
            return False

    def __repr__(self):
        return f"({self.left} {self.root.operator} {self.right} {self.root.interval} {self.root.name})"

def count_leaf_nodes(tree: Attack_tree) -> int:
    if isinstance(tree, Leaf):
        return 1
    elif isinstance(tree, Attack_tree):
        left_count = count_leaf_nodes(tree.left) if tree.left else 0
        right_count = count_leaf_nodes(tree.right) if tree.right else 0
        return left_count + right_count
    else:
        return 0

def intersect(I1, I2):
    new_tmin = max(I1.tmin, I2.tmin)
    new_tmax = min(I1.tmax, I2.tmax)
    if new_tmin <= new_tmax:
        return Interval(new_tmin, new_tmax)
    else:
        return None

def propagate(formula: Attack_tree):
    errors = []

    def helper(subtree):
        match subtree:
            case Attack_tree(left=left, root=root, right=right):
                name = root.name
                interval = root.interval

                if isinstance(left, Leaf):
                    if left.duration > (interval.tmax - interval.tmin):
                        errors.append(f"Leaf node {left.name} duration cannot match the interval of {name}")
                else:
                    left_intersect = intersect(interval, left.root.interval)
                    if left_intersect is None:
                        errors.append(f"The intersection of {left.root.name} {left.root.interval} and the parent interval {name} {interval} is empty")
                    else:
                        left.root.interval = left_intersect
                        helper(left)

                if isinstance(right, Leaf):
                    if right.duration > (interval.tmax - interval.tmin):
                        errors.append(f"Leaf node {right.name} duration cannot match the interval of {name}")
                else:
                    right_intersect = intersect(interval, right.root.interval)
                    if right_intersect is None:
                        errors.append(f"The intersection of {right.root.name} {right.root.interval} and the parent interval {name} {interval} is empty")
                    else:
                        right.root.interval = right_intersect
                        helper(right)

    helper(formula)
    
    if errors:
        return errors
    else:
        return 

def generate_tikz_code(subtree):
    if isinstance(subtree, Leaf):
        return f"node {{ {subtree.name} \\\\ $\\Delta$={subtree.duration}\\\\cost={subtree.cost} }}"
    elif isinstance(subtree, Attack_tree):
        node = subtree.root
        operator_label = {'||': 'OR', '&': 'AND', ';': 'SAND'}[node.operator]
        interval_label = f"$[{node.interval.tmin},{node.interval.tmax}]$"
        left_code = generate_tikz_code(subtree.left)
        right_code = generate_tikz_code(subtree.right)
        return f"node {{ {node.name} \\\\ {operator_label} \\\\ {interval_label} }} child {{ {left_code} }} child {{ {right_code} }}"
    return ""

def mygen(tree):
    if isinstance(tree, Attack_tree):
        node = tree.root
        operator_label = {'||': 'OR', '&': 'AND', ';': 'SAND'}[node.operator]
        interval_label = f"$[{node.interval.tmin},{node.interval.tmax}]$"
        left_code = generate_tikz_code(tree.left)
        right_code = generate_tikz_code(tree.right)
        return f"{{ {node.name} \\\\ {operator_label} \\\\ {interval_label} }} child {{ {left_code} }} child {{ {right_code} }}"
    else:
        return ""

def draw_attack_tree(tree, filename):
    tikz_code = r"""
    \documentclass{standalone}
    \usepackage{tikz}
    \usetikzlibrary{trees}
    \begin{document}
    \begin{tikzpicture}[
      edge from parent fork down, sibling distance=3cm, level distance=3cm,
      level 1/.style={sibling distance=4cm},
      level 2/.style={sibling distance=2cm},
      every node/.style={fill=white,draw, align=center}
      ]
      \node """ + mygen(tree) + r"""
      ;
    \end{tikzpicture}
    \end{document}
    """

    with open(f"{filename}.tex", "w") as file:
        file.write(tikz_code)

    os.system(f"pdflatex {filename}.tex")

def to_z3interval(interval):
    return Z3interval.mk_interval(interval.tmin, interval.tmax)

def add_leaf_constraints(leaf, index, trace, opt):
    event = trace[index]
    ttei = Event.inter(event)
    tidt = Event.name(event)
    cost = Event.q(event)
    
    leaf_interval = to_z3interval(leaf.interval)
    opt.add(Z3interval.ti(ttei) >= Z3interval.ti(leaf_interval))
    opt.add(Z3interval.ts(ttei) <= Z3interval.ts(leaf_interval))
    opt.add(Z3interval.ts(ttei) - Z3interval.ti(ttei) == leaf.duration)
    opt.add(cost == leaf.cost)
    opt.add(tidt == leaf.name)

def parse_tree_to_z3(node, trace, opt, index, variables):
    if isinstance(node, Leaf):
        if node.name not in variables:
            variables[node.name] = (Bool(node.name), index)
        add_leaf_constraints(node, index, trace, opt)
        return variables[node.name][0]
    elif isinstance(node, Node):
        left_expr = parse_tree_to_z3(node.left, trace, opt, index * 2, variables)
        right_expr = parse_tree_to_z3(node.right, trace, opt, index * 2 + 1, variables)
        if node.operator == '&':
            return And(left_expr, right_expr)
        elif node.operator == '||':
            return Or(left_expr, right_expr)
        elif node.operator == ';':  # Assuming ';' is for sequential and can be handled similarly to AND
            return And(left_expr, right_expr)
        else:
            raise ValueError(f"Unsupported operator: {node.operator}")
    else:
        raise TypeError("Unsupported node type")
    
# Define the event datatype
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval), ('q', IntSort()))
Event = Event.create()

# Create a sequence sort for Events
Trace = SeqSort(Event)

interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)

Insert_rem = Leaf("IRID", 5, 70)
Open_inf = Leaf("OID", 4, 300)
Send_virus = Leaf("ASVVI", 29, 30)
Loading_main = Leaf("LMD", 1, 0)
Steal_cert = Leaf("SDC", 20, 300)

# Assigning intervals to leaves
Insert_rem.interval = Interval(2, 7)
Open_inf.interval = Interval(1, 5)
Send_virus.interval = Interval(1, 30)
Loading_main.interval = Interval(1, 1)
Steal_cert.interval = Interval(5, 20)

Injectionvia = Node("&", Interval(5, 16), "IVRD", Open_inf, Insert_rem)
Infectingac = Node("&", Interval(3, 40), "IC", Send_virus, Injectionvia)
selfi = Node("&", Interval(10, 200), "SI", Steal_cert, Infectingac)

# Initialize Z3 optimizer
opt = Optimize()

# Define the trace
trace = Const('trace', Trace)

# Parse the tree, add constraints, and link with the trace
variables = {}
root_expr = parse_tree_to_z3(Injectionvia, trace, opt, 0, variables)
#print(root_expr)
opt.add(root_expr)
for x in opt.assertions():
    print(x)

# Check the satisfiability of the constraints
if opt.check() == sat:
    model = opt.model()
    print("Satisfiable model found:")
    for var in variables:
        print(f"{var} = {model[variables[var][0]]}")
    for i in range(len(variables)):
        event = trace[i]
        idtt = model.evaluate(Event.name(event))
        interval = model.evaluate(Event.inter(event))
        ttb = model.evaluate(Z3interval.ti(interval))
        ttf = model.evaluate(Z3interval.ts(interval))
        costl = model.evaluate(Event.q(event))
        if ttb.as_long() <= ttf.as_long():
            print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost = {costl}")
else:
    print("No satisfiable model found.")





