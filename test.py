# TESTING
from py_starchat.decision_table import StarChatState
from py_starchat.decision_table import DecisionTable
from py_starchat.starchat_client import StarChatClient
import os
import os.path as path
import json
import logging

logging.basicConfig(level=logging.DEBUG)

# TESTING py_starchat.decision_table
# FOLDER = path.join(os.environ['DATA_DIR'], 'production_indices/production_indices.2019.11.21')
FOLDER = '/Users/miche/workdir/Documents/projects/decisionTablesQualityCheck/decision_tables'
file = 'index_finnish_56_cd3ca2893b634888b56d67dfa318064b.json'
with open(path.join(FOLDER, file)) as f:
    table = json.load(f)

# test StarChatState
tmp = StarChatState(starchat_version='4')
tmp.set_all(table['hits'][0]['document'])
print(tmp)

# test modified_decision_table()
dt = DecisionTable(table, version='4')
modified_table = dt.modified_decision_table()
new_dt = DecisionTable(modified_table)

for state_obj in dt.states:
    if state_obj.has_keywords() and state_obj.has_queries():
        state_name = state_obj.state
        print()
        print(state_name)
        print(new_dt.get_analyzers()[state_name])
        print(dt.get_analyzers()[state_name])

# test get_parents()
for state_obj in dt.states:
    state_name = state_obj.state
    parents = dt.get_parents(state_name)
    if parents:
        print()
        print(state_name)
        print(parents)

# TESTING py_starchat.starchat_client
VERSION = '5.1'
if VERSION.split('.')[0] == '4':
    TEST_INDEX = 'index_english_test'
    DEC_TABLE = '/Users/miche/workdir/Documents/projects/decisionTablesQualityCheck/decision_tables/index_english_100_35518858035e47769cdd02cbe3807d2a.json'
else:
    TEST_INDEX = 'index_getjenny_english_test'
    DEC_TABLE = '/Users/miche/Documents/data/log_dump/poas_eng_dec_tab.json'
sc_client = StarChatClient(port='8888', version=VERSION)
sc_client.authenticate('admin', 'adminp4ssw0rd')
assert sc_client.check_service()

if sc_client.version_major == '4':
    assert sc_client.index_create(TEST_INDEX).status_code == 200
elif sc_client.version_major == '5':
    assert sc_client.index_create(TEST_INDEX).status_code == 201

assert sc_client.index_exists(TEST_INDEX)

out = sc_client.load_decision_table_file(TEST_INDEX, DEC_TABLE)

if sc_client.version_major == '4':
    assert all(out.values())
elif sc_client.version == '5.1':
    assert out.status_code == 200

sc_client.decision_table_dump(TEST_INDEX)

print('Number of states loaded: {}'.format(sc_client.states_count(TEST_INDEX)))
response = sc_client.get_next_response(TEST_INDEX, 'hei', threshold=0.0)
answer = response[0]['bubble']
print(answer)
assert sc_client.index_delete(TEST_INDEX).status_code == 200
assert not sc_client.index_exists(TEST_INDEX)
sc_client.close()

# Test terms
with open('../schemas/add_term.json') as f:
    new_terms = json.load(f)["terms"]
sc_client.add_term('index_getjenny_english_0', new_terms)
sc_client.delete_term('index_getjenny_english_0', ['hello'])
out = sc_client.get_term('index_getjenny_english_0', ['hello'])
