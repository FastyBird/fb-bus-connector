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
FastyBird BUS connector plugin receivers module proxy
"""

# Python base dependencies
import uuid
from queue import Full as QueueFull
from queue import Queue
from typing import List, Optional, Set

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.api.v1parser import V1Parser
from fb_bus_connector_plugin.api.v1validator import V1Validator
from fb_bus_connector_plugin.exceptions import (
    InvalidStateException,
    ParsePayloadException,
)
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.receivers.base import BaseReceiver
from fb_bus_connector_plugin.receivers.entities import BaseEntity
from fb_bus_connector_plugin.types import ProtocolVersion


@inject
class Receiver:
    """
    BUS messages receivers proxy

    @package        FastyBird:FbBusConnectorPlugin!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __receivers: Set[BaseReceiver]
    __queue: Queue
    __parser: V1Parser
    __validator: V1Validator

    __logger: Logger

    # -----------------------------------------------------------------------------

    @inject
    def __init__(
        self,
        receivers: List[BaseReceiver],
        parser: V1Parser,
        validator: V1Validator,
        logger: Logger,
    ) -> None:
        self.__receivers = set(receivers)
        self.__parser = parser
        self.__validator = validator

        self.__logger = logger

        self.__queue = Queue(maxsize=1000)

    # -----------------------------------------------------------------------------

    def append(self, entity: BaseEntity) -> None:
        """Append new entity to process"""
        try:
            self.__queue.put(item=entity)

        except QueueFull:
            self.__logger.error("Connector processing queue is full. New messages could not be added")

    # -----------------------------------------------------------------------------

    def loop(self) -> None:
        """Process received message"""
        try:
            if not self.__queue.empty():
                entity = self.__queue.get()

                if isinstance(entity, BaseEntity):
                    for receiver in self.__receivers:
                        receiver.receive(entity=entity)

        except InvalidStateException as ex:
            self.__logger.error("Received message could not be processed")
            self.__logger.exception(ex)

    # -----------------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Check if all messages are processed"""
        return self.__queue.empty()

    # -----------------------------------------------------------------------------

    def on_message(  # pylint: disable=too-many-arguments
        self,
        payload: bytearray,
        length: int,
        address: Optional[int],
        client_id: uuid.UUID,
        protocol_version: ProtocolVersion,
    ) -> None:
        """Handle received message"""
        if self.__validator.validate_version(payload=payload, protocol_version=protocol_version) is False:
            return

        if self.__validator.validate(payload=payload, protocol_version=protocol_version) is False:
            self.__logger.warning(
                "Received message is not valid FIB %s convention message: %s",
                protocol_version.value,
                payload,
            )

            return

        try:
            entity = self.__parser.parse_message(
                payload=payload,
                length=length,
                address=address,
                client_id=client_id,
                protocol_version=protocol_version,
            )

        except ParsePayloadException as ex:
            self.__logger.error("Received message could not be successfully parsed to entity")
            self.__logger.exception(ex)

            return

        self.append(entity=entity)
