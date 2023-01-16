# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext
### à adapter en fonction de notre problematique
from booking_details import BookingDetails


class Intent(Enum):
    #les intentions de LUIS
    BOOK_FLIGHT = "book"#"Book_flight"#"BookFlight"
    NONE_INTENT = "NoneIntent"
    # # # # # # #
    #on enleve les intentions non utiles
    #CANCEL = "Cancel"
    #GET_WEATHER = "GetWeather"

def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    '''fonction de recuperation de l'intention au plus haut score'''
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ): #-> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None
        print("on teste requete luis")
        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)
            # recognizer_Result est le json de resultats de LUIS qu'on peut voir en tracant dans l'emulateur
            # l'objet doit avoir des attributs intents et entities
            # mais on peut passer par des get de dict si on connait le schema 
            # recognizer_result.intents doit etre equivalent à recognizer_result.get("intents")
            # on tri les intentions par score decroissant pour recuperer la plus probable
            print("on teste requete luis")
            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )

            if intent == Intent.BOOK_FLIGHT.value:
                result = BookingDetails()
            #c'est ici qu'on transforme la réponse de LUIS en result qu on initialise vide avec booking details
            # We need to get the result from the LUIS JSON which at every level returns an array.
            # on s'aide de la trace du recognizer result dans l'emulateur pour savoir ce qu on get    
            
                # We need to get the result from the LUIS JSON which at every level returns an array.
                
                # Destination -------------------------------
                # on cherche entites->$instance->"dst_city"
                # le {} de defaut permet d'eviter une erreur si la key $instance pas trouvé
                # le [] permet de renvoyer une liste vide si besoin comme on calcul la len derriere
                # https://docs.microsoft.com/en-us/azure/cognitive-services/luis/luis-migration-api-v3
                # $instance est fourni seulement pour l'api v3 et il faut le verbose flag
                
                #le to entites est dsl_city dans le json de notr emodèle LUIS
                to_entities = recognizer_result.entities.get("$instance", {}).get(
                    "dst_city", []
                )
                if len(to_entities) > 0:
                    #tu capitalises la destination si elle existe
                    result.destination = to_entities[0]["text"].capitalize()
                    # # # pas de test si l aeroport autorisé: correspond pas à notre schema
                    #if recognizer_result.entities.get("To", [{"$instance": {}}])[0][
                    #    "$instance"
                    #]:
                    #    result.destination = to_entities[0]["text"].capitalize()
                    #else:
                    #    result.unsupported_airports.append(
                    #        to_entities[0]["text"].capitalize()
                    #    )

                # From --------------------------------------    
                from_entities = recognizer_result.entities.get("$instance", {}).get(
                    "or_city", []
                )
                if len(from_entities) > 0:
                    result.origin = from_entities[0]["text"].capitalize()
                    #if recognizer_result.entities.get("From", [{"$instance": {}}])[0][
                    #    "$instance"
                    #]:
                    #    result.origin = from_entities[0]["text"].capitalize()
                    #else:
                    #    result.unsupported_airports.append(
                    #        from_entities[0]["text"].capitalize()
                    #    )

                # This value will be a TIMEX. And we are only interested in a Date so grab the first result and drop
                # the Time part. TIMEX is a format that represents DateTime expressions that include some ambiguity.
                # e.g. missing a Year.
                # Departure ---------------------------------
                #recherche de la start date en entity simple avec un get de dict
                departure_date_entities = recognizer_result.entities.get("str_date", [])
                if departure_date_entities:
                    #si l'entity str_date existe on recupere le datetime le plus anterieur
                    #attention il y aura 2 datetime normalement dans le cas complet
                    
                    datetime_entities = recognizer_result.entities.get("datetime", [])
                    if datetime_entities:
                        dt_tresh="2122-06-10"
                        for dt_entity in datetime_entities:
                            if dt_entity['type'] == 'date':
                                if dt_entity['timex'][0] <= dt_tresh:
                                    dt_tresh=dt_entity['timex'][0]
                        result.departure_date = dt_tresh
                    else:
                         result.departure_date = None
                else:
                     result.departure_date=None

                # Return -------------------------------------
                #on de recherche que la end date sans passer par la datetime
                return_date_entities = recognizer_result.entities.get("end_date", [])
                if return_date_entities:
                    # Sometimes it's a list
                    #if isinstance(return_date_entities, list):
                    #    result.return_date = ' '.join(return_date_entities)
                    #else:
                    datetime_entities = recognizer_result.entities.get("datetime", [])
                    if datetime_entities:
                        dt_tresh="0122-06-10"
                        for dt_entity in datetime_entities:
                            if dt_entity['type'] == 'date':
                                if dt_entity['timex'][0] >= dt_tresh:
                                    dt_tresh=dt_entity['timex'][0]
                        result.return_date = dt_tresh
                    else:
                         result.return_date=None
                else:
                     result.return_date=None

                # DateRange au cas ou
                datetime_entities = recognizer_result.entities.get("datetime", [])
                print("yoooooooo")
                if datetime_entities:
                    print("yo1")
                    dt_tresh="0122-06-10"
                    for dt_entity in datetime_entities:
                        print("yo2")
                        if dt_entity['type'] == "daterange":
                            print(dt_entity['timex'][0].strip("()").split(","))
                            if len(dt_entity['timex'][0].strip("()").split(","))==3:
                                print("yo4")
                                if result.departure_date==None:
                                    print("yo5")
                                    result.departure_date = dt_entity['timex'][0].strip("()").split(",")[0]
                                    print(dt_entity['timex'][0].split()[0])
                                if result.return_date==None:
                                    print("yo6")
                                    result.return_date = dt_entity['timex'][0].strip("()").split(",")[1]
                

                # Budget --------------------------------------
                budget_entities = recognizer_result.entities.get("$instance", {}).get(
                    "budget", []
                )
                if len(budget_entities) > 0:
                    #result.budget = "$" + budget_entities[0]["text"].capitalize()
                    result.budget = budget_entities[0]["text"].capitalize()
                else:
                    result.budget = None
                print(result)

            

        except Exception as exception:
            print(exception)

        return intent, result
