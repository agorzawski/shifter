
from shifts.models import *
from members.models import *


def main():

    print('Creating shifts slots')

    morningSlot = Slot(name='Morning', hour_start='07:00:00', hour_end='15:00:00', abbreviation='AM')
    morningSlot.save()
    afternoonSlot = Slot(name='Afternoon', hour_start='14:00:00', hour_end='21:00:00', abbreviation='PM')
    afternoonSlot.save()
    slot = Slot(name='Normal Working Hours', hour_start='08:00:00', hour_end='17:00:00', abbreviation='NWH')
    slot.save()

    print('Creating Member roles')
    roleLM = Role(name='LineManager', priority=50, abbreviation='LM')
    roleLM.save()
    roleLM = Role(name='ShiftLeader', priority=10, abbreviation='SL')
    roleLM.save()
    roleLM = Role(name='TS2ShiftLeader', priority=10, abbreviation='TS2SL')
    roleLM.save()
    roleLM = Role(name='Operator', priority=30, abbreviation='OP')
    roleLM.save()
    roleLM = Role(name='SystemExpert', abbreviation='SE')
    roleLM.save()

    print('Creating Shifts roles')
    roleLM = ShiftRole(name='TS2 Support', abbreviation='TS2S')
    roleLM.save()
    roleLM = ShiftRole(name='OnCall', abbreviation='OC')
    roleLM.save()
    roleLM = ShiftRole(name='OnCall Electrical', abbreviation='OCE')
    roleLM.save()
    roleLM = ShiftRole(name='OnCall PSS', abbreviation='OCPSS')
    roleLM.save()
    roleLM = ShiftRole(name='OnCall Cryogenics', abbreviation='OCC')
    roleLM.save()
    roleLM = ShiftRole(name='OnCall Infra', abbreviation='OCI')
    roleLM.save()

    print('Done.')

if __name__ == '__main__':
    main()
