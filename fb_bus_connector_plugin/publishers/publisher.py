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
FastyBird BUS connector plugin client publishers module proxy
"""

# Python base dependencies
from typing import List, Set

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.publishers.base import BasePublisher
from fb_bus_connector_plugin.registry.records import DeviceRecord


@inject
class Publisher:  # pylint: disable=too-few-public-methods
    """
    BUS publishers proxy

    @package        FastyBird:FbBusConnectorPlugin!
    @module         publishers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __publishers: Set[BasePublisher]

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        publishers: List[BasePublisher],
    ) -> None:
        self.__publishers = set(publishers)

    # -----------------------------------------------------------------------------

    def handle(
        self,
        device: DeviceRecord,
    ) -> bool:
        """Handle publish read or write message to device"""
        result = True

        for publisher in self.__publishers:
            if not publisher.handle(device=device):
                result = False

        return result
