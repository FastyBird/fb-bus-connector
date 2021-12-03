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
FastyBird BUS connector plugin client handlers module handler for API v1
"""

# Python base dependencies
import uuid
from typing import Optional

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.api.v1parser import V1Parser
from fb_bus_connector_plugin.api.v1validator import V1Validator
from fb_bus_connector_plugin.exceptions import ParsePayloadException
from fb_bus_connector_plugin.handlers.base import BaseHandler
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.receivers.receiver import Receiver


@inject(alias=BaseHandler)
class ApiV1Handler(BaseHandler):  # pylint: disable=too-few-public-methods
    """
    BUS messages handler for API v1

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         handlers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __parser: V1Parser
    __receiver: Receiver

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        parser: V1Parser,
        receiver: Receiver,
        logger: Logger,
    ) -> None:
        BaseHandler.__init__(self, logger=logger)

        self.__parser = parser
        self.__receiver = receiver

    # -----------------------------------------------------------------------------

    def on_message(self, payload: bytearray, length: int, address: Optional[int], client_id: uuid.UUID) -> None:
        """On receive message event"""
        if V1Validator.validate_version(payload=payload) is False:
            return

        if V1Validator.validate(payload=payload) is False:
            self._logger.warning("Received message is not valid FIB v1 convention message: %s", payload)

            return

        try:
            entity = self.__parser.parse_message(
                payload=payload,
                length=length,
                address=address,
                client_id=client_id,
            )

        except ParsePayloadException as ex:
            self._logger.error("Received message could not be successfully parsed to entity")
            self._logger.exception(ex)

            return

        self.__receiver.append(entity=entity)
