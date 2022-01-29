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
FastyBird BUS connector receivers module receiver for device messages
"""

# Library dependencies
import logging
from datetime import datetime
from typing import Union

from fastybird_metadata.devices_module import ConnectionState
from fastybird_metadata.types import ButtonPayload, SwitchPayload
from kink import inject

# Library libs
from fastybird_fb_bus_connector.logger import Logger
from fastybird_fb_bus_connector.pairing.apiv1 import ApiV1Pairing
from fastybird_fb_bus_connector.receivers.entities import (
    BaseEntity,
    DeviceDiscoveryEntity,
    MultipleRegistersEntity,
    PongEntity,
    ReadMultipleRegistersEntity,
    ReadSingleRegisterEntity,
    RegisterStructureEntity,
    ReportSingleRegisterEntity,
    SingleRegisterEntity,
    WriteMultipleRegistersEntity,
    WriteSingleRegisterEntity,
)
from fastybird_fb_bus_connector.receivers.receiver import IReceiver
from fastybird_fb_bus_connector.registry.model import DevicesRegistry, RegistersRegistry
from fastybird_fb_bus_connector.registry.records import RegisterRecord
from fastybird_fb_bus_connector.types import RegisterType


@inject(alias=IReceiver)
class DeviceItemReceiver(IReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for devices messages

    @package        FastyBird:FbBusConnector!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __devices_registry: DevicesRegistry

    __logger: Union[Logger, logging.Logger]

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        devices_registry: DevicesRegistry,
        logger: Union[Logger, logging.Logger] = logging.getLogger("dummy"),
    ) -> None:
        self.__devices_registry = devices_registry

        self.__logger = logger

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:
        """Handle received message"""
        if not isinstance(entity, PongEntity):
            return

        device_record = self.__devices_registry.get_by_address(address=entity.device_address)

        if device_record is None:
            self.__logger.error(
                "Message is for unknown device: %d",
                entity.device_address,
                extra={
                    "device": {
                        "address": entity.device_address,
                    },
                },
            )

            return

        self.__devices_registry.set_state(device=device_record, state=ConnectionState.UNKNOWN)

        # Reset communication info
        self.__devices_registry.reset_communication(device=device_record)


@inject(alias=IReceiver)
class RegisterItemReceiver(IReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for registers messages

    @package        FastyBird:FbBusConnector!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    __logger: Union[Logger, logging.Logger]

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        logger: Union[Logger, logging.Logger] = logging.getLogger("dummy"),
    ) -> None:
        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

        self.__logger = logger

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:  # pylint: disable=too-many-branches
        """Handle received message"""
        if not isinstance(entity, (SingleRegisterEntity, MultipleRegistersEntity)):
            return

        device_record = self.__devices_registry.get_by_address(address=entity.device_address)

        if device_record is None:
            self.__logger.error(
                "Message is for unknown device %d",
                entity.device_address,
                extra={
                    "device": {
                        "address": entity.device_address,
                    },
                },
            )

            return

        if isinstance(entity, SingleRegisterEntity):
            register_address, register_value = entity.register_value

            register_record = self.__registers_registry.get_by_address(
                device_id=device_record.id,
                register_type=entity.register_type,
                register_address=register_address,
            )

            if register_record is None:
                self.__logger.error(
                    "Message is for unknown register %s:%d",
                    entity.register_type,
                    register_address,
                    extra={
                        "device": {
                            "id": device_record.id.__str__(),
                        },
                    },
                )

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
                    self.__logger.error(
                        "Message is for unknown register %s:%d",
                        entity.registers_type,
                        register_address,
                        extra={
                            "device": {
                                "id": device_record.id.__str__(),
                            },
                        },
                    )

                    continue

                self.__write_value_to_register(register_record=register_record, value=register_value)

        if isinstance(
            entity,
            (
                ReadSingleRegisterEntity,
                ReadMultipleRegistersEntity,
                WriteSingleRegisterEntity,
                WriteMultipleRegistersEntity,
            ),
        ):
            # Reset communication info
            self.__devices_registry.reset_communication(device=device_record)

        if isinstance(entity, ReportSingleRegisterEntity):
            # Reset reading pointer
            self.__devices_registry.reset_reading_register(device=device_record)

    # -----------------------------------------------------------------------------

    def __write_value_to_register(
        self,
        register_record: RegisterRecord,
        value: Union[str, int, float, bool, datetime, ButtonPayload, SwitchPayload, None],
    ) -> None:
        if value is not None:
            self.__registers_registry.set_actual_value(
                register=register_record,
                value=value,
            )


@inject(alias=IReceiver)
class DiscoverReceiver(IReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for devices discovery messages

    @package        FastyBird:FbBusConnector!
    @module         receivers/pairing

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __device_pairing: ApiV1Pairing

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_pairing: ApiV1Pairing,
    ) -> None:
        self.__device_pairing = device_pairing

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:
        """Handle received message"""
        if isinstance(entity, DeviceDiscoveryEntity):
            self.__receive_set_device_discovery(entity=entity)

            return

        if isinstance(entity, RegisterStructureEntity):
            self.__receive_register_structure(entity=entity)

            return

    # -----------------------------------------------------------------------------

    def __receive_set_device_discovery(self, entity: DeviceDiscoveryEntity) -> None:
        self.__device_pairing.append_device(
            # Device description
            device_address=entity.device_address,
            device_max_packet_length=entity.device_max_packet_length,
            device_serial_number=entity.device_serial_number,
            device_state=entity.device_state,
            device_hardware_version=entity.device_hardware_version,
            device_hardware_model=entity.device_hardware_model,
            device_hardware_manufacturer=entity.device_hardware_manufacturer,
            device_firmware_version=entity.device_firmware_version,
            device_firmware_manufacturer=entity.device_firmware_manufacturer,
            # Registers sizes info
            input_registers_size=entity.input_registers_size,
            output_registers_size=entity.output_registers_size,
            attributes_registers_size=entity.attributes_registers_size,
        )

    # -----------------------------------------------------------------------------

    def __receive_register_structure(self, entity: RegisterStructureEntity) -> None:
        if entity.register_type in (RegisterType.INPUT, RegisterType.OUTPUT, RegisterType.ATTRIBUTE):
            if entity.register_type == RegisterType.INPUT:
                # Update register record
                self.__device_pairing.append_input_register(
                    register_address=entity.register_address,
                    # Configure register data type
                    register_data_type=entity.register_data_type,
                )

            elif entity.register_type == RegisterType.OUTPUT:
                # Update register record
                self.__device_pairing.append_output_register(
                    register_address=entity.register_address,
                    # Configure register data type
                    register_data_type=entity.register_data_type,
                )

            elif entity.register_type == RegisterType.ATTRIBUTE:
                # Update register record
                self.__device_pairing.append_attribute_register(
                    register_address=entity.register_address,
                    # Configure register details
                    register_data_type=entity.register_data_type,
                    register_name=entity.register_name,
                    register_settable=entity.register_settable,
                    register_queryable=entity.register_queryable,
                )
