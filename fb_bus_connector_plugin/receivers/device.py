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
FastyBird BUS connector plugin receivers module receiver for device messages
"""

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.receivers.base import BaseReceiver
from fb_bus_connector_plugin.receivers.entities import BaseEntity, DeviceStateEntity
from fb_bus_connector_plugin.registry.model import DevicesRegistry


@inject(alias=BaseReceiver)
class DeviceItemReceiver(BaseReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for devices messages

    @package        FastyBird:FbBusConnectorPlugin!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __devices_registry: DevicesRegistry

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        devices_registry: DevicesRegistry,
        logger: Logger,
    ) -> None:
        super().__init__(logger=logger)

        self.__devices_registry = devices_registry

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:
        """Handle received message"""
        if not isinstance(entity, DeviceStateEntity):
            return

        device_record = self.__devices_registry.get_by_address(
            client_id=entity.client_id,
            address=entity.device_address,
        )

        if device_record is None:
            self._logger.error("Message is for unknown device %d", entity.device_address)

            return

        self.__devices_registry.set_state(device=device_record, state=entity.device_state)

        # Reset communication info
        self.__devices_registry.reset_communication(device=device_record)
