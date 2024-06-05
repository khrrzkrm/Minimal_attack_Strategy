from z3 import *
from AttackT_Struct import Attack_tree,Interval,Node
# Define the event datatypefrom z3 import *
import random
Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('t_b', IntSort()),('t_f', IntSort()))
Event = Event.create()
Trace = ArraySort(IntSort(), Event)
# Declare the array with fixed length
trace = Array('trace', IntSort(), Event)

def z3_strategy_optimizer(formula:Attack_tree) -> (z3.Optimize):
    opt = Optimize()
    cost_sum = Int('cost_sum')
    cost_elements = []
    match formula:
        case Node(name=name, interval=interval,duration=duration, cost=c):
            label='pt'+name
            i= Int(label)
            event_i= Select(trace, i)
            ttb=Event.t_b(event_i)
            ttf=Event.t_f(event_i)
            tidt=Event.name(event_i)
            t_min= interval.tmin
            t_max= interval.tmax
            opt.add(And(ttb >= t_min, ttf<= t_max, ttf-ttb  == duration, tidt==name))
            cost_elements.append(c)
        case Attack_tree(left=left, operator='&', right=right):
            opt_l=z3_strategy_optimizer(left)
            opt_r= z3_strategy_optimizer(right)
            combine_solvers_and(opt_l, opt_r)
            opt=opt_l
        case _:
            print("Unsupported formula type", file=sys.stderr)
    opt.add(cost_sum == sum(cost_elements))
    opt.minimize(cost_sum)
    return opt
            
            
            
            
def combine_solvers_and(left_solver, right_solver):
    for constraint in right_solver.assertions():
        left_solver.add(constraint)
            
        
        
def synthetize(formula:Attack_tree) -> ():
        temp_opt=Optimize()
        temp_opt=z3_strategy_optimizer(formula)
        for c in temp_opt.assertions(): 
             print(c)
        if temp_opt.check() == sat:
            m = temp_opt.model()
            print("Satisfiable trace with minimum cost:")
            print(x)
            for i in range(x):
                event = Select(trace, i)
                idtt = m.evaluate(Event.name(event))
                time_stamp1 = m.evaluate(Event.t_b(event))
                time_stamp2 = m.evaluate(Event.t_f(event))
                print(f"Event {i}: Node = {idtt}, Start_time = {time_stamp1}, End_time = {time_stamp2}")
            return
        else:
            core = temp_opt.unsat_core()
            for c in core:
                print(c)
            print("No satisfiable trace exists.")
    
interval1 = Interval(1, 100)
interval2 = Interval(0, 100)
Node_1 = Node("n_1", interval1, 10,12)
print(type(Node_1))
Node_2 = Node('n_2', interval2, 5,7)
Conjunction= Attack_tree(Node_1, '&', Node_2)

synthetize(Conjunction)