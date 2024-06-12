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

def LeafToZ3(leaf: Leaf, root: Node, sol: Solver, bound: int, trace: SeqRef) -> Solver:
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
    sol.add(Or(clauses))
    return sol

def z3_attack_solver(formula: Attack_tree, bound: int, trace: SeqRef) -> Solver:
    sol = Solver()
    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if isinstance(left, Attack_tree):
                sol_l = z3_attack_solver(left, bound, trace)
            elif isinstance(left, Leaf):
                sol_l = Solver()
                LeafToZ3(left, root, sol_l, bound, trace)
            
            if isinstance(right, Attack_tree):
                sol_r = z3_attack_solver(right, bound, trace)
            elif isinstance(right, Leaf):
                sol_r = Solver()
                LeafToZ3(right, root, sol_r, bound, trace)
                
            if root.operator == '&':
                combined_assertions = And(*sol_l.assertions(), *sol_r.assertions())
                sol.add(combined_assertions)
            elif root.operator == '||':
                combined_assertions = Or(*sol_l.assertions(), *sol_r.assertions())
                sol.add(combined_assertions)
            else: 
                print("case not handled yet")
                return None
    
    for i in range(bound - 1):
        ttei_i = Event.inter(trace[i])  # Use indexing for sequences
        ttei_j = Event.inter(trace[i + 1])  # Use indexing for sequences
        ttmax = Z3interval.ts(ttei_i)
        ttmin = Z3interval.ti(ttei_j)
        sol.add(ttmax <= ttmin)
        
    return sol

# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem = Leaf("IRID", 5, 70)
Open_inf = Leaf("OID", 4, 1)
Send_virus = Leaf("ASVVI", 29, 30)
Loading_main = Leaf("LMD", 100, 0)
Steal_cert = Leaf("SDC", 100, 1)

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
        for x in range(0, n + 1):
            print(f"new bound {x}")
            temp_sol = Solver() 
            temp_sol = z3_attack_solver(formula1, x, trace)
            for c in temp_sol.assertions(): 
                print(c)
            if temp_sol.check() == sat:
                m = temp_sol.model()
                print("Satisfiable trace:")
                cost = 0
                for i in range(x):
                    event = trace[i]  # Use indexing for sequences
                    idtt = m.evaluate(Event.name(event))
                    interval = m.evaluate(Event.inter(event))
                    ttb = m.evaluate(Z3interval.ti(interval))
                    ttf = m.evaluate(Z3interval.ts(interval))
                    costl = m.evaluate(Event.q(event))
                    # Check interval validity and only print valid intervals
                    if ttb.as_long() <= ttf.as_long():
                        print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost = {costl}")
                        cost += costl.as_long()
                print(f"The total cost of this attack is {cost}")
                return
        else:
            print("no solution")
    else: 
        for c in formula1:
            print(c)
                 
synthetize(Tree_SI)
