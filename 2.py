import os

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

    def __str__(self):
        return f"Node(idt={self.name}, duration={self.duration}, cost={self.cost})"

    def __repr__(self):
        return self.__str__()


class Node:
    def __init__(self, operator, interval, idt):
        self.operator = operator
        self.interval = interval
        self.name = idt

    def __str__(self):
        return f"Node(idt={self.name}, operator={self.operator}, interval={self.interval})"

    def __repr__(self):
        return self.__str__()


class Attack_tree:
    def __init__(self, node, left, right):
        if node.operator not in {'||', '&', ';'}:
            raise ValueError(f"Invalid operator '{node.operator}'. Operator must be '&', '||', or ';'.")
        self.node = node
        self.left = left
        self.right = right

    def add(self, i):
        new_node = Node(self.node.operator, self.node.interval.add(i), self.node.name)
        new_left = self.left.add(i) if hasattr(self.left, 'add') else self.left + i
        new_right = self.right.add(i) if hasattr(self.right, 'add') else self.right + i
        return Attack_tree(new_node, new_left, new_right)

    def __repr__(self):
        return f"({self.node} {self.left} {self.right})"


def generate_tikz_code(subtree):
    if isinstance(subtree, Leaf):
        return f"node {{{subtree.name} \\\\ $\\Delta$={subtree.duration}\\\\cost={subtree.cost}}}"
    elif isinstance(subtree, Attack_tree):
        node = subtree.node
        operator_label = {'||': 'OR', '&': 'AND', ';': 'SEQ'}[node.operator]
        interval_label = f"$[{node.interval.tmin},{node.interval.tmax}]$"
        left_code = generate_tikz_code(subtree.left)
        right_code = generate_tikz_code(subtree.right)
        return f"node {{{node.name} \\\\ {operator_label} \\\\ {interval_label}}} child {{ {left_code} }} child {{ {right_code} }}"
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
      """ + generate_tikz_code(tree) + r"""
      ;
    \end{tikzpicture}
    \end{document}
    """

    with open(f"{filename}.tex", "w") as file:
        file.write(tikz_code)

    os.system(f"pdflatex {filename}.tex")

# Example usage:
interval = Interval(1, 10)
leaf1 = Leaf("Leaf1", 5, 100)
leaf2 = Leaf("Leaf2", 3, 50)
leaf3 = Leaf("Leaf3", 4, 70)
leaf4 = Leaf("Leaf4", 2, 30)
node_and = Node('&', Interval(2, 8), "LeftSubTree")
node_seq = Node(';', Interval(3, 7), "RightSubTree")
left_tree = Attack_tree(node_and, leaf1, leaf2)
right_tree = Attack_tree(node_seq, leaf3, leaf4)
root_node = Node('||', Interval(1, 10), "Root")
tree = Attack_tree(root_node, left_tree, right_tree)
draw_attack_tree(tree, "attack_tree")
