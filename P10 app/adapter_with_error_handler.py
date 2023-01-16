# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

### rien à changer ici
import sys
import traceback
from datetime import datetime

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    TurnContext,
)
from botbuilder.schema import ActivityTypes, Activity

#########
from config import DefaultConfig
#pour permettre d'envoyer les logs sur app insight
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

CONFIG = DefaultConfig()
#########


class AdapterWithErrorHandler(BotFrameworkAdapter):
    def __init__(
        self,
        settings: BotFrameworkAdapterSettings,
        conversation_state: ConversationState,
    ):
        super().__init__(settings)
        self._conversation_state = conversation_state

        #############
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(AzureLogHandler(connection_string=CONFIG.APPINSIGHTS_CONNECT))
        self.logger.setLevel(logging.INFO)
        #############

        # Catch-all for errors.
        async def on_error(context: TurnContext, error: Exception):
            # This check writes out errors to console log
            # NOTE: In production environment, you should consider logging this to Azure
            #       application insights.
            print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
            traceback.print_exc()

            logger = logging.getLogger(__name__)
            logger.addHandler(AzureLogHandler(connection_string=CONFIG.APPINSIGHTS_CONNECT))
            logger.setLevel(logging.INFO)
            logger.error("The bot encountered an error or bug to fix")
            # Send a message to the user
            await context.send_activity("The bot encountered an error or bug.")
            await context.send_activity(
                "To continue to run this bot, please fix the bot source code."
            )
            # Send a trace activity if we're talking to the Bot Framework Emulator
            if context.activity.channel_id == "emulator":
                # Create a trace activity that contains the error object
                trace_activity = Activity(
                    label="TurnError",
                    name="on_turn_error Trace",
                    timestamp=datetime.utcnow(),
                    type=ActivityTypes.trace,
                    value=f"{error}",
                    value_type="https://www.botframework.com/schemas/error",
                )
                # Send a trace activity, which will be displayed in Bot Framework Emulator
                await context.send_activity(trace_activity)

            # Clear out state
            nonlocal self
            await self._conversation_state.delete(context)

        self.on_turn_error = on_error
