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
FastyBird BUS connector clients module client for API v1
"""

# pylint: disable=too-many-lines

# Python base dependencies
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Union

# Library dependencies
from fastybird_metadata.devices_module import ConnectionState
from fastybird_metadata.types import ButtonPayload, DataType, SwitchPayload
from kink import inject

# Library libs
from fastybird_fb_bus_connector.api.v1builder import V1Builder
from fastybird_fb_bus_connector.clients.client import IClient
from fastybird_fb_bus_connector.exceptions import BuildPayloadException
from fastybird_fb_bus_connector.logger import Logger
from fastybird_fb_bus_connector.registry.model import (
    DevicesRegistry,
    DiscoveredDevicesRegistry,
    DiscoveredRegistersRegistry,
    RegistersRegistry,
)
from fastybird_fb_bus_connector.registry.records import (
    DeviceRecord,
    DiscoveredAttributeRegisterRecord,
    DiscoveredDeviceRecord,
    DiscoveredInputRegisterRecord,
    DiscoveredOutputRegisterRecord,
    DiscoveredRegisterRecord,
    RegisterRecord,
)
from fastybird_fb_bus_connector.transporters.transporter import ITransporter
from fastybird_fb_bus_connector.types import DeviceAttribute, Packet, RegisterType


@inject(alias=IClient)
class ApiV1Client(IClient):  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """
    Communication client for API v1

    @package        FastyBird:FbBusConnector!
    @module         clients/apiv1

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __discovery_enabled: bool = True

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    __discovered_devices_registry: DiscoveredDevicesRegistry
    __discovered_registers_registry: DiscoveredRegistersRegistry

    __discovery_attempts: int = 0
    __total_discovery_attempts: int = 0

    __transporter: ITransporter

    __processed_devices: List[str] = []
    __processed_devices_registers: Dict[str, Set[str]] = {}

    __broadcasting_discovery_finished: bool = False
    __last_discovery_broadcast_request_send_timestamp: float = 0.0

    __logger: Union[Logger, logging.Logger]

    __MAX_TRANSMIT_ATTEMPTS: int = 5  # Maximum count of sending packets before gateway mark device as lost

    __PING_DELAY: float = 15.0  # Delay between pings packets
    __READ_STATE_DELAY: float = 5.0  # Delay between read state packets

    __PACKET_RESPONSE_DELAY: float = 0.5  # Waiting time before another packet is sent
    __PACKET_RESPONSE_WAITING_TIME: float = 0.5
    __BROADCAST_WAITING_DELAY: float = 2.0  # Maximum time gateway will wait for reply during broadcasting

    __MAX_DISCOVERY_ATTEMPTS: int = 5  # Maxim count of sending search device packets
    __MAX_TOTAL_DISCOVERY_ATTEMPTS: int = (
        100  # Maximum total count of packets before gateway mark paring as unsuccessful
    )
    __DISCOVERY_BROADCAST_DELAY: float = 2.0  # Waiting delay before another broadcast is sent
    __DEVICE_DISCOVERY_DELAY: float = 5.0  # Waiting delay paring is marked as unsuccessful

    __ADDRESS_NOT_ASSIGNED: int = 255

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        discovered_devices_registry: DiscoveredDevicesRegistry,
        discovered_registers_registry: DiscoveredRegistersRegistry,
        transporter: ITransporter,
        logger: Union[Logger, logging.Logger] = logging.getLogger("dummy"),
    ) -> None:
        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

        self.__discovered_devices_registry = discovered_devices_registry
        self.__discovered_registers_registry = discovered_registers_registry

        self.__transporter = transporter

        self.__logger = logger

        self.__processed_devices = []
        self.__processed_devices_registers = {}

    # -----------------------------------------------------------------------------

    def enable_discovery(self) -> None:
        """Enable client devices discovery"""
        self.__discovery_enabled = True

        self.__logger.info("Discovery mode is activated")

    # -----------------------------------------------------------------------------

    def disable_discovery(self) -> None:
        """Disable client devices discovery"""
        self.__discovery_enabled = False

        self.__total_discovery_attempts = 0
        self.__last_discovery_broadcast_request_send_timestamp = 0.0
        self.__total_discovery_attempts = 0
        self.__discovery_attempts = 0

        self.__broadcasting_discovery_finished = False

        self.__discovered_devices_registry.reset()

        self.__logger.info("Discovery mode is deactivated")

    # -----------------------------------------------------------------------------

    def handle(self) -> None:
        """Handle connected devices"""
        if self.__transporter.packet_to_be_sent > 0:
            return

        if self.__discovery_enabled:
            self.__process_discovery()

        else:
            for device in self.__devices_registry:
                if not device.enabled:
                    continue

                if device.id.__str__() not in self.__processed_devices:
                    self.__process_device(device=device)

                    self.__processed_devices.append(device.id.__str__())

                    return

            self.__processed_devices = []

    # -----------------------------------------------------------------------------

    def __process_device(self, device: DeviceRecord) -> None:  # pylint: disable=too-many-return-statements
        """Handle client read or write message to device"""
        device_address = self.__get_address_for_device(device=device)

        if device_address is None:
            self.__logger.error(
                "Device address could not be fetched from registry. Device is disabled and have to be re-discovered",
                extra={
                    "device": {
                        "id": device.id.__str__(),
                        "serial_number": device.serial_number,
                    },
                },
            )

            self.__devices_registry.disable(device=device)

            return

        # Maximum send packet attempts was reached device is now marked as lost
        if device.transmit_attempts >= self.__MAX_TRANSMIT_ATTEMPTS:
            if self.__devices_registry.is_device_lost(device=device):
                self.__devices_registry.reset_communication(device=device)

                self.__logger.info(
                    "Device with address: %s is still lost",
                    device_address,
                    extra={
                        "device": {
                            "id": device.id.__str__(),
                            "serial_number": device.serial_number,
                            "address": device_address,
                        },
                    },
                )

            else:
                self.__logger.info(
                    "Device with address: %s is lost",
                    device_address,
                    extra={
                        "device": {
                            "id": device.id.__str__(),
                            "serial_number": device.serial_number,
                            "address": device_address,
                        },
                    },
                )

                self.__devices_registry.set_device_is_lost(device=device)

            return

        # Device state is lost...
        if self.__devices_registry.is_device_lost(device=device):
            # ...wait for ping delay...
            if (time.time() - device.last_packet_timestamp) >= self.__PING_DELAY:
                # ...then try to PING device
                self.__send_ping_handler(device=device, device_address=device_address)

            return

        # Device state is unknown...
        if self.__devices_registry.is_device_unknown(device=device):
            # ...wait for read state delay...
            if (time.time() - device.last_packet_timestamp) >= self.__READ_STATE_DELAY:
                # ...ask device for its state
                self.__send_read_device_state_handler(device=device, device_address=device_address)

            return

        # Check if device is in RUNNING mode
        if not self.__devices_registry.is_device_running(device=device):
            return

        if self.__write_register_handler(device=device, device_address=device_address):
            return

        if self.__read_registers_handler(device=device, device_address=device_address):
            return

    # -----------------------------------------------------------------------------

    def __process_discovery(self) -> None:
        """Handle discovery process"""
        # Connector protection
        if self.__total_discovery_attempts >= self.__MAX_TOTAL_DISCOVERY_ATTEMPTS:
            self.__logger.info("Maximum attempts reached. Disabling discovery procedure to prevent infinite loop")

            self.disable_discovery()

            return

        if not self.__broadcasting_discovery_finished:
            # Check if search counter is reached
            if self.__discovery_attempts < self.__MAX_DISCOVERY_ATTEMPTS:
                # Search timeout is not reached, new devices could be searched
                if (
                    self.__last_discovery_broadcast_request_send_timestamp == 0
                    or time.time() - self.__last_discovery_broadcast_request_send_timestamp
                    >= self.__DISCOVERY_BROADCAST_DELAY
                ):
                    # Broadcast discovery request for new device
                    self.__broadcast_discover_devices_handler()

            # Searching for devices finished
            else:
                self.__broadcasting_discovery_finished = True

                self.__discovered_devices_registry.prepare_devices()

            return

        # Check if some devices are in queue
        if len(self.__discovered_devices_registry) == 0:
            self.disable_discovery()

            return

        # Device for discovery is assigned
        for discovered_device in self.__discovered_devices_registry:
            # Max device discovery attempts were reached
            if discovered_device.transmit_attempts >= self.__MAX_TRANSMIT_ATTEMPTS or (
                discovered_device.last_packet_timestamp != 0.0
                and time.time() - discovered_device.last_packet_timestamp >= self.__DEVICE_DISCOVERY_DELAY
            ):
                self.__logger.warning(
                    "Discovery could not be finished, device: %s is lost. Moving to next device in queue",
                    discovered_device.serial_number,
                    extra={
                        "device": {
                            "serial_number": discovered_device.serial_number,
                            "address": discovered_device.address,
                        },
                    },
                )

                # Move to next device in queue
                self.__discovered_devices_registry.remove(serial_number=discovered_device.serial_number)

                return

            # Packet was sent to device, waiting for device reply
            if discovered_device.waiting_for_packet:
                return

            # Check if are some registers left for initialization
            register_record = next(
                iter(
                    [
                        register
                        for register in self.__discovered_registers_registry.get_all_by_device(
                            device_serial_number=discovered_device.serial_number
                        )
                        if register.data_type == DataType.UNKNOWN
                    ]
                ),
                None,
            )

            if register_record is not None:
                self.__send_provide_register_structure_handler(
                    discovered_device=discovered_device,
                    discovered_register=register_record,
                )

            # Set device to operating mode
            else:
                self.__send_finalize_device_discovery_handler(discovered_device=discovered_device)

    # -----------------------------------------------------------------------------

    def __send_ping_handler(self, device: DeviceRecord, device_address: int) -> None:
        result = self.__transporter.send_packet(
            address=device_address,
            payload=V1Builder.build_ping(),
        )

        self.__validate_result(result=result, device=device)

    # -----------------------------------------------------------------------------

    def __send_read_device_state_handler(self, device: DeviceRecord, device_address: int) -> None:
        state_attribute = self.__registers_registry.get_by_name(device_id=device.id, name=DeviceAttribute.STATE.value)

        if state_attribute is None:
            self.__logger.error(
                "Device state attribute register could not be fetched from registry",
                extra={
                    "device": {
                        "id": device.id.__str__(),
                        "serial_number": device.serial_number,
                    },
                },
            )

            return

        output_content = V1Builder.build_read_single_register_value(
            register_type=state_attribute.type,
            register_address=state_attribute.address,
        )

        result = self.__transporter.send_packet(
            address=device_address,
            payload=output_content,
            waiting_time=self.__PACKET_RESPONSE_WAITING_TIME,
        )

        self.__validate_result(result=result, device=device)

    # -----------------------------------------------------------------------------

    def __write_register_handler(self, device: DeviceRecord, device_address: int) -> bool:
        for register_type in (RegisterType.OUTPUT, RegisterType.ATTRIBUTE):
            if self.__write_single_register(
                device=device,
                device_address=device_address,
                register_type=register_type,
            ):
                return True

        return False

    # -----------------------------------------------------------------------------

    def __read_registers_handler(self, device: DeviceRecord, device_address: int) -> bool:
        input_registers = self.__registers_registry.get_all_for_device(
            device_id=device.id,
            register_type=RegisterType.INPUT,
        )

        output_registers = self.__registers_registry.get_all_for_device(
            device_id=device.id,
            register_type=RegisterType.OUTPUT,
        )

        # Get all input & output registers for device
        registers = input_registers + output_registers
        # Sort them by ID
        registers.sort(key=lambda r: (r.type.value, r.address))

        if device.id.__str__() not in self.__processed_devices_registers:
            self.__processed_devices_registers[device.id.__str__()] = set()

        for register in registers:
            if (
                register.id.__str__() not in self.__processed_devices_registers[register.device_id.__str__()]
                and time.time() - register.reading_timestamp >= device.sampling_time
            ):
                read_result = self.__read_multiple_registers(
                    device=device,
                    device_address=device_address,
                    register_type=register.type,
                    start_address=register.address,
                )

                self.__processed_devices_registers[device.id.__str__()].add(register.id.__str__())

                return read_result

        attribute_registers = self.__registers_registry.get_all_for_device(
            device_id=device.id,
            register_type=RegisterType.ATTRIBUTE,
        )
        attribute_registers.sort(key=lambda r: r.address)

        for attribute_register in attribute_registers:
            if (
                attribute_register.id.__str__()
                not in self.__processed_devices_registers[attribute_register.device_id.__str__()]
                and time.time() - attribute_register.reading_timestamp >= device.sampling_time
                and attribute_register.queryable
            ):
                read_result = self.__read_single_register(
                    device=device,
                    device_address=device_address,
                    register_type=attribute_register.type,
                    register_address=attribute_register.address,
                )

                self.__processed_devices_registers[device.id.__str__()].add(attribute_register.id.__str__())

                self.__registers_registry.set_reading_timestamp(register=attribute_register, timestamp=time.time())

                return read_result

        self.__processed_devices_registers[device.id.__str__()] = set()

        return True

    # -----------------------------------------------------------------------------

    def __broadcast_discover_devices_handler(self) -> None:
        """Broadcast devices discovery packet to bus"""
        # Set counters & flags...
        self.__discovery_attempts += 1
        self.__total_discovery_attempts += 1
        self.__last_discovery_broadcast_request_send_timestamp = time.time()

        self.__logger.debug("Preparing to broadcast search devices")

        self.__transporter.broadcast_packet(
            payload=V1Builder.build_discovery(),
            waiting_time=self.__BROADCAST_WAITING_DELAY,
        )

    # -----------------------------------------------------------------------------

    def __send_provide_register_structure_handler(
        self,
        discovered_device: DiscoveredDeviceRecord,
        discovered_register: DiscoveredRegisterRecord,
    ) -> None:
        """We know basic device structure, let's get structure for each register"""
        output_content = V1Builder.build_read_single_register_structure(
            register_type=discovered_register.type,
            register_address=discovered_register.address,
            serial_number=(
                discovered_device.serial_number if discovered_device.address == self.__ADDRESS_NOT_ASSIGNED else None
            ),
        )

        # Mark that gateway is waiting for reply from device...
        self.__discovered_devices_registry.set_waiting_for_packet(
            device=discovered_device,
            packet_type=Packet.READ_SINGLE_REGISTER_STRUCTURE,
        )

        self.__total_discovery_attempts += 1

        if discovered_device.address == self.__ADDRESS_NOT_ASSIGNED:
            self.__transporter.broadcast_packet(
                payload=output_content,
                waiting_time=self.__BROADCAST_WAITING_DELAY,
            )

        else:
            result = self.__transporter.send_packet(
                address=discovered_device.address,
                payload=output_content,
            )

            if result is False:
                # Mark that gateway is not waiting any reply from device
                self.__discovered_devices_registry.set_waiting_for_packet(device=discovered_device, packet_type=None)

    # -----------------------------------------------------------------------------

    def __send_finalize_device_discovery_handler(self, discovered_device: DiscoveredDeviceRecord) -> None:
        existing_device = self.__devices_registry.get_by_serial_number(serial_number=discovered_device.serial_number)

        if (
            # New device is without bus address
            discovered_device.address == self.__ADDRESS_NOT_ASSIGNED
            or (
                # Or device bus address is different from stored in connector registry
                existing_device is not None
                and discovered_device.address != self.__devices_registry.get_address(device=existing_device)
                and self.__devices_registry.get_address(device=existing_device) is not None
            )
        ):
            # Bus address have to be updated to correct one
            self.__write_discovered_device_new_address(
                discovered_device=discovered_device,
            )

        # No other actions are required...
        else:
            # Device could be restarted to running mode
            self.__write_discovered_device_state(
                discovered_device=discovered_device,
            )

        # Move to next device in queue
        self.__discovered_devices_registry.remove(serial_number=discovered_device.serial_number)

    # -----------------------------------------------------------------------------

    def __read_single_register(  # pylint: disable=too-many-branches
        self,
        device: DeviceRecord,
        device_address: int,
        register_type: RegisterType,
        register_address: int,
    ) -> bool:
        output_content = V1Builder.build_read_single_register_value(
            register_type=register_type,
            register_address=register_address,
        )

        result = self.__transporter.send_packet(
            address=device_address,
            payload=output_content,
        )

        self.__validate_result(result=result, device=device)

        return True

    # -----------------------------------------------------------------------------

    def __read_multiple_registers(  # pylint: disable=too-many-branches
        self,
        device: DeviceRecord,
        device_address: int,
        register_type: RegisterType,
        start_address: Optional[int],
    ) -> bool:
        register_size = len(
            self.__registers_registry.get_all_for_device(device_id=device.id, register_type=register_type)
        )

        if start_address is None:
            start_address = 0

        if register_type in (RegisterType.INPUT, RegisterType.OUTPUT):
            # Calculate maximum count registers per one packet
            # e.g. max_packet_length = 24 => max_readable_registers_count = 4
            #   - only 4 registers could be read in one packet
            max_readable_registers_count = (self.__get_max_packet_length_for_device(device=device) - 8) // 4

        else:
            return True

        # Calculate reading address based on maximum reading length and start address
        # e.g. start_address = 0 and max_readable_registers_count = 3 => max_readable_addresses = 2
        # e.g. start_address = 3 and max_readable_registers_count = 3 => max_readable_addresses = 5
        # e.g. start_address = 0 and max_readable_registers_count = 8 => max_readable_addresses = 7
        max_readable_addresses = start_address + max_readable_registers_count - 1

        if (max_readable_addresses + 1) >= register_size:
            if start_address == 0:
                read_length = register_size

            else:
                read_length = register_size - start_address

        else:
            read_length = max_readable_registers_count

        next_address = start_address + read_length

        # Validate registers reading length
        if read_length <= 0:
            return True

        output_content = V1Builder.build_read_multiple_registers_values(
            register_type=register_type,
            start_address=start_address,
            registers_count=read_length,
        )

        result = self.__transporter.send_packet(
            address=device_address,
            payload=output_content,
        )

        self.__validate_result(result=result, device=device)

        if result is True:
            for register_address in range(start_address, next_address):
                register = self.__registers_registry.get_by_address(
                    device_id=device.id,
                    register_type=register_type,
                    register_address=register_address,
                )

                if register is not None:
                    self.__processed_devices_registers[device.id.__str__()].add(register.id.__str__())

                    self.__registers_registry.set_reading_timestamp(register=register, timestamp=time.time())

        return True

    # -----------------------------------------------------------------------------

    def __write_single_register(
        self,
        device: DeviceRecord,
        device_address: int,
        register_type: RegisterType,
    ) -> bool:
        registers = self.__registers_registry.get_all_for_device(
            device_id=device.id,
            register_type=register_type,
        )

        for register in registers:
            if register.expected_value is not None and register.expected_pending is None:
                if self.__write_value_to_single_register(
                    device=device,
                    device_address=device_address,
                    register=register,
                    write_value=register.expected_value,
                ):
                    self.__registers_registry.set_expected_pending(register=register, timestamp=time.time())

                    return True

        return False

    # -----------------------------------------------------------------------------

    def __write_value_to_single_register(
        self,
        device: DeviceRecord,
        device_address: int,
        register: RegisterRecord,
        write_value: Union[str, int, float, bool, datetime, ButtonPayload, SwitchPayload],
    ) -> bool:
        try:
            output_content = V1Builder.build_write_single_register_value(
                register_type=register.type,
                register_address=register.address,
                register_data_type=register.data_type,
                register_name=None,
                write_value=write_value,
            )

        except BuildPayloadException as ex:
            self.__logger.error(
                "Value couldn't be written into register",
                extra={
                    "device": {
                        "id": device.id.__str__(),
                    },
                    "register": {
                        "address": register.address,
                        "type": register.type.value,
                        "data_type": register.data_type.value,
                    },
                    "exception": {
                        "message": str(ex),
                        "code": type(ex).__name__,
                    },
                },
            )

            # There is some problem with transforming expected value, write is skipped & cleared
            self.__registers_registry.set_expected_value(register=register, value=None)

            return False

        result = self.__transporter.send_packet(
            address=device_address,
            payload=output_content,
            waiting_time=self.__PACKET_RESPONSE_WAITING_TIME,
        )

        self.__validate_result(result=result, device=device)

        return result

    # -----------------------------------------------------------------------------

    def __validate_result(self, result: bool, device: DeviceRecord) -> None:
        self.__devices_registry.set_last_packet_timestamp(device=device, last_packet_timestamp=time.time())

        if not result:
            # ...but packet was not received by device, mark that gateway is not waiting for reply from device
            self.__devices_registry.increment_transmit_attempts(device=device)

    # -----------------------------------------------------------------------------

    def __get_address_for_device(self, device: DeviceRecord) -> Optional[int]:
        address_attribute = self.__registers_registry.get_by_name(
            device_id=device.id,
            name=DeviceAttribute.ADDRESS.value,
        )

        if address_attribute is None or not isinstance(address_attribute.actual_value, int):
            return None

        return address_attribute.actual_value

    # -----------------------------------------------------------------------------

    def __get_max_packet_length_for_device(self, device: DeviceRecord) -> int:
        max_packet_length_attribute = self.__registers_registry.get_by_name(
            device_id=device.id,
            name=DeviceAttribute.MAX_PACKET_LENGTH.value,
        )

        if max_packet_length_attribute is None or not isinstance(max_packet_length_attribute.actual_value, int):
            return 80

        return max_packet_length_attribute.actual_value

    # -----------------------------------------------------------------------------

    def __write_discovered_device_new_address(
        self,
        discovered_device: DiscoveredDeviceRecord,
    ) -> None:
        """Discovered device is without address or with different address. Let's try to write new address to device"""
        address_register = next(
            iter(
                [
                    register
                    for register in self.__discovered_registers_registry.get_all_by_device(
                        device_serial_number=discovered_device.serial_number
                    )
                    if isinstance(register, DiscoveredAttributeRegisterRecord)
                    and register.name == DeviceAttribute.ADDRESS.value
                ]
            ),
            None,
        )

        if address_register is None:
            self.__logger.warning(
                "Register with stored address of discovered device could not be loaded. Discovery couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                        "address": discovered_device.address,
                    },
                },
            )

            return

        # Discovered device actual address
        actual_address = discovered_device.address

        # Assign new address to device
        free_address = self.__devices_registry.find_free_address()

        if free_address is None:
            self.__logger.warning(
                "No free address for new device is available. Discovery couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                        "address": discovered_device.address,
                    },
                },
            )

            return

        discovered_device.address = free_address

        updated_device = self.__devices_registry.get_by_serial_number(serial_number=discovered_device.serial_number)

        if updated_device is not None:
            updated_device_address = self.__devices_registry.get_address(device=updated_device)

            if updated_device_address is not None and updated_device_address != self.__ADDRESS_NOT_ASSIGNED:
                # Use address stored before
                discovered_device.address = updated_device_address

        try:
            output_content = V1Builder.build_write_single_register_value(
                register_type=address_register.type,
                register_address=address_register.address,
                register_data_type=address_register.data_type,
                register_name=address_register.name,
                write_value=discovered_device.address,
                serial_number=(
                    discovered_device.serial_number if actual_address == self.__ADDRESS_NOT_ASSIGNED else None
                ),
            )

        except BuildPayloadException as ex:
            self.__logger.warning(
                "New device address couldn't be written into register. Discovery couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                        "address": discovered_device.address,
                    },
                    "exception": {
                        "message": str(ex),
                        "code": type(ex).__name__,
                    },
                },
            )

            return

        # Data to write are ready to be broadcast, lets persist device into registry
        self.__finalize_discovered_device(discovered_device=discovered_device)

        # After device update their address, it should be restarted in running mode
        if actual_address == self.__ADDRESS_NOT_ASSIGNED:
            self.__transporter.broadcast_packet(
                payload=output_content,
                waiting_time=self.__BROADCAST_WAITING_DELAY,
            )

        else:
            result = self.__transporter.send_packet(
                address=actual_address,
                payload=output_content,
                waiting_time=self.__BROADCAST_WAITING_DELAY,
            )

            if result is False:
                self.__logger.warning(
                    "Device address couldn't written into device. Device have to be discovered again",
                    extra={
                        "device": {
                            "serial_number": discovered_device.serial_number,
                            "address": discovered_device.address,
                        },
                    },
                )

    # -----------------------------------------------------------------------------

    def __write_discovered_device_state(
        self,
        discovered_device: DiscoveredDeviceRecord,
    ) -> None:
        """Discovered device is ready to be used. Discoverable mode have to be deactivated"""
        state_register = next(
            iter(
                [
                    register
                    for register in self.__discovered_registers_registry.get_all_by_device(
                        device_serial_number=discovered_device.serial_number
                    )
                    if isinstance(register, DiscoveredAttributeRegisterRecord)
                    and register.name == DeviceAttribute.STATE.value
                ]
            ),
            None,
        )

        if state_register is None:
            self.__logger.warning(
                "Register with stored state could not be loaded. Discovery couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                        "address": discovered_device.address,
                    },
                },
            )

            return

        try:
            output_content = V1Builder.build_write_single_register_value(
                register_type=state_register.type,
                register_address=state_register.address,
                register_data_type=state_register.data_type,
                register_name=state_register.name,
                write_value=ConnectionState.RUNNING.value,
            )

        except BuildPayloadException as ex:
            self.__logger.warning(
                "Device state couldn't be written into register. Discovery couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                        "address": discovered_device.address,
                    },
                    "exception": {
                        "message": str(ex),
                        "code": type(ex).__name__,
                    },
                },
            )

            return

        # Data to write are ready to be broadcast, lets persist device into registry
        self.__finalize_discovered_device(discovered_device=discovered_device)

        # When device state is changed, discovery mode will be deactivated
        result = self.__transporter.send_packet(
            address=discovered_device.address,
            payload=output_content,
        )

        if result is False:
            self.__logger.warning(
                "Device state couldn't written into device. State have to be changed manually",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                        "address": discovered_device.address,
                    },
                },
            )

    # -----------------------------------------------------------------------------

    def __finalize_discovered_device(
        self,
        discovered_device: DiscoveredDeviceRecord,
    ) -> None:
        """Persist discovered device into connector registry"""
        existing_device = self.__devices_registry.get_by_serial_number(serial_number=discovered_device.serial_number)

        device_record = self.__devices_registry.create_or_update(
            device_id=uuid.uuid4() if existing_device is None else existing_device.id,
            device_serial_number=discovered_device.serial_number,
            device_enabled=False,
            hardware_manufacturer=discovered_device.hardware_manufacturer,
            hardware_model=discovered_device.hardware_model,
            hardware_version=discovered_device.hardware_version,
            firmware_manufacturer=discovered_device.firmware_manufacturer,
            firmware_version=discovered_device.firmware_version,
        )

        for register in self.__discovered_registers_registry.get_all_by_device(
            device_serial_number=discovered_device.serial_number
        ):
            existing_register = self.__registers_registry.get_by_address(
                device_id=device_record.id, register_type=register.type, register_address=register.address
            )

            if isinstance(register, (DiscoveredInputRegisterRecord, DiscoveredOutputRegisterRecord)):
                self.__registers_registry.create_or_update(
                    device_id=device_record.id,
                    register_id=uuid.uuid4() if existing_register is None else existing_register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_data_type=register.data_type,
                )

            elif isinstance(register, DiscoveredAttributeRegisterRecord):
                attribute_register = self.__registers_registry.create_or_update(
                    device_id=device_record.id,
                    register_id=uuid.uuid4() if existing_register is None else existing_register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_data_type=register.data_type,
                    register_name=register.name,
                    register_queryable=register.queryable,
                    register_settable=register.settable,
                )

                if register.name == DeviceAttribute.ADDRESS.value:
                    self.__registers_registry.set_actual_value(
                        register=attribute_register,
                        value=discovered_device.address,
                    )

                if register.name == DeviceAttribute.STATE.value:
                    self.__registers_registry.set_actual_value(
                        register=attribute_register,
                        value=discovered_device.state.value,
                    )

                if register.name == DeviceAttribute.MAX_PACKET_LENGTH.value:
                    self.__registers_registry.set_actual_value(
                        register=attribute_register,
                        value=discovered_device.max_packet_length,
                    )

        # Device initialization is finished, enable it for communication
        device_record = self.__devices_registry.enable(device=device_record)

        # Update device state
        device_record = self.__devices_registry.set_state(device=device_record, state=ConnectionState.UNKNOWN)
        # Update lact packet sent status
        self.__devices_registry.set_last_packet_timestamp(device=device_record, last_packet_timestamp=time.time())
