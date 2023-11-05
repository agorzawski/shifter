from django_cron import CronJobBase, Schedule


class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 5

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'shifter.my_cron_job'

    def do(self):
        print("============")
        print('=> simple job every {} minutes'.format(self.RUN_EVERY_MINS))