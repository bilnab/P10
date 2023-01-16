# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

#on adapte les details du booking à notre problématique
class BookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        #on ajoute les variables de notre problématique
        departure_date: str = None,
        return_date: str = None,
        budget: str = None,
        ####
        unsupported_airports=None,
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.origin = origin
        ######
        self.departure_date = departure_date,
        self.return_date = return_date
        self.budget = budget
        ######
        self.unsupported_airports = unsupported_airports
