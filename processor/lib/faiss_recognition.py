import time
import faiss
import numpy as np
from threading import Thread
from uuid import uuid4

try:
    from lib.database.connection import custom_connect, test_default_connect
    from lib.database.amodels import UnknownPerson, KnownPerson
except ModuleNotFoundError:
    from database.connection import custom_connect
    from database.models import UnknownPerson, KnownPerson


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

class FSearch(object):
    def __init__(self, clusters=5, dimension=128, **kwargs):

        self._added = False
        self._trained = False
        self.dimension = dimension
        self.n_clusters = clusters

        self.index = None
    
    def train(self, encodings, **kwargs):
        assert not self._trained
        try:
            startTime = time.time()
            print("[INFO] Training data to clustering")
            train_vectors = np.array(encodings).astype('float32')
            quantiser = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(
                quantiser, self.dimension,
                self.n_clusters, faiss.METRIC_L2
            )
            self.index.train(train_vectors)
            self._trained = True
            print("[INFO] Elapsed time for training: {}".format(time.time() - startTime))
        except Exception as e:
            print("train {}".format(e))
            self._trained = False

    def add(self, encodings, **kwargs):
        encodings = np.array(encodings).astype('float32')
        self.index.add(encodings)

    def save_index(self, **kwargs):
        try:
            faiss.write_index(self.index, 'faiss_recognition.index')
            print("[INFO] Index has been written")
        except:
            pass

    def load_index(self, name='faiss_search.index', **kwargs):
        try:
            self.index = faiss.read_index(name)
        except:
            self.index = None

    def isTrained(self):
        return self.index.is_trained

    def search(self, encodings, matches=50):
        try:
            if len(encodings) > 0:
                query = np.array(encodings).astype('float32')
                distances, indexes = self.index.search(query, matches)
                # print(distances)
                return distances, indexes
            else:
                return [], []
        except Exception as e:
            print("In search: {}".format(e))
            return [], []

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
            else:
                self.faissSearch.add(self.updater.data['encodings'])
            print("[INFO] Handler Search has been prepared.")
        except Exception as e:
            print("[INFO] {}".format(e))

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
                print("[INFO] Counts: {}".format(counts))
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
            #self.save_new_encodings(newIds, newEncodings)

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
            Thread(target=self.save_on_db(id_code, encoding)).start()

        # Add encodings to faiss index for fast search
        self.faissSearch.add(encodings)

    def save_on_db(self, id_code, encoding):
        UnknownPerson(code=id_code, encodings=[encoding]).save()
        

def main():
    handler = HandlerSearch()
    handler.prepare_for_searches()

    encodings = handler.updater.data['encodings'][: 10]
    ids, names = handler.search(encodings)
    print(ids, names)

    # Adding new encodings
    encodings = np.random.random((5, 128)).astype('float32')
    handler.save_new_encoding(encodings)
    ids, names = handler.search(encodings)

    print(ids, names)