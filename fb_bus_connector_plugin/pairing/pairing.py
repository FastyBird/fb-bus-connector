#!/usr/bin/python3

#     Copyright 2021. FastyBird s.r.o.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

"""
FastyBird BUS connector plugin client pairing module proxy
"""

# Python base dependencies
from typing import List

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.pairing.base import BasePairing


@inject
class DevicesPairing:  # pylint: disable=too-few-public-methods
    """
    BUS pairing handler proxy

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         pairing

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __pairing: List[BasePairing]

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        pairing: List[BasePairing],
    ) -> None:
        self.__pairing = pairing

    # -----------------------------------------------------------------------------

    def handle(self) -> None:
        """Handle publish devices pairing messages"""
        for pairing in self.__pairing:
            if pairing.is_enabled():
                pairing.handle()

    # -----------------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """Check if any paring handler is enabled"""
        for pairing in self.__pairing:
            if pairing.is_enabled():
                return True

        return False
