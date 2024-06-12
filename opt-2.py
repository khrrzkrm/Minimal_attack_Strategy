from z3 import *
from AttackT_Struct import Attack_tree, Interval, Leaf, Node, propagate, generate_tikz_code, draw_attack_tree, count_leaf_nodes

# Define the event datatype
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval), ('q', IntSort()))
Event = Event.create()

# Create a sequence sort for Events
Trace = SeqSort(Event)

def to_z3interval(interval):
    z3_interval = Z3interval.mk_interval(interval.tmin, interval.tmax)
    return z3_interval

def generate_disjoint_constraints(interval1, interval2):
    interval1_ti = Z3interval.ti(interval1)
    interval1_ts = Z3interval.ts(interval1)
    interval2_ti = Z3interval.ti(interval2)
    interval2_ts = Z3interval.ts(interval2)
    disjoint_constraint = Or(interval1_ts <= interval2_ti, interval2_ts <= interval1_ti)
    return disjoint_constraint

def LeafToZ3(leaf: Leaf, root: Node, opt: Optimize, bound: int, trace: SeqRef) -> Optimize:
    label = 'pt' + leaf.name
    i = Int(label)
    event_i = trace[i]
    ttei = Event.inter(event_i)
    tidt = Event.name(event_i)
    cost = Event.q(event_i)
    rootint = to_z3interval(root.interval)
    leafcost = leaf.cost
    clauses = []
    for x in range(bound):
        clauses.append(And(Z3interval.ti(ttei) >= Z3interval.ti(rootint),
                           Z3interval.ts(ttei) <= Z3interval.ts(rootint),
                           Z3interval.ts(ttei) - Z3interval.ti(ttei) == leaf.duration,
                           cost == leafcost,
                           tidt == leaf.name,
                           i == x))
    opt.add(Or(clauses))
    return opt

def z3_attack_solver(formula: Attack_tree, bound: int, trace: SeqRef) -> Optimize:
    opt = Optimize()
    total_cost = Int('total_cost')
    cost_sum = 0

    if isinstance(formula, Attack_tree):
        left, root, right = formula.left, formula.root, formula.right
        
        if isinstance(left, Attack_tree):
            opt_l = z3_attack_solver(left, bound, trace)
        elif isinstance(left, Leaf):
            opt_l = Optimize()
            LeafToZ3(left, root, opt_l, bound, trace)
        
        if isinstance(right, Attack_tree):
            opt_r = z3_attack_solver(right, bound, trace)
        elif isinstance(right, Leaf):
            opt_r = Optimize()
            LeafToZ3(right, root, opt_r, bound, trace)
        
        if root.operator == '&':
            combined_assertions = And(*opt_l.assertions(), *opt_r.assertions())
            opt.add(combined_assertions)
        elif root.operator == '||':
            combined_assertions = Xor(*opt_l.assertions(), *opt_r.assertions())
            opt.add(combined_assertions)
        else:
            print("Operator not handled yet")
            return None

    for i in range(bound - 1):
        ttei_i = Event.inter(trace[i])
        ttei_j = Event.inter(trace[i + 1])
        ttmax = Z3interval.ts(ttei_i)
        ttmin = Z3interval.ti(ttei_j)
        opt.add(ttmax <= ttmin)
    
    for i in range(bound):
        event = trace[i]
        ttei = Event.inter(event)
        ttb = Z3interval.ti(ttei)
        ttf = Z3interval.ts(ttei)
        cost_sum += If(ttb <= ttf, Event.q(event), 0)
    
    opt.add(total_cost == cost_sum)
    opt.minimize(total_cost)
        
    return opt

# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem = Leaf("IRID", 5, 70)
Open_inf = Leaf("OID", 4, 300)
Send_virus = Leaf("ASVVI", 29, 30)
Loading_main = Leaf("LMD", 1, 0)
Steal_cert = Leaf("SDC", 20, 300)

Injectionvia = Node("&", Interval(5, 16), "IVRD")
Infectingac = Node("||", Interval(3, 40), "IC")
selfi = Node("&", Interval(10, 200), "SI")

Tree_injection = Attack_tree(Injectionvia, Open_inf, Insert_rem)
Tree_infecting = Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI = Attack_tree(selfi, Steal_cert, Tree_infecting)

def synthetize(formula: Attack_tree):
    trace = Const('trace', Trace)
    formula1 = propagate(formula)
    if isinstance(formula1, Attack_tree):
        draw_attack_tree(formula1, 'test')
        n = count_leaf_nodes(formula1)
        print(n)
        for x in range(0, n + 1):
            print(f"new bound {x}")
            opt = z3_attack_solver(formula1, x, trace)
            for c in opt.assertions(): 
                print(c)
            if opt.check() == sat:
                m = opt.model()
                print("Satisfiable trace:")
                total_cost = m.evaluate(Int('total_cost'))
                print(f"The total cost of this attack is {total_cost}")
                for i in range(x):
                    event = trace[i]
                    idtt = m.evaluate(Event.name(event))
                    interval = m.evaluate(Event.inter(event))
                    ttb = m.evaluate(Z3interval.ti(interval))
                    ttf = m.evaluate(Z3interval.ts(interval))
                    costl = m.evaluate(Event.q(event))
                    if ttb.as_long() <= ttf.as_long():
                        print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost = {costl}")
                return
        else:
            print("There exists no possible timed scheduling for the attack")
    else: 
        for c in formula1:
            print(c)

synthetize(Tree_SI)
