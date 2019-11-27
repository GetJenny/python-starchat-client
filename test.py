# TESTING py_starchat.decision_table
from py_starchat.decision_table import StarChatState
from py_starchat.decision_table import DecisionTable
import os
import os.path as path
import json
import logging

logging.basicConfig(level=logging.DEBUG)

FOLDER = path.join(os.environ['DATA_DIR'], 'production_indices/production_indices.2019.11.21')
file = 'index_english_4_a6c173696326467686ab4fb253015b59.json'
with open(path.join(FOLDER, file)) as f:
    table = json.load(f)

# test StarChatState
tmp = StarChatState(starchat_version='4')
tmp.set_all(table['hits'][0]['document'])
print(tmp)

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
