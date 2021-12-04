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
FastyBird BUS connector plugin receivers module base receiver
"""

# Python base dependencies
from abc import ABC, abstractmethod

# Library libs
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.receivers.entities import BaseEntity


class BaseReceiver(ABC):  # pylint: disable=too-few-public-methods
    """
    BUS messages base receiver

    @package        FastyBird:FbBusConnectorPlugin!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    _logger: Logger

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        logger: Logger,
    ) -> None:
        self._logger = logger

    # -----------------------------------------------------------------------------

    @abstractmethod
    def receive(self, entity: BaseEntity) -> None:
        """Handle received entity"""
