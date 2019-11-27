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


class StarChatState:
    """
    Objects of this class contain all the information stored in each state of a starChat decision table
    """

    def __init__(self, starchat_version: str='4'):
        self.starchat_version = starchat_version
        self.state = None,
        self.analyzer = None,
        self.queries = None,
        self.success_value = None,
        self.failure_value = None,
        self.bubble = None,
        self.version = None,
        self.execution_order = None,
        self.action_input = None,
        self.action = None,
        self.max_state_count = None

    def __str__(self):
        out = ''
        out += 'self.state: {}\n'.format(self.state)
        out += 'self.analyzer: {}\n'.format(self.analyzer)
        out += 'self.queries: {}\n'.format(self.queries)
        out += 'self.success_value: {}\n'.format(self.success_value)
        out += 'self.failure_value: {}\n'.format(self.failure_value)
        out += 'self.bubble: {}\n'.format(self.bubble)
        out += 'self.version: {}\n'.format(self.version)
        out += 'self.execution_order: {}\n'.format(self.execution_order)
        out += 'self.action_input: {}\n'.format(self.action_input)
        out += 'self.action: {}\n'.format(self.action)
        out += 'self.max_state_count: {}'.format(self.max_state_count)
        return out

    def set_state(self, state_name: str) -> None:
        self.state = state_name

    def set_analyzer(self, analyzer: str) -> None:
        self.analyzer = analyzer

    def set_queries(self, queries: list) -> None:
        self.queries = queries

    def set_success_value(self, success_value: str) -> None:
        self.success_value = success_value

    def set_failure_value(self, failure_value: str) -> None:
        self.failure_value = failure_value

    def set_bubble(self, bubble: str) -> None:
        self.bubble = bubble

    def set_version(self, version: int) -> None:
        self.version = version

    def set_execution_order(self, exec_order: int) -> None:
        self.execution_order = exec_order

    def set_action_input(self, action_input: dict) -> None:
        self.action_input = action_input

    def set_action(self, action: str) -> None:
        self.action = action

    def set_max_state_count(self, max_state_count: int) -> None:
        self.max_state_count = max_state_count

    def set_all(self, state_specs: dict) -> None:
        self.set_state(state_specs['state'])
        self.set_analyzer(state_specs['analyzer'])
        self.set_queries(state_specs['queries'])
        self.set_bubble(state_specs['bubble'])
        self.set_version(state_specs['version'])
        self.set_action(state_specs['action'])
        if get_major_version(self.starchat_version) == '4':
            self.set_success_value(state_specs['success_value'])
            self.set_failure_value(state_specs['failure_value'])
            self.set_execution_order(state_specs['execution_order'])
            self.set_action_input(state_specs['action_input'])
            self.set_max_state_count(state_specs['max_state_count'])
        elif get_major_version(self.starchat_version) == '5':
            self.set_success_value(state_specs['successValue'])
            self.set_failure_value(state_specs['failureValue'])
            self.set_execution_order(state_specs['executionOrder'])
            self.set_action_input(state_specs['actionInput'])
            self.set_max_state_count(state_specs['maxStateCount'])
        else:
            logger.error('StarChat Version {} not supported'.format(self.starchat_version))

    def has_keywords(self) -> bool:
        """
        Check if the state has keywords in the analyzer expression
        :return: bool
        """
        if 'keyword("' in self.analyzer:
            return True
        else:
            return False

    def has_queries(self) -> bool:
        """
        Check if a the state has whisperer's queries
        :return: bool
        """
        if self.queries:
            return True
        else:
            return False


class DecisionTable:
    """Class to extract informations from and about a StarChat decision table"""

    def __init__(self, json_table: dict, version='4.2'):
        self.dec_table = json_table
        try:
            assert get_major_version(version) in ['4', '5']
        except AssertionError:
            logger.critical('Unsupported version {}'.format(version))
        self.version = version
        self.version_major = get_major_version(version)
        self.states = [StarChatState(starchat_version=self.version) for _ in json_table['hits']]
        for hit, state_obj in zip(json_table['hits'], self.states):
            state_obj.set_all(hit['document'])

    def get_state(self, state_name):
        """
        Get the StarChatState object corresponding to a given state name
        :return: StarChatState object
        """
        for state_obj in self.states:
            if state_obj.state == state_name:
                return state_obj
        return None

    def get_analyzers(self):
        """
        Get analyzers expressions
        :return: dict() containing state_name: analyzer_expression pairs
        """
        return {state_obj.state: state_obj.analyzer for state_obj in self.states}

    def get_queries(self):
        """
        Get whisperer's queries
        :return: dict() containing state_name: list_of_queries pairs
        """
        return {state_obj.state: state_obj.queries for state_obj in self.states}

    def states_with_keywords(self):
        """
        Give the list of states with analyzer expression
        :return: list of bool
        """
        return [state_obj.has_keywords() for state_obj in self.states]

    def states_with_queries(self):
        """
        Give the list of states with at least one whisperer's query
        :return: list of bool
        """
        return [state_obj.has_queries() for state_obj in self.states]

    def modified_analyzer(self, state):
        """
        Give the expression of the analyzer for the given state after removing the max(serach()) part and keeping
        the reinfConjunction() part
        :param state: name of the state
        :return: string containing the modified analyzer expression
        """
        # get state object
        state_obj = self.get_state(state)
        # check if state has both analyzer and query
        if state_obj.has_keywords() and state_obj.has_queries():
            out = copy.deepcopy(state_obj.analyzer)  # get original analyzer expression
            out = out.replace('search("{}"), '.format(state), '')
            out = out[out.find('(') + 1: -1]
            logger.debug('New analyzer expression for state "{}": {}'.format(state, out))
            return out
        else:
            logger.debug(
                ('Skipping state "{}" (needs bot analyzer and queries to be modified). Returning original analyzer.'
                 .format(state))
            )
            return state_obj.analyzer

    def modified_decision_table(self):
        """
        Give the expression of the modified decision table, where:
         * states without analyzers are removed
         * states with both search and analyzer are changed in order to remove the search part
        :return: dict() containing the modified decision table
        """
        logger.info('\nBuilding modified decision table...\n')
        new_hits = []
        for index, state_obj in enumerate(self.states):
            if not state_obj.has_keywords():
                logger.debug('Skipping state "{}" in decision table (no keywords).'.format(state_obj.state))
            else:
                new_hit = copy.deepcopy(self.dec_table['hits'][index])
                assert new_hit['document']['state'] == state_obj.state  # check index-state match
                new_hit['document']['queries'] = []
                new_hit['document']['analyzer'] = self.modified_analyzer(state_obj.state)
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
        Convert decision table in order to be compatible with a different StarChat version
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
