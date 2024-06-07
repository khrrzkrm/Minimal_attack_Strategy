from z3 import *
from AttackT_Struct import Attack_tree, Interval, Leaf, Node

# Define the Z3 interval datatype
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

# Define the event datatype
Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval))
Event = Event.create()

# Using a list to store events
trace = []
active_events = []

def to_z3interval(interval):
    return Z3interval.mk_interval(interval.tmin, interval.tmax)

def z3_attack_model(formula: Attack_tree, n: int) -> Solver:
    solver = Solver()
    event_costs = []

    def handle_leaf(leaf, interval, index):
        if index >= n:
            return 0  # Skip if index exceeds the bound
        event_active = Bool(f'event_active_{index}')
        active_events.append(event_active)

        event_i = Const(f'event_{index}', Event)
        ttei = Event.inter(event_i)
        ttb = Z3interval.ti(ttei)
        ttf = Z3interval.ts(ttei)
        tidt = Event.name(event_i)
        t_min = interval.tmin
        t_max = interval.tmax

        solver.add(Implies(event_active, And(ttb >= t_min, ttf <= t_max, ttf - ttb == leaf.duration, tidt == leaf.name)))
        trace.append(event_i)  # Append the event to the trace list
        event_costs.append(If(event_active, leaf.cost, 0))

    def process_tree(tree, interval, index):
        if isinstance(tree, Leaf):
            handle_leaf(tree, interval, index)
        elif isinstance(tree, Attack_tree):
            left_index = index * 2 + 1
            right_index = index * 2 + 2

            process_tree(tree.left, tree.root.interval, left_index)
            process_tree(tree.right, tree.root.interval, right_index)

            if tree.root.operator == '&':
                combined_assertions = And(*solver.assertions())
                solver.add(combined_assertions)
            elif tree.root.operator == '||':
                combined_assertions = Or(*solver.assertions())
                solver.add(combined_assertions)
            else:
                print("Operator case not handled yet")
                return None

    # Start processing from the root with index 0
    if isinstance(formula, Leaf):
        handle_leaf(formula, formula.interval, 0)
    elif isinstance(formula, Attack_tree):
        process_tree(formula, formula.root.interval, 0)

    # Ensure all intervals in the trace are disjoint
    for i in range(len(trace)):
        for j in range(i + 1, len(trace)):
            ttei_i = Event.inter(trace[i])
            ttei_j = Event.inter(trace[j])
            ttb_i = Z3interval.ti(ttei_i)
            ttf_i = Z3interval.ts(ttei_i)
            ttb_j = Z3interval.ti(ttei_j)
            ttf_j = Z3interval.ts(ttei_j)
            disjoint_constraint = Or(ttf_i <= ttb_j, ttf_j <= ttb_i)
            solver.add(Implies(And(active_events[i], active_events[j]), disjoint_constraint))

    # Constraint to limit the number of active events to at most n
    solver.add(Sum([If(event_active, 1, 0) for event_active in active_events]) <= n)

    return solver

# Example usage
Insert_rem = Leaf("IRID", 4, 100)
Open_inf = Leaf("OID", 2, 1)

Injectionvia = Node("&", Interval(5, 10), "IVRD")

Tree_injection = Attack_tree(Injectionvia, Open_inf, Insert_rem)

def synthetize(formula: Attack_tree, n: int):
    global active_events  # Ensure this variable is global
    solver = z3_attack_model(formula, n)
    for c in solver.assertions():
        print(c)
    if solver.check() == sat:
        m = solver.model()
        synthesized_trace = []
        print("Satisfiable trace:")
        for i in range(len(trace)):
            event = trace[i]
            if is_true(m.eval(active_events[i])):
                idtt = m.evaluate(Event.name(event))
                interval = m.evaluate(Event.inter(event))
                ttb = m.evaluate(Z3interval.ti(interval))
                ttf = m.evaluate(Z3interval.ts(interval))
                synthesized_trace.append((idtt, ttb, ttf))
                print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}")
        return synthesized_trace
    else:
        print("No satisfiable trace exists.")
        return []

# The durations of the events (2 and 4) within the same interval [5, 10] should overlap,
# making it impossible to satisfy both at the same time.
synthesized_trace = synthetize(Tree_injection, 3)  # Specify the maximum number of events in the trace
print(f"Synthesized Trace: {synthesized_trace}")
