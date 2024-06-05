from z3 import *
from AttackT_Struct import Attack_tree,Interval,Node


def minimal_attack_strategy(tree):
    opt = Optimize()
    cost_elements = []

    def process_node(node, i):
        ttb = Int(f'ttb_{i}')
        ttf = Int(f'ttf_{i}')
        tidt = String(f'tidt_{i}')
        t_min = node.interval.tmin
        t_max = node.interval.tmax
        duration = node.duration
        cost = node.cost

        opt.add(ttb >= t_min, ttf <= t_max, ttf - ttb >= duration, tidt == node.name)
        cost_elements.append(If(ttb >= t_min, cost, 0))

    def process_tree(tree, i):
        if isinstance(tree, Node):
            process_node(tree, i)
        elif isinstance(tree, Attack_tree):
            left = tree.left
            right = tree.right
            operator = tree.operator
            if operator == '||':
                c_l= left.cost
                c_r= right.cost
                if c_r<c_l:
                    process_tree(right,i)
                else:
                    process_tree(left,i)
            elif operator == '&':
                process_tree(left, i)
                process_tree(right, i + 1)
            elif operator == ';':
                process_tree(left, i)
                process_tree(right, i + 1)

    def process_tree_or(tree, i):
        left = tree.left
        right = tree.right

        opt_left = Optimize()
        opt_right = Optimize()

        process_node_opt(left, opt_left, i)
        process_node_opt(right, opt_right, i + 1)

        left_cost_elements = []
        right_cost_elements = []

        extract_costs(opt_left, left_cost_elements, i)
        extract_costs(opt_right, right_cost_elements, i + 1)

        combined_cost = If(Or(*opt_left.assertions()), Sum(left_cost_elements), 0) + \
                        If(Or(*opt_right.assertions()), Sum(right_cost_elements), 0)

        opt.add(Or(*opt_left.assertions(), *opt_right.assertions()))
        cost_elements.append(combined_cost)

    def process_node_opt(node, opt, i):
        ttb = Int(f'ttb_{i}')
        ttf = Int(f'ttf_{i}')
        tidt = String(f'tidt_{i}')
        t_min = node.interval.tmin
        t_max = node.interval.tmax
        duration = node.duration
        cost = node.cost

        opt.add(ttb >= t_min, ttf <= t_max, ttf - ttb >= duration, tidt == node.name)

    process_tree(tree, 0)

    cost_sum = Int('cost_sum')
    opt.add(cost_sum == Sum(cost_elements))
    opt.minimize(cost_sum)

    if opt.check() == sat:
        model = opt.model()
        strategy = []
        for i in range(len(cost_elements)):
            idt = model[String(f'tidt_{i}')]
            ttb = model[Int(f'ttb_{i}')]
            ttf = model[Int(f'ttf_{i}')]
            cost = model.eval(cost_elements[i])
            strategy.append((idt, Interval(ttb.as_long(), ttf.as_long()), cost))
        return strategy
    else:
        return None

# Example usage
interval1 = Interval(1, 100)
interval2 = Interval(0, 100)
node1 = Node("n1", interval1, 10, 12)
node2 = Node('n2', interval2, 5, 7)
tree1 = Attack_tree(node1, '||', node2)
tree2 = Attack_tree(node2, '&', node2)
tree3= Attack_tree(tree1, '&', tree2)

strategy = minimal_attack_strategy(tree3)
print(strategy)