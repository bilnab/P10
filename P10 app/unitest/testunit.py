import sys
sys.path.append('..')

import unittest
from config import DefaultConfig
from azure.cognitiveservices.language.luis.authoring import LUISAuthoringClient
from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient
from msrest.authentication import CognitiveServicesCredentials


CONFIG = DefaultConfig()

clientRuntime = LUISRuntimeClient(endpoint='https://' + CONFIG.LUIS_API_HOST_NAME, credentials=CognitiveServicesCredentials(CONFIG.LUIS_API_KEY))
request ='I want to go from Paris to London from the 2022-10-22 until the 2022-10-24 for a budget of 1000 $'
response = clientRuntime.prediction.resolve(CONFIG.LUIS_APP_ID, query=request)

#for c, entity in enumerate(response.entities):
#    print(entity)

# classe scenario de test qui est une classe fille de unittest.TestCase
class TestLuisReco(unittest.TestCase):

    def test_intent(self):
        """intention testing"""
        #self.assertEqual(response.top_scoring_intent.intent,'book')
        self.assertTrue(response.top_scoring_intent.intent == 'book', "intention testing - FAILURE")

    def test_origin(self):
        """origin testing."""
        for c, entity in enumerate(response.entities):
            if entity.type == 'or_city':
                self.assertTrue(entity.entity == 'paris', "origine city testing - FAILURE")

    def test_dest(self):
        """destination testing."""
        for c, entity in enumerate(response.entities):
            if entity.type == 'dst_city':
                self.assertTrue(entity.entity == 'london', "destination city testing - FAILURE")

    def test_budget(self):
        """budget testing."""
        for c, entity in enumerate(response.entities):
            if entity.type == 'budget':
                self.assertTrue(entity.entity == '1000 $', "budget testing - FAILURE")

    def test_daterange(self):
        """budget testing."""
        for c, entity in enumerate(response.entities):
            if entity.type == 'daterange':
                self.assertTrue(entity.entity == 'from the 2022-02-10 until the 2022-04-10', "daterange testing - FAILURE")
                self.assertTrue(entity.start == '2022-02-10', "daterange start date testing - FAILURE")
                self.assertTrue(entity.end == '2022-04-10', "daterange end date testing - FAILURE")


if __name__ == '__main__':
    unittest.main()