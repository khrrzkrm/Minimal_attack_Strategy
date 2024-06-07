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
        return f"Leaf(idt={self.name}, duration={self.duration}, cost={self.cost})"

    def __repr__(self):
        return self.__str__()

class Node:
    def __init__(self, operator, interval, idt, left, right):
        self.interval = interval
        self.name = idt
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return f"Node(idt={self.name}, operator={self.operator}, interval={self.interval}, left={self.left}, right={self.right})"

    def __repr__(self):
        return self.__str__()

def compute_constraints(tree, prefix=""):
    constraints = []
    ttb = Int(f"{prefix}ttb")
    ttf = Int(f"{prefix}ttf")
    tidt = String(f"{prefix}tidt")

    def process_leaf(leaf, prefix):
        ttb = Int(f"{prefix}ttb")
        ttf = Int(f"{prefix}ttf")
        tidt = String(f"{prefix}tidt")
        return And(tidt == leaf.name, ttf - ttb == leaf.duration)

    def process_tree(tree, prefix):
        ttb = Int(f"{prefix}ttb")
        ttf = Int(f"{prefix}ttf")
        tidt = String(f"{prefix}tidt")
        if isinstance(tree, Leaf):
            return process_leaf(tree, prefix)
        elif isinstance(tree, Node):
            left = tree.left
            right = tree.right
            operator = tree.operator
            tmin, tmax = tree.interval.tmin, tree.interval.tmax
            if operator == '||':
                left_constraints = compute_constraints(left, prefix + "L")
                right_constraints = compute_constraints(right, prefix + "R")
                return And(ttb >= tmin, ttf <= tmax, Or(left_constraints, right_constraints))
            elif operator == '&':
                left_constraints = compute_constraints(left, prefix + "L")
                right_constraints = compute_constraints(right, prefix + "R")
                return And(ttb >= tmin, ttf <= tmax, left_constraints, right_constraints)
            elif operator == ';':
                left_constraints = compute_constraints(left, prefix + "L")
                right_constraints = compute_constraints(right, prefix + "R")
                return And(ttb >= tmin, ttf <= tmax, left_constraints, right_constraints)

    constraints.append(process_tree(tree, prefix))
    return And(constraints)

# Example usage
interval1 = Interval(1, 100)
interval2 = Interval(10, 50)
interval3 = Interval(20, 30)

leaf1 = Leaf("leaf1", 10, 5)
leaf2 = Leaf("leaf2", 20, 10)
leaf3 = Leaf("leaf3", 5, 3)
leaf4 = Leaf("leaf4", 15, 7)

node1 = Node('||', interval2, "node1", leaf1, leaf2)
node2 = Node(';', interval3, "node2", leaf3, leaf4)
root = Node('&&', interval1, "root", node1, node2)

print(root)

# Compute constraints
constraints = compute_constraints(root)
print(constraints)

# Example of using Z3 to check satisfiability
# s = Solver()
# s.add(constraints)
# if s.check() == sat:
#     print("Satisfiable")
#     m = s.model()
#     print(m)
# else:
#     print("Unsatisfiable")
