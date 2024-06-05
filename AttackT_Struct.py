import os

class Interval:
    def __init__(self, tmin, tmax):
        # Validate tmax as either an integer or 'inf'
        if not (isinstance(tmax, int) or tmax == float('inf')):
            raise ValueError(f"Invalid tmax '{tmax}'. tmax must be an integer or 'inf'.")
        if tmax == 'inf':
            tmax = float('inf')
        # Validate tmin is less than or equal to tmax
        if not isinstance(tmin, int) or tmin > tmax:
            raise ValueError(f"Invalid interval with tmin {tmin} and tmax {tmax}. tmin must be an integer and tmin <= tmax.")
        self.tmin = tmin
        self.tmax = tmax

    def add(self, i):
        new_tmin = self.tmin + i
        # Handle infinity case
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
        self.interval = interval
        self.name = idt
        self.operator = operator
        
    def __str__(self):
        return f"Node(idt={self.name}, duration={self.operator}, cost={self.interval})"

    def __repr__(self):
        return self.__str__()

class Attack_tree:
    def __init__(self, node, left, right):
        if node.operator not in {'||', '&', ';'}:
            raise ValueError(f"Invalid operator '{node.operator}'. Operator must be '&', '||', or ';'.")
        self.root = node
        self.left = left
        self.right = right
        

    def add(self, i):
        new_left = self.left.add(i) if hasattr(self.left, 'add') else self.left + i
        new_right = self.right.add(i) if hasattr(self.right, 'add') else self.right + i
        return Attack_tree(self.root, new_left, new_right)
    
    def is_valid_tree(self, node):
        """
        Recursive function to check if the node is a Leaf or Attack_tree.
        """
        if isinstance(node, Leaf):
            return True
        elif isinstance(node, Attack_tree):
            return self.is_valid_tree(node.left) and self.is_valid_tree(node.right)
        else:
            return False
    # def time_feasible(self):
    #     """
    #     Recursively checks the intervals of parent nodes to include the intervals
    #     of their child nodes throughout the tree structure.
    #     """
    #     parentmin= self.node.interval.tmin
    #     parentmax= self.node.interval.tmax
    #     if isinstance(self.left, Attack_tree):
    #         childmin= self.left.node.interval.tmin
    #         childmax= self.left.node.interval.tmax
    #         if(parentmin>)
    #     if isinstance(self.right, Attack_tree):
    #         childmin= self.left.node.interval.tmin
    #         childmax= self.left.node.interval.tmax
    #         self.right.time_feasible()  

    def __repr__(self):
        return f"({self.root.left} {self.root.operator} {self.root.right} {self.root.interval} {self.root.name})"

def generate_tikz_code(subtree):
    if isinstance(subtree, Leaf):
        return f"node {{ {subtree.name} \\\\ $\\Delta$={subtree.duration}\\\\cost={subtree.cost} }}"
    elif isinstance(subtree, Attack_tree):
        node=subtree.root
        operator_label = {'||': 'OR', '&': 'AND', ';': 'SEQ'}[node.operator]
        interval_label = f"$[{node.interval.tmin},{node.interval.tmax}]$"
        left_code = generate_tikz_code(subtree.left)
        right_code = generate_tikz_code(subtree.right)
        return f"node {{ {node.name} \\\\ {operator_label} \\\\ {interval_label} }} child {{ {left_code} }} child {{ {right_code} }}"
    return ""

def mygen(tree): 
    if isinstance(tree, Attack_tree):
        node=tree.root
        operator_label = {'||': 'OR', '&': 'AND', ';': 'SEQ'}[node.operator]
        interval_label = f"$[{node.interval.tmin},{node.interval.tmax}]$"
        left_code = generate_tikz_code(tree.left)
        right_code = generate_tikz_code(tree.right)
        return f"{{ {node.name} \\\\ {operator_label} \\\\ {interval_label} }} child {{ {left_code} }} child {{ {right_code} }}"
    else:
        return ""
        
        
    

def draw_attack_tree(tree, filename):
    operator_label = {'||': 'OR', '&': 'AND', ';': 'SEQ'}[tree.root.operator]
    interval_label = f"$[{tree.root.interval.tmin},{tree.root.interval.tmax}]$"
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



# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(3, 7)


Insert_rem=Leaf("IRID",10,100)
Open_inf=Leaf("OID",2,1)
Send_virus=Leaf("ASVVI",1,100 )
Loading_main=Leaf("LMD",1,0 )
Steal_cert=Leaf("SDC",1,1 )

Injectionvia=Node(";",Interval(5,10),"IVRD")
Infectingac=Node("||",Interval(3,7),"IC")
selfi=Node("&",Interval(10,33),"SI")

Tree_injection= Attack_tree(Injectionvia,Open_inf , Insert_rem)
Tree_infecting= Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI= Attack_tree(selfi,Steal_cert,Tree_infecting)

leaf1 = Leaf("Leaf1", 5, 2000)
leaf2 = Leaf("Leaf2", 3, 50)
leaf3 = Leaf("Leaf3", 4, 70)
leaf4 = Leaf("Leaf4", 2, 30)
left_sub_tree = Attack_tree(Node("||", interval_left_sub, "OR"), leaf1, leaf2)
right_sub_tree = Attack_tree(Node(";", interval_right_sub, "SEQ"), leaf3, leaf4)

illformedtree = Attack_tree(Node(";", interval_right_sub, "SEQ"), Node(";", interval_right_sub, "SEQ"), Node(";", interval_right_sub, "SEQ"))

# if illformedtree.is_valid_tree(illformedtree):
#     print("The tree structure is valid.")
# else:
#     print("The tree structure is not valid.")

root_tree = Attack_tree(Node("&", interval_root, "Root"), left_sub_tree, right_sub_tree)
draw_attack_tree(Tree_SI,'SI_tree')


