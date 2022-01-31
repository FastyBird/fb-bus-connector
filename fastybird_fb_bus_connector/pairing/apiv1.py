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
FastyBird BUS connector discovery module handler for API v1
"""

# Python base dependencies
import logging
import time
import uuid
from typing import Optional, Set, Union

# Library dependencies
from fastybird_metadata.devices_module import ConnectionState
from fastybird_metadata.types import DataType
from kink import inject

# Library libs
from fastybird_fb_bus_connector.api.v1builder import V1Builder
from fastybird_fb_bus_connector.clients.client import Client
from fastybird_fb_bus_connector.exceptions import BuildPayloadException
from fastybird_fb_bus_connector.logger import Logger
from fastybird_fb_bus_connector.pairing.pairing import IPairing
from fastybird_fb_bus_connector.registry.model import DevicesRegistry, RegistersRegistry
from fastybird_fb_bus_connector.registry.records import (
    DiscoveredAttributeRegisterRecord,
    DiscoveredDeviceRecord,
    DiscoveredInputRegisterRecord,
    DiscoveredOutputRegisterRecord,
    DiscoveredRegisterRecord,
)
from fastybird_fb_bus_connector.types import (
    DeviceAttribute,
    ProtocolVersion,
    RegisterType,
)


@inject(alias=IPairing)
class ApiV1Pairing(IPairing):  # pylint: disable=too-many-instance-attributes
    """
    BUS discovery handler for API v1

    @package        FastyBird:FbBusConnector!
    @module         pairing/apiv1

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __enabled: bool = True

    __discovered_devices: Set[DiscoveredDeviceRecord] = set()

    __discovered_device: Optional[DiscoveredDeviceRecord] = None
    __discovered_device_registers: Set[DiscoveredRegisterRecord] = set()

    __last_request_send_timestamp: float = 0.0

    __waiting_for_reply: bool = False
    __discovery_attempts: int = 0
    __device_attempts: int = 0
    __total_attempts: int = 0

    __broadcasting_discovery_finished: bool = False

    __MAX_DISCOVERY_ATTEMPTS: int = 5  # Maxim count of sending search device packets
    __MAX_DEVICE_ATTEMPTS: int = 5  # Maximum count of packets before gateway mark paring as unsuccessful
    __MAX_TOTAL_TRANSMIT_ATTEMPTS: int = (
        100  # Maximum total count of packets before gateway mark paring as unsuccessful
    )
    __DISCOVERY_BROADCAST_DELAY: float = 2.0  # Waiting delay before another broadcast is sent
    __DEVICE_DISCOVERY_DELAY: float = 5.0  # Waiting delay paring is marked as unsuccessful
    __BROADCAST_WAITING_DELAY: float = 2.0  # Maximum time gateway will wait for reply during broadcasting

    __ADDRESS_NOT_ASSIGNED: int = 255

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    __client: Client

    __logger: Union[Logger, logging.Logger]

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        client: Client,
        logger: Union[Logger, logging.Logger] = logging.getLogger("dummy"),
    ) -> None:
        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

        self.__client = client

        self.__logger = logger

    # -----------------------------------------------------------------------------

    def handle(self) -> None:
        """Handle discovery process"""
        if self.__enabled is False:
            return

        # Connector protection
        if self.__total_attempts >= self.__MAX_TOTAL_TRANSMIT_ATTEMPTS:
            self.__logger.info("Maximum attempts reached. Disabling discovery procedure to prevent infinite loop")

            self.disable()

        if not self.__broadcasting_discovery_finished:
            # Check if search counter is reached
            if self.__discovery_attempts < self.__MAX_DISCOVERY_ATTEMPTS:
                # Search timeout is not reached, new devices could be searched
                if (
                    self.__last_request_send_timestamp == 0
                    or time.time() - self.__last_request_send_timestamp >= self.__DISCOVERY_BROADCAST_DELAY
                ):
                    # Broadcast discovery request for new device
                    self.__broadcast_discover_devices_handler()

            # Searching for devices finished
            else:
                self.__broadcasting_discovery_finished = True

                # Move to device for discovery
                self.__process_discovered_device()

        # Device for discovery is assigned
        elif self.__discovered_device is not None:
            # Max device discovery attempts were reached
            if (
                self.__device_attempts >= self.__MAX_DEVICE_ATTEMPTS
                or time.time() - self.__last_request_send_timestamp >= self.__DEVICE_DISCOVERY_DELAY
            ):
                self.__logger.warning(
                    "Discovery could not be finished, device: %s is lost. Moving to next device in queue",
                    self.__discovered_device.serial_number,
                    extra={
                        "device": {
                            "serial_number": self.__discovered_device.serial_number,
                            "address": self.__discovered_device.address,
                        },
                    },
                )

                # Move to next device in queue
                self.__process_discovered_device()

                return

            # Packet was sent to device, waiting for device reply
            if self.__waiting_for_reply:
                return

            # Check if are some registers left for initialization
            register_record = next(
                iter(
                    [
                        register
                        for register in self.__discovered_device_registers
                        if register.data_type == DataType.UNKNOWN
                    ]
                ),
                None,
            )

            if register_record is not None:
                self.__send_provide_register_structure_handler(
                    discovered_device=self.__discovered_device,
                    discovered_register=register_record,
                )

            # Set device to operating mode
            else:
                self.__send_finalize_device_discovery_handler(discovered_device=self.__discovered_device)

    # -----------------------------------------------------------------------------

    def enable(self) -> None:
        """Enable devices discovery"""
        self.__enabled = True

        self.__reset_pointers()

        self.__logger.info("Discovery mode is activated")

    # -----------------------------------------------------------------------------

    def disable(self) -> None:
        """Disable devices discovery"""
        self.__enabled = False

        self.__reset_pointers()

        self.__logger.info("Discovery mode is deactivated")

    # -----------------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """Check if discovery is enabled"""
        return self.__enabled is True

    # -----------------------------------------------------------------------------

    def version(self) -> ProtocolVersion:
        """Discovery supported protocol version"""
        return ProtocolVersion.V1

    # -----------------------------------------------------------------------------

    def append_device(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        device_address: int,
        device_max_packet_length: int,
        device_serial_number: str,
        device_state: ConnectionState,
        device_hardware_version: str,
        device_hardware_model: str,
        device_hardware_manufacturer: str,
        device_firmware_version: str,
        device_firmware_manufacturer: str,
        input_registers_size: int,
        output_registers_size: int,
        attributes_registers_size: int,
    ) -> None:
        """Set discovered device data"""
        discovered_device = DiscoveredDeviceRecord(
            device_address=device_address,
            device_max_packet_length=device_max_packet_length,
            device_serial_number=device_serial_number,
            device_state=device_state,
            device_hardware_version=device_hardware_version,
            device_hardware_model=device_hardware_model,
            device_hardware_manufacturer=device_hardware_manufacturer,
            device_firmware_version=device_firmware_version,
            device_firmware_manufacturer=device_firmware_manufacturer,
            input_registers_size=input_registers_size,
            output_registers_size=output_registers_size,
            attributes_registers_size=attributes_registers_size,
        )

        if discovered_device not in self.__discovered_devices:
            self.__discovered_devices.add(discovered_device)

            self.__logger.info(
                "Discovered device %s[%d] %s[%s]:%s",
                device_serial_number,
                device_address,
                device_hardware_version,
                device_hardware_model,
                device_firmware_version,
            )

    # -----------------------------------------------------------------------------

    def append_input_register(
        self,
        register_address: int,
        register_data_type: DataType,
    ) -> None:
        """Append discovered device register"""
        # Reset counters & flags...
        self.__device_attempts = 0
        self.__total_attempts = 0

        self.__waiting_for_reply = False

        if self.__discovered_device is None:
            return

        configured_register = DiscoveredInputRegisterRecord(
            register_address=register_address,
            register_data_type=register_data_type,
        )

        if configured_register not in self.__discovered_device_registers:
            self.__logger.warning(
                "Register: %d[%d] for device: %s could not be found in registry",
                register_address,
                RegisterType.INPUT.value,
                self.__discovered_device.serial_number,
                extra={
                    "device": {
                        "serial_number": self.__discovered_device.serial_number,
                        "address": self.__discovered_device.address,
                    },
                },
            )

            return

        self.__discovered_device_registers.remove(configured_register)
        self.__discovered_device_registers.add(configured_register)

        self.__logger.info(
            "Configured register: %d[%d] for device: %s",
            register_address,
            RegisterType.INPUT.value,
            self.__discovered_device.serial_number,
            extra={
                "device": {
                    "serial_number": self.__discovered_device.serial_number,
                    "address": self.__discovered_device.address,
                },
            },
        )

    # -----------------------------------------------------------------------------

    def append_output_register(
        self,
        register_address: int,
        register_data_type: DataType,
    ) -> None:
        """Append discovered device output register"""
        # Reset counters & flags...
        self.__device_attempts = 0
        self.__total_attempts = 0

        self.__waiting_for_reply = False

        if self.__discovered_device is None:
            return

        configured_register = DiscoveredOutputRegisterRecord(
            register_address=register_address,
            register_data_type=register_data_type,
        )

        if configured_register not in self.__discovered_device_registers:
            self.__logger.warning(
                "Register: %d[%d] for device: %s could not be found in registry",
                register_address,
                RegisterType.OUTPUT.value,
                self.__discovered_device.serial_number,
                extra={
                    "device": {
                        "serial_number": self.__discovered_device.serial_number,
                        "address": self.__discovered_device.address,
                    },
                },
            )

            return

        self.__discovered_device_registers.remove(configured_register)
        self.__discovered_device_registers.add(configured_register)

        self.__logger.info(
            "Configured register: %d[%d] for device: %s",
            register_address,
            RegisterType.OUTPUT.value,
            self.__discovered_device.serial_number,
            extra={
                "device": {
                    "serial_number": self.__discovered_device.serial_number,
                    "address": self.__discovered_device.address,
                },
            },
        )

    # -----------------------------------------------------------------------------

    def append_attribute_register(  # pylint: disable=too-many-arguments
        self,
        register_address: int,
        register_name: Optional[str],
        register_data_type: DataType,
        register_settable: bool,
        register_queryable: bool,
    ) -> None:
        """Append discovered device attribute"""
        # Reset counters & flags...
        self.__device_attempts = 0
        self.__total_attempts = 0

        self.__waiting_for_reply = False

        if self.__discovered_device is None:
            return

        configured_register = DiscoveredAttributeRegisterRecord(
            register_address=register_address,
            register_name=register_name,
            register_data_type=register_data_type,
            register_settable=register_settable,
            register_queryable=register_queryable,
        )

        if configured_register not in self.__discovered_device_registers:
            self.__logger.warning(
                "Register: %d[%d] for device: %s could not be found in registry",
                register_address,
                RegisterType.ATTRIBUTE.value,
                self.__discovered_device.serial_number,
                extra={
                    "device": {
                        "serial_number": self.__discovered_device.serial_number,
                        "address": self.__discovered_device.address,
                    },
                },
            )

            return

        self.__discovered_device_registers.remove(configured_register)
        self.__discovered_device_registers.add(configured_register)

        self.__logger.info(
            "Configured register: %d[%d] for device: %s",
            register_address,
            RegisterType.ATTRIBUTE.value,
            self.__discovered_device.serial_number,
            extra={
                "device": {
                    "serial_number": self.__discovered_device.serial_number,
                    "address": self.__discovered_device.address,
                },
            },
        )

    # -----------------------------------------------------------------------------

    def __reset_pointers(self) -> None:
        self.__discovered_devices = set()

        self.__discovered_device = None
        self.__discovered_device_registers = set()

        self.__last_request_send_timestamp = 0.0

        self.__waiting_for_reply = False
        self.__discovery_attempts = 0
        self.__device_attempts = 0
        self.__total_attempts = 0

        self.__broadcasting_discovery_finished = False

    # -----------------------------------------------------------------------------

    def __process_discovered_device(self) -> None:
        """Pick one device from discovered devices and try to finish device discovery process"""
        # Reset counters & flags...
        self.__device_attempts = 0
        self.__total_attempts = 0

        self.__discovered_device = None
        self.__discovered_device_registers = set()

        self.__waiting_for_reply = False

        try:
            self.__discovered_device = self.__discovered_devices.pop()

        except KeyError:
            self.__logger.info("No device for discovering in registry. Disabling paring procedure")

            self.disable()

            return

        # Try to find device in registry
        existing_device = self.__devices_registry.get_by_serial_number(
            serial_number=self.__discovered_device.serial_number,
        )

        # Discovering new device...
        if existing_device is None:
            # Check if device has address or not
            if self.__discovered_device.address != self.__ADDRESS_NOT_ASSIGNED:
                # Check if other device with same address is present in registry
                device_by_address = self.__devices_registry.get_by_address(address=self.__discovered_device.address)

                if device_by_address is not None:
                    self.__logger.warning(
                        "Address used by discovered device is assigned to other registered device",
                        extra={
                            "device": {
                                "serial_number": self.__discovered_device.serial_number,
                                "address": self.__discovered_device.address,
                            },
                        },
                    )

                    # Move to next device in queue
                    self.__process_discovered_device()

                    return

            self.__logger.info(
                "New device: %s with address: %d was successfully prepared for registering",
                self.__discovered_device.serial_number,
                self.__discovered_device.address,
                extra={
                    "device": {
                        "serial_number": self.__discovered_device.serial_number,
                        "address": self.__discovered_device.address,
                    },
                },
            )

        # Discovering existing device...
        else:
            # Check if other device with same address is present in registry
            device_by_address = self.__devices_registry.get_by_address(address=self.__discovered_device.address)

            if (
                device_by_address is not None
                and device_by_address.serial_number != self.__discovered_device.serial_number
            ):
                self.__logger.warning(
                    "Address used by discovered device is assigned to other registered device",
                    extra={
                        "device": {
                            "serial_number": self.__discovered_device.serial_number,
                            "address": self.__discovered_device.address,
                        },
                    },
                )

                # Move to next device in queue
                self.__process_discovered_device()

                return

            self.__logger.info(
                "Existing device: %s with address: %d was successfully prepared for updating",
                self.__discovered_device.serial_number,
                self.__discovered_device.address,
                extra={
                    "device": {
                        "serial_number": self.__discovered_device.serial_number,
                        "address": self.__discovered_device.address,
                    },
                },
            )

            # Update device state
            self.__devices_registry.set_state(device=existing_device, state=ConnectionState.INIT)

        # Input registers
        self.__configure_registers(
            discovered_device=self.__discovered_device,
            registers_type=RegisterType.INPUT,
        )

        # Output registers
        self.__configure_registers(
            discovered_device=self.__discovered_device,
            registers_type=RegisterType.OUTPUT,
        )

        # Attribute registers
        self.__configure_registers(
            discovered_device=self.__discovered_device,
            registers_type=RegisterType.ATTRIBUTE,
        )

        self.__logger.info(
            "Configured registers: (Input: %d, Output: %d, Attribute: %d) for device: %s",
            self.__discovered_device.input_registers_size,
            self.__discovered_device.output_registers_size,
            self.__discovered_device.attributes_registers_size,
            self.__discovered_device.serial_number,
            extra={
                "device": {
                    "serial_number": self.__discovered_device.serial_number,
                    "address": self.__discovered_device.address,
                },
            },
        )

    # -----------------------------------------------------------------------------

    def __broadcast_discover_devices_handler(self) -> None:
        """Broadcast devices discovery packet to bus"""
        # Set counters & flags...
        self.__discovery_attempts += 1
        self.__total_attempts += 1
        self.__last_request_send_timestamp = time.time()

        self.__logger.debug("Preparing to broadcast search devices")

        self.__client.broadcast_packet(payload=V1Builder.build_discovery(), waiting_time=self.__BROADCAST_WAITING_DELAY)

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
        self.__device_attempts += 1
        self.__total_attempts += 1

        self.__waiting_for_reply = True
        self.__last_request_send_timestamp = time.time()

        if discovered_device.address == self.__ADDRESS_NOT_ASSIGNED:
            self.__client.broadcast_packet(payload=output_content, waiting_time=self.__BROADCAST_WAITING_DELAY)

        else:
            result = self.__client.send_packet(address=discovered_device.address, payload=output_content)

            if result is False:
                # Mark that gateway is not waiting any reply from device
                self.__waiting_for_reply = False

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
                discovered_registers=self.__discovered_device_registers,
            )

        # No other actions are required...
        else:
            # Device could be restarted to running mode
            self.__write_discovered_device_state(
                discovered_device=discovered_device,
                discovered_registers=self.__discovered_device_registers,
            )

        # Move to next device in queue
        self.__process_discovered_device()

    # -----------------------------------------------------------------------------

    def __configure_registers(self, discovered_device: DiscoveredDeviceRecord, registers_type: RegisterType) -> None:
        """Prepare discovered devices registers"""
        if registers_type == RegisterType.INPUT:
            registers_size = discovered_device.input_registers_size

        elif registers_type == RegisterType.OUTPUT:
            registers_size = discovered_device.output_registers_size

        elif registers_type == RegisterType.ATTRIBUTE:
            registers_size = discovered_device.attributes_registers_size

        else:
            return

        # Register data type will be reset to unknown
        register_data_type = DataType.UNKNOWN

        for i in range(registers_size):
            if registers_type == RegisterType.INPUT:
                # Create register record in registry
                self.__discovered_device_registers.add(
                    DiscoveredInputRegisterRecord(
                        register_address=i,
                        register_data_type=register_data_type,
                    )
                )

            elif registers_type == RegisterType.OUTPUT:
                # Create register record in registry
                self.__discovered_device_registers.add(
                    DiscoveredOutputRegisterRecord(
                        register_address=i,
                        register_data_type=register_data_type,
                    )
                )

            elif registers_type == RegisterType.ATTRIBUTE:
                # Create register record in registry
                self.__discovered_device_registers.add(
                    DiscoveredAttributeRegisterRecord(
                        register_address=i,
                        register_data_type=register_data_type,
                        register_name=None,
                        register_settable=False,
                        register_queryable=False,
                    )
                )

    # -----------------------------------------------------------------------------

    def __write_discovered_device_new_address(
        self,
        discovered_device: DiscoveredDeviceRecord,
        discovered_registers: Set[DiscoveredRegisterRecord],
    ) -> None:
        """Discovered device is without address or with different address. Let's try to write new address to device"""
        address_register = next(
            iter(
                [
                    register
                    for register in discovered_registers
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
        self.__finalize_device(discovered_device=discovered_device, discovered_registers=discovered_registers)

        # After device update their address, it should be restarted in running mode
        if actual_address == self.__ADDRESS_NOT_ASSIGNED:
            self.__client.broadcast_packet(payload=output_content, waiting_time=self.__BROADCAST_WAITING_DELAY)

        else:
            result = self.__client.send_packet(
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
        discovered_registers: Set[DiscoveredRegisterRecord],
    ) -> None:
        """Discovered device is ready to be used. Discoverable mode have to be deactivated"""
        state_register = next(
            iter(
                [
                    register
                    for register in discovered_registers
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
        self.__finalize_device(discovered_device=discovered_device, discovered_registers=discovered_registers)

        # When device state is changed, discovery mode will be deactivated
        result = self.__client.send_packet(address=discovered_device.address, payload=output_content)

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

    def __finalize_device(
        self,
        discovered_device: DiscoveredDeviceRecord,
        discovered_registers: Set[DiscoveredRegisterRecord],
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

        for register in discovered_registers:
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
