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
FastyBird BUS connector plugin clients module base client
"""

# Python base dependencies
import uuid
from abc import ABC, abstractmethod
from typing import List

# Library libs
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.types import ProtocolVersion


class BaseClient(ABC):
    """
    Base client

    @package        FastyBird:FbBusConnectorPlugin!
    @module         clients

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

    @property
    @abstractmethod
    def id(self) -> uuid.UUID:  # pylint: disable=invalid-name
        """Client unique identifier"""

    # -----------------------------------------------------------------------------

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Client state"""

    # -----------------------------------------------------------------------------

    @property
    @abstractmethod
    def version(self) -> ProtocolVersion:
        """Protocol version used by client"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def broadcast_packet(self, payload: List[int], waiting_time: float = 0.0) -> bool:
        """Broadcast packet to all devices"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def send_packet(self, address: int, payload: List[int], waiting_time: float = 0.0) -> bool:
        """Send packet to specific device address"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def handle(self) -> int:
        """Handle clients communication"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def enable(self) -> bool:
        """Enable client communication"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def disable(self) -> bool:
        """Disable client communication"""
