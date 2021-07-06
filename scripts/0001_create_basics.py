
from shifts.models import *
from members.models import *


def main():

    print('Creating shifts slots')

    # morningSlot = Slot(name='Morning', hour_start='07:00:00', hour_end='15:00:00', abbreviation='AM')
    # morningSlot.save()
    # afternoonSlot = Slot(name='Afternoon', hour_start='14:00:00', hour_end='21:00:00', abbreviation='PM')
    # afternoonSlot.save()
    # slot = Slot(name='Normal Working Hours', hour_start='08:00:00', hour_end='17:00:00', abbreviation='NWH')
    # slot.save()

    slot = Slot(name='Normal Working Hours', hour_start=datetime.time(8,0,0), hour_end=datetime.time(16,30,0), abbreviation='NWH', color='#47844D', op=True)
    slot.save()
    slot = Slot(name='Afternoon', hour_start=datetime.time(12, 30, 0), hour_end=datetime.time(16, 30, 0), abbreviation='PM', color='#999999', op=True)
    slot.save()
    slot = Slot(name='Morning', hour_start=datetime.time(6,0,0), hour_end=datetime.time(14,00,0), abbreviation='AM', color='#47844D')
    slot.save()
    slot = Slot(name='Evening', hour_start=datetime.time(14, 0, 0), hour_end=datetime.time(22, 00, 00), abbreviation='EV', color='#4E779A')
    slot.save()
    slot = Slot(name='Night', hour_start=datetime.time(22, 0, 0), hour_end=datetime.time(6, 0, 0), abbreviation='NG', color='#222222')
    slot.save()
    slot = Slot(name='OnCall', hour_start=datetime.time(8,0,0), hour_end=datetime.time(16,30,0), abbreviation='OC', color='#47844D')
    slot.save()

    slot = Slot(name='Linac Evening Shift', hour_start=datetime.time(15,30,0), hour_end=datetime.time(23,30,0), abbreviation='LES', color='#999999')
    slot.save()
    slot = Slot(name='Linac Morning Shift', hour_start=datetime.time(7,30,0), hour_end=datetime.time(15,30,0), abbreviation='LMS', color='#47844D')
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
    roleLM = ShiftRole(name='Office', abbreviation='OFF')
    roleLM.save()
    print('Done.')

if __name__ == '__main__':
    main()
