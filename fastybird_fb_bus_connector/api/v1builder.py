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
FastyBird BUS connector api module builder for API v1
"""

# Python base dependencies
from datetime import datetime
from typing import List, Optional, Union

# Library dependencies
from fastybird_metadata.devices_module import ConnectionState
from fastybird_metadata.types import ButtonPayload, DataType, SwitchPayload

# Library libs
from fastybird_fb_bus_connector.exceptions import BuildPayloadException
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


class V1Builder:
    """
    BUS payload builder

    @package        FastyBird:FbBusConnector!
    @module         api/v1builder

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @staticmethod
    def build_ping() -> List[int]:
        """Build payload for device ping&pong"""
        return [
            ProtocolVersion.V1.value,
            Packet.PING.value,
        ]

    # -----------------------------------------------------------------------------

    @staticmethod
    def build_discovery() -> List[int]:
        """Build payload for device discover"""
        return [
            ProtocolVersion.V1.value,
            Packet.DISCOVER.value,
        ]

    # -----------------------------------------------------------------------------

    @staticmethod
    def build_read_single_register_value(
        register_type: RegisterType,
        register_address: int,
    ) -> List[int]:
        """Build payload for single register value reading"""
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.READ_SINGLE_REGISTER_VALUE.value,
            register_type.value,
            register_address >> 8,
            register_address & 0xFF,
        ]

        return output_content

    # -----------------------------------------------------------------------------

    @staticmethod
    def build_read_multiple_registers_values(
        register_type: RegisterType,
        start_address: int,
        registers_count: int,
    ) -> List[int]:
        """Build payload for multiple registers values reading"""
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.READ_MULTIPLE_REGISTERS_VALUES.value,
            register_type.value,
            start_address >> 8,
            start_address & 0xFF,
            registers_count >> 8,
            registers_count & 0xFF,
        ]

        return output_content

    # -----------------------------------------------------------------------------

    @staticmethod
    def build_read_single_register_structure(
        register_type: RegisterType,
        register_address: int,
        serial_number: Optional[str] = None,
    ) -> List[int]:
        """Build payload for single register structure reading"""
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.READ_SINGLE_REGISTER_STRUCTURE.value,
            register_type.value,
            register_address >> 8,
            register_address & 0xFF,
        ]

        if serial_number is not None:
            output_content.append(len(serial_number))

            for char in serial_number:
                output_content.append(ord(char))

        return output_content

    # -----------------------------------------------------------------------------

    @staticmethod
    def build_write_single_register_value(  # pylint: disable=too-many-arguments
        register_type: RegisterType,
        register_address: int,
        register_data_type: DataType,
        register_name: Optional[str],
        write_value: Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime],
        serial_number: Optional[str] = None,
    ) -> List[int]:
        """Build payload for single register value writing"""
        output_content: List[int] = [
            ProtocolVersion.V1.value,
            Packet.WRITE_SINGLE_REGISTER_VALUE.value,
            register_type.value,
            register_address >> 8,
            register_address & 0xFF,
        ]

        if (
            register_data_type
            in (
                DataType.CHAR,
                DataType.UCHAR,
                DataType.SHORT,
                DataType.USHORT,
                DataType.INT,
                DataType.UINT,
                DataType.FLOAT,
                DataType.BOOLEAN,
            )
            and isinstance(write_value, (int, float, bool))
        ):
            transformed_value = ValueTransformHelpers.transform_to_bytes(
                data_type=register_data_type,
                value=write_value,
            )

            # Value could not be transformed
            if transformed_value is None:
                raise BuildPayloadException("Value to be written into register could not be transformed")

            for value in transformed_value:
                output_content.append(value)

        # SPECIAL TRANSFORMING FOR STATE ATTRIBUTE
        elif (
            register_data_type == DataType.ENUM
            and register_type == RegisterType.ATTRIBUTE
            and register_name == DeviceAttribute.STATE.value
        ):
            transformed_value = ValueTransformHelpers.transform_to_bytes(
                data_type=DataType.UCHAR,
                value=StateTransformHelpers.transform_for_device(device_state=ConnectionState(write_value)).value,
            )

            # Value could not be transformed
            if transformed_value is None:
                raise BuildPayloadException("Value to be written into register could not be transformed")

            for value in transformed_value:
                output_content.append(value)

        else:
            raise BuildPayloadException("Unsupported register data type")

        if serial_number is not None:
            output_content.append(len(serial_number))

            for char in serial_number:
                output_content.append(ord(char))

        return output_content
