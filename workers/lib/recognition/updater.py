import time
import numpy as np
from lib.database.connection import test_default_connect, custom_connect
from lib.database.amodels import KnownPerson, UnknownPerson

class Updater(object):
    def __init__(self, **kwargs):
        self.data = {
            'ids': [],
            'names': [],
            'encodings': []
        }
        self._loaded = False

    def getData(self, _filter, **kwargs):
        if _filter in list(self.data.keys()):
            return self.data[_filter]
        else:
            return self.data

    def getUser(self, index):
        assert index < len(self.data['ids'])
        return self.data['ids'][index], self.data['names'][index]
            
    def load_data_from_db(self, **kwargs):
        assert not self._loaded
        try:
            startTime = time.time()
            test_default_connect()

            for person in UnknownPerson.objects.filter():
                if not person.code in self.data['ids']:
                    for encoding in person.encodings:
                        self.data['ids'].append(person.code)
                        self.data['names'].append('{name}'.format(name='Unknown'))
                        self.data['encodings'].append(
                            np.array(encoding)
                        )
            for person in KnownPerson.objects.filter():
                if not person.dni in self.data['ids']:
                    for encoding in person.encodings:
                        self.data['ids'].append(person.dni)
                        self.data['names'].append('{name} {surname}'.format(
                            name=person.names[0], surname=person.surnames[0]
                        ))
                        self.data['encodings'].append(np.array(encoding))

            self._loaded = True
            print("[INFO] {} data has been loaded in {}".format(
                len(self.data['ids']), time.time() - startTime
            ))
        except Exception as e:
            print(e)
            self._loaded = False