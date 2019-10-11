import copy
import logging
logger = logging.getLogger(__name__)


class DecisionTable:
    """Class to extract informations from and about a StarChat decision table"""

    def __init__(self, json_table, version='4.2'):
        self.dec_table = json_table
        self.states = [hit['document']['state'] for hit in json_table['hits']]
        self.analyzers = dict()
        self.queries = dict()
        try:
            assert version in ['4.2', '5.1']
        except AssertionError:
            logger.critical('Unsupported version {}'.format(version))
        self.version = version

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
        if self.version == '5.1':
            modified_dec_table['maxScore'] = self.dec_table['maxScore']
        elif self.version == '4.2':
            modified_dec_table['max_score'] = self.dec_table['max_score']
        return modified_dec_table


# # TESTING
# import os
# import os.path as path
# import json
# FOLDER = 'decision_tables'
# file = os.listdir(FOLDER)[0]
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
