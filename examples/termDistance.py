# Add terms to starchat and compute distances between term vectors
import urllib.request
from py_starchat.starchat_client import StarChatClient
import os.path as path
import zipfile
import numpy as np

SC_VERSION = '5.1'
USER = 'admin'
PASSWORD = 'adminp4ssw0rd'
SC_INDEX = 'index_getjenny_english_0'

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

# read the word vectors (use 50-dimensional vectors for testing)
embeddings_dict = dict()
with open('glove.6B.50d.txt', 'r') as f:
    for line_count, line in enumerate(f):
        if line_count % 500 == 0:
            print(line_count)
        values = line.split()
        word = values[0]
        vector = np.asarray(values[1:], 'float32')
        embeddings_dict[word] = vector

# get vectors for a list of words
my_terms = [
    'test',
    'hello',
    'hi',
    'chocolate',
    'milk',
    'commerce',
    'market'
]

my_vectors = dict()
for term in my_terms:
    if term in embeddings_dict.keys():
        my_vectors[term] = embeddings_dict[term]
    else:
        print('Term {} missing from loaded embeddings'.format(term))

del embeddings_dict  # to save memory!


# load vectors into StarChat
def term_input(term, vector):
    out = {
        "term": term,
        # "synonyms": {'hi': 0.6},
        # "antonyms": {'goodbye': 0.3},
        # "tags": "tag1 tag2",
        # "features": {'POS': 'name'},
        "vector": vector,
        # "frequencyBase": 410301,
        # "frequencyStem": 601301,
        # "score": 0.9
    }
    return out


sc_terms = list()
for term, vector in my_vectors.items():
    print(term)
    sc_terms.append(term_input(term, vector.tolist()))

sc_client.delete_term(SC_INDEX, my_terms)
sc_client.add_term(index_name=SC_INDEX, terms=sc_terms)


# sc_client.get_term(SC_INDEX, ['chocolate'])

# check distances among pairs of words
sc_distances = sc_client.term_distance(index_name=SC_INDEX, terms=my_terms)  # get distances
cos_dists = [(el['cosDistance'], (el['term1'], el['term2'])) for el in sc_distances]
euc_dists = [(el['eucDistance'], (el['term1'], el['term2'])) for el in sc_distances]

print('Word pairs sorted by cosine distance')
for score, pair in sorted(cos_dists):
    print('\t', score, pair)

print('Word pairs sorted by euclidean distance')
for score, pair in sorted(euc_dists):
    print('\t', score, pair)
