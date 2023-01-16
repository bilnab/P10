# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle date/time resolution for booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    DateTimePrompt,
    PromptValidatorContext,
    PromptOptions,
    DateTimeResolution,
)
from .cancel_and_help_dialog import CancelAndHelpDialog


class InDateResolverDialog(CancelAndHelpDialog):
    """Resolve the date"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(InDateResolverDialog, self).__init__(
            dialog_id or InDateResolverDialog.__name__, 
            telemetry_client
        )
        self.telemetry_client = telemetry_client

        date_time_prompt = DateTimePrompt(
            DateTimePrompt.__name__, 
            InDateResolverDialog.datetime_prompt_validator
        )
        date_time_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            "WF_Departure_Date_Dialog", [self.dep_date_ask_step, self.end_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(date_time_prompt)
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = "WF_Departure_Date_Dialog"

    async def dep_date_ask_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the date."""
        timex = step_context.options

        prompt_msg = "when do you want to leave?"
        reprompt_msg = (
            "I'm sorry, for best results, please enter your travel "
            "date including the month, day and year."
        )

        if timex is None:
            # We were not given any date at all so prompt the user.
            return await step_context.prompt(
                DateTimePrompt.__name__,
                PromptOptions(  # pylint: disable=bad-continuation
                    prompt=MessageFactory.text(prompt_msg),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )

        # We have a Date we just need to check it is unambiguous.
        #if "definite" in Timex(timex).types:
        #plus logique de reprompt si date pas defini
        if "definite" not in Timex(timex).types:
            # This is essentially a "reprompt" of the data we were given up front.
            return await step_context.prompt(
                DateTimePrompt.__name__, PromptOptions(prompt=reprompt_msg)
            )

        return await step_context.next(DateTimeResolution(timex=timex))

    async def end_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""
        timex = step_context.result[0].timex
        return await step_context.end_dialog(timex)

    @staticmethod
    async def datetime_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        """ Validate the date provided is in proper form. """
        if prompt_context.recognized.succeeded:
            timex = prompt_context.recognized.value[0].timex.split("T")[0]

            # TODO: Needs TimexProperty
            return "definite" in Timex(timex).types

        return False

class OutDateResolverDialog(CancelAndHelpDialog):
    """Resolve the date"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(OutDateResolverDialog, self).__init__(
            dialog_id or OutDateResolverDialog.__name__, 
            telemetry_client
        )
        self.telemetry_client = telemetry_client

        date_time_prompt = DateTimePrompt(
            DateTimePrompt.__name__, 
            OutDateResolverDialog.datetime_prompt_validator
        )
        date_time_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            "WF_Return_Date_Dialog", [self.ret_date_ask_step, self.end_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(date_time_prompt)
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = "WF_Return_Date_Dialog"

    async def ret_date_ask_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the date."""
        timex = step_context.options

        prompt_msg = "when do you want to come back?"
        reprompt_msg = (
            "I'm sorry, for best results, please enter your travel "
            "date including the month, day and year."
        )

        if timex is None:
            # We were not given any date at all so prompt the user.
            return await step_context.prompt(
                DateTimePrompt.__name__,
                PromptOptions(  # pylint: disable=bad-continuation
                    prompt=MessageFactory.text(prompt_msg),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )

        # We have a Date we just need to check it is unambiguous.
        #if "definite" in Timex(timex).types:
        #plus logique de reprompt si date pas defini
        if "definite" not in Timex(timex).types:
            # This is essentially a "reprompt" of the data we were given up front.
            return await step_context.prompt(
                DateTimePrompt.__name__, PromptOptions(prompt=reprompt_msg)
            )

        return await step_context.next(DateTimeResolution(timex=timex))

    async def end_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""
        timex = step_context.result[0].timex
        return await step_context.end_dialog(timex)

    @staticmethod
    async def datetime_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        """ Validate the date provided is in proper form. """
        if prompt_context.recognized.succeeded:
            timex = prompt_context.recognized.value[0].timex.split("T")[0]

            # TODO: Needs TimexProperty
            return "definite" in Timex(timex).types

        return False