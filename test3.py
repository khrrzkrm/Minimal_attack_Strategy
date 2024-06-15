from z3 import *

# Define datatypes
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('name', StringSort()), ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval), ('q', IntSort()))
Event = Event.create()

# Solver setup
solver = Solver()

# Define variables
interval_ASVVI = Const('interval_ASVVI', Z3interval)
ti_ASVVI = Int('ti_ASVVI')
ts_ASVVI = Int('ts_ASVVI')
ASVVI = Bool('ASVVI')

interval_OID = Const('interval_OID', Z3interval)
ti_OID = Int('ti_OID')
ts_OID = Int('ts_OID')
OID = Bool('OID')

interval_IRID = Const('interval_IRID', Z3interval)
ti_IRID = Int('ti_IRID')
ts_IRID = Int('ts_IRID')
IRID = Bool('IRID')

IVRD = Bool('IVRD')
IC = Bool('IC')
root = Bool('root')

# Constraints
solver.add(Implies(ASVVI,
    And(ti_ASVVI >= 3,
        ts_ASVVI <= 40,
        ts_ASVVI - ti_ASVVI == 1,
        q(Event.mk_event(ASVVI,
                         mk_interval(interval_ASVVI, ti_ASVVI, ts_ASVVI),
                         30)) == 30,
        name(Event.mk_event(ASVVI,
                            mk_interval(interval_ASVVI, ti_ASVVI, ts_ASVVI),
                            30)) == ASVVI)))

solver.add(Implies(OID,
    And(ti_OID >= 5,
        ts_OID <= 16,
        ts_OID - ti_OID == 9,
        q(Event.mk_event(OID,
                         mk_interval(interval_OID, ti_OID, ts_OID),
                         14)) == 14,
        name(Event.mk_event(OID,
                            mk_interval(interval_OID, ti_OID, ts_OID),
                            14)) == OID)))

solver.add(Implies(IRID,
    And(ti_IRID >= 5,
        ts_IRID <= 16,
        ts_IRID - ti_IRID == 8,
        q(Event.mk_event(IRID,
                         mk_interval(interval_IRID, ti_IRID, ts_IRID),
                         10)) == 10,
        name(Event.mk_event(IRID,
                            mk_interval(interval_IRID, ti_IRID, ts_IRID),
                            10)) == IRID)))

solver.add(Implies(IVRD, And(OID, IRID)))
solver.add(Implies(IC, Xor(ASVVI, And(OID, IRID))))
solver.add(Implies(root, IC))
solver.add(root == True)
solver.add(ASVVI == True)
solver.add(IVRD == False)
solver.add(OID == False)
solver.add(IRID == False)

# Check satisfiability
if solver.check() == sat:
    print("Satisfiable with ASVVI true, IVRD false, OID false, and IRID false")
    m = solver.model()
    for d in m.decls():
        print(f"{d.name()} = {m[d]}")
else:
    print("Unsatisfiable")
    core = solver.unsat_core()
    print(f"Unsat core: {core}")
