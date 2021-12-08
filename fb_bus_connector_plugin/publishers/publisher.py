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
from datetime import datetime
from typing import List, Set, Union

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.publishers.base import BasePublisher
from fb_bus_connector_plugin.registry.model import DevicesRegistry
from fb_bus_connector_plugin.types import ButtonPayloadType, SwitchPayloadType, DeviceDataType


@inject
class Publisher:  # pylint: disable=too-few-public-methods
    """
    BUS publishers proxy

    @package        FastyBird:FbBusConnectorPlugin!
    @module         publishers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __publishers: Set[BasePublisher]

    __devices_registry: DevicesRegistry

    __processed_devices: List[str] = []

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        publishers: List[BasePublisher],
        devices_registry: DevicesRegistry,
    ) -> None:
        self.__publishers = set(publishers)

        self.__devices_registry = devices_registry

    # -----------------------------------------------------------------------------

    def loop(self) -> None:
        """Handle publish read or write message to device"""
        # Check for processing queue
        if len(self.__processed_devices) >= len(self.__devices_registry):
            self.__processed_devices = []

        for device in self.__devices_registry:
            if device.id.__str__() not in self.__processed_devices and device.enabled and device.ready:
                for publisher in self.__publishers:
                    if publisher.handle(device=device):
                        self.__processed_devices.append(device.id.__str__())

    # -----------------------------------------------------------------------------

    @staticmethod
    def broadcast_value(
        broadcast_key: str,
        broadcast_value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime],
        broadcast_data_type: DeviceDataType,
    ) -> bool:
        """Broadcast value for given key"""
        print("PREPARING BROADCAST: %s:%s:%s", broadcast_key, broadcast_value, broadcast_data_type)

        return False
