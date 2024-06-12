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
    # Create the Z3 interval using the mk_interval constructor
    z3_interval = Z3interval.mk_interval(interval.tmin, interval.tmax)
    return z3_interval

def generate_disjoint_constraints(interval1, interval2):
    # Extract the ti and ts fields from the intervals
    interval1_ti = Z3interval.ti(interval1)
    interval1_ts = Z3interval.ts(interval1)
    interval2_ti = Z3interval.ti(interval2)
    interval2_ts = Z3interval.ts(interval2)
    
    # Create constraints to ensure the intervals do not intersect
    # For the intervals to be disjoint: ts1 <= ti2 or ts2 <= ti1
    disjoint_constraint = Or(interval1_ts <= interval2_ti, interval2_ts <= interval1_ti)
    
    return disjoint_constraint

def LeafToZ3(leaf: Leaf, root: Node, opt: Optimize, bound: int, trace: SeqRef) -> Optimize:
    label = 'pt' + leaf.name
    i = Int(label)
    event_i = trace[i]  # Use indexing for sequences
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

def z3_attack_solver(formula: Attack_tree, n: int, trace: SeqRef) -> Optimize:
    opt = Optimize()
    total_cost = Int('total_cost')
    cost_sum = IntVal(0)

    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if isinstance(left, Attack_tree):
                opt = z3_attack_solver(left, n, trace)
            elif isinstance(left, Leaf):
                LeafToZ3(left, root, opt, n, trace)
            
            if isinstance(right, Attack_tree):
                opt = z3_attack_solver(right, n, trace)
            elif isinstance(right, Leaf):
                LeafToZ3(right, root, opt, n, trace)
                
            if root.operator == '&':
                combined_assertions = And(*opt.assertions())
                opt.add(combined_assertions)
            elif root.operator == '||':
                combined_assertions = Or(*opt.assertions())
                opt.add(combined_assertions)
            else: 
                print("case not handled yet")
                return None

    # Add constraints to ensure the length of the trace is less than n
    length = Int('length')
    opt.add(length < n)
    for i in range(n):
        event = trace[i]
        ttei = Event.inter(event)
        ttb = Z3interval.ti(ttei)
        ttf = Z3interval.ts(ttei)
        valid_event = And(ttb <= ttf, i < length)
        cost_sum = If(valid_event, cost_sum + Event.q(event), cost_sum)
    
    opt.add(total_cost == cost_sum)
    opt.minimize(total_cost)
        
    return opt

# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem = Leaf("IRID", 5, 70)
Open_inf = Leaf("OID", 4, 1)
Send_virus = Leaf("ASVVI", 29, 30)
Loading_main = Leaf("LMD", 1, 0)
Steal_cert = Leaf("SDC", 1, 1)

Injectionvia = Node("||", Interval(5, 16), "IVRD")
Infectingac = Node("&", Interval(3, 40), "IC")
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
        opt = z3_attack_solver(formula1, n, trace)
        for c in opt.assertions(): 
            print(c)
        if opt.check() == sat:
            m = opt.model()
            print("Satisfiable trace:")
            total_cost = m.evaluate(Int('total_cost'))
            print(f"The total cost of this attack is {total_cost}")
            length = m.evaluate(Int('length')).as_long()
            for i in range(length):
                event = trace[i]  # Use indexing for sequences
                idtt = m.evaluate(Event.name(event))
                interval = m.evaluate(Event.inter(event))
                ttb = m.evaluate(Z3interval.ti(interval))
                ttf = m.evaluate(Z3interval.ts(interval))
                costl = m.evaluate(Event.q(event))
                    # Check interval validity and only print valid intervals
                if ttb.as_long() <= ttf.as_long():
                    print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost = {costl}")
                return
            else:
                print("no solution")
    else: 
        for c in formula1:
            print(c)

synthetize(Tree_SI)
