import numpy as np
from uuid import uuid4
from .search import FSearch
from .updater import Updater
from threading import Thread
from lib.database.amodels import UnknownPerson

class HandlerSearch(object):

    def __init__(self, **kwargs):
        self.updater = Updater()
        self.faissSearch = FSearch()

    def prepare_for_searches(self, **kwargs):
        try:
            self.updater.load_data_from_db()
            self.faissSearch.load_index()
            if self.faissSearch.index == None:
                self.faissSearch.train(self.updater.data['encodings'])
                self.faissSearch.add(self.updater.data['encodings'])
                self.faissSearch.save_index(name='faiss.index')
            else:
                self.faissSearch.add(self.updater.data['encodings'])
            print("[INFO] Handler Search has been prepared.")
        except Exception as e:
            print("[ERRNO] {}".format(e))

    def search(self, encodings, matches=5, confidence=0.09):
        distances, indexes = self.faissSearch.search(encodings, matches)
        
        ids = []
        names = []
        newIds = []
        newEncodings = []

        for i, indexList in enumerate(indexes):
            counts = {}
            founds = {}
            for j, index in enumerate(indexList):
                if index != -1 and distances[i, j] < confidence:
                    try:
                        id_code = self.updater.data['ids'][index]

                        if not id_code in counts:
                            counts[id_code] = 1
                        else:
                            counts[id_code] += 1

                        if id_code not in founds.keys():
                            founds[id_code] = self.updater.data['names'][index]
                    except IndexError as e:
                        print(e)

                # Its about a new person (a new Unknown person)
                elif (index == -1 or distances[i, j] > confidence) and j == 0:
                    break
            
            try:
                #print("[INFO] Counts: {}".format(counts))
                id_code = max(counts, key=counts.get)
                name = founds[id_code]
                ids.append(id_code)
                names.append(name)
            except ValueError:
                new_code = str(uuid4()).replace('-', '')[:8]
                newIds.append(new_code)
                newEncodings.append(encodings[i])

                # Append new Unknown on list of results
                ids.append(new_code)
                names.append('Unknown')

        if len(newEncodings) > 0:
            newEncodings = np.array(newEncodings).astype('float32')
            assert len(newIds) == len(newEncodings)
            self.save_new_encodings(newIds, newEncodings)

        #print("[INFO] elapsed time: {}".format(time.time() - startTime))

        return ids, names

    def save_new_encodings(self, ids, encodings):
        # Generate len(encodings) ids and len(encodings) names
        ids_list = ids
        names_list = ['Unknown' for _ in range(len(encodings))]

        # Save ids and names for searching
        [self.updater.data['ids'].append(id_code) for id_code in ids_list]
        [self.updater.data['names'].append(name) for name in names_list]

        # Save new encodings on mongodb
        for encoding, id_code in zip(encodings, ids_list):
            encoding = [float(x) for x in encoding]
            Thread(target=self.save_on_db(id_code, encoding), daemon=True).start()

        # Add encodings to faiss index for fast search
        self.faissSearch.add(encodings)

    def save_on_db(self, id_code, encoding):
        UnknownPerson(code=id_code, encodings=[encoding]).save()