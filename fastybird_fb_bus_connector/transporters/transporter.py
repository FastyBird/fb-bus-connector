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
FastyBird BUS connector transporters module proxy
"""

# Python base dependencies
import logging
from typing import List, Set, Union

from fastybird_fb_bus_connector.logger import Logger

# Library libs
from fastybird_fb_bus_connector.transporters.base import ITransporter
from fastybird_fb_bus_connector.transporters.pjon import PjonTransporter


class Transporter:
    """
    Transporters proxy

    @package        FastyBird:FbBusConnector!
    @module         transporters/transporter

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __transporters: Set[ITransporter]

    __logger: Union[Logger, logging.Logger]

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        logger: Union[Logger, logging.Logger] = logging.getLogger("dummy"),
    ) -> None:
        self.__transporters = set()

        self.__logger = logger

    # -----------------------------------------------------------------------------

    def initialize(
        self,
        address: int,
        baud_rate: int,
        interface: str,
    ) -> None:
        """Register new transporter to proxy"""
        self.__transporters.add(
            PjonTransporter(  # pylint: disable=no-value-for-parameter
                address=address,
                baud_rate=baud_rate,
                interface=interface,
                logger=self.__logger,
            )
        )

    # -----------------------------------------------------------------------------

    def broadcast_packet(
        self,
        payload: List[int],
        waiting_time: float = 0.0,
    ) -> bool:
        """Broadcast packet to all devices"""
        result = True

        for transporter in self.__transporters:
            if not transporter.broadcast_packet(payload=payload, waiting_time=waiting_time):
                result = False

        return result

    # -----------------------------------------------------------------------------

    def send_packet(
        self,
        address: int,
        payload: List[int],
        waiting_time: float = 0.0,
    ) -> bool:
        """Send packet to specific device address"""
        result = True

        for transporter in self.__transporters:
            if not transporter.send_packet(address=address, payload=payload, waiting_time=waiting_time):
                result = False

        return result

    # -----------------------------------------------------------------------------

    def handle(self) -> int:
        """Handle communication from transporters"""
        packets_to_be_sent = 0

        for transporter in self.__transporters:
            transporter_packets_to_be_sent = transporter.handle()

            packets_to_be_sent = packets_to_be_sent + transporter_packets_to_be_sent

        return packets_to_be_sent
