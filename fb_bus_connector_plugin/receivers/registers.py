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
FastyBird BUS connector plugin receivers module receiver for registers messages
"""

# Python base dependencies
from datetime import datetime
from typing import Union

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.receivers.base import BaseReceiver
from fb_bus_connector_plugin.receivers.entities import (
    BaseEntity,
    MultipleRegistersEntity,
    PubSubBroadcastEntity,
    PubSubWriteKeyEntity,
    ReadMultipleRegistersEntity,
    ReadSingleRegisterEntity,
    ReportSingleRegisterEntity,
    SingleRegisterEntity,
    WriteMultipleRegistersEntity,
    WriteSingleRegisterEntity,
)
from fb_bus_connector_plugin.registry.model import DevicesRegistry, RegistersRegistry
from fb_bus_connector_plugin.registry.records import RegisterRecord
from fb_bus_connector_plugin.types import (
    ButtonPayloadType,
    SwitchPayloadType,
    WriteKeyType,
)


@inject(alias=BaseReceiver)
class RegisterItemReceiver(BaseReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for registers messages

    @package        FastyBird:FbBusConnectorPlugin!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        logger: Logger,
    ) -> None:
        super().__init__(logger=logger)

        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:  # pylint: disable=too-many-branches
        """Handle received message"""
        if not isinstance(
            entity, (SingleRegisterEntity, MultipleRegistersEntity, PubSubWriteKeyEntity, PubSubBroadcastEntity)
        ):
            return

        device_record = self.__devices_registry.get_by_address(
            client_id=entity.client_id,
            address=entity.device_address,
        )

        if device_record is None:
            self._logger.error("Message is for unknown device %d", entity.device_address)

            return

        if isinstance(entity, SingleRegisterEntity):
            register_address, register_value = entity.register_value

            register_record = self.__registers_registry.get_by_address(
                device_id=device_record.id,
                register_type=entity.register_type,
                register_address=register_address,
            )

            if register_record is None:
                self._logger.error("Message is for unknown register %s:%d", entity.register_type, register_address)

                return

            self.__write_value_to_register(register_record=register_record, value=register_value)

        elif isinstance(entity, MultipleRegistersEntity):
            for register_address, register_value in entity.registers_values:
                register_record = self.__registers_registry.get_by_address(
                    device_id=device_record.id,
                    register_type=entity.registers_type,
                    register_address=register_address,
                )

                if register_record is None:
                    self._logger.error(
                        "Message is for unknown register %s:%d",
                        entity.registers_type,
                        register_address,
                    )

                    continue

                self.__write_value_to_register(register_record=register_record, value=register_value)

        elif isinstance(entity, PubSubWriteKeyEntity):
            register_record = self.__registers_registry.get_by_address(
                device_id=device_record.id,
                register_type=entity.register_type,
                register_address=entity.register_address,
            )

            if register_record is None:
                self._logger.error(
                    "Message is for unknown register %s:%d", entity.register_type, entity.register_address
                )

                return

            self.__registers_registry.set_pubsub_key_written(
                register=register_record,
                pubsub_key_written=WriteKeyType.YES,
            )

            self.__registers_registry.set_waiting_for_data(register=register_record, waiting_for_data=False)

        elif isinstance(entity, PubSubBroadcastEntity):
            register_record = self.__registers_registry.get_by_key(register_key=entity.register_key)

            if register_record is None:
                self._logger.error("Message is for unknown register %s", entity.register_key)

                return

            self.__write_value_to_register(register_record=register_record, value=entity.register_value)

        if isinstance(
            entity,
            (
                ReadSingleRegisterEntity,
                ReadMultipleRegistersEntity,
                WriteSingleRegisterEntity,
                WriteMultipleRegistersEntity,
                PubSubWriteKeyEntity,
            ),
        ):
            # Reset communication info
            self.__devices_registry.reset_communication(device=device_record)

        if isinstance(entity, (ReportSingleRegisterEntity, PubSubBroadcastEntity)):
            # Reset reading pointer
            self.__devices_registry.reset_reading_register(device=device_record)

    # -----------------------------------------------------------------------------

    def __write_value_to_register(
        self,
        register_record: RegisterRecord,
        value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None],
    ) -> None:
        if value is not None:
            self.__registers_registry.set_actual_value(
                register=register_record,
                value=value,
            )
