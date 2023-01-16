# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from datatypes_date_time.timex import Timex
import datetime

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions
from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.schema import InputHints
from .cancel_and_help_dialog import CancelAndHelpDialog
from .date_resolver_dialog import InDateResolverDialog, OutDateResolverDialog

#########
from config import DefaultConfig
#pour permettre d'envoyer les logs sur app insight
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

CONFIG = DefaultConfig()
#########

class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client
        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        #############
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(AzureLogHandler(connection_string=CONFIG.APPINSIGHTS_CONNECT))
        self.logger.setLevel(logging.INFO)
        #############

        wf_book_dialog = WaterfallDialog(#WaterfallDialog.__name__,
            "WF_Book_Dialog",
            [
                self.destination_step,
                self.origin_step,
                #self.travel_date_step,
                self.departure_date_step,
                self.return_date_step,
                self.budget_step,
                self.book_confirm_step, #on rajoute la confirmation de propal
                self.end_step,
            ],
        )
        wf_book_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))

        
        self.add_dialog(
            InDateResolverDialog(InDateResolverDialog.__name__, self.telemetry_client)
        )
        self.add_dialog(
            OutDateResolverDialog(OutDateResolverDialog.__name__, self.telemetry_client)
        )
        self.add_dialog(wf_book_dialog)

        self.initial_dialog_id = "WF_Book_Dialog" #WaterfallDialog.__name__ #peut etre la à changer

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination."""
        booking_details = step_context.options

        #si LUIS n'a pas trouvé au préalable 
        if booking_details.destination is None:
            self.logger.info("Bot ask for destination")
            #la methode MessageFactory.text accepte un input par defaut
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("To which city would you like to travel?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation


        #on passe au prochain step du dialogue 
        return await step_context.next(booking_details.destination)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.destination = step_context.result
        self.logger.info(f"Destination: {booking_details.destination}")

        if booking_details.origin is None:
            self.logger.info("Bot ask for origin")
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("From which city will you be travelling?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.origin)

    async def departure_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel in date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.origin = step_context.result
        self.logger.info(f"Origin: {booking_details.origin}")
        #si pas de date de depart on interroge
        if not booking_details.departure_date or self.is_ambiguous(
            booking_details.departure_date
        ):
            self.logger.info("Bot ask for departure date")
            return await step_context.begin_dialog(
                InDateResolverDialog.__name__, booking_details.departure_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.departure_date)
    
    async def return_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel in date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.departure_date = step_context.result
        self.logger.info(f"departure date: {booking_details.departure_date}")
        #si pas de date de depart on interroge
        if not booking_details.return_date or self.is_ambiguous(
            booking_details.return_date
        ):
            self.logger.info("Bot ask for return date")
            return await step_context.begin_dialog(
                OutDateResolverDialog.__name__, booking_details.return_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.return_date)

    async def budget_step(
        self, step_context: WaterfallStepContext
        ) -> DialogTurnResult:
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.return_date = step_context.result
        self.logger.info(f"return date: {booking_details.return_date}")
        if booking_details.budget is None:
            self.logger.info("Bot ask for budget")
            message_text = "What is your budget?"
            prompt_message = MessageFactory.text(
                message_text, message_text, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__, PromptOptions(prompt=prompt_message)
            )
        return await step_context.next(booking_details.budget)

    async def book_confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.budget = step_context.result
        self.logger.info(f"budget: {booking_details.budget}")
        #strptime pour passer un string en objet datetime
        departure_date = datetime.datetime.strptime(booking_details.departure_date, "%Y-%m-%d").date()
        return_date = datetime.datetime.strptime(booking_details.return_date, "%Y-%m-%d").date()
        msg = (
            f"Please confirm, you want to book a flight from: { booking_details.origin } to { booking_details.destination }"
            f" from {departure_date.strftime('%B %d %Y')}"
            f" to {return_date.strftime('%B %d %Y')}."
            f" for a budget of {booking_details.budget}."
        )

        self.logger.info(f"Bot ask for booking confirmation: {msg}")
        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def end_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""
        #dans tous les cas on end le dialog mais en fonction de la reponse au confirmprompt
        #on passe en resultat les booking details ou rien
        if step_context.result:
            booking_details = step_context.options
            #booking_details.travel_date = step_context.result
            #si yes
            return await step_context.end_dialog(booking_details)
        #si no
        return await step_context.end_dialog()

    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
