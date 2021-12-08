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
FastyBird BUS connector plugin receivers module receiver for pairing messages
"""

# Python base dependencies
import uuid

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.pairing.apiv1 import ApiV1Pairing
from fb_bus_connector_plugin.receivers.base import BaseReceiver
from fb_bus_connector_plugin.receivers.entities import (
    BaseEntity,
    DeviceSearchEntity,
    DeviceWriteAddressEntity,
    PairingFinishedEntity,
    RegisterStructureEntity,
)
from fb_bus_connector_plugin.registry.model import DevicesRegistry, RegistersRegistry
from fb_bus_connector_plugin.registry.records import (
    PairingAttributeRegisterRecord,
    PairingInputRegisterRecord,
    PairingOutputRegisterRecord,
    PairingSettingRegisterRecord,
)
from fb_bus_connector_plugin.types import PairingCommand, RegisterType


@inject(alias=BaseReceiver)
class PairingReceiver(BaseReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for pairing messages

    @package        FastyBird:FbBusConnectorPlugin!
    @module         receivers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    __device_pairing: ApiV1Pairing

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        device_pairing: ApiV1Pairing,
        logger: Logger,
    ) -> None:
        super().__init__(logger=logger)

        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

        self.__device_pairing = device_pairing

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:
        """Handle received message"""
        if isinstance(entity, DeviceSearchEntity):
            self.__receive_set_device_for_pairing(entity=entity)

            return

        if isinstance(entity, DeviceWriteAddressEntity):
            self.__receive_write_address(entity=entity)

            return

        if isinstance(entity, RegisterStructureEntity):
            self.__receive_register_structure(entity=entity)

            return

        if isinstance(entity, PairingFinishedEntity):
            self.__receive_pairing_finished(entity=entity)

            return

    # -----------------------------------------------------------------------------

    def __receive_set_device_for_pairing(self, entity: DeviceSearchEntity) -> None:
        # Try to find sender by serial number
        device_record = self.__devices_registry.get_by_serial_number(serial_number=entity.device_serial_number)

        device = self.__device_pairing.append_device(
            client_id=entity.client_id,
            device_id=device_record.id if device_record is not None else uuid.uuid4(),
            device_address=entity.device_address,
            device_max_packet_length=entity.device_max_packet_length,
            device_serial_number=entity.device_serial_number,
            device_hardware_version=entity.device_hardware_version,
            device_hardware_model=entity.device_hardware_model,
            device_hardware_manufacturer=entity.device_hardware_manufacturer,
            device_firmware_version=entity.device_firmware_version,
            device_firmware_manufacturer=entity.device_firmware_manufacturer,
            input_registers_size=entity.input_registers_size,
            output_registers_size=entity.output_registers_size,
            attributes_registers_size=entity.attributes_registers_size,
            settings_registers_size=entity.settings_registers_size,
            device_pub_sub_pub_support=entity.pub_sub_pub_support,
            device_pub_sub_sub_support=entity.pub_sub_sub_support,
            device_max_subscriptions=entity.pub_sub_max_subscriptions,
            device_max_subscription_conditions=entity.pub_sub_max_subscription_conditions,
            device_max_subscription_actions=entity.pub_sub_max_subscription_actions,
        )

        self._logger.debug(
            "Found device %s[%d] %s[%s]:%s",
            device.serial_number,
            device.address,
            device.hardware_version,
            device.hardware_model,
            device.firmware_version,
        )

    # -----------------------------------------------------------------------------

    def __receive_write_address(self, entity: DeviceWriteAddressEntity) -> None:
        if self.__device_pairing.pairing_device is None:
            return

        if self.__device_pairing.pairing_device.serial_number != entity.device_serial_number:
            self._logger.warning(
                "[%s] Device confirmed address assign, but with serial number mismatch",
                self.__device_pairing.pairing_device.serial_number,
            )

            return

        self._logger.debug(
            "[%s] Device confirmed address assign",
            self.__device_pairing.pairing_device.serial_number,
        )

        # Mark step as finished
        self.__device_pairing.append_pairing_cmd(command=PairingCommand.WRITE_ADDRESS)

    # -----------------------------------------------------------------------------

    def __receive_register_structure(self, entity: RegisterStructureEntity) -> None:
        if self.__device_pairing.pairing_device is None:
            return

        if entity.register_type in (RegisterType.INPUT, RegisterType.OUTPUT):
            register_record = next(
                iter(
                    [
                        item
                        for item in self.__device_pairing.pairing_device_registers
                        if item.type == entity.register_type and item.address == entity.register_address
                    ]
                ),
                None,
            )

            if register_record is None:
                self._logger.warning(
                    "[%s] Register: %d[%s] could not be found in registry",
                    self.__device_pairing.pairing_device.serial_number,
                    entity.register_address,
                    entity.register_data_type,
                )

                return

            if entity.register_type == RegisterType.INPUT:
                # Update register record
                self.__device_pairing.append_input_register(
                    register_id=register_record.id,
                    register_address=register_record.address,
                    register_key=register_record.key,
                    # Configure register data type
                    register_data_type=entity.register_data_type,
                )

            elif entity.register_type == RegisterType.OUTPUT:
                # Update register record
                self.__device_pairing.append_output_register(
                    register_id=register_record.id,
                    register_address=register_record.address,
                    register_key=register_record.key,
                    # Configure register data type
                    register_data_type=entity.register_data_type,
                )

            self._logger.debug(
                "[%s] Configured register: %d[%d]",
                self.__device_pairing.pairing_device.serial_number,
                register_record.address,
                register_record.type.value,
            )

        elif entity.register_type == RegisterType.ATTRIBUTE:
            attribute_record = next(
                iter(
                    [
                        item
                        for item in self.__device_pairing.pairing_device_registers
                        if item.type == entity.register_type and item.address == entity.register_address
                    ]
                ),
                None,
            )

            # Check if register is created
            if attribute_record is None:
                self._logger.warning(
                    "[%s] Device attribute: %d could not be found in registry",
                    self.__device_pairing.pairing_device.serial_number,
                    entity.register_address,
                )

                return

            self.__device_pairing.append_attribute(
                attribute_id=attribute_record.id,
                attribute_address=attribute_record.address,
                attribute_key=attribute_record.key,
                attribute_data_type=entity.register_data_type,
                attribute_name=entity.register_name,
                attribute_settable=entity.register_settable,
                attribute_queryable=entity.register_queryable,
            )

            self._logger.debug(
                "[{%s] Configured device attribute: %d",
                self.__device_pairing.pairing_device.serial_number,
                attribute_record.address,
            )

        elif entity.register_type == RegisterType.SETTING:
            setting_record = next(
                iter(
                    [
                        item
                        for item in self.__device_pairing.pairing_device_registers
                        if item.type == entity.register_type and item.address == entity.register_address
                    ]
                ),
                None,
            )

            # Check if setting is created
            if setting_record is None:
                self._logger.warning(
                    "[%s] Device setting: %d could not be found in registry",
                    self.__device_pairing.pairing_device.serial_number,
                    entity.register_address,
                )

                return

            self.__device_pairing.append_setting(
                setting_id=setting_record.id,
                setting_address=setting_record.address,
                setting_data_type=entity.register_data_type,
                setting_name=entity.register_name,
            )

            self._logger.debug(
                "[{%s] Configured device setting: %d",
                self.__device_pairing.pairing_device.serial_number,
                setting_record.address,
            )

        # Check if device has other register to initialize
        if not self.__device_pairing.move_to_next_register_for_init():
            # Mark step as finished
            self.__device_pairing.append_pairing_cmd(command=PairingCommand.PROVIDE_REGISTER_STRUCTURE)

    # -----------------------------------------------------------------------------

    def __receive_pairing_finished(self, entity: PairingFinishedEntity) -> None:
        if self.__device_pairing.pairing_device is None:
            return

        # Create new or update existing device record in registry
        device_record = self.__devices_registry.create(
            client_id=entity.client_id,
            device_id=self.__device_pairing.pairing_device.id,
            device_address=self.__device_pairing.pairing_device.address,
            device_serial_number=self.__device_pairing.pairing_device.serial_number,
            device_max_packet_length=self.__device_pairing.pairing_device.max_packet_length,
            device_enabled=False,
            device_pub_sub_pub_support=self.__device_pairing.pairing_device.pub_sub_pub_support,
            device_pub_sub_sub_support=self.__device_pairing.pairing_device.pub_sub_sub_support,
            device_pub_sub_sub_max_subscriptions=self.__device_pairing.pairing_device.pub_sub_max_subscriptions,
            device_pub_sub_sub_max_conditions=self.__device_pairing.pairing_device.pub_sub_max_subscription_conditions,
            device_pub_sub_sub_max_actions=self.__device_pairing.pairing_device.pub_sub_max_subscription_actions,
            hardware_manufacturer=self.__device_pairing.pairing_device.hardware_manufacturer,
            hardware_model=self.__device_pairing.pairing_device.hardware_model,
            hardware_version=self.__device_pairing.pairing_device.hardware_version,
            firmware_manufacturer=self.__device_pairing.pairing_device.firmware_manufacturer,
            firmware_version=self.__device_pairing.pairing_device.firmware_version,
        )

        # Set received state
        self.__devices_registry.set_state(device=device_record, state=entity.device_state)

        for register in self.__device_pairing.pairing_device_registers:
            if isinstance(register, (PairingInputRegisterRecord, PairingOutputRegisterRecord)):
                self.__registers_registry.create(
                    device_id=device_record.id,
                    register_id=register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_data_type=register.data_type,
                    register_key=register.key,
                )

            elif isinstance(register, PairingAttributeRegisterRecord):
                self.__registers_registry.create(
                    device_id=device_record.id,
                    register_id=register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_data_type=register.data_type,
                    register_name=register.name,
                    register_queryable=register.queryable,
                    register_settable=register.settable,
                    register_key=register.key,
                )

            elif isinstance(register, PairingSettingRegisterRecord):
                self.__registers_registry.create(
                    device_id=device_record.id,
                    register_id=register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_name=register.name,
                    register_data_type=register.data_type,
                    register_key=register.key,
                )

        # Disable pairing
        self.__device_pairing.discover_device()
