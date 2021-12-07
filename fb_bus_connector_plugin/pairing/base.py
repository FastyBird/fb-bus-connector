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
FastyBird BUS connector plugin client pairing module base handler
"""

# Python base dependencies
import uuid
from abc import ABC, abstractmethod
from typing import List, Union

# Library libs
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.types import ProtocolVersion


class BasePairing(ABC):  # pylint: disable=too-few-public-methods
    """
    BUS pairing base handler

    @package        FastyBird:FbBusConnectorPlugin!
    @module         pairing

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
    def loop(self) -> None:
        """Handle pairing messages"""

    # -----------------------------------------------------------------------------

    def enable(self, client_id: Union[uuid.UUID, List[uuid.UUID], None] = None) -> None:
        """Enable devices pairing"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if any paring handler is enabled"""

    # -----------------------------------------------------------------------------

    def disable(self) -> None:
        """Disable devices pairing"""

    # -----------------------------------------------------------------------------

    @abstractmethod
    def version(self) -> ProtocolVersion:
        """Pairing supported protocol version"""
