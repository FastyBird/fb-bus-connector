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
FastyBird BUS connector registry module models
"""

# Python base dependencies
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

# Library dependencies
from fastybird_devices_module.repositories.state import (
    IChannelPropertyStateRepository,
    IDevicePropertyStateRepository,
)
from fastybird_metadata.devices_module import ConnectionState
from fastybird_metadata.types import ButtonPayload, DataType, SwitchPayload
from kink import inject
from whistle import EventDispatcher

# Library libs
from fastybird_fb_bus_connector.events.events import (
    AttributeRegisterRecordCreatedOrUpdatedEvent,
    DeviceRecordCreatedOrUpdatedEvent,
    InputOutputRegisterRecordCreatedOrUpdatedEvent,
    RegisterActualValueEvent,
)
from fastybird_fb_bus_connector.exceptions import InvalidStateException
from fastybird_fb_bus_connector.registry.records import (
    AttributeRegisterRecord,
    DeviceRecord,
    InputRegisterRecord,
    OutputRegisterRecord,
    RegisterRecord,
)
from fastybird_fb_bus_connector.types import DeviceAttribute, Packet, RegisterType


class DevicesRegistry:  # pylint: disable=too-many-public-methods
    """
    Devices registry

    @package        FastyBird:FbBusConnector!
    @module         registry/model

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __items: Dict[str, DeviceRecord] = {}

    __iterator_index = 0

    __registers_registry: "RegistersRegistry"

    __event_dispatcher: EventDispatcher

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        registers_registry: "RegistersRegistry",
        event_dispatcher: EventDispatcher,
    ) -> None:
        self.__items = {}

        self.__registers_registry = registers_registry

        self.__event_dispatcher = event_dispatcher

    # -----------------------------------------------------------------------------

    def get_by_id(self, device_id: uuid.UUID) -> Optional[DeviceRecord]:
        """Find device in registry by given unique identifier"""
        items = self.__items.copy()

        return next(
            iter([record for record in items.values() if device_id.__eq__(record.id)]),
            None,
        )

    # -----------------------------------------------------------------------------

    def get_by_address(self, address: int) -> Optional[DeviceRecord]:
        """Find device in registry by given unique address"""
        addresses_attributes = self.__registers_registry.get_all_by_name(name=DeviceAttribute.ADDRESS.value)

        for address_attribute in addresses_attributes:
            if address_attribute.actual_value == address:
                return self.get_by_id(device_id=address_attribute.device_id)

        return None

    # -----------------------------------------------------------------------------

    def get_by_serial_number(self, serial_number: str) -> Optional[DeviceRecord]:
        """Find device in registry by given unique serial number"""
        items = self.__items.copy()

        return next(iter([record for record in items.values() if record.serial_number == serial_number]), None)

    # -----------------------------------------------------------------------------

    def append(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        device_id: uuid.UUID,
        device_serial_number: str,
        device_enabled: bool,
        hardware_manufacturer: Optional[str] = None,
        hardware_model: Optional[str] = None,
        hardware_version: Optional[str] = None,
        firmware_manufacturer: Optional[str] = None,
        firmware_version: Optional[str] = None,
    ) -> DeviceRecord:
        """Append new device or update existing device in registry"""
        device: DeviceRecord = DeviceRecord(
            device_id=device_id,
            serial_number=device_serial_number,
            enabled=device_enabled,
            hardware_manufacturer=hardware_manufacturer,
            hardware_model=hardware_model,
            hardware_version=hardware_version,
            firmware_manufacturer=firmware_manufacturer,
            firmware_version=firmware_version,
        )

        self.__items[device.id.__str__()] = device

        return device

    # -----------------------------------------------------------------------------

    def create_or_update(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        device_id: uuid.UUID,
        device_serial_number: str,
        device_enabled: bool,
        hardware_manufacturer: Optional[str] = None,
        hardware_model: Optional[str] = None,
        hardware_version: Optional[str] = None,
        firmware_manufacturer: Optional[str] = None,
        firmware_version: Optional[str] = None,
    ) -> DeviceRecord:
        """Create new attribute record"""
        device_record = self.append(
            device_id=device_id,
            device_serial_number=device_serial_number,
            device_enabled=device_enabled,
            hardware_manufacturer=hardware_manufacturer,
            hardware_model=hardware_model,
            hardware_version=hardware_version,
            firmware_manufacturer=firmware_manufacturer,
            firmware_version=firmware_version,
        )

        self.__event_dispatcher.dispatch(
            event_id=DeviceRecordCreatedOrUpdatedEvent.EVENT_NAME,
            event=DeviceRecordCreatedOrUpdatedEvent(record=device_record),
        )

        return device_record

    # -----------------------------------------------------------------------------

    def remove(self, device_id: uuid.UUID) -> None:
        """Remove device from registry"""
        items = self.__items.copy()

        for record in items.values():
            if device_id.__eq__(record.id):
                try:
                    del self.__items[record.id.__str__()]

                    self.__registers_registry.reset(device_id=record.id)

                except KeyError:
                    pass

                break

    # -----------------------------------------------------------------------------

    def reset(self) -> None:
        """Reset devices registry to initial state"""
        self.__items = {}

        self.__registers_registry.reset()

    # -----------------------------------------------------------------------------

    def enable(self, device: DeviceRecord) -> DeviceRecord:
        """Enable device for communication"""
        device.enabled = True

        self.__update(updated_device=device, dispatch=True)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def disable(self, device: DeviceRecord) -> DeviceRecord:
        """Enable device for communication"""
        device.enabled = False

        self.__update(updated_device=device, dispatch=True)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def set_state(self, device: DeviceRecord, state: ConnectionState) -> DeviceRecord:
        """Set device actual state"""
        actual_state = self.__registers_registry.get_by_name(
            device_id=device.id,
            name=DeviceAttribute.STATE.value,
        )

        if actual_state is None:
            raise InvalidStateException(
                "Device state could not be updated. Attribute register was not found in registry",
            )

        if state == ConnectionState.RUNNING:
            device.reset_reading_register(True)
            # Reset lost timestamp
            device.lost_timestamp = 0

        if state == ConnectionState.LOST:
            if actual_state is None or actual_state.actual_value != state.value:
                # Set lost timestamp
                device.lost_timestamp = time.time()

            # Reset device communication state
            device.reset_communication()

        if state == ConnectionState.UNKNOWN:
            device.reset_reading_register(True)
            # Reset lost timestamp
            device.lost_timestamp = 0
            # Reset device communication state
            device.reset_communication()

        self.__registers_registry.set_actual_value(register=actual_state, value=state.value)

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def get_state(self, device: DeviceRecord) -> ConnectionState:
        """Get device actual state"""
        actual_state = self.__registers_registry.get_by_name(
            device_id=device.id,
            name=DeviceAttribute.STATE.value,
        )

        if (
            actual_state is None
            or actual_state.actual_value is None
            or not isinstance(actual_state.actual_value, str)
            or not ConnectionState.has_value(actual_state.actual_value)
        ):
            return ConnectionState.UNKNOWN

        return ConnectionState(actual_state.actual_value)

    # -----------------------------------------------------------------------------

    def set_device_is_lost(self, device: DeviceRecord) -> DeviceRecord:
        """Mark device as lost"""
        return self.set_state(device=device, state=ConnectionState.LOST)

    # -----------------------------------------------------------------------------

    def is_device_running(self, device: DeviceRecord) -> bool:
        """Is device in running state?"""
        return self.get_state(device=device) == ConnectionState.RUNNING

    # -----------------------------------------------------------------------------

    @staticmethod
    def is_device_lost(device: DeviceRecord) -> bool:
        """Is device in lost state?"""
        return device.lost_timestamp != 0

    # -----------------------------------------------------------------------------

    def is_device_unknown(self, device: DeviceRecord) -> bool:
        """Is device in unknown state?"""
        return self.get_state(device=device) == ConnectionState.UNKNOWN

    # -----------------------------------------------------------------------------

    def get_address(self, device: DeviceRecord) -> Optional[int]:
        """Get device actual state"""
        actual_address = self.__registers_registry.get_by_name(
            device_id=device.id,
            name=DeviceAttribute.ADDRESS.value,
        )

        if actual_address is None or not isinstance(actual_address.actual_value, int):
            return None

        return actual_address.actual_value

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

    def set_last_packet_timestamp(self, device: DeviceRecord, last_packet_timestamp: float) -> DeviceRecord:
        """Reset device last packet sent timestamp"""
        device.last_packet_timestamp = last_packet_timestamp

        self.__update(updated_device=device)

        updated_device = self.get_by_id(device.id)

        if updated_device is None:
            raise InvalidStateException("Device record could not be re-fetched from registry after update")

        return updated_device

    # -----------------------------------------------------------------------------

    def find_free_address(self) -> Optional[int]:
        """Find free address for new device"""
        addresses_attributes = self.__registers_registry.get_all_by_name(DeviceAttribute.ADDRESS.value)

        reserved_addresses: List[int] = []

        for address_attribute in addresses_attributes:
            if isinstance(address_attribute.actual_value, int):
                reserved_addresses.append(address_attribute.actual_value)

        for address in range(1, 251):
            if address not in reserved_addresses:
                return address

        return None

    # -----------------------------------------------------------------------------

    def __update(self, updated_device: DeviceRecord, dispatch: bool = False) -> bool:
        """Update device record"""
        self.__items[updated_device.id.__str__()] = updated_device

        if dispatch:
            self.__event_dispatcher.dispatch(
                event_id=DeviceRecordCreatedOrUpdatedEvent.EVENT_NAME,
                event=DeviceRecordCreatedOrUpdatedEvent(record=updated_device),
            )

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


@inject(
    bind={
        "device_property_state_repository": IDevicePropertyStateRepository,
        "channel_property_state_repository": IChannelPropertyStateRepository,
    }
)
class RegistersRegistry:
    """
    Registers registry

    @package        FastyBird:FbBusConnector!
    @module         registry/model

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __items: Dict[str, RegisterRecord] = {}

    __event_dispatcher: EventDispatcher

    __device_property_state_repository: Optional[IDevicePropertyStateRepository] = None
    __channel_property_state_repository: Optional[IChannelPropertyStateRepository] = None

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        device_property_state_repository: Optional[IDevicePropertyStateRepository] = None,
        channel_property_state_repository: Optional[IChannelPropertyStateRepository] = None,
    ) -> None:
        self.__items = {}

        self.__event_dispatcher = event_dispatcher

        self.__device_property_state_repository = device_property_state_repository
        self.__channel_property_state_repository = channel_property_state_repository

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

    def get_by_name(
        self,
        device_id: uuid.UUID,
        name: str,
    ) -> Optional[AttributeRegisterRecord]:
        """Get device attribute register by name"""
        items = self.__items.copy()

        return next(
            iter(
                [
                    record
                    for record in items.values()
                    if isinstance(record, AttributeRegisterRecord)
                    and record.name == name
                    and device_id.__eq__(record.device_id)
                ]
            ),
            None,
        )

    # -----------------------------------------------------------------------------

    def get_all_by_name(
        self,
        name: str,
    ) -> List[AttributeRegisterRecord]:
        """Get all attributes registers by name"""
        items = self.__items.copy()

        return [
            record for record in items.values() if isinstance(record, AttributeRegisterRecord) and record.name == name
        ]

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

    def append_input_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DataType,
    ) -> InputRegisterRecord:
        """Append new register or replace existing register in registry"""
        existing_register = self.get_by_id(register_id=register_id)

        register = InputRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_data_type=register_data_type,
        )

        if existing_register is None and self.__channel_property_state_repository is not None:
            stored_state = self.__channel_property_state_repository.get_by_id(property_id=register_id)

            if stored_state is not None:
                register.actual_value = stored_state.actual_value
                register.expected_value = stored_state.expected_value
                register.expected_pending = stored_state.pending

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def append_output_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DataType,
    ) -> OutputRegisterRecord:
        """Append new register or replace existing register in registry"""
        existing_register = self.get_by_id(register_id=register_id)

        register = OutputRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_data_type=register_data_type,
        )

        if existing_register is None and self.__channel_property_state_repository is not None:
            stored_state = self.__channel_property_state_repository.get_by_id(property_id=register_id)

            if stored_state is not None:
                register.actual_value = stored_state.actual_value
                register.expected_value = stored_state.expected_value
                register.expected_pending = stored_state.pending

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def append_attribute_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DataType,
        register_name: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
    ) -> AttributeRegisterRecord:
        """Append new attribute register or replace existing register in registry"""
        existing_register = self.get_by_id(register_id=register_id)

        register = AttributeRegisterRecord(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_data_type=register_data_type,
            register_name=register_name,
            register_settable=register_settable,
            register_queryable=register_queryable,
        )

        if existing_register is None and self.__device_property_state_repository is not None:
            stored_state = self.__device_property_state_repository.get_by_id(property_id=register_id)

            if stored_state is not None:
                register.actual_value = stored_state.actual_value
                register.expected_value = stored_state.expected_value
                register.expected_pending = stored_state.pending

        self.__items[register.id.__str__()] = register

        return register

    # -----------------------------------------------------------------------------

    def create_or_update(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_type: RegisterType,
        register_data_type: DataType,
        register_name: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
    ) -> RegisterRecord:
        """Create new register record"""
        if register_type == RegisterType.INPUT:
            input_register = self.append_input_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_data_type=register_data_type,
            )

            self.__event_dispatcher.dispatch(
                event_id=InputOutputRegisterRecordCreatedOrUpdatedEvent.EVENT_NAME,
                event=InputOutputRegisterRecordCreatedOrUpdatedEvent(record=input_register),
            )

            return input_register

        if register_type == RegisterType.OUTPUT:
            output_register = self.append_output_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_data_type=register_data_type,
            )

            self.__event_dispatcher.dispatch(
                event_id=InputOutputRegisterRecordCreatedOrUpdatedEvent.EVENT_NAME,
                event=InputOutputRegisterRecordCreatedOrUpdatedEvent(record=output_register),
            )

            return output_register

        if register_type == RegisterType.ATTRIBUTE:
            attribute_register = self.append_attribute_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_data_type=register_data_type,
                register_name=register_name,
                register_settable=register_settable,
                register_queryable=register_queryable,
            )

            self.__event_dispatcher.dispatch(
                event_id=AttributeRegisterRecordCreatedOrUpdatedEvent.EVENT_NAME,
                event=AttributeRegisterRecordCreatedOrUpdatedEvent(record=attribute_register),
            )

            return attribute_register

        raise ValueError("Provided register type is not supported")

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

    def set_actual_value(
        self,
        register: RegisterRecord,
        value: Union[str, int, float, bool, datetime, ButtonPayload, SwitchPayload, None],
    ) -> RegisterRecord:
        """Set actual value to register"""
        existing_record = self.get_by_id(register_id=register.id)

        register.actual_value = value

        self.__update(register=register)

        updated_register = self.get_by_id(register.id)

        if updated_register is None:
            raise InvalidStateException("Register record could not be re-fetched from registry after update")

        self.__event_dispatcher.dispatch(
            event_id=RegisterActualValueEvent.EVENT_NAME,
            event=RegisterActualValueEvent(
                original_record=existing_record,
                updated_record=updated_register,
            ),
        )

        return updated_register

    # -----------------------------------------------------------------------------

    def set_expected_value(
        self,
        register: RegisterRecord,
        value: Union[str, int, float, bool, datetime, ButtonPayload, SwitchPayload, None],
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
