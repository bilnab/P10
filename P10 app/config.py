#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Configuration for the bot."""

import os


class DefaultConfig:
    """Configuration for the bot."""

    PORT = 8000 #3978 #8080
    HOST = '0.0.0.0' #'localhost'
    APP_ID = os.environ.get("MicrosoftAppId","40ee6c86-cce6-4f8f-b315-a19cf1b34e84")#clé à mettre du azure bot channel
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword","9oF8Q~FIrC4MMOYffBOxZrycDk-gCgePWGhqqczV")#faut prendre la value et non le secret id
    LUIS_APP_ID = os.environ.get("LuisAppId", "742890f8-77f9-4b15-8f45-257554e9e900")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "2e9b1d71c34c40e09607079d58f2140e")
    # LUIS endpoint host name, ie "westus.api.cognitive.microsoft.com"
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "westeurope.api.cognitive.microsoft.com")

        #azure app insight key for monitoring
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get(
        "AppInsightsInstrumentationKey", "be8d3e38-9d15-4e3f-82c8-8af964ea2741"
    )
    APPINSIGHTS_CONNECT = os.environ.get(
        "AppInsightsConnect","InstrumentationKey=be8d3e38-9d15-4e3f-82c8-8af964ea2741;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/;LiveEndpoint=https://westeurope.livediagnostics.monitor.azure.com/")
