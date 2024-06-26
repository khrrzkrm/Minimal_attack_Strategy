from z3 import *
from AttackT_Struct import Attack_tree,Interval,Leaf,Node,propagate,generate_tikz_code,draw_attack_tree,count_leaf_nodes
# Define the event datatypefrom z3 import *
import random

Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval',('ti',IntSort()),('ts',IntSort()))
Z3interval = Z3interval.create()
Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval),('q',IntSort()))
Event = Event.create()
Trace = ArraySort(IntSort(), Event)

def to_z3interval(interval):
    # Create the Z3 interval using the mk_interval constructor
    z3_interval = Z3interval.mk_interval(interval.tmin, interval.tmax)
    return z3_interval

def generate_disjoint_constraints(interval1, interval2):
    # Extract the tmin and tmax fields from the intervals
    interval1_tmin = Z3interval.tmin(interval1)
    interval1_tmax = Z3interval.tmax(interval1)
    interval2_tmin = Z3interval.tmin(interval2)
    interval2_tmax = Z3interval.tmax(interval2)
    
    # Create constraints to ensure the intervals do not intersect
    # For the intervals to be disjoint: tmax1 < tmin2 or tmax2 < tmin1
    disjoint_constraint = Or(interval1_tmax < interval2_tmin, interval2_tmax < interval1_tmin)
    
    return disjoint_constraint

def LeafToZ3(leaf:Leaf,root:Node,sol:z3.Solver,bound:int,trace:z3.ArrayRef)->(BoolRef):
            label=leaf.name
            i= Int(label)
            event_i= Select(trace, i)
            ttei = Event.inter(event_i)
            tidt = Event.name(event_i)
            cost = Event.q(event_i)
            rootint = to_z3interval(root.interval)
            leafcost=leaf.cost
            clauses = []
            #sol.add(Implies(Bool(leaf.name),And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration,cost==leafcost, tidt==leaf.name,i<=bound,i>=0)))
            sol.assert_and_track(And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration,cost==leafcost, tidt==leaf.name,i<=bound,i>=0),Bool(leaf.name))
            return Bool(leaf.name)


def z3_attack_solver(formula:Attack_tree,sol:z3.Solver,bound:Int,trace:z3.ArrayRef) -> (BoolRef):
    cost_sum = Int('cost_sum')
    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if(isinstance(left,Attack_tree)):
                bool_l=z3_attack_solver(left,sol,bound,trace)
            elif(isinstance(left,Leaf)):
               bool_l=LeafToZ3(left,root,sol,bound,trace)
            if(isinstance(right,Attack_tree)):
                bool_r=z3_attack_solver(right,sol,bound,trace)
            elif(isinstance(right,Leaf)):
                bool_r=LeafToZ3(right,root,sol,bound,trace)
                
            
            if root.operator=='&':
                temp_bool= Bool(root.name)
                sol.assert_and_track(And(bool_l, bool_r),temp_bool)
                return temp_bool
            elif root.operator=='||':
               return Xor(bool_l, bool_r)
            else: 
                print("case not handeled yet")
                return None
            
def synthetize(formula:Attack_tree) -> ():
        trace = Array('trace', IntSort(), Event)
        formula1=propagate(formula)
        if(isinstance(formula1,Attack_tree)):
            draw_attack_tree(formula1, 'test')
            n=count_leaf_nodes(formula1)
            for x in range(0,n+1):
                temp_sol=Solver() 
                temp_sol.set(unsat_core=True)
                for i in range(x):
                    ttei_i = Event.inter(trace[i])
                    ttei_j = Event.inter(trace[i+1])
                    ttmax = Z3interval.ts(ttei_i)
                    ttmini= Z3interval.ti(ttei_i)
                    ttmin = Z3interval.ti(ttei_j)
                    ttmaxj = Z3interval.ts(ttei_j)
                    temp_sol.assert_and_track(And(ttmax<=ttmin,ttmini<=ttmax, ttmin <= ttmaxj),Bool(i))
                print(f"new bound{x}")
                # print(f"new boud{x}")
                root_expr= z3_attack_solver(formula1,temp_sol,x,trace)
                temp_sol.assert_and_track(root_expr,Bool('root'))
                for b in temp_sol.assertions():
                    print(b)
                if temp_sol.check() == sat:
                    m = temp_sol.model()
                    print("Satisfiable trace:")
                    cost=0
                    for i in range(x+1):
                        event = Select(trace, i)
                        idtt = m.evaluate(Event.name(event))
                        interval = m.evaluate(Event.inter(event))
                        ttb = m.evaluate(Z3interval.ti(interval))
                        ttf = m.evaluate(Z3interval.ts(interval))
                        costl = m.evaluate(Event.q(event))
                        print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf},cost={costl}")
                        cost=cost+costl.as_long()
                    print(f"the total cost of this attack is {cost}")
                    return
            if temp_sol.check() == unsat:
                for c in temp_sol.assertions():
                    print(c)
                core = temp_sol.unsat_core()
                print(f"timed scheduling at max length {x} conflinct between:")
                for c in core:
                    print(c)          
        else: 
            for c in formula1:
                print(c)

def optimize(formula:Attack_tree) -> ():
        trace = Array('trace', IntSort(), Event)
        formula1=propagate(formula)
        if(isinstance(formula1,Attack_tree)):
            draw_attack_tree(formula1, 'test')
            n=count_leaf_nodes(formula1)
            for x in range(1,n):
                #print(f"new boud{x}")
                # print(f"new boud{x}")
                temp_opt=Optimize() 
                Bool_exp= z3_attack_solver(formula1,temp_opt,x,trace)
                temp_opt.assert_and_track(Bool_exp)
                costs=[]
                cost_sum = Int('cost_sum')
                trace_positions = [Int(f'trace_pos_{i}') for i in range(4)]
                temp_opt.add(Distinct(trace_positions))
                for i in range (x):
                    event_i= Select(trace, i)
                    cost = Event.q(event_i)
                    costs.append(cost)
                temp_opt.add(cost_sum==Sum(costs))
                temp_opt.minimize(cost_sum)
                # for c in temp_opt.assertions(): 
                #       print(c)
                if temp_opt.check() == sat:
                    m = temp_opt.model()
                    cost=0
                    for i in range(x+1):
                        event = Select(trace, i)
                        idtt = m.evaluate(Event.name(event))
                        interval = m.evaluate(Event.inter(event))
                        ttb = m.evaluate(Z3interval.ti(interval))
                        ttf = m.evaluate(Z3interval.ts(interval))
                        costl = m.evaluate(Event.q(event))
                        v=0
                        if ttb.as_long() <= ttf.as_long():
                          print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost = {costl}")
                          cost=cost+costl.as_long()
                          v=v+1
                    print(f"This is the minimal cost attack of length {x-v}, the total cost: {cost}")
                    print(f"new length:")
                    
                else:
                    print(F"no local optimum for {x} ")
        else: 
            for c in formula1:
                print(c)

# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem=Leaf("IRID",5,10)
Open_inf=Leaf("OID",5,14)
Send_virus=Leaf("ASVVI",1,30 )
Loading_main=Leaf("LMD",1,0 )
Steal_cert=Leaf("SDC",1,1 )

Injectionvia=Node("&",Interval(5,16),"IVRD")
Infectingac=Node("&",Interval(3,40),"IC")
selfi=Node("&",Interval(10,200),"SI")

Tree_injection= Attack_tree(Injectionvia,Open_inf , Insert_rem)
Tree_infecting= Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI= Attack_tree(selfi,Steal_cert,Tree_infecting)


                 

synthetize(Tree_SI)
            
            
            
            

            

    
