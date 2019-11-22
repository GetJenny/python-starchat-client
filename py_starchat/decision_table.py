import copy
import logging
from .utilities import get_major_version

logger = logging.getLogger(__name__)


def change_dict(my_dict: dict, to_replace: dict) -> None:
    """
    Utility function to change all keys in a nested dictionary
    :param my_dict: dictionary to be modified. Note that the dictionary given as argument is modified in place.
    :param to_replace: dictionary containing the keys to be modified, given as {old_key_name: new_key_name, ...}
    :return: None
    """
    if type(my_dict) == list:
        for el in my_dict:
            change_dict(el, to_replace)
    elif type(my_dict) == dict:
        for key, value in my_dict.items():
            if key in to_replace.keys():
                new_key = to_replace[key]
            else:
                new_key = key
            my_dict[new_key] = my_dict.pop(key)
            change_dict(value, to_replace)
    else:
        pass


class DecisionTable:
    """Class to extract informations from and about a StarChat decision table"""

    def __init__(self, json_table: dict, version='4.2'):
        self.dec_table = json_table
        self.states = [hit['document']['state'] for hit in json_table['hits']]
        self.analyzers = dict()
        self.queries = dict()
        try:
            assert get_major_version(version) in ['4', '5']
        except AssertionError:
            logger.critical('Unsupported version {}'.format(version))
        self.version = version
        self.version_major = get_major_version(version)

    def read_analyzers(self):
        """
        Read all analyzer expressions in the decision table.
        The expressions are accessible in DecisionTable.analyzers (dict)
        :return:
        """
        for entry in self.dec_table['hits']:
            entry = entry['document']
            self.analyzers[entry['state']] = entry['analyzer']
        pass

    def read_queries(self):
        """
        Read all queries in the decision table.
        The queries are accessible in DecisionTable.queries (dict)
        :return:
        """
        for entry in self.dec_table['hits']:
            entry = entry['document']
            self.queries[entry['state']] = entry['queries']
        pass

    def get_analyzers(self):
        """
        Get analyzers expressions
        :return: dict() containing state_name: analyzer_expression pairs
        """
        if not self.analyzers:
            logger.info('Running DecisionTable.read_analyzers()')
            self.read_analyzers()
        return self.analyzers

    def get_queries(self):
        """
        Get whisperer's queries
        :return: dict() containing state_name: list_of_queries pairs
        """
        if not self.queries:
            logger.info('Running DecisionTable.read_queries()')
            self.read_queries()
        return self.queries

    def has_keywords(self, state):
        """
        Check if a specific state has keywords in the analyzer expression
        :param state: name of the state
        :return: bool
        """
        if not self.analyzers:
            logger.info('Running DecisionTable.read_analyzers()')
            self.read_analyzers()
        if 'keyword("' in self.analyzers[state]:
            return True
        else:
            return False

    def has_queries(self, state):
        """
        Check if a specific state has whisperer's queries
        :param state: name of the state
        :return: bool
        """
        if not self.queries:
            logger.info('Running DecisionTable.read_queries()')
            self.read_queries()
        if self.queries[state]:
            return True
        else:
            return False

    def states_with_keywords(self):
        """
        Give the list of states with analyzer expression
        :return: list of bool
        """
        if not self.analyzers:
            logger.info('Running DecisionTable.read_analyzers()')
            self.read_analyzers()
        return [self.has_keywords(state) for state in self.states]

    def states_with_queries(self):
        """
        Give the list of states with at least one whisperer's query
        :return: list of bool
        """
        if not self.queries:
            logger.info('Running DecisionTable.read_queries()')
            self.read_queries()
        return [self.has_queries(state) for state in self.states]

    def modified_analyzer(self, state):
        """
        Give the expression of the analyzer for the given state after removing the max(serach()) part and keeping
        the reinfConjunction() part
        :param state: name of the state
        :return: string containing the modified analyzer expression
        """
        # check if state has analyzer and query
        if self.has_keywords(state) and self.has_queries(state):
            out = self.analyzers[state]
            out = out.replace('search("{}"), '.format(state), '')
            out = out[out.find('(') + 1: -1]
            return out
        else:
            logger.debug(
                ('State "{}" needs bot analyzer and queries to be modified. Returning original analyzer expression.'
                 .format(state))
            )
            return self.analyzers[state]

    def modified_decision_table(self):
        """
        Give the expression of the modified decision table, where:
         * states without analyzers are removed
         * states with both search and analyzer are changed in order to remove the search part
        :return: dict() containing the modified decision table
        """
        logger.info('\nBuilding modified decision table...\n')
        new_hits = []
        for index, (state, has_analyzer) in enumerate(zip(self.states, self.states_with_keywords())):
            if not has_analyzer:
                logger.debug('Skipping state "{}" in decision table (no analyzer expression).'.format(state))
            else:
                new_hit = copy.deepcopy(self.dec_table['hits'][index])
                assert new_hit['document']['state'] == state  # check index-state match
                new_hit['document']['queries'] = []
                new_hit['document']['analyzer'] = self.modified_analyzer(state)
                new_hits.append(new_hit)
        modified_dec_table = dict()
        modified_dec_table['hits'] = new_hits
        modified_dec_table['total'] = len(new_hits)
        if self.version_major == '5':
            modified_dec_table['maxScore'] = self.dec_table['maxScore']
        elif self.version_major == '4':
            modified_dec_table['max_score'] = self.dec_table['max_score']
        return modified_dec_table

    def to_version(self, out_version: str):
        """
        Convert decision table in roder to be compatible with a different StarChat version
        :param out_version: the output decision table will be compatible with the out_version version of StarChat
        :return: DecisionTable object with decision table in format compatible with the desired StarChat version
        """
        v4_to_v5 = {
            'max_score': 'maxScore',
            'state_data': 'stateData',
            'success_value': 'successValue',
            'failure_value': 'failureValue',
            'execution_order': 'executionOrder',
            'action_input': 'actionInput',
            'max_state_count': 'maxStateCount'
        }
        out_version_major = get_major_version(out_version)
        try:
            assert out_version_major in ['4', '5']
        except AssertionError:
            logger.error(' Version {} not supported. Accepted output versions are 4.x and 5.x'.format(out_version))
        if out_version_major == self.version_major:
            return self.dec_table
        else:
            dec_table_out = copy.deepcopy(self.dec_table)
            if out_version_major == '5':  # convert from version 4 to 5
                change_dict(dec_table_out, v4_to_v5)
            else:  # convert from version 5 to 4
                change_dict(dec_table_out, {v: k for k, v in v4_to_v5.items()})
            return DecisionTable(json_table=dec_table_out, version=out_version_major)


# # TESTING
# import os
# import os.path as path
# import json
# FOLDER = '../../data/benchmark-dataset'
# file = 'index_english_75_a04a9dcf5a524e01b278a085ad2af4d7.json'
# with open(path.join(FOLDER, file)) as f:
#     table = json.load(f)
#
# dt = DecisionTable(table)
# modified_table = dt.modified_decision_table()
# new_dt = DecisionTable(modified_table)
#
# for state in new_dt.states:
#     print()
#     print(state)
#     print(new_dt.get_analyzers()[state])
#     print(dt.get_analyzers()[state])
