from z3 import *

# Define the event datatype
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval), ('q', IntSort()))
Event = Event.create()

trace = Array('trace', IntSort(), Event)

# Declare the variables
bound = Int('bound')
ASVVI_pointer = Int('ASVVI_pointer')
OID_pointer = Int('OID_pointer')
IRID_pointer = Int('IRID_pointer')

# Define the boolean variables
ASVVI_bool = Bool('ASVVI_bool')
OID_bool = Bool('OID_bool')
IRID_bool = Bool('IRID_bool')

sol = Solver()

# Group all constraints into one literal
constraints = And(
    # Bound constraints
    And(bound <= 3, bound >= 1),
    
    # Non-overlapping constraints for consecutive events
    ts(inter(trace[0])) <= ti(inter(trace[1])),
    ts(inter(trace[1])) <= ti(inter(trace[2])),
    ts(inter(trace[2])) <= ti(inter(trace[3])),
    
    # Event constraints for ASVVI with implication
    Implies(ASVVI_bool, And(
        ti(inter(trace[ASVVI_pointer])) >= ti(mk_interval(3, 40)),
        ts(inter(trace[ASVVI_pointer])) <= ts(mk_interval(3, 40)),
        ts(inter(trace[ASVVI_pointer])) - ti(inter(trace[ASVVI_pointer])) == 29,
        q(trace[ASVVI_pointer]) == 30,
        name(trace[ASVVI_pointer]) == "ASVVI",
        ASVVI_pointer <= bound,
        ASVVI_pointer >= 0
    )),
    
    # Event constraints for OID with implication
    Implies(OID_bool, And(
        ti(inter(trace[OID_pointer])) >= ti(mk_interval(5, 16)),
        ts(inter(trace[OID_pointer])) <= ts(mk_interval(5, 16)),
        ts(inter(trace[OID_pointer])) - ti(inter(trace[OID_pointer])) == 4,
        q(trace[OID_pointer]) == 1,
        name(trace[OID_pointer]) == "OID",
        OID_pointer <= bound,
        OID_pointer >= 0
    )),
    
    # Event constraints for IRID with implication
    Implies(IRID_bool, And(
        ti(inter(trace[IRID_pointer])) >= ti(mk_interval(5, 16)),
        ts(inter(trace[IRID_pointer])) <= ts(mk_interval(5, 16)),
        ts(inter(trace[IRID_pointer])) - ti(inter(trace[IRID_pointer])) == 5,
        q(trace[IRID_pointer]) == 70,
        name(trace[IRID_pointer]) == "IRID",
        IRID_pointer <= bound,
        IRID_pointer >= 0
    )),
    
    # Final constraint to connect boolean variables
    And(ASVVI_bool, And(OID_bool, IRID_bool))
)

# Add the combined constraints to the solver
sol.add(constraints)

# Check satisfiability
if sol.check() == sat:
    m = sol.model()
    print("Satisfiable trace:")
    cost = 0
    max_size = 4  # Based on bound constraints
    for i in range(max_size):
        if m.eval(Select(trace, i), model_completion=True).decl().kind() != Z3_OP_UNINTERPRETED:
            event = Select(trace, i)
            idtt = m.evaluate(Event.name(event))
            interval = m.evaluate(Event.inter(event))
            ttb = m.evaluate(Z3interval.ti(interval))
            ttf = m.evaluate(Z3interval.ts(interval))
            costl = m.evaluate(Event.q(event))
            print(f"Event {i}: Node = {idtt}, Start_time = {ttb}, End_time = {ttf}, cost={costl}")
            cost += costl.as_long()
        else:
            break
    print(f"The total cost of this attack is {cost}")
else:
    print("No solution")
