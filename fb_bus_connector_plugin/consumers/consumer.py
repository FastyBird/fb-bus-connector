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
FastyBird BUS connector plugin messages consumers module proxy
"""

# Python base dependencies
from abc import ABC, abstractmethod
from queue import Full as QueueFull
from queue import Queue
from typing import Set

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.consumers.entities import BaseEntity
from fb_bus_connector_plugin.exceptions import InvalidStateException
from fb_bus_connector_plugin.logger import Logger


class IConsumer(ABC):  # pylint: disable=too-few-public-methods
    """
    Entity consumer interface

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @abstractmethod
    def consume(self, entity: BaseEntity) -> None:
        """Consume entity"""


@inject
class Consumer:
    """
    Messages entities consumer

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __consumers: Set[IConsumer]
    __queue: Queue

    __logger: Logger

    # -----------------------------------------------------------------------------

    @inject
    def __init__(
        self,
        logger: Logger,
    ) -> None:
        self.__consumers = set()

        self.__logger = logger

        self.__queue = Queue(maxsize=1000)

    # -----------------------------------------------------------------------------

    def append(self, entity: BaseEntity) -> None:
        """Append new entity for consume"""
        try:
            self.__queue.put(item=entity)

        except QueueFull:
            self.__logger.error("Consumer processing queue is full. New messages could not be added")

    # -----------------------------------------------------------------------------

    def consume(self) -> None:
        """Consume message"""
        try:
            if not self.__queue.empty():
                entity = self.__queue.get()

                if isinstance(entity, BaseEntity):
                    for consumer in self.__consumers:
                        consumer.consume(entity=entity)

        except InvalidStateException as ex:
            self.__logger.error("Received message could not be consumed")
            self.__logger.exception(ex)

    # -----------------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Check if all messages are handled"""
        return self.__queue.empty()

    # -----------------------------------------------------------------------------

    def register_consumer(
        self,
        consumer: IConsumer,
    ) -> None:
        """Register new consumer to proxy"""
        self.__consumers.add(consumer)
