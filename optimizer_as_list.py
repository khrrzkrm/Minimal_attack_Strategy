from z3 import *
from AttackT_Struct import Attack_tree,Interval,Leaf,Node,propagate,generate_tikz_code,draw_attack_tree,count_leaf_nodes
# Define the event datatypefrom z3 import *
import random

Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('name', StringSort()),('ti',IntSort()),('ts',IntSort()))
Z3interval = Z3interval.create()
Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval),('q',IntSort()))
Event = Event.create()



def LeafToZ3(leaf: Leaf, root: Node, sol: z3.Solver, intervals: set,costs:list,) -> (BoolRef, set,list):
    inter_i = String('interval_' + leaf.name)
    infi = Int('ti_' + leaf.name)
    supi = Int('ts_' + leaf.name)
    interv = Z3interval.mk_interval(inter_i, infi, supi)
    event_i = Event.mk_event(String(leaf.name), interv, leaf.cost)
    
    min_val = root.interval.tmin
    max_val = root.interval.tmax
    
    intervals.add((interv, inter_i))
    
    sol.add(Implies(Bool(leaf.name),And(
        infi >= min_val,
        supi <= max_val,
        supi - infi == leaf.duration,
        Event.q(event_i) == leaf.cost,
        Event.name(event_i) == String(leaf.name)
    )))
    costs.append(If(Bool(leaf.name), leaf.cost, 0))
    
    return Bool(leaf.name), intervals,costs


    
def z3_attack_solver(formula:Attack_tree,sol:z3.Solver,intervals:set,costs:list) -> (BoolRef,set,list):
    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if(isinstance(left,Attack_tree)):
                #intervals=set()   
                bool_l,l,costsl=z3_attack_solver(left,sol,intervals,costs)
            elif(isinstance(left,Leaf)):
                intervals=set()  
                bool_l,l,costsl=LeafToZ3(left,root,sol,intervals,costs)
            if(isinstance(right,Attack_tree)):
                #intervals=set()  
                bool_r,r,cotsr=z3_attack_solver(right,sol,intervals,costs)
            elif(isinstance(right,Leaf)):
                intervals=set()  
                bool_r,r,cotsr=LeafToZ3(right,root,sol,intervals,costs) 
            if root.operator=='&':
                temp_bool= Bool(root.name)
                #sol.add(Implies(temp_bool,And(bool_l, bool_r)))
                sol.assert_and_track(Implies(temp_bool,And(bool_l, bool_r)),f'solving{temp_bool}')
                for i in l:
                    vi, namei = i
                    ti_i = Z3interval.ti(vi)
                    ts_i = Z3interval.ts(vi)
                    for j in r:
                        vj, namej = j
                        ti_j = Z3interval.ti(vj)
                        ts_j = Z3interval.ts(vj)
                        sol.assert_and_track(Or(ts_i <= ti_j, ts_j <= ti_i),Bool(f"Disjoint({namei},{namej})"))
                    
                intervals= l | r
                return temp_bool,intervals,costs
            elif root.operator=='||':
                temp_bool= Bool(root.name)
                sol.add(Implies(temp_bool,Xor(bool_l, bool_r)))
                intervals= l | r
                return temp_bool,intervals,costs
            else: 
                print("case not handeled yet")
                return None

def get_true_bools(model):
    true_bools = []
    for d in model.decls():
        if is_bool(model[d]) and is_true(model[d]):
            true_bools.append(d.name())
    return true_bools

def collect_intervals(model, true_bools):
    intervals = []
    for prefix in true_bools:
        ti_name = f"ti_{prefix}"
        ts_name = f"ts_{prefix}"
        ti = model.eval(Int(ti_name), model_completion=True)
        ts = model.eval(Int(ts_name), model_completion=True)
        if ti.as_long() !=0 and ts.as_long() !=0:
            intervals.append((prefix, (ti, ts)))
    return intervals




def synthetize(formula:Attack_tree) -> ():
        formula1=propagate(formula)
        if(isinstance(formula1,Attack_tree)):
            #draw_attack_tree(formula1, 'test')
            temp_sol=Solver() 
            temp_sol.set(unsat_core=True)
            intervals=set()
            root_expr,intervals,forget= z3_attack_solver(formula1,temp_sol,intervals,[])
            temp_sol.assert_and_track(root_expr,Bool('root'))
            temp_sol.add(Bool('root') == True)
            # for b in temp_sol.assertions():
            #      print(b)
            if temp_sol.check() == sat:
                m = temp_sol.model()
                print("Possible attack by model:")
                tb=get_true_bools(m)
                for t in tb:
                    print(t)
                print("Attack Timing is:")
                solution= collect_intervals(m,tb)
                for name,i in solution:
                    print(F"{name} assigned to {i}")
                
                
            elif temp_sol.check() == unsat:
                core = temp_sol.unsat_core()
                print(f"Unsat Core is:")
                for c in core:
                    print(c)
        else:
            print("the attack tree the following problem:")
            for c in formula1:
                print(c)       
                
def optimize(formula:Attack_tree) -> ():
        formula1=propagate(formula)
        #draw_attack_tree(formula1, 'test')
        if(isinstance(formula1,Attack_tree)):
            temp_sol=Optimize() 
            intervals=set()
            root_expr,intervals,costs= z3_attack_solver(formula1,temp_sol,intervals,[])
            temp_sol.assert_and_track(root_expr,Bool('root'))
            temp_sol.add(Bool('root') == True)
            temp_sol.minimize(Sum(costs))
            #for b in temp_sol.assertions():
            #    print(b)
            if temp_sol.check() == sat:
                m = temp_sol.model()
                min_cost = m.eval(Sum(costs))
                print(f"Minimal cost attack has the: {min_cost}")
                tb=get_true_bools(m)
                print("Attack Timing is:")
                # for d in m.decls():
                #     print(d)
                solution= collect_intervals(m,tb)
                for name,i in solution:
                    print(F"{name} assigned to {i}")
                
                
            elif temp_sol.check() == unsat:
                core = temp_sol.unsat_core()
                print(f"Unsat Core is:")
                for c in core:
                    print(c)
        else:
            print("the attack tree the following problem:")
            for c in formula1:
                print(c)                       
                    
                    



        