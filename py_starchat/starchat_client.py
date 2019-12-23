import json
import time
import logging
import requests
from .utilities import get_major_version

logger = logging.getLogger(__name__)


class StarChatClient:

    def __init__(self,
                 url: str = 'http://localhost',
                 port: str = '8888',
                 version: str = '5.1') -> None:

        self.address = '{}:{}'.format(url, port)
        self.session = requests.Session()
        assert version in ['4.1', '4.2', '5.1']
        self.version = version
        self.version_major = get_major_version(version)

    def authenticate(self, user: str, password: str) -> None:
        """
        Set credentials for authentication to StarChat
        :param user: user name
        :param password: password
        :return: None
        """
        self.session.auth = (user, password)
        pass

    def check_service(self) -> bool:
        """
        Check connection to StarChat
        :return: True if connection to starChat returned status code 200, False otherwise
        """
        response = self.session.get(self.address)
        try:
            assert response.status_code == 200
            return True
        except AssertionError:
            logger.info('Something went wrong connecting to StarChat on {}'.format(self.address))
            return False

    def get_indices(self):
        """
        Get all StarChat indices
        :return: list containing names of indices (including `starchat_system` indices)
        """
        response = self.session.get('{}/system_indices'.format(self.address))
        return response.json()

    def index_exists(self, index_name: str) -> bool:
        """
        Check if the index is present on StarChat
        :param index_name: name of the index
        :return: True if index already present, False otherwise
        """
        response = self.session.get('{}/{}/index_management'.format(self.address, index_name))
        if self.version == '4.1':
            res = response.json()['message'] == 'IndexCheck: state({}.state, true) question({}.question, true) term({}.term, true)'.format(*([index_name] * 3))
        else:
            res = response.json()['check']
        return res

    def index_delete(self, index_name: str):
        """
        Delete index from StarChat
        :param index_name: name opf the index to be deleted
        :return: StarChat response
        """
        response = self.session.delete('{}/{}/index_management'.format(self.address, index_name))
        return response

    def index_create(self, index_name: str):
        """
        Create index in StarChat
        :param index_name: name of the index to be created
        :return: StarChat response
        """
        response = self.session.post('{}/{}/index_management/create'.format(self.address, index_name))
        return response

    def load_decision_table(self, index_name: str, json: dict):
        """
        Load a single state to StarChat
        :param index_name: name of the StarChat index
        :param json:
        :return: StarChat response
        """
        if self.version_major == '4':
            response = self.session.post('{}/{}/decisiontable'.format(self.address, index_name),
                                         json=json)
            return response
        # TODO: modify to work also with starchat version 5.1
        # elif self.version == '5.1':
        #     response = self.session.post('{}/{}/decisiontable'.format(self.address, index_name),
        #                                  json=json)
        # return response

    def load_decision_table_file(self, index_name: str, decision_table_path: str):
        """
        Load decision table in json format to starchat index
        :param index_name: name of the index
        :param decision_table_path: path to the json file
        :return: when version == 4.2, reutrns dict() containing `state` - `check` pairs.
                    `check` can be True or False, depending on the status code for each state upload to starchat.
                 when version == 5.1, returns StarChat response
        """
        if self.version_major == '4':
            with open(decision_table_path, encoding='utf-8') as f:
                table = json.load(f)
                out = dict()
            for hit in table['hits']:
                state = hit['document']['state']
                response = self.load_decision_table(index_name, hit['document'])
                status_code = response.status_code
                try:
                    assert status_code == 201
                    out[state] = True
                except AssertionError:
                    logger.warning(('Something went wrong loading state {} (StarChat returned status code {})'
                                    .format(state, status_code)))
                    out[state] = False
            return out
        elif self.version == '5.1':
            files = {'json': open(decision_table_path, 'rb')}
            response = self.session.post('{}/{}/decisiontable/upload/json'.format(self.address, index_name),
                                         files=files)
            return response

    def decision_table_dump(self, index_name):
        """
        Get the decision table loaded for a StarChat index
        :param index_name: name of the index
        :return: dict containing the decision table
        """
        response = self.session.get('{}/{}/decisiontable?dump=true'.format(self.address, index_name))
        return response.json()

    def states_count(self, index_name: str, patience_time: int = 5, trials: int = 5):
        """
        Return number of states loaded in index.
        :param index_name: name of the index
        :param patience_time: time in seconds to wait between calls to StarChat if service does not respond promptly
        :param trials: maximum number of calls to StarChat before giving up if request time out
        :return: int specifying the number of entries that are present in the index
        """
        if self.version_major == '4':
            url = '{}/{}/decisiontable_analyzer'.format(self.address, index_name)
            label = 'num_of_entries'
        else:
            url = '{}/{}/decisiontable/analyzer'.format(self.address, index_name)
            label = 'numOfEntries'
        response = self.session.post(url)
        counter = 0
        while response.status_code != 200 and counter < trials:
            counter += 1
            logger.info('StarChatClient.states_count: giving some time to StarChat...')
            time.sleep(patience_time)
            response = self.session.post(url)
        try:
            assert response.status_code == 200
            return response.json()[label]
        except AssertionError:
            logger.warning('Something went wrong checking the number of entries in index "{}"'.format(index_name))
            return None

    def get_next_response(self, index_name: str, text: str, conversation_id: str = '42', threshold: float = 0.01):
        """
        Get answer from StarChat (see `/<index_name>/get_next_response` API in StarChat documentation)
        :param index_name: name of the StarChat index
        :param text: text sent to StarChat
        :param conversation_id: conversation identifier
        :param threshold: threshold used to filter StarChat answers
        :return: json with StarChat output
        """
        if self.version_major == '4':
            body = {
                "conversation_id": conversation_id,
                "user_input": {
                    "text": text
                },
                "values": {
                    "return_value": "",
                    "data": {}
                },
                "threshold": threshold
            }
        else:
            body = {
                "conversationId": conversation_id,
                "userInput": {
                    "text": text
                },
                "values": {
                    "returnValue": "",
                    "data": {}
                },
                "threshold": threshold
            }
        response = self.session.post('{}/{}/get_next_response'.format(self.address, index_name),
                                     json=body)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    def get_term(self, index_name: str, terms: list):
        """
        Retrieve a list of terms from the terms table
        :param index_name: name of the index
        :param terms: list of strings corresponding to terms to be retrieved
        :return: dict containing starchat output
        """
        assert type(terms) == list, 'Argument `terms` should be a list of strings'
        assert all([type(el) == str for el in terms]), 'Argument `terms` should be a list of strings'
        body = {"ids": terms}
        response = self.session.post('{}/{}/term/get'.format(self.address, index_name),
                                     json=body)
        return response.json()

    def add_term(self, index_name: str, terms: list):
        """
        Index terms in a StarChat index
        :param index_name: name of the index
        :param terms: list of dict objects with format as given in schemas/add_term.json
        :return: dict containing starchat output
        """
        assert type(terms) == list, 'Argument `terms` should be a list of json objects'
        assert all([type(el) == dict for el in terms]), 'Argument `terms` should be a list of json objects'
        body = {'terms': terms}
        response = self.session.post('{}/{}/term/index'.format(self.address, index_name),
                                     json=body)
        return response.json()

    def delete_term(self, index_name: str, terms: list):
        """
        Delete terms in a StarChat index
        :param index_name: name of the index
        :param terms: list of strings corresponding to terms to be deleted
        :return: dict containing starchat output
        """
        assert type(terms) == list, 'Argument `terms` should be a list of strings'
        assert all([type(el) == str for el in terms]), 'Argument `terms` should be a list of strings'
        body = {'ids': terms}
        response = self.session.post('{}/{}/term/delete'.format(self.address, index_name),
                                     json=body)
        return response.json()

    def term_distance(self, index_name: str, terms: list):
        """
        Compute all the pairwise distances between the listed terms
        :param index_name: name of the index
        :param terms: list of strings corresponding to terms to be compared
        :returns: dict containing starchat output
        """
        assert type(terms) == list, 'Argument `terms` should be a list of strings'
        assert all([type(el) == str for el in terms]), 'Argument `terms` should be a list of strings'
        body = {'ids': terms}
        response = self.session.post('{}/{}/term/distance'.format(self.address, index_name),
                                     json=body)
        return response.json()

    def close(self):
        self.session.close()


# # TESTING
# VERSION = '4.1'
# if VERSION.split('.')[0] == '4':
#     TEST_INDEX = 'index_english_test'
#     DEC_TABLE = '/Users/miche/workdir/Documents/projects/decisionTablesQualityCheck/decision_tables/index_english_100_35518858035e47769cdd02cbe3807d2a.json'
# else:
#     TEST_INDEX = 'index_getjenny_english_test'
#     DEC_TABLE = '/Users/miche/Documents/data/log_dump/poas_eng_dec_tab.json'
# sc_client = StarChatClient(port='8888', version=VERSION)
# sc_client.authenticate('admin', 'adminp4ssw0rd')
# assert sc_client.check_service()
#
# if sc_client.version_major == '4':
#     assert sc_client.index_create(TEST_INDEX).status_code == 200
# elif sc_client.version_major == '5':
#     assert sc_client.index_create(TEST_INDEX).status_code == 201
#
# assert sc_client.index_exists(TEST_INDEX)
#
# out = sc_client.load_decision_table_file(TEST_INDEX, DEC_TABLE)
#
# if sc_client.version_major == '4':
#     assert all(out.values())
# elif sc_client.version == '5.1':
#     assert out.status_code == 200
#
# sc_client.decision_table_dump(TEST_INDEX)
#
# print('Number of states loaded: {}'.format(sc_client.states_count(TEST_INDEX)))
# response = sc_client.get_next_response(TEST_INDEX, 'hei', threshold=0.0)
# answer = response[0]['bubble']
# print(answer)
# assert sc_client.index_delete(TEST_INDEX).status_code == 200
# assert not sc_client.index_exists(TEST_INDEX)
# sc_client.close()
