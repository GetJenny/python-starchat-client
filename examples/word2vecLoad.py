# Add Word2Vec to StarChat
import urllib.request
from py_starchat.starchat_client import StarChatClient
import os.path as path
import zipfile
import numpy as np
import time

SC_VERSION = '5.1'
USER = 'admin'
PASSWORD = 'adminp4ssw0rd'
SC_INDEX = 'index_getjenny_english_common_0'

# setup starchat client
sc_client = StarChatClient(version=SC_VERSION)
sc_client.authenticate(user=USER, password=PASSWORD)
assert sc_client.check_service(), 'Something went wrong connecting to StarChat'

# check for presence of index
assert sc_client.index_exists(SC_INDEX), 'Index {} does not seem to be on StarChat'.format(SC_INDEX)

# get vectors from word2vec model (using Glove vectors as test)
if not path.isfile('glove.6B.zip'):
    print('Beginning file download...')
    url = 'http://nlp.stanford.edu/data/glove.6B.zip'
    urllib.request.urlretrieve(url, 'glove.6B.zip')
if not path.isfile('glove.6B.50d.txt'):
    with zipfile.ZipFile('glove.6B.zip', 'r') as zip_ref:
        zip_ref.extractall('.')

# read the word vectors (use 50-dimensional vectors for testing) and load into StarChat
t0 = time.time()
with open('glove.6B.50d.txt', 'r') as f:
    for line_count, line in enumerate(f):
        if line_count >= 1000:
            break
        if line_count % 100 == 0:
            print(line_count)
        # get word and vector
        values = line.split()
        word = values[0]
        vector = np.asarray(values[1:], 'float32')
        # load vector into StarChat
        terms = [{"term": word, "vector": vector.tolist()}]
        response = sc_client.add_term(SC_INDEX, terms)
print('Elapsed time: {}'.format(time.time() - t0))
