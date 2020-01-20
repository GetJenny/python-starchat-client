#test starchat tokenizer
from py_starchat.starchat_client import StarChatClient
import logging

logging.basicConfig(level=logging.INFO)

SC_VERSION = '5.1'
USER = 'admin'
PASSWORD = 'adminp4ssw0rd'
SC_INDEX = 'index_getjenny_english_0'

# setup starchat client
sc_client = StarChatClient(version=SC_VERSION)
sc_client.authenticate(user=USER, password=PASSWORD)
assert sc_client.check_service(), 'Something went wrong connecting to StarChat'

# get available tokenizers
tokenizers = sc_client.get_tokenizers(SC_INDEX)
print('Available tokenizers are {}'.format(tokenizers))

# tokenize sentence
sentence = 'hi, please tokenize this text'

res = sc_client.tokenize(SC_INDEX, sentence)
print('Tokenizer output is {}'.format(res))