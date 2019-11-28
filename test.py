# TESTING py_starchat.decision_table
from py_starchat.decision_table import StarChatState
from py_starchat.decision_table import DecisionTable
import os
import os.path as path
import json
import logging

logging.basicConfig(level=logging.DEBUG)

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
