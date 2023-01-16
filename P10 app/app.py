# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This sample shows how to create a bot that demonstrates the following:
- Use [LUIS](https://www.luis.ai) to implement core AI capabilities.
- Implement a multi-turn conversation using Dialogs.
- Handle user interruptions for such things as `Help` or `Cancel`.
- Prompt for and validate requests for information from the user.
#######
ici on s'assure que les client de telemetry sont utilisés la ou on le desire
on fait quelques modifs pour le dep
#######
"""
#http pour travailler avec le protocole http
#HTTPStatus  définit une liste de codes d'état HTTP et les messages associés
from http import HTTPStatus

#to run a web server
from aiohttp import web
from aiohttp.web import Request, Response, json_response
#microsoft bot builder
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    UserState,
    TelemetryLoggerMiddleware,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from botbuilder.applicationinsights import ApplicationInsightsTelemetryClient
from botbuilder.integration.applicationinsights.aiohttp import (
    AiohttpTelemetryProcessor,
    bot_telemetry_middleware,
)

from config import DefaultConfig
from dialogs import MainDialog, BookingDialog
from bots import DialogAndWelcomeBot

from adapter_with_error_handler import AdapterWithErrorHandler
from flight_booking_recognizer import FlightBookingRecognizer

CONFIG = DefaultConfig()

# Create adapter.
# prend en compte la demande sous forme d'activité et la fait passer au gestionnaire de turn du bot
# joue un peu le role de douane in/out
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)

# Create MemoryStorage, UserState and ConversationState

# Pourquoi ai-je besoin d’un état ?
#  L’état conserve également les données plus longtemps que le tour actuel, 
#  afin que votre bot conserve les informations au cours d’une conversation à plusieurs tours

#au sein des bots, il existe differentes couches pour gerer l'etat
    # couche stockage
        # stockage memoire à usage de test volatile et temporaire
        # stockage blob azure
        # stockage cosmodb à eviter 
    # gestion de l'état (un etat est limité à un canal)
        #automatise lecture/ecriture dans le stockage
        # 3 collections de propriétés d'état à gerer:
            #etat user (dispo à tout moment de communication bot- ce user peu importe la conv )
                ## adapté au suivi du contexte de la conversation
                # clé {Activity.ChannelId}/users/{Activity.From.Id}#YourPropertyName
            #etat conversation (dispo à tout moment de communication bot- ce user, peu importe le user, pour une conv spécifique de groupe)
                ## adapté au suivi des informations relatives à l’utilisateur
                # clé {Activity.ChannelId}/conversations/{Activity.Conversation.Id}#YourPropertyName
            #etat conversation privée (limité à une conv specifique et un user specifique)
                ## adapté aux canaux qui prennent en charge les conversations de groupe, 
                ## mais où vous souhaitez suivre les informations spécifiques à l’utilisateur et à la conversation
                # clé {Activity.ChannelId}/conversations/{Activity.Conversation.Id}/users/{Activity.From.Id}#YourPropertyName

#intialisation d'une couche mémoire
#provient de botbuilder core
MEMORY = MemoryStorage()
#initialisation d'un user state et d'un conversation state
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

#initialisation de l'adaptateur : a besoin des settings et du conversation state
#provient du adapter_with_error_handler.py
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
# l'adaptateur gere la connectivité avec les channels
ADAPTER = AdapterWithErrorHandler(SETTINGS, CONVERSATION_STATE)

# Create telemetry client.
# Note the small 'client_queue_size'.  This is for demonstration purposes.  Larger queue sizes
# result in fewer calls to ApplicationInsights, improving bot performance at the expense of
# less frequent updates.
INSTRUMENTATION_KEY = CONFIG.APPINSIGHTS_INSTRUMENTATION_KEY
TELEMETRY_CLIENT = ApplicationInsightsTelemetryClient(
    INSTRUMENTATION_KEY, telemetry_processor=AiohttpTelemetryProcessor(), client_queue_size=10
)

# Code for enabling activity and personal information logging.
# Middleware for logging incoming, outgoing, updated or deleted Activity messages. 
# Uses the botTelemetryClient interface.
    #permet d'enregistrer un gestionnaire (handler) de middleware
TELEMETRY_LOGGER_MIDDLEWARE = TelemetryLoggerMiddleware(telemetry_client=TELEMETRY_CLIENT, log_personal_information=False)
ADAPTER.use(TELEMETRY_LOGGER_MIDDLEWARE)

# Create dialogs and Bot
####IMPORTANT client de telemetry pour LUIS à ajouter sinon pas de log dans appinsight
#on ajoute le telemetry_client en parametre pour envoyer les luis results sur app insight
RECOGNIZER = FlightBookingRecognizer(CONFIG,telemetry_client=TELEMETRY_CLIENT)
#RECOGNIZER = FlightBookingRecognizer(CONFIG)
#on peut ajouter la telemetry pour pour le booking dialog
BOOKING_DIALOG = BookingDialog(telemetry_client=TELEMETRY_CLIENT)
#BOOKING_DIALOG = BookingDialog()
DIALOG = MainDialog(RECOGNIZER, BOOKING_DIALOG, telemetry_client=TELEMETRY_CLIENT)
BOT = DialogAndWelcomeBot(CONVERSATION_STATE, USER_STATE, DIALOG, TELEMETRY_CLIENT)


# Listen for incoming requests on /api/messages.
async def messages(req: Request) -> Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)

# For aiohttp deployment: www.youtube.com/watch?v=eLMYd4LGAu8
# https://docs.microsoft.com/fr-fr/azure/app-service/configure-language-python#customize-startup-command
# On Azure Portal: App Service >> Web App Configuration >> General Settings
# Update <Startup Command> with:
# python3.8 -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func
# Note : app(.py) is the name of the app

def init_func(argv):
    APP = web.Application(middlewares=[bot_telemetry_middleware, aiohttp_error_middleware])
    APP.router.add_post("/api/messages", messages)
    return APP

# If the python interpreter is running that module (the source file) as the main program, it sets the special __name__ variable to have a value “__main__”. If this file is being imported from another module, 
# __name__ will be set to the module’s name. Module’s name is available as value to __name__ global variable. 

if __name__ == "__main__":
    APP = init_func(None)

    try:
        # Run app in production
        web.run_app(APP, host=CONFIG.HOST, port=CONFIG.PORT)#'0.0.0.0', port=CONFIG.PORT)#'localhost', port=CONFIG.PORT)#
    except Exception as error:
        raise error

#APP = web.Application(middlewares=[bot_telemetry_middleware, aiohttp_error_middleware])
#APP.router.add_post("/api/messages", messages)
#
#if __name__ == "__main__":
#    try:
#        web.run_app(APP, host="localhost", port=CONFIG.PORT)
#    except Exception as error:
#        raise error

###retente