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
FastyBird BUS connector plugin client publishers module publisher for API v1
"""

# Python base dependencies
import time
from datetime import datetime
from typing import List, Optional, Union

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.clients.client import Client
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.publishers.base import BasePublisher
from fb_bus_connector_plugin.registry.model import DevicesRegistry, RegistersRegistry
from fb_bus_connector_plugin.registry.records import DeviceRecord, RegisterRecord
from fb_bus_connector_plugin.types import (
    ButtonPayloadType,
    DeviceDataType,
    Packet,
    ProtocolVersion,
    RegisterType,
    SwitchPayloadType,
    WriteKeyType,
)
from fb_bus_connector_plugin.utilities.helpers import DataTransformHelpers


@inject(alias=BasePublisher)
class ApiV1Publisher(BasePublisher):  # pylint: disable=too-few-public-methods
    """
    BUS publisher for API v1

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         publishers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __MAX_TRANSMIT_ATTEMPTS: int = 5  # Maximum count of sending packets before gateway mark device as lost

    __PING_DELAY: float = 15.0  # Delay in s after reaching maximum packet sending attempts

    __PACKET_RESPONSE_DELAY: float = 0.5  # Waiting delay before another packet is sent
    __PACKET_RESPONSE_WAITING_TIME: float = 0.5

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    __client: Client

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        client: Client,
        logger: Logger,
    ) -> None:
        super().__init__(logger=logger)

        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

        self.__client = client

    # -----------------------------------------------------------------------------

    def handle(self, device: DeviceRecord) -> bool:  # pylint: disable=too-many-return-statements
        """Handle publish read or write message to device"""
        # Maximum send packet attempts was reached device is now marked as lost
        if device.transmit_attempts >= self.__MAX_TRANSMIT_ATTEMPTS:
            if device.is_lost:
                self.__devices_registry.reset_communication(device=device)

                self._logger.debug("Device with address: %s is still lost", device.address)

            else:
                self._logger.debug("Device with address: %s is lost", device.address)

                self.__devices_registry.set_device_is_lost(device=device)

            return True

        # If device is marked as lost...
        if device.is_lost:
            # ...and wait for lost delay...
            if (time.time() - device.last_packet_timestamp) >= self.__PING_DELAY:
                # ...then try to PING device
                self.__send_ping_handler(device=device)

            return True

        # Check for delay between reading
        if device.waiting_for_packet is None or (
            device.waiting_for_packet is not None
            and time.time() - device.last_packet_timestamp >= self.__PACKET_RESPONSE_DELAY
        ):
            # Device state is unknown...
            if device.is_unknown:
                # ...ask device for its state
                self.__send_read_device_state_handler(device=device)

                return True

            # Check if device is in RUNNING mode
            if not device.is_running:
                return False

            if self.__write_registers_keys_handler(device=device):
                return True

            if time.time() - device.get_last_register_reading_timestamp() >= device.sampling_time:
                if self.__read_registers_handler(device=device):
                    return True

            if self.__write_register_handler(device=device):
                return True

        return False

    # -----------------------------------------------------------------------------

    def version(self) -> ProtocolVersion:
        """Pairing supported protocol version"""
        return ProtocolVersion.V1

    # -----------------------------------------------------------------------------

    def __write_registers_keys_handler(self, device: DeviceRecord) -> bool:
        # Check if device has PUB/SUB support
        if not device.pub_sub_pub_support:
            return False

        registers = self.__registers_registry.get_all_for_device(device_id=device.id)

        for register in registers:
            if (
                register.pubsub_key_written == WriteKeyType.NO
                and not register.waiting_for_data
                and register.key is not None
            ):
                self.__write_key_to_register(device=device, register=register)

                return True

        return False

    # -----------------------------------------------------------------------------

    def __read_registers_handler(self, device: DeviceRecord) -> bool:
        reading_address, reading_register_type = device.get_reading_register()

        for register_type in RegisterType:
            if len(
                self.__registers_registry.get_all_for_device(device_id=device.id, register_type=register_type)
            ) > 0 and (reading_register_type == register_type or reading_register_type is None):
                return self.__read_multiple_registers(
                    device=device,
                    register_type=register_type,
                    start_address=reading_address,
                )

        return False

    # -----------------------------------------------------------------------------

    def __write_register_handler(self, device: DeviceRecord) -> bool:
        for register_type in (RegisterType.OUTPUT, RegisterType.ATTRIBUTE, RegisterType.SETTING):
            if self.__write_single_register_handler(device=device, register_type=register_type):
                return True

        return False

    # -----------------------------------------------------------------------------

    def __send_ping_handler(self, device: DeviceRecord) -> None:
        # 0 => Packet identifier
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.PING.value,
        ]

        result = self.__client.send_packet(
            address=device.address,
            payload=output_content,
            client_id=device.client_id,
        )

        self.__validate_result(result=result, packet_type=Packet.PONG, device=device)

    # -----------------------------------------------------------------------------

    def __send_read_device_state_handler(self, device: DeviceRecord) -> None:
        # 0 => Packet identifier
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.READ_STATE.value,
        ]

        result = self.__client.send_packet(
            address=device.address,
            payload=output_content,
            waiting_time=1,
            client_id=device.client_id,
        )

        self.__validate_result(result=result, packet_type=Packet.READ_STATE, device=device)

    # -----------------------------------------------------------------------------

    def __read_multiple_registers(
        self,
        device: DeviceRecord,
        register_type: RegisterType,
        start_address: Optional[int],
    ) -> bool:
        register_size = len(
            self.__registers_registry.get_all_for_device(device_id=device.id, register_type=register_type)
        )

        if start_address is None:
            start_address = 0

        # 0 => Packet identifier
        # 1 => Register type
        # 2 => High byte of register address
        # 3 => Low byte of register address
        # 4 => High byte of registers length
        # 5 => Low byte of registers length
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.READ_MULTIPLE_REGISTERS.value,
            register_type.value,
            start_address >> 8,
            start_address & 0xFF,
        ]

        if register_type in (RegisterType.INPUT, RegisterType.OUTPUT):
            # Calculate maximum count registers per one packet
            # eg. max_packet_length = 24 => max_readable_registers_count = 4
            #   - only 4 registers could be read in one packet
            max_readable_registers_count = (device.max_packet_length - 8) // 4

        else:
            return False

        # Calculate reading address based on maximum reading length and start address
        # eg. start_address = 0 and max_readable_registers_count = 3 => max_readable_addresses = 2
        # eg. start_address = 3 and max_readable_registers_count = 3 => max_readable_addresses = 5
        # eg. start_address = 0 and max_readable_registers_count = 8 => max_readable_addresses = 7
        max_readable_addresses = start_address + max_readable_registers_count - 1

        if (max_readable_addresses + 1) >= register_size:
            if start_address == 0:
                read_length = register_size
                next_address = start_address + read_length

            else:
                read_length = register_size - start_address
                next_address = start_address + read_length

        else:
            read_length = max_readable_registers_count
            next_address = start_address + read_length

        # Validate registers reading length
        if read_length <= 0:
            return False

        output_content.append(read_length >> 8)
        output_content.append(read_length & 0xFF)

        result = self.__client.send_packet(
            address=device.address,
            payload=output_content,
            client_id=device.client_id,
        )

        self.__validate_result(result=result, packet_type=Packet.READ_MULTIPLE_REGISTERS, device=device)

        if result is True:
            # ...and update reading pointer
            device = self.__devices_registry.set_reading_register(
                device=device,
                register_address=next_address,
                register_type=register_type,
            )

            # Check pointer against to registers size
            if (next_address + 1) > register_size:
                self.__update_reading_pointer(device=device)

        return True

    # -----------------------------------------------------------------------------

    def __write_single_register_handler(self, device: DeviceRecord, register_type: RegisterType) -> bool:
        registers = self.__registers_registry.get_all_for_device(
            device_id=device.id,
            register_type=register_type,
        )

        for register in registers:
            if register.expected_value is not None and register.expected_pending is None:
                if self.__write_value_to_single_register(
                    device=device,
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
        register: RegisterRecord,
        write_value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime],
    ) -> bool:
        # 0     => Packet identifier
        # 1     => Register type
        # 2     => High byte of register address
        # 3     => Low byte of register address
        # 4-n   => Write value
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.WRITE_SINGLE_REGISTER.value,
            register.type.value,
            register.address >> 8,
            register.address & 0xFF,
        ]

        if (
            register.data_type
            in (
                DeviceDataType.UINT8,
                DeviceDataType.UINT16,
                DeviceDataType.UINT32,
                DeviceDataType.INT8,
                DeviceDataType.INT16,
                DeviceDataType.INT32,
                DeviceDataType.FLOAT32,
                DeviceDataType.BOOLEAN,
                DeviceDataType.STRING,
                DeviceDataType.DATE,
                DeviceDataType.TIME,
                DeviceDataType.DATETIME,
            )
            and isinstance(write_value, (int, float, bool))
        ):
            transformed_value = DataTransformHelpers.transform_value_to_bytes(
                data_type=register.data_type,
                value=write_value,
            )

            # Value could not be transformed
            if transformed_value is None:
                return False

            for value in transformed_value:
                output_content.append(value)

        else:
            self._logger.error("Trying to write unsupported data type: %s for register", register.data_type)

            return False

        result = self.__client.send_packet(
            address=device.address,
            payload=output_content,
            waiting_time=self.__PACKET_RESPONSE_WAITING_TIME,
            client_id=device.client_id,
        )

        self.__validate_result(result=result, packet_type=Packet.WRITE_SINGLE_REGISTER, device=device)

        return result

    # -----------------------------------------------------------------------------

    def __write_key_to_register(
        self,
        device: DeviceRecord,
        register: RegisterRecord,
    ) -> bool:
        if register.key is None:
            return False

        # 0   => Packet identifier
        # 1   => Registers type
        # 2   => High byte of registers address
        # 3   => Low byte of registers address
        # 4-n => Key string
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.PUB_SUB_WRITE_REGISTER_KEY.value,
            register.type.value,
            register.address >> 8,
            register.address & 0xFF,
            len(register.key),
        ]

        for char in register.key:
            output_content.append(ord(char))

        result = self.__client.send_packet(
            address=device.address,
            payload=output_content,
            waiting_time=self.__PACKET_RESPONSE_WAITING_TIME,
            client_id=device.client_id,
        )

        self.__validate_result(result=result, packet_type=Packet.PUB_SUB_WRITE_REGISTER_KEY, device=device)

        if result is True:
            self.__registers_registry.set_waiting_for_data(
                register=register,
                waiting_for_data=True,
            )

        return result

    # -----------------------------------------------------------------------------

    def __validate_result(self, result: bool, packet_type: Packet, device: DeviceRecord) -> None:
        if result is True:
            # Mark that gateway is waiting for reply from device...
            self.__devices_registry.set_waiting_for_packet(device=device, packet_type=packet_type)

        else:
            # Mark that gateway is waiting for reply from device...
            self.__devices_registry.set_waiting_for_packet(device=device, packet_type=None)

    # -----------------------------------------------------------------------------

    def __update_reading_pointer(self, device: DeviceRecord) -> None:
        _, reading_register_type = device.get_reading_register()

        if reading_register_type is not None:
            if reading_register_type == RegisterType.INPUT:
                if (
                    len(
                        self.__registers_registry.get_all_for_device(
                            device_id=device.id, register_type=RegisterType.OUTPUT
                        )
                    )
                    > 0
                ):
                    self.__devices_registry.set_reading_register(
                        device=device,
                        register_address=0,
                        register_type=RegisterType.OUTPUT,
                    )

                    return

        self.__devices_registry.reset_reading_register(device=device)
