# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import datetime
from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import (
    MessageFactory,
    TurnContext,
    BotTelemetryClient,
    NullTelemetryClient,
)
from botbuilder.schema import InputHints
from datetime import datetime
from booking_details import BookingDetails
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from .booking_dialog import BookingDialog

#########
from config import DefaultConfig
#pour permettre d'envoyer les logs sur app insight
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

CONFIG = DefaultConfig()
#########


class MainDialog(ComponentDialog):
    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        booking_dialog: BookingDialog,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)
        self.telemetry_client = telemetry_client or NullTelemetryClient()

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = self.telemetry_client

        booking_dialog.telemetry_client = self.telemetry_client

        #############
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(AzureLogHandler(connection_string=CONFIG.APPINSIGHTS_CONNECT))
        self.logger.setLevel(logging.INFO)
        #############

        #la classe MainDialog
        wf_dialog = WaterfallDialog(
            "WF_Main_Dialog", [self.intro_politeness_step, self.luis_intention_step, self.pre_final_step, self.final_booking_summary_step]
        )
        wf_dialog.telemetry_client = self.telemetry_client

        self._luis_recognizer = luis_recognizer
        self._booking_dialog_id = booking_dialog.id #"WF_Book_Dialog"#wf_book_dialog.id #booking_dialog#.id

        self.add_dialog(text_prompt)
        self.add_dialog(booking_dialog)
        self.add_dialog(wf_dialog)

        self.initial_dialog_id = "WF_Main_Dialog"

    async def intro_politeness_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # si pas de luis recognizer paramétré , on envoie une recommendation
        # puis continuera tout de meme sans LUIS
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )

            return await step_context.next(None)

        message_text = (
            str(step_context.options)
            if step_context.options
            else "hello, I am flybot, how can I help you?"
        )

        # Message d'intro de politesse qui attend une réponse
        self.logger.info(f"Bot introduction: {message_text}")

        return await step_context.prompt(
            TextPrompt.__name__, PromptOptions(prompt=MessageFactory.text(
            message_text, message_text, InputHints.expecting_input)
            )
        )

    async def luis_intention_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            # si LUIS pas config, on lance le booking dialog avec des bookingdetails vides
            self.logger.warning("LUIS not configured")
            self.logger.info("Booking Dialog beginning")
            return await step_context.begin_dialog(
                self._booking_dialog_id, BookingDetails()
            )

        self.logger.info("Luis Call")
        # on appelle LUIS pour decoder l'intention et les détails
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )
        self.logger.info(f"client utterance: {step_context.context.activity.text}")


        # CAS 1: LUIS trouve BOOK_flight et donne des resultats
        # on lance le bookingdialog par le booking_dialog_id en donnant les details luis_results trouvés par LUIS
        if intent == Intent.BOOK_FLIGHT.value and luis_result:
            self.logger.info("Luis returns a BOOKING intention")
            # Show a warning for Origin and Destination if we can't resolve them.
            await MainDialog._show_warning_for_unsupported_cities(
                step_context.context, luis_result
            )

            # Run the BookingDialog giving it whatever details we have from the LUIS call.
            self.logger.info("Booking Dialog beginning")
            return await step_context.begin_dialog(self._booking_dialog_id, luis_result)

        #on n a pas parametrer d'intention de demande demande de meteo dans LUIS, on laisse donc tomber
        #if intent == Intent.GET_WEATHER.value:
        #    get_weather_text = "TODO: get weather flow here"
        #    get_weather_message = MessageFactory.text(
        #        get_weather_text, get_weather_text, InputHints.ignoring_input
        #    )
        #    await step_context.context.send_activity(get_weather_message)

        # CAS 2: LUIS trouve NONE
        # on lance le bookingdialog par le booking_dialog_id en donnant les details luis_results trouvés par LUIS
        if intent == Intent.NONE_INTENT.value:
            didnt_understand_text = (
                "Sorry, I didn't get that. Please try asking in a different way"
            )
            self.logger.warning("Luis returns a NONE intention")
            await step_context.context.send_activity(MessageFactory.text(
                didnt_understand_text, didnt_understand_text, InputHints.ignoring_input
            ))

        return await step_context.next(None)

    async def pre_final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        #si pas la bonne proposition , on stoppe le dialogue et on repart du début
        if step_context.result is None:
            self.logger.warning("CANCEL BOOKING")
            msg_txt = (
                f"it seems that you want to cancel your request, let's try again from the beginning"
                f" What can I do for you?"
            )
            message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            return await step_context.replace_dialog(self.id, msg_txt)

        #sinon on passe au step suivant en passant le step_context.result non vide pour etre utiliser dans le summary
        return await step_context.next(step_context.result)

    async def final_booking_summary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.
        if step_context.result is not None:
            result = step_context.result

            # Now we have all the booking details call the booking service.

            # If the call to the booking service was successful tell the user.
            # time_property = Timex(result.travel_date)
            # travel_date_msg = time_property.to_natural_language(datetime.now())
            departure_date = datetime.strptime(result.departure_date, "%Y-%m-%d").date()
            return_date = datetime.strptime(result.return_date, "%Y-%m-%d").date()
            final_summary_txt = (
                f"I have booked a fly from { result.origin } to { result.destination } on {departure_date.strftime('%B %d %Y')}"
                f" and return on {return_date.strftime('%B %d %Y')}."
                f" with a budget of {result.budget} $."
            )
            self.logger.info(f"BOOKING CONFIRMED: {final_summary_txt}")

            await step_context.context.send_activity(MessageFactory.text(
                 final_summary_txt,  final_summary_txt, InputHints.ignoring_input))

        return await step_context.end_dialog()


    @staticmethod
    async def _show_warning_for_unsupported_cities(
        context: TurnContext, luis_result: BookingDetails
    ) -> None:
        """
        Shows a warning if the requested From or To cities are recognized as entities but they are not in the Airport entity list.
        In some cases LUIS will recognize the From and To composite entities as a valid cities but the From and To Airport values
        will be empty if those entity values can't be mapped to a canonical item in the Airport.
        """
        if luis_result.unsupported_airports:
            message_text = (
                f"Sorry but the following airports are not supported:"
                f" {', '.join(luis_result.unsupported_airports)}"
            )
            message = MessageFactory.text(
                message_text, message_text, InputHints.ignoring_input
                )
            await context.send_activity(message)
