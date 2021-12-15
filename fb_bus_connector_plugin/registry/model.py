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
FastyBird BUS connector plugin registry module models
"""

# Python base dependencies
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.consumers.consumer import Consumer
from fb_bus_connector_plugin.exceptions import (
    InvalidArgumentException,
    InvalidStateException,
)
from fb_bus_connector_plugin.registry.records import (
    AttributeRegisterRecord,
    DeviceRecord,
    InputRegisterRecord,
    OutputRegisterRecord,
    RegisterRecord,
    SettingRegisterRecord,
)
from fb_bus_connector_plugin.types import (
    ButtonPayloadType,
    ConnectionState,
    DeviceDataType,
    Packet,
    RegisterType,
    SwitchPayloadType,
    WriteKeyType,
)


@inject
class DevicesRegistry:
    """
    Devices registry

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __items: Dict[str, DeviceRecord] = {}

    __iterator_index = 0

    __MAX_ADDRESS: int = 253

    __consumer: Consumer

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        consumer: Consumer,
    ) -> None:
        self.__consumer = consumer

    # -----------------------------------------------------------------------------

    def get_by_id(self, device_id: uuid.UUID) -> Optional[DeviceRecord]:
        """Find device in registry by given unique identifier"""
        items = self.__items.copy()

        return next(
            iter([record for record in items.values() if device_id.__eq__(record.id)]),
            None,
        )

    # -----------------------------------------------------------------------------

    def get_by_address(self, client_id: uuid.UUID, address: int) -> Optional[DeviceRecord]:
        """Find device in registry by given unique address"""
        items = self.__items.copy()

        return next(
            iter(
                [
                    record
                    for record in items.values()
                    if record.address == address and client_id.__eq__(record.client_id)
                ]
            ),
            None,
        )

    # -----------------------------------------------------------------------------

    def get_by_serial_number(self, serial_number: str) -> Optional[DeviceRecord]:
        """Find device in registry by given unique serial number"""
        items = self.__items.copy()

        return next(iter([record for record in items.values() if record.serial_number == serial_number]), None)

    # -----------------------------------------------------------------------------

    def get_all_for_connector(self, client_id: uuid.UUID) -> List[DeviceRecord]:
        """Get all devices by connector"""
        items = self.__items.copy()

        return [record for record in items.values() if client_id.__eq__(record.client_id)]

    # -----------------------------------------------------------------------------

    def initialize(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        client_id: uuid.UUID,
        device_id: uuid.UUID,
        device_address: int,
        device_serial_number: str,
        device_max_packet_length: int,
        device_enabled: bool,
        device_ready: bool = False,
        device_pub_sub_pub_support: bool = False,
        device_pub_sub_sub_support: bool = False,
        device_pub_sub_sub_max_subscriptions: int = 0,
        device_pub_sub_sub_max_conditions: int = 0,
        device_pub_sub_sub_max_actions: int = 0,
        hardware_manufacturer: Optional[str] = None,
        hardware_model: Optional[str] = None,
        hardware_version: Optional[str] = None,
        firmware_manufacturer: Optional[str] = None,
        firmware_version: Optional[str] = None,
    ) -> DeviceRecord:
        """Append new device or update existing device in registry"""
        device: DeviceRecord = DeviceRecord(
            client_id=client_id,
            device_id=device_id,
            address=device_address,
            serial_number=device_serial_number,
            max_packet_length=device_max_packet_length,
            enabled=device_enabled,
            ready=device_ready,
            pub_sub_pub_support=device_pub_sub_pub_support,
            pub_sub_sub_support=device_pub_sub_sub_support,
            pub_sub_sub_max_subscriptions=device_pub_sub_sub_max_subscriptions,
            pub_sub_sub_max_conditions=device_pub_sub_sub_max_conditions,
            pub_sub_sub_max_actions=device_pub_sub_sub_max_actions,
            hardware_manufacturer=hardware_manufacturer,
            hardware_model=hardware_model,
            hardware_version=hardware_version,
            firmware_manufacturer=firmware_manufacturer,
            firmware_version=firmware_version,
        )

        self.__items[device.id.__str__()] = device

        return device

    # -----------------------------------------------------------------------------

    def create(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        client_id: uuid.UUID,
        device_id: uuid.UUID,
        device_address: int,
        device_serial_number: str,
        device_max_packet_length: int,
        device_enabled: bool,
        device_ready: bool = False,
        device_pub_sub_pub_support: bool = False,
        device_pub_sub_sub_support: bool = False,
        device_pub_sub_sub_max_subscriptions: int = 0,
        device_pub_sub_sub_max_conditions: int = 0,
        device_pub_sub_sub_max_actions: int = 0,
        hardware_manufacturer: Optional[str] = None,
        hardware_model: Optional[str] = None,
        hardware_version: Optional[str] = None,
        firmware_manufacturer: Optional[str] = None,
        firmware_version: Optional[str] = None,
    ) -> DeviceRecord:
        """Create new attribute record"""
        device_record = self.initialize(
            client_id=client_id,
            device_id=device_id,
            device_address=device_address,
            device_serial_number=device_serial_number,
            device_max_packet_length=device_max_packet_length,
            device_enabled=device_enabled,
            device_ready=device_ready,
            device_pub_sub_pub_support=device_pub_sub_pub_support,
            device_pub_sub_sub_support=device_pub_sub_sub_support,
            device_pub_sub_sub_max_subscriptions=device_pub_sub_sub_max_subscriptions,
            device_pub_sub_sub_max_conditions=device_pub_sub_sub_max_conditions,
            device_pub_sub_sub_max_actions=device_pub_sub_sub_max_actions,
            hardware_manufacturer=hardware_manufacturer,
            hardware_model=hardware_model,
            hardware_version=hardware_version,
            firmware_manufacturer=firmware_manufacturer,
            firmware_version=firmware_version,
        )

        self.__consumer.propagate_device_record(device_record=device_record)

        return device_record

    # -----------------------------------------------------------------------------

    def remove(self, device_id: uuid.UUID) -> None:
        """Remove device from registry"""
        items = self.__items.copy()

        for record in items.values():
            if device_id.__eq__(record.id):
                try:
                    del self.__items[record.id.__str__()]

                except KeyError:
                    pass

                break

    # -----------------------------------------------------------------------------

    def reset(self, client_id: Optional[uuid.UUID] = None) -> None:
        """Reset devices registry to initial state"""
        items = self.__items.copy()

        if client_id is not None:
            for record in items.values():
                if client_id.__eq__(record.client_id):
                    self.remove(device_id=record.id)

        else:
            self.__items = {}

    # -----------------------------------------------------------------------------

    def set_ready(self, device: DeviceRecord, ready: bool = True) -> DeviceRecord:
        """Set device ready for communication state"""
        device.ready = ready

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def enable(self, device: DeviceRecord) -> DeviceRecord:
        """Enable device for communication"""
        device.enabled = True

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        self.__consumer.propagate_device_record_state(device_record=updated_device)

        return updated_device

    # -----------------------------------------------------------------------------

    def disable(self, device: DeviceRecord) -> DeviceRecord:
        """Enable device for communication"""
        device.enabled = False

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        self.__consumer.propagate_device_record_state(device_record=updated_device)

        return updated_device

    # -----------------------------------------------------------------------------

    def set_state(self, device: DeviceRecord, state: ConnectionState) -> DeviceRecord:
        """Set device actual state"""
        device.state = state

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        self.__consumer.propagate_device_record_state(device_record=updated_device)

        return updated_device

    # -----------------------------------------------------------------------------

    def set_device_is_lost(self, device: DeviceRecord) -> DeviceRecord:
        """Mark device as lost"""
        return self.set_state(device=device, state=ConnectionState.UNKNOWN)

    # -----------------------------------------------------------------------------

    def reset_communication(self, device: DeviceRecord) -> DeviceRecord:
        """Reset device communication registers"""
        device.reset_communication()

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def set_waiting_for_packet(self, device: DeviceRecord, packet_type: Optional[Packet]) -> DeviceRecord:
        """Mark that gateway is waiting for reply from device"""
        device.waiting_for_packet = packet_type

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def set_reading_register(
        self,
        device: DeviceRecord,
        register_address: int,
        register_type: RegisterType,
    ) -> DeviceRecord:
        """Set device register reading pointer"""
        device.set_reading_register(register_address=register_address, register_type=register_type)

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def reset_reading_register(self, device: DeviceRecord, reset_timestamp: bool = False) -> DeviceRecord:
        """Reset device register reading pointer"""
        device.reset_reading_register(reset_timestamp=reset_timestamp)

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def find_free_address(self, client_id: uuid.UUID) -> Optional[int]:
        """Fin first free address slot in registry"""
        reserved_addresses: List[int] = []

        for record in self.get_all_for_connector(client_id=client_id):
            reserved_addresses.append(record.address)

        free_address: Optional[int] = None

        for i in range(1, self.__MAX_ADDRESS):
            if i not in reserved_addresses:
                free_address = i

                break

        return free_address

    # -----------------------------------------------------------------------------

    def __update(self, updated_device: DeviceRecord) -> bool:
        """Update device record"""
        self.__items[updated_device.id.__str__()] = updated_device

        return True

    # -----------------------------------------------------------------------------

    def __iter__(self) -> "DevicesRegistry":
        # Reset index for nex iteration
        self.__iterator_index = 0

        return self

    # -----------------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.__items.values())

    # -----------------------------------------------------------------------------

    def __next__(self) -> DeviceRecord:
        if self.__iterator_index < len(self.__items.values()):
            items: List[DeviceRecord] = list(self.__items.values())

            result: DeviceRecord = items[self.__iterator_index]

            self.__iterator_index += 1

            return result

        # Reset index for nex iteration
        self.__iterator_index = 0

        # End of iteration
        raise StopIteration


@inject
class RegistersRegistry:
    """
    Registers registry

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __items: Dict[str, RegisterRecord] = {}

    __consumer: Consumer

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        consumer: Consumer,
    ) -> None:
        self.__consumer = consumer

    # -----------------------------------------------------------------------------

    def get_all_for_device(
        self,
        device_id: uuid.UUID,
        register_type: Optional[RegisterType] = None,
    ) -> List[RegisterRecord]:
        """Get all registers for device by type"""
        items = self.__items.copy()

        return [
            record
            for record in items.values()
            if device_id.__eq__(record.device_id) and (register_type is None or record.type == register_type)
        ]

    # -----------------------------------------------------------------------------

    def get_by_id(self, register_id: uuid.UUID) -> Optional[RegisterRecord]:
        """Get register by identifier"""
        items = self.__items.copy()

        return next(iter([record for record in items.values() if register_id.__eq__(record.id)]), None)

    # -----------------------------------------------------------------------------

    def get_by_address(
        self,
        device_id: uuid.UUID,
        register_type: RegisterType,
        register_address: int,
    ) -> Optional[RegisterRecord]:
        """Get register by its address"""
        items = self.__items.copy()

        return next(
            iter(
                [
                    record
                    for record in items.values()
                    if device_id.__eq__(record.device_id)
                    and record.address == register_address
                    and record.type == register_type
                ]
            ),
            None,
        )

    # -----------------------------------------------------------------------------

    def get_by_key(self, register_key: str) -> Optional[RegisterRecord]:
        """Get register by its unique key"""
        items = self.__items.copy()

        return next(iter([record for record in items.values() if record.key == register_key]), None)

    # -----------------------------------------------------------------------------

    def initialize_input_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DeviceDataType,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> InputRegisterRecord:
        """Append new register or replace existing register in registry"""
        register = InputRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_ready=register_ready,
            register_pubsub_key_written=register_pubsub_key_written,
        )

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def initialize_output_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DeviceDataType,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> OutputRegisterRecord:
        """Append new register or replace existing register in registry"""
        register = OutputRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_ready=register_ready,
            register_pubsub_key_written=register_pubsub_key_written,
        )

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def initialize_attribute_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DeviceDataType,
        register_ready: bool = False,
        register_name: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> AttributeRegisterRecord:
        """Append new attribute register or replace existing register in registry"""
        register = AttributeRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_ready=register_ready,
            register_name=register_name,
            register_settable=register_settable,
            register_queryable=register_queryable,
            register_pubsub_key_written=register_pubsub_key_written,
        )

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def initialize_setting_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DeviceDataType,
        register_ready: bool = False,
        register_name: Optional[str] = None,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> SettingRegisterRecord:
        """Append new setting register or replace existing register in registry"""
        register = SettingRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_ready=register_ready,
            register_name=register_name,
            register_pubsub_key_written=register_pubsub_key_written,
        )

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def create(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_type: RegisterType,
        register_data_type: DeviceDataType,
        register_ready: bool = False,
        register_name: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> RegisterRecord:
        """Create new register record"""
        if register_type == RegisterType.INPUT:
            input_register = self.initialize_input_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=register_data_type,
                register_ready=register_ready,
                register_pubsub_key_written=register_pubsub_key_written,
            )

            self.__consumer.propagate_register_record(register_record=input_register)

            return input_register

        if register_type == RegisterType.OUTPUT:
            output_register = self.initialize_output_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=register_data_type,
                register_ready=register_ready,
                register_pubsub_key_written=register_pubsub_key_written,
            )

            self.__consumer.propagate_register_record(register_record=output_register)

            return output_register

        if register_type == RegisterType.ATTRIBUTE:
            attribute_register = self.initialize_attribute_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=register_data_type,
                register_ready=register_ready,
                register_name=register_name,
                register_settable=register_settable,
                register_queryable=register_queryable,
                register_pubsub_key_written=register_pubsub_key_written,
            )

            self.__consumer.propagate_register_record(register_record=attribute_register)

            return attribute_register

        if register_type == RegisterType.SETTING:
            setting_register = self.initialize_setting_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=register_data_type,
                register_ready=register_ready,
                register_name=register_name,
                register_pubsub_key_written=register_pubsub_key_written,
            )

            self.__consumer.propagate_register_record(register_record=setting_register)

            return setting_register

        raise InvalidArgumentException("Provided register type is not supported")

    # -----------------------------------------------------------------------------

    def remove(self, register_id: uuid.UUID) -> None:
        """Remove register from registry"""
        items = self.__items.copy()

        for record in items.values():
            if register_id.__eq__(record.id):
                try:
                    del self.__items[record.id.__str__()]

                except KeyError:
                    pass

                break

    # -----------------------------------------------------------------------------

    def reset(self, device_id: Optional[uuid.UUID] = None, registers_type: Optional[RegisterType] = None) -> None:
        """Reset registers registry"""
        items = self.__items.copy()

        if device_id is not None or registers_type is not None:
            for record in items.values():
                if (device_id is None or device_id.__eq__(record.device_id)) and (
                    registers_type is None or record.type == registers_type
                ):
                    self.remove(register_id=record.id)

        else:
            self.__items = {}

    # -----------------------------------------------------------------------------

    def set_ready(self, register: RegisterRecord, ready: bool = True) -> RegisterRecord:
        """Set register ready for communication state"""
        register.ready = ready

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        return updated_register

    # -----------------------------------------------------------------------------

    def set_pubsub_key_written(
        self,
        register: RegisterRecord,
        pubsub_key_written: WriteKeyType = WriteKeyType.YES,
    ) -> RegisterRecord:
        """Set register ready for communication state"""
        register.pubsub_key_written = pubsub_key_written

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        return updated_register

    # -----------------------------------------------------------------------------

    def set_actual_value(
        self,
        register: RegisterRecord,
        value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime],
    ) -> RegisterRecord:
        """Set actual value to register"""
        register.actual_value = value

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        self.__consumer.propagate_register_record_value(register_record=updated_register)

        return updated_register

    # -----------------------------------------------------------------------------

    def set_expected_value(
        self,
        register: RegisterRecord,
        value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None],
    ) -> RegisterRecord:
        """Set expected value to register"""
        register.expected_value = value

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        return updated_register

    # -----------------------------------------------------------------------------

    def set_expected_pending(self, register: RegisterRecord, timestamp: float) -> RegisterRecord:
        """Set expected value transmit timestamp"""
        register.expected_pending = timestamp

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        return updated_register

    # -----------------------------------------------------------------------------

    def set_waiting_for_data(self, register: RegisterRecord, waiting_for_data: bool) -> RegisterRecord:
        """Set register is waiting for any data"""
        register.waiting_for_data = waiting_for_data

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        return updated_register

    # -----------------------------------------------------------------------------

    def __update(self, register: RegisterRecord) -> bool:
        items = self.__items.copy()

        for record in items.values():
            if record.id == register.id:
                self.__items[register.id.__str__()] = register

                return True

        return False
