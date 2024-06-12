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

# Declare the array with fixed length


# def LeafToZ3(leaf:Leaf,root:Node,opt:z3.Solver,bound:int)->(z3.Solver):
#     label='pt'+leaf.name
#     i= Int(label)
#     event_i= Select(trace, i)
#     ttei = Event.inter(event_i)
#     tidt = Event.name(event_i)
#     rootint = to_z3interval(root.interval)
#     clauses = []
#     for x in range(bound):
#             clauses.append(And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration, tidt==leaf.name,i==x))
#     opt.add(And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration, tidt==leaf.name,i<=bound))
#     return opt
    

def LeafToZ3O(leaf:Leaf,root:Node,opt:z3.Solver,bound:int,trace:z3.ArrayRef)->(z3.Optimize):
            label='pt'+leaf.name
            i= Int(label)
            event_i= Select(trace, i)
            cost = Event.q(event_i)
            ttei = Event.inter(event_i)
            tidt = Event.name(event_i)
            
            rootint = to_z3interval(root.interval)
            leafcost=leaf.cost
            clauses = []
            for x in range(bound):
                clauses.append(And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration,cost==leafcost, tidt==leaf.name,i==x))
            opt.add(Or(clauses))
            return opt
            # for x in range(bound):
            #     clauses.append(i == x)
            # opt.add(Or(clauses))
            # opt.add(And(Z3interval.ti(ttei) >= Z3interval.ti(rootint),
            # Z3interval.ts(ttei) <= Z3interval.ts(rootint),
            # Z3interval.ts(ttei) - Z3interval.ti(ttei) == leaf.duration,
            # tidt == leaf.name,
            # Sum([If(i == x, 1, 0) for x in range(bound)]) == 1 ))
            # return opt

def z3_attack_optimizer(formula:Attack_tree,bound:Int,trace:z3.ArrayRef) -> (z3.Solver,Int):
    opt = Optimize()
    total_cost = Int('total_cost')
    leaf_costs = []
    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if(isinstance(left,Attack_tree)):
                opt_l=z3_attack_optimizer(left,bound,trace)
            elif(isinstance(left,Leaf)):
                opt_l=Optimize()
                LeafToZ3O(left,root,opt_l,bound,trace)
            if(isinstance(right,Attack_tree)):
                opt_r=z3_attack_optimizer(right,bound,trace)
            elif(isinstance(right,Leaf)):
                opt_r=Optimize()
                LeafToZ3O(right,root,opt_r,bound,trace)
                
            
            if root.operator=='&':
                combined_assertions = And(*opt_l.assertions(), *opt_r.assertions())
                opt.add(combined_assertions)
            elif root.operator=='||':
                if len(opt_l.assertions()) == 1 or len(opt_r.assertions()) == 1:
                    combined_assertions = Xor(opt_l.assertions()[0], opt_r.assertions()[0])
                elif len(opt_l.assertions()) > 1 or len(opt_r.assertions()) > 1:
                    combined_assertions = Or(And(*opt_l.assertions()), And(*opt_r.assertions()))
                else:
                    raise ValueError("Unexpected number of assertions")
                opt.add(combined_assertions)
                #print(combined_assertions)
            else: 
                print("case not handeled yet")
                return None

    for i in range(bound-1):
        ttei_i = Event.inter(trace[i])
        ttei_j = Event.inter(trace[i+1])
        ttmax = Z3interval.ts(ttei_i)
        ttmin = Z3interval.ti(ttei_j)
        opt.add(ttmax<=ttmin)
    return opt




# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem=Leaf("IRID",5,10)
Open_inf=Leaf("OID",4,1)
Send_virus=Leaf("ASVVI",29,30 )
Loading_main=Leaf("LMD",1,0 )
Steal_cert=Leaf("SDC",1,1 )

Injectionvia=Node("&",Interval(5,16),"IVRD")
Infectingac=Node("||",Interval(3,40),"IC")
selfi=Node("&",Interval(10,200),"SI")

Tree_injection= Attack_tree(Injectionvia,Open_inf , Insert_rem)
Tree_infecting= Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI= Attack_tree(selfi,Steal_cert,Tree_infecting)

def optimize(formula:Attack_tree) -> ():
        trace = Array('trace', IntSort(), Event)
        formula1=propagate(formula)
        if(isinstance(formula1,Attack_tree)):
            #draw_attack_tree(formula1, 'test')
            n=count_leaf_nodes(formula1)
            for x in range(3,n+1):
                #print(f"new boud{x}")
                # print(f"new boud{x}")
                temp_opt=Optimize() 
                temp_opt= z3_attack_optimizer(formula1,x,trace)
                costs=[]
                cost_sum = Int('cost_sum')
                for i in range (x):
                    event_i= Select(trace, i)
                    cost = Event.q(event_i)
                    costs.append(cost)
                temp_opt.add(cost_sum==Sum(costs))
                temp_opt.minimize(cost_sum)
                # for c in temp_opt.assertions(): 
                #     print(c)
                if temp_opt.check() == sat:
                    m = temp_opt.model()
                    cost=0
                    for i in range(x):
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
                    print(F"no solution for {x} ")
        else: 
            print("not a three")
                 

optimize(Tree_SI)
            
            
            
            

            

    
