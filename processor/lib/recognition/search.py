import time
import faiss
import numpy as np

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