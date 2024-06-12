from z3 import *
from AttackT_Struct import Attack_tree, Interval, Leaf, Node, propagate, generate_tikz_code, draw_attack_tree, count_leaf_nodes

# Define the Z3 interval datatype
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

# Define the event datatype
Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval), ('q', IntSort()))
Event = Event.create()

def to_z3interval(interval):
    return Z3interval.mk_interval(interval.tmin, interval.tmax)

def LeafToZ3(leaf: Leaf, root: Node, sol: z3.Solver) -> (z3.Solver,z3.DatatypeRef):
    label = 'pt' + leaf.name
    event_i = Const(label, Event)
    cost = Event.q(event_i)
    ttei = Event.inter(event_i)
    tidt = Event.name(event_i)
    intervals.append(event_i)
    print(type(event_i))
    rootint = to_z3interval(root.interval)
    leafcost = leaf.cost
    sol.add(
        Z3interval.ti(ttei) >= Z3interval.ti(rootint),
        Z3interval.ts(ttei) <= Z3interval.ts(rootint),
        Z3interval.ts(ttei) - Z3interval.ti(ttei) == leaf.duration,
        cost == leafcost,
        tidt == leaf.name
    )
    return sol,event_i

def z3_attack_solver(formula: Attack_tree,intervals) -> (z3.Solver):
    sol=Solver()
    intervals=[]
    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if(isinstance(left,Attack_tree)):
                print(here)
                sol_l=Solver()
                sol_l,var_l=z3_attack_solver(left,intervals)
                print(len(sol_l.assertions()))
            elif(isinstance(left,Leaf)):
                sol_l=Solver()
                sol_l,intervals_l=LeafToZ3(left,root,sol_l)
            if(isinstance(right,Attack_tree)):
                sol_r=Solver()
                sol_r=z3_attack_solver(right,intervals)
                print(len(sol_r.assertions()))
            elif(isinstance(right,Leaf)):
                sol_r=Solver()
                sol_r,interval_r=LeafToZ3(right,root,sol_r)
            if root.operator=='&':
                combined_assertions = And(*sol_l.assertions(), *sol_r.assertions())
                sol.add(combined_assertions)
            elif root.operator=='||':
                combined_assertions = Or(*sol_l.assertions(), *sol_r.assertions())
                sol.add(combined_assertions)
            else: 
                print("case not handeled yet")
                return None
    return sol,intervals

# def synthetize(formula: Attack_tree) -> ():
#     trace = Array('trace', IntSort(), Event)
#     formula1 = propagate(formula)
#     if isinstance(formula1, Attack_tree):
#         draw_attack_tree(formula1, 'test')
#         n = count_leaf_nodes(formula1)
#         for x in range(0, n + 1):
#             print(f"new bound {x}")
#             temp_opt = z3_attack_solver(formula1, x, trace)
#             for c in temp_opt.assertions():
#                 print(c)
#             if temp_opt.check() == sat:
#                 m = temp_opt.model()
#                 print("Satisfiable trace with minimum cost:")
#                 total_cost = m.evaluate(Int('total_cost')).as_long()
#                 for i in range(x):
#                     event = Select(trace, i)
#                     idtt = m.evaluate(Event.name(event))
#                     interval = m.evaluate(Event.inter(event))
#                     ttb = m.evaluate(Z3interval.ti(interval))
#                     ttf = m.evaluate(Z3interval.ts(interval))
#                     costl = m.evaluate(Event.q(event))
#                     print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost = {costl}")
#                 print(f"The total cost of this attack is {total_cost}")
#                 return
#             else:
#                 print("No solution found for bound", x)
#     else:
#         for c in formula1:
#             print(c)

# Example usage:
Insert_rem = Leaf("IRID", 5, 70)
Open_inf = Leaf("OID", 4, 1)
Send_virus = Leaf("ASVVI", 29, 30)
Loading_main = Leaf("LMD", 1, 0)
Steal_cert = Leaf("SDC", 1, 1)

Injectionvia = Node("||", Interval(5, 16), "IVRD")
Infectingac = Node("&", Interval(3, 40), "IC")
selfi = Node("&", Interval(10, 33), "SI")

Tree_injection = Attack_tree(Injectionvia, Open_inf, Insert_rem)
Tree_infecting = Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI = Attack_tree(selfi, Steal_cert, Tree_infecting)

sol=Solver()
intervals=[]
sol,intervals=z3_attack_solver(Tree_injection ,intervals )
event_i = Const('ptIRID', Event)
event_j = Const('ptOID', Event)
sol.add(Or(event_i,event_j))
#print(len(sol.assertions()))
for c in sol.assertions():
    print(c)
for i in intervals:
    print(i)
