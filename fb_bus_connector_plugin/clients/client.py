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
FastyBird BUS connector plugin clients module proxy
"""

# Python base dependencies
import uuid
from typing import List, Optional, Set

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.clients.base import BaseClient
from fb_bus_connector_plugin.clients.pjon import PjonClient
from fb_bus_connector_plugin.exceptions import InvalidArgumentException
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.receivers.receiver import Receiver
from fb_bus_connector_plugin.types import ClientType, ProtocolVersion


class Client:
    """
    Plugin client proxy

    @package        FastyBird:FbBusConnectorPlugin!
    @module         clients

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __clients: Set[BaseClient]

    # -----------------------------------------------------------------------------

    @inject
    def __init__(self) -> None:
        self.__clients = set()

    # -----------------------------------------------------------------------------

    def register_client(self, client: BaseClient) -> None:
        """Register new client to proxy"""
        self.__clients.add(client)

    # -----------------------------------------------------------------------------

    def remove_client(self, client_id: uuid.UUID) -> bool:
        """Remove client from clients"""
        for client in self.__clients:
            if client_id.__eq__(client.id):
                self.__clients.remove(client)

        return False

    # -----------------------------------------------------------------------------

    def reset_clients(self) -> None:
        """Reset registered clients"""
        self.__clients = set()

    # -----------------------------------------------------------------------------

    def enable_client(self, client_id: Optional[uuid.UUID] = None) -> bool:
        """Enable one or more clients"""
        for client in self.__clients:
            if client_id is None or client_id.__eq__(client.id):
                return client.enable()

        return False

    # -----------------------------------------------------------------------------

    def disable_client(self, client_id: Optional[uuid.UUID] = None) -> bool:
        """Disable one or more clients"""
        for client in self.__clients:
            if client_id is None or client_id.__eq__(client.id):
                return client.disable()

        return False

    # -----------------------------------------------------------------------------

    def broadcast_packet(
        self,
        payload: List[int],
        waiting_time: float = 0.0,
        client_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Broadcast packet to all devices"""
        result = True

        for client in self.__clients:
            if (client_id is None or client_id.__eq__(client.id)) and client.enabled:
                if not client.broadcast_packet(payload=payload, waiting_time=waiting_time):
                    result = False

        return result

    # -----------------------------------------------------------------------------

    def send_packet(
        self,
        address: int,
        payload: List[int],
        waiting_time: float = 0.0,
        client_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """Send packet to specific device address"""
        result = True

        for client in self.__clients:
            if (client_id is None or client_id.__eq__(client.id)) and client.enabled:
                if not client.send_packet(address=address, payload=payload, waiting_time=waiting_time):
                    result = False

        return result

    # -----------------------------------------------------------------------------

    def loop(self) -> int:
        """Handle communication from client"""
        packets_to_be_sent = 0

        for client in self.__clients:
            if client.enabled:
                client_packets_to_be_sent = client.handle()

                packets_to_be_sent = packets_to_be_sent + client_packets_to_be_sent

        return packets_to_be_sent


class ClientFactory:  # pylint: disable=too-few-public-methods
    """
    Plugin client factory

    @package        FastyBird:FbBusConnectorPlugin!
    @module         clients

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __client: Client
    __receiver: Receiver

    __logger: Logger

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        client: Client,
        receiver: Receiver,
        logger: Logger,
    ) -> None:
        self.__client = client
        self.__receiver = receiver

        self.__logger = logger

    # -----------------------------------------------------------------------------

    def create(  # pylint: disable=too-many-arguments
        self,
        client_id: uuid.UUID,
        client_type: ClientType,
        client_address: Optional[int],
        client_baud_rate: Optional[int],
        client_interface: Optional[str],
        protocol_version: ProtocolVersion,
    ) -> None:
        """Create new client"""
        if client_type == ClientType.PJON:
            client = PjonClient(
                client_id=client_id,
                client_address=client_address,
                client_baud_rate=client_baud_rate,
                client_interface=client_interface,
                client_state=True,
                protocol_version=protocol_version,
                receiver=self.__receiver,
                logger=self.__logger,
            )

            self.__client.register_client(client=client)

            self.__logger.debug(
                "Created PJON client: %s to interface: %s",
                client_id.__str__(),
                client_interface,
                extra={
                    "client_id": client_id.__str__(),
                    "client_interface": client_interface,
                    "client_address": client_address,
                    "client_baud_rate": client_baud_rate,
                    "protocol_version": protocol_version,
                },
            )

            return

        raise InvalidArgumentException(f"Unsupported client type: {client_type}")
