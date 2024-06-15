from z3 import *

# Define the interval and event datatypes
Z3interval = Datatype('Interval')
Z3interval.declare('mk_interval', ('name', StringSort()), ('ti', IntSort()), ('ts', IntSort()))
Z3interval = Z3interval.create()

Event = Datatype('Event')
Event.declare('mk_event', ('name', StringSort()), ('inter', Z3interval), ('q', IntSort()))
Event = Event.create()

# Create solver
solver = Solver()
solver.set(unsat_core=True)

# Define variables
ASVVI = Bool('ASVVI')
OID = Bool('OID')
IRID = Bool('IRID')
IVRD = Bool('IVRD')
IC = Bool('IC')
root = Bool('root')
interval_ASVVI = Z3interval.mk_interval(String('interval_ASVVI'), Int('ti_ASVVI'), Int('ts_ASVVI'))
interval_OID = Z3interval.mk_interval(String('interval_OID'), Int('ti_OID'), Int('ts_OID'))
interval_IRID = Z3interval.mk_interval(String('interval_IRID'), Int('ti_IRID'), Int('ts_IRID'))
ti_ASVVI = Z3interval.ti(interval_ASVVI)
ts_ASVVI = Z3interval.ts(interval_ASVVI)
ti_OID = Z3interval.ti(interval_OID)
ts_OID = Z3interval.ts(interval_OID)
ti_IRID = Z3interval.ti(interval_IRID)
ts_IRID = Z3interval.ts(interval_IRID)

# Add the constraints for ASVVI
solver.assert_and_track( And(ti_ASVVI >= 3,
        ts_ASVVI <= 40,
        ts_ASVVI - ti_ASVVI == 1,
        Event.q(Event.mk_event(String('ASVVI'), interval_ASVVI, 30)) == 30,
        Event.name(Event.mk_event(String('ASVVI'), interval_ASVVI, 30)) == String('ASVVI')),ASVVI
   )

# Add the constraints for OID
solver.add(Implies(OID, And(ti_OID >= 5,
        ts_OID <= 16,
        ts_OID - ti_OID == 9,
        Event.q(Event.mk_event(String('OID'), interval_OID, 14)) == 14,
        Event.name(Event.mk_event(String('OID'), interval_OID, 14)) == String('OID'))))

# Add the constraints for IRID
solver.add(
    And(ti_IRID >= 5,
        ts_IRID <= 16,
        ts_IRID - ti_IRID == 8,
        Event.q(Event.mk_event(String('IRID'), interval_IRID, 10)) == 10,
        Event.name(Event.mk_event(String('IRID'), interval_IRID, 10)) == String('IRID')),IRID)

# Add IVRD dependency constraint
solver.add(Implies(IVRD, And(OID, IRID)))

# Add disjoint constraint for OID and IRID
solver.assert_and_track(
    Or(ts_OID <= ti_IRID, ts_IRID <= ti_OID),Bool('Dis(interval_OID, interval_IRID)'))

# Add IC dependency constraint
solver.add(Implies(IC, Xor(ASVVI, IVRD)))

# Add root dependency constraint
solver.add(Implies(root, IC))

# Ensure that root is true
solver.add(root == True)

for c in solver.assertions():
    print(c)
# Check satisfiability
if solver.check() == sat:
    model = solver.model()
    print("Satisfiable with root true")
    for d in model.decls():
        print(f"{d.name()} = {model[d]}")
else:
    print("Unsatisfiable with root true")
    core = solver.unsat_core()
    print("Unsat core:")
    for c in core:
        print(c)
