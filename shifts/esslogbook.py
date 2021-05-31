import elog


class LogEntry:

    def __init__(self, author=None, subject=None, body=None, tags=[], date=None, shiftId=None):
        self.author = author
        self.subject = subject
        self.body = body
        self.tags = tags
        self.date = date
        self.shiftId = shiftId


def getLogbook(user=None, password=None, urlLogbook='https://ics-elog-test.esss.lu.se', nameLogbook='Operation'):
    return elog.open(urlLogbook,
                     logbook=nameLogbook,
                     user=user,
                     password=password,
                     use_ssl=True)


def getEntries(logbook, shiftId):
    return (LogEntry(author='Arek', shiftId='20210528X', body='<h4> summary</h4><b>nice entry</b>', date='some date', subject='PSS1 problem'),
            LogEntry(author='Arek', shiftId='20210528X', body='<h4> PSS1 summary</h4><b>nice entry</b>', date='some date', subject='PSS1 problem solved'),)


def createEntry(logbook, entry_body, dict_of_attributes):
    new_msg_id = logbook.post(entry_body, attributes=dict_of_attributes, encoding='HTML')


def prepareBeamModeChange(logbook, shiftId, shiftLeader, operator, shiftLeaderPhone):
    pass


if __name__ == "__main__":
    pass