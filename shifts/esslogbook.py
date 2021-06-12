import elog
import os


class LogEntry:
    def __init__(self, author=None, subject=None, body=None, tags=[], type=None, timestamp=None, shiftId=None, attachements=None):
        self.author = author
        self.subject = subject
        self.type = type
        self.body = body
        self.tags = tags
        self.timestamp = timestamp
        self.shiftId = shiftId
        self.attachements = attachements


class EssLogbook:
    def __init__(self):
        server = os.getenv('LOGBOOK_SERVER', '')
        username = os.getenv('LOGBOOK_USER', '')
        password = os.getenv('LOGBOOK_PASSWORD', '')
        self.nameLogbook = 'Operation'
        self.logbook = elog.open(server,
                                 logbook=self.nameLogbook,
                                 user=username,
                                 password=password,
                                 use_ssl=True)

    def getEntries(self, shiftId=None):
        if shiftId is None:
            return ()
        toReturn = []
        for logMsgId in self.logbook.search({'Shift ID': shiftId}):
            message, attributes, attachements = self.logbook.read(logMsgId)
            toReturn.append(LogEntry(author=attributes['Author'],
                                     subject=attributes['Subject'],
                                     timestamp=attributes['Date'],  # TODO convert to date time
                                     type=attributes['Entry Type'],
                                     shiftId=attributes['Shift ID'],
                                     body=message,
                                     attachements=attachements))
        return toReturn
        # return (
        # LogEntry(author='Arek', shiftId='20210528X', body='<h4> summary</h4><b>nice entry</b>', timestamp='some date',
        #          subject='PSS1 problem'),
        # LogEntry(author='Arek', shiftId='20210528X', body='<h4> PSS1 summary</h4><b>nice entry</b>',
        #          timestamp='some date', subject='PSS1 problem solved'),)

    def getLastShiftIds(self, lastMessages= 100, lastDistinctToShow=10):
        x = self.logbook.get_last_message_id()
        toReturn = []
        for oneMId in range(x-lastMessages, x):
            try:
                message, attributes, attachements = self.logbook.read(oneMId)
                toReturn.append(attributes['Shift ID'])
            except:
                pass
        return list(set(toReturn))[:lastDistinctToShow]


if __name__ == "__main__":
    pass
