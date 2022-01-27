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
FastyBird BUS connector pairing module handler for API v1
"""

# Python base dependencies
import logging
import time
import uuid
from typing import List, Optional, Set, Union

# Library dependencies
from fastybird_metadata.devices_module import ConnectionState
from fastybird_metadata.types import DataType
from kink import inject

# Library libs
from fastybird_fb_bus_connector.clients.client import Client
from fastybird_fb_bus_connector.logger import Logger
from fastybird_fb_bus_connector.pairing.base import IPairing
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
    Packet,
    ProtocolVersion,
    RegisterType,
)
from fastybird_fb_bus_connector.utilities.helpers import (
    StateTransformHelpers,
    ValueTransformHelpers,
)


@inject(alias=IPairing)
class ApiV1Pairing(IPairing):  # pylint: disable=too-many-instance-attributes
    """
    BUS pairing handler for API v1

    @package        FastyBird:FbBusConnector!
    @module         pairing/apiv1

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __enabled: bool = True

    __discovered_devices: Set[DiscoveredDeviceRecord] = set()

    __pairing_device: Optional[DiscoveredDeviceRecord] = None
    __pairing_device_registers: Set[DiscoveredRegisterRecord] = set()

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
    __MAX_PAIRING_DELAY: float = 5.0  # Waiting delay paring is marked as unsuccessful
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
        """Handle pairing process"""
        if self.__enabled is False:
            return

        # Pairing gateway protection
        if self.__total_attempts >= self.__MAX_TOTAL_TRANSMIT_ATTEMPTS:
            self.disable()

            self.__logger.info("Maximum attempts reached. Disabling pairing procedure to prevent infinite loop")

        if not self.__broadcasting_discovery_finished:
            # Check if search counter is reached
            if self.__discovery_attempts < self.__MAX_DISCOVERY_ATTEMPTS:
                # Search timeout is not reached, new devices could be searched
                if (
                    self.__last_request_send_timestamp == 0
                    or time.time() - self.__last_request_send_timestamp >= self.__DISCOVERY_BROADCAST_DELAY
                ):
                    # Broadcast pairing request for new device
                    self.__broadcast_discover_devices_handler()

            # Searching for devices finished
            else:
                self.__broadcasting_discovery_finished = True

                # Move to device for pairing
                self.__process_discovered_device()

        # Device for pairing is assigned
        elif self.__pairing_device is not None:
            # Max pairing attempts were reached
            if (
                self.__device_attempts >= self.__MAX_DEVICE_ATTEMPTS
                or time.time() - self.__last_request_send_timestamp >= self.__MAX_PAIRING_DELAY
            ):
                self.__logger.warning(
                    "Pairing could not be finished, device: %s is lost. Moving to next device in queue",
                    self.__pairing_device.serial_number,
                    extra={
                        "device": {
                            "serial_number": self.__pairing_device.serial_number,
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
                    [register for register in self.__pairing_device_registers if register.data_type == DataType.UNKNOWN]
                ),
                None,
            )

            if register_record is not None:
                self.__send_provide_register_structure_handler(
                    discovered_device=self.__pairing_device,
                    discovered_register=register_record,
                )

            # Set device to operating mode
            else:
                self.__send_finalize_discovery_handler(discovered_device=self.__pairing_device)

    # -----------------------------------------------------------------------------

    def enable(self) -> None:
        """Enable devices pairing"""
        self.__enabled = True

        self.__reset_pointers()

        self.__logger.debug("Pairing mode is activated")

    # -----------------------------------------------------------------------------

    def disable(self) -> None:
        """Disable devices pairing"""
        self.__enabled = False

        self.__reset_pointers()

        self.__logger.debug("Pairing mode is deactivated")

    # -----------------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """Check if pairing is enabled"""
        return self.__enabled is True

    # -----------------------------------------------------------------------------

    def version(self) -> ProtocolVersion:
        """Pairing supported protocol version"""
        return ProtocolVersion.V1

    # -----------------------------------------------------------------------------

    def append_device(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        device_address: int,
        device_max_packet_length: int,
        device_serial_number: str,
        device_hardware_version: str,
        device_hardware_model: str,
        device_hardware_manufacturer: str,
        device_firmware_version: str,
        device_firmware_manufacturer: str,
        input_registers_size: int,
        output_registers_size: int,
        attributes_registers_size: int,
    ) -> None:
        """Set pairing device data"""
        in_register = next(
            iter([record for record in self.__discovered_devices if device_serial_number == record.serial_number]),
            None,
        )

        if in_register is not None:
            return

        # Check if device by serial number is stored in connector registry
        device_record = self.__devices_registry.get_by_serial_number(serial_number=device_serial_number)

        self.__discovered_devices.add(
            DiscoveredDeviceRecord(
                device_id=device_record.id if device_record is not None else uuid.uuid4(),
                device_address=device_address,
                device_max_packet_length=device_max_packet_length,
                device_serial_number=device_serial_number,
                device_hardware_version=device_hardware_version,
                device_hardware_model=device_hardware_model,
                device_hardware_manufacturer=device_hardware_manufacturer,
                device_firmware_version=device_firmware_version,
                device_firmware_manufacturer=device_firmware_manufacturer,
                input_registers_size=input_registers_size,
                output_registers_size=output_registers_size,
                attributes_registers_size=attributes_registers_size,
            )
        )

        self.__logger.debug(
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
        self.__waiting_for_reply = False

        if self.__pairing_device is None:
            return

        discovered_register = next(
            iter(
                [
                    register
                    for register in self.__pairing_device_registers
                    if register.type == RegisterType.INPUT and register.address == register_address
                ]
            ),
            None,
        )

        if discovered_register is None:
            self.__logger.warning(
                "Register: %d[%s] for device: %s could not be found in registry",
                register_address,
                RegisterType.INPUT,
                self.__pairing_device.serial_number,
                extra={
                    "device": {
                        "address": self.__pairing_device.address,
                        "serial_number": self.__pairing_device.serial_number,
                    },
                },
            )

            return

        for register in self.__pairing_device_registers:
            if register.id == discovered_register.id:
                self.__pairing_device_registers.remove(register)

                break

        self.__pairing_device_registers.add(
            DiscoveredInputRegisterRecord(
                register_id=discovered_register.id,
                register_address=register_address,
                register_data_type=register_data_type,
            )
        )

        self.__logger.debug(
            "Configured register: %d[%d] for device: %s",
            register_address,
            RegisterType.INPUT,
            self.__pairing_device.serial_number,
            extra={
                "device": {
                    "address": self.__pairing_device.address,
                    "serial_number": self.__pairing_device.serial_number,
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
        self.__waiting_for_reply = False

        if self.__pairing_device is None:
            return

        discovered_register = next(
            iter(
                [
                    register
                    for register in self.__pairing_device_registers
                    if register.type == RegisterType.OUTPUT and register.address == register_address
                ]
            ),
            None,
        )

        if discovered_register is None:
            self.__logger.warning(
                "Register: %d[%s] for device: %s could not be found in registry",
                register_address,
                RegisterType.OUTPUT,
                self.__pairing_device.serial_number,
                extra={
                    "device": {
                        "address": self.__pairing_device.address,
                        "serial_number": self.__pairing_device.serial_number,
                    },
                },
            )

            return

        for register in self.__pairing_device_registers:
            if register.id == discovered_register.id:
                self.__pairing_device_registers.remove(register)

                break

        self.__pairing_device_registers.add(
            DiscoveredOutputRegisterRecord(
                register_id=discovered_register.id,
                register_address=register_address,
                register_data_type=register_data_type,
            )
        )

        self.__logger.debug(
            "Configured register: %d[%d] for device: %s",
            register_address,
            RegisterType.OUTPUT,
            self.__pairing_device.serial_number,
            extra={
                "device": {
                    "address": self.__pairing_device.address,
                    "serial_number": self.__pairing_device.serial_number,
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
        self.__waiting_for_reply = False

        if self.__pairing_device is None:
            return

        discovered_register = next(
            iter(
                [
                    register
                    for register in self.__pairing_device_registers
                    if register.type == RegisterType.ATTRIBUTE and register.address == register_address
                ]
            ),
            None,
        )

        if discovered_register is None:
            self.__logger.warning(
                "Register: %d[%s] for device: %s could not be found in registry",
                register_address,
                RegisterType.ATTRIBUTE,
                self.__pairing_device.serial_number,
                extra={
                    "device": {
                        "address": self.__pairing_device.address,
                        "serial_number": self.__pairing_device.serial_number,
                    },
                },
            )

            return

        for register in self.__pairing_device_registers:
            if register.id == discovered_register.id:
                self.__pairing_device_registers.remove(register)

                break

        self.__pairing_device_registers.add(
            DiscoveredAttributeRegisterRecord(
                register_id=discovered_register.id,
                register_address=register_address,
                register_name=register_name,
                register_data_type=register_data_type,
                register_settable=register_settable,
                register_queryable=register_queryable,
            )
        )

        self.__logger.debug(
            "Configured register: %d[%d] for device: %s",
            register_address,
            RegisterType.ATTRIBUTE,
            self.__pairing_device.serial_number,
            extra={
                "device": {
                    "address": self.__pairing_device.address,
                    "serial_number": self.__pairing_device.serial_number,
                },
            },
        )

    # -----------------------------------------------------------------------------

    def __reset_pointers(self) -> None:
        self.__discovered_devices = set()

        self.__pairing_device = None
        self.__pairing_device_registers = set()

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

        self.__pairing_device = None
        self.__pairing_device_registers = set()

        self.__waiting_for_reply = False

        try:
            self.__pairing_device = self.__discovered_devices.pop()

        except KeyError:
            self.disable()

            self.__logger.info("No device for discovering in registry. Disabling paring procedure")

            return

        # Try to find device in registry
        device_record = self.__devices_registry.get_by_serial_number(serial_number=self.__pairing_device.serial_number)

        # Pairing new device...
        if device_record is None:
            # Check if device has address or not
            if self.__pairing_device.address != self.__ADDRESS_NOT_ASSIGNED:
                # Check if other device with same address is present in registry
                device_by_address = self.__devices_registry.get_by_address(address=self.__pairing_device.address)

                if device_by_address is not None:
                    self.__logger.warning(
                        "Device address is assigned to other other device",
                        extra={
                            "device": {
                                "address": self.__pairing_device.address,
                                "serial_number": self.__pairing_device.serial_number,
                            },
                        },
                    )

                    # Move to next device in queue
                    self.__process_discovered_device()

                    return

            self.__logger.debug(
                "New device: %s with address: %d was successfully prepared for pairing",
                self.__pairing_device.serial_number,
                self.__pairing_device.address,
                extra={
                    "device": {
                        "serial_number": self.__pairing_device.serial_number,
                        "address": self.__pairing_device.address,
                    },
                },
            )

        # Pairing existing device...
        else:
            # Check if other device with same address is present in registry
            device_by_address = self.__devices_registry.get_by_address(address=self.__pairing_device.address)

            if device_by_address is not None and device_by_address.serial_number != self.__pairing_device.serial_number:
                self.__logger.warning(
                    "Device address is assigned to other other device",
                    extra={
                        "device": {
                            "address": self.__pairing_device.address,
                            "serial_number": self.__pairing_device.serial_number,
                        },
                    },
                )

                # Move to next device in queue
                self.__process_discovered_device()

                return

            self.__logger.debug(
                "Existing device: %s with address: %d was successfully prepared for pairing",
                self.__pairing_device.serial_number,
                self.__pairing_device.address,
                extra={
                    "device": {
                        "serial_number": self.__pairing_device.serial_number,
                        "address": self.__pairing_device.address,
                    },
                },
            )

            # Update device state
            self.__devices_registry.set_state(device=device_record, state=ConnectionState.INIT)

        # Input registers
        self.__configure_registers(
            discovered_device=self.__pairing_device,
            registers_type=RegisterType.INPUT,
        )

        # Output registers
        self.__configure_registers(
            discovered_device=self.__pairing_device,
            registers_type=RegisterType.OUTPUT,
        )

        # Attribute registers
        self.__configure_registers(
            discovered_device=self.__pairing_device,
            registers_type=RegisterType.ATTRIBUTE,
        )

        self.__logger.debug(
            "Configured registers: (Input: %d, Output: %d, Attribute: %d) for device: %s",
            self.__pairing_device.input_registers_size,
            self.__pairing_device.output_registers_size,
            self.__pairing_device.attributes_registers_size,
            self.__pairing_device.serial_number,
            extra={
                "device": {
                    "serial_number": self.__pairing_device.serial_number,
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

        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.DISCOVER.value,
        ]

        self.__logger.debug("Preparing to broadcast search devices")

        self.__client.broadcast_packet(payload=output_content, waiting_time=self.__BROADCAST_WAITING_DELAY)

    # -----------------------------------------------------------------------------

    def __send_provide_register_structure_handler(
        self,
        discovered_device: DiscoveredDeviceRecord,
        discovered_register: DiscoveredRegisterRecord,
    ) -> None:
        """We know basic device structure, let's get structure for each register"""
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.READ_SINGLE_REGISTER_STRUCTURE.value,
            discovered_register.type.value,
            discovered_register.address >> 8,
            discovered_register.address & 0xFF,
        ]

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

    def __send_finalize_discovery_handler(self, discovered_device: DiscoveredDeviceRecord) -> None:
        if discovered_device.address == self.__ADDRESS_NOT_ASSIGNED:
            self.__write_discovered_device_new_address(
                discovered_device=discovered_device,
                discovered_registers=self.__pairing_device_registers,
            )

        else:
            self.__write_discovered_device_state(
                discovered_device=discovered_device,
                discovered_registers=self.__pairing_device_registers,
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
            register_record = self.__registers_registry.get_by_address(
                device_id=discovered_device.id,
                register_type=registers_type,
                register_address=i,
            )

            if register_record is not None:
                if registers_type == RegisterType.INPUT:
                    # Update register record in registry
                    self.__pairing_device_registers.add(
                        DiscoveredInputRegisterRecord(
                            register_id=register_record.id,
                            register_address=register_record.address,
                            # Reset register configuration
                            register_data_type=register_data_type,
                        )
                    )

                elif registers_type == RegisterType.OUTPUT:
                    # Update register record in registry
                    self.__pairing_device_registers.add(
                        DiscoveredOutputRegisterRecord(
                            register_id=register_record.id,
                            register_address=register_record.address,
                            # Reset register configuration
                            register_data_type=register_data_type,
                        )
                    )

                elif registers_type == RegisterType.ATTRIBUTE:
                    # Update register record in registry
                    self.__pairing_device_registers.add(
                        DiscoveredAttributeRegisterRecord(
                            register_id=register_record.id,
                            register_address=register_record.address,
                            # Reset register configuration
                            register_data_type=register_data_type,
                            register_name=None,
                            register_settable=False,
                            register_queryable=False,
                        )
                    )

            else:
                if registers_type == RegisterType.INPUT:
                    # Create register record in registry
                    self.__pairing_device_registers.add(
                        DiscoveredInputRegisterRecord(
                            register_id=uuid.uuid4(),
                            register_address=i,
                            register_data_type=register_data_type,
                        )
                    )

                elif registers_type == RegisterType.OUTPUT:
                    # Create register record in registry
                    self.__pairing_device_registers.add(
                        DiscoveredOutputRegisterRecord(
                            register_id=uuid.uuid4(),
                            register_address=i,
                            register_data_type=register_data_type,
                        )
                    )

                elif registers_type == RegisterType.ATTRIBUTE:
                    # Create register record in registry
                    self.__pairing_device_registers.add(
                        DiscoveredAttributeRegisterRecord(
                            register_id=uuid.uuid4(),
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
        """Discovered device is without address. Let's try to write new address to device"""
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
                "Register with stored address could not be loaded. Pairing couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                    },
                },
            )

            return

        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.WRITE_SINGLE_REGISTER_VALUE.value,
            address_register.type.value,
            address_register.address >> 8,
            address_register.address & 0xFF,
        ]

        transformed_value = ValueTransformHelpers.transform_to_bytes(
            data_type=address_register.data_type,
            value=5,  # TODO: Search for free address  # pylint: disable=fixme
        )

        # Value could not be transformed
        if transformed_value is None:
            self.__logger.warning(
                "New device address couldn't be transformed for transfer. Pairing couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                    },
                },
            )

            return

        for value in transformed_value:
            output_content.append(value)

        # Data to write are ready to be broadcast, lets persist device into registry
        self.__finalize_device(discovered_device=discovered_device, discovered_registers=discovered_registers)

        # After device update their address, it should be restarted in running mode
        self.__client.broadcast_packet(payload=output_content, waiting_time=self.__BROADCAST_WAITING_DELAY)

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
                "Register with stored state could not be loaded. Pairing couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                    },
                },
            )

            return

        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.WRITE_SINGLE_REGISTER_VALUE.value,
            state_register.type.value,
            state_register.address >> 8,
            state_register.address & 0xFF,
        ]

        transformed_value = ValueTransformHelpers.transform_to_bytes(
            data_type=state_register.data_type,
            value=StateTransformHelpers.transform_for_device(device_state=ConnectionState.RUNNING).value,
        )

        # Value could not be transformed
        if transformed_value is None:
            self.__logger.warning(
                "Device state couldn't be transformed for transfer. Pairing couldn't be finished",
                extra={
                    "device": {
                        "serial_number": discovered_device.serial_number,
                    },
                },
            )

            return

        for value in transformed_value:
            output_content.append(value)

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
        device_record = self.__devices_registry.create_or_update(
            device_id=discovered_device.id,
            device_serial_number=discovered_device.serial_number,
            device_enabled=False,
            hardware_manufacturer=discovered_device.hardware_manufacturer,
            hardware_model=discovered_device.hardware_model,
            hardware_version=discovered_device.hardware_version,
            firmware_manufacturer=discovered_device.firmware_manufacturer,
            firmware_version=discovered_device.firmware_version,
        )

        for register in discovered_registers:
            if isinstance(register, (DiscoveredInputRegisterRecord, DiscoveredOutputRegisterRecord)):
                self.__registers_registry.create_or_update(
                    device_id=device_record.id,
                    register_id=register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_data_type=register.data_type,
                )

            elif isinstance(register, DiscoveredAttributeRegisterRecord):
                self.__registers_registry.create_or_update(
                    device_id=device_record.id,
                    register_id=register.id,
                    register_type=register.type,
                    register_address=register.address,
                    register_data_type=register.data_type,
                    register_name=register.name,
                    register_queryable=register.queryable,
                    register_settable=register.settable,
                )

        # Device initialization is finished, enable it for communication
        self.__devices_registry.enable(device=device_record)

        # Update device state
        self.__devices_registry.set_state(device=device_record, state=ConnectionState.UNKNOWN)
