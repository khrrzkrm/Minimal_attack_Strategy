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


# def LeafToZ3(leaf:Leaf,root:Node,sol:z3.Solver,bound:int)->(z3.Solver):
#     label='pt'+leaf.name
#     i= Int(label)
#     event_i= Select(trace, i)
#     ttei = Event.inter(event_i)
#     tidt = Event.name(event_i)
#     rootint = to_z3interval(root.interval)
#     clauses = []
#     for x in range(bound):
#             clauses.append(And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration, tidt==leaf.name,i==x))
#     sol.add(And(Z3interval.ti(ttei)>= Z3interval.ti(rootint), Z3interval.ts(ttei)<= Z3interval.ts(rootint), Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration, tidt==leaf.name,i<=bound))
#     return sol
    

def LeafToZ3(leaf:Leaf,root:Node,sol:z3.Solver,bound:z3.ArithRef,trace:z3.ArrayRef)->(BoolRef):
            pointer=leaf.name+'_pointer'
            boolean=Bool(leaf.name+'_bool')
            i= Int(pointer)
            event_i= Select(trace, i)
            ttei = Event.inter(event_i)
            tidt = Event.name(event_i)
            cost = Event.q(event_i)
            rootint = to_z3interval(root.interval)
            leafcost=leaf.cost
            clauses = []
            sol.add(Implies(boolean,And(Z3interval.ti(ttei)>= Z3interval.ti(rootint),
                        Z3interval.ts(ttei)<= Z3interval.ts(rootint),
                        Z3interval.ts(ttei) - Z3interval.ti(ttei)   == leaf.duration,
                        cost==leafcost, tidt==leaf.name,i<=bound, 0<=i)))
            
            
            return boolean
            # for x in range(bound):
            #     clauses.append(i == x)
            # sol.add(Or(clauses))
            # sol.add(And(Z3interval.ti(ttei) >= Z3interval.ti(rootint),
            # Z3interval.ts(ttei) <= Z3interval.ts(rootint),
            # Z3interval.ts(ttei) - Z3interval.ti(ttei) == leaf.duration,
            # tidt == leaf.name,
            # Sum([If(i == x, 1, 0) for x in range(bound)]) == 1 ))
            # return sol

def z3_attack_solver(formula:Attack_tree,sol:z3.Solver,trace:z3.ArrayRef) -> (BoolRef):
    cost_sum = Int('cost_sum')
    bouninho=Int('bound')
    b=count_leaf_nodes(formula)
    match formula:
        case Attack_tree(left=left, root=root, right=right):
            if(isinstance(left,Attack_tree)):
                bool_l=z3_attack_solver(left,sol,trace)
            elif(isinstance(left,Leaf)):
               bool_l=LeafToZ3(left,root,sol,bouninho,trace)
            if(isinstance(right,Attack_tree)):
                bool_r=z3_attack_solver(right,sol,trace)
            elif(isinstance(right,Leaf)):
                bool_r=LeafToZ3(right,root,sol,bouninho,trace)
                
            
            if root.operator=='&':
                return And(bool_l, bool_r)
            elif root.operator=='||':
               return Xor(bool_l, bool_r)
            else: 
                print("case not handeled yet")
                print("case not handeled yet")
                return None
           
  




# Example usage:
interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem=Leaf("IRID",5,70)
Open_inf=Leaf("OID",4,1)
Send_virus=Leaf("ASVVI",29,30 )
Loading_main=Leaf("LMD",1,0 )
Steal_cert=Leaf("SDC",1,1 )

Injectionvia=Node("&",Interval(5,16),"IVRD")
Infectingac=Node("&",Interval(3,40),"IC")
selfi=Node("||",Interval(10,200),"SI")

Tree_injection= Attack_tree(Injectionvia,Open_inf , Insert_rem)
Tree_infecting= Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI= Attack_tree(selfi,Steal_cert,Tree_infecting)

def synthetize(formula:Attack_tree) -> ():
        trace = Array('trace', IntSort(), Event)
        formula1=propagate(formula)
        if(isinstance(formula1,Attack_tree)):
            draw_attack_tree(formula1, 'test')
            temp_sol=Solver() 
            bouninho=Int('bound')
            bound=count_leaf_nodes(formula)
            temp_sol.add(And(bouninho<=bound+1, bouninho>=0))
            for i in range(bound):
                ttei_i = Event.inter(trace[i])
                ttei_j = Event.inter(trace[i+1])
                ttmax = Z3interval.ts(ttei_i)
                ttmin = Z3interval.ti(ttei_j)
                temp_sol.add(ttmax<ttmin) 
            # iridpoint= Int('IRID_pointer')
            # aswipoint= Int('ASVVI_pointer')
            # oidpoint= Int('OID_pointer')
            #temp_sol.add(And(oidpoint!=aswipoint, aswipoint!= iridpoint, iridpoint!=oidpoint))
            root_expr= z3_attack_solver(formula1,temp_sol,trace)
            temp_sol.add(root_expr)
            for b in temp_sol.assertions():
                print(b)
            if temp_sol.check() == sat:
                m = temp_sol.model()
                print("Satisfiable trace:")
                cost=0
                for i in range(5):
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
            else:
                print("no solution")
        else: 
            for c in formula1:
                print(c)
                 

synthetize(Tree_infecting)
            
            
            
            

            

    
