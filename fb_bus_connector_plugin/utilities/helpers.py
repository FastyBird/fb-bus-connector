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
FastyBird BUS connector plugin helpers
"""

# Python base dependencies
import struct
from datetime import datetime
from typing import Dict, List, Optional, Union

# Library dependencies
from fastnumbers import fast_float, fast_int
from modules_metadata.devices_module import DeviceConnectionState
from modules_metadata.types import ButtonPayload, DataType, SwitchPayload

# Library libs
from fb_bus_connector_plugin.exceptions import InvalidArgumentException
from fb_bus_connector_plugin.types import (
    ButtonPayloadType,
    ConnectionState,
    DeviceDataType,
    Packet,
    PacketContent,
    SwitchPayloadType,
)


class TextHelpers:
    """
    Payload text helpers

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         utilities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @staticmethod
    def extract_text_from_payload(payload: bytearray, start_pointer: int, length: Optional[int] = None) -> str:
        """Extract text from provided payload"""
        char_list: List[str] = []

        count = 0

        for i in range(start_pointer, len(payload)):
            if (
                PacketContent.has_value(int(payload[i])) and PacketContent(int(payload[i])) == PacketContent.DATA_SPACE
            ) or (length is not None and count == length):
                break

            char_list.append(chr(int(payload[i])))
            count += 1

        return "".join(char_list)

    # -----------------------------------------------------------------------------

    @staticmethod
    def find_space_in_payload(payload: bytearray, start_pointer: int) -> int:
        """Find space character position in provided payload"""
        for i in range(start_pointer, len(payload)):
            if PacketContent.has_value(int(payload[i])) and PacketContent(int(payload[i])) == PacketContent.DATA_SPACE:
                return i

        return -1

    # -----------------------------------------------------------------------------


class StateHelpers:
    """
    Device state helpers

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         utilities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @staticmethod
    def transform_state_for_gateway(device_state: ConnectionState) -> DeviceConnectionState:
        """Transform connector device state representation to application device state"""
        if device_state == ConnectionState.RUNNING:
            # Device is running and ready for operate
            return DeviceConnectionState.RUNNING

        if device_state == ConnectionState.STOPPED:
            # Device is actually stopped
            return DeviceConnectionState.STOPPED

        if device_state == ConnectionState.PAIRING:
            # Device is actually stopped
            return DeviceConnectionState.INIT

        if device_state == ConnectionState.ERROR:
            # Device is actually stopped
            return DeviceConnectionState.ALERT

        # Device is in unknown state
        return DeviceConnectionState.UNKNOWN

    # -----------------------------------------------------------------------------

    @staticmethod
    def transform_state_for_device(device_state: DeviceConnectionState) -> Optional[ConnectionState]:
        """Transform application device state representation to connector device state"""
        if device_state == DeviceConnectionState.RUNNING:
            return ConnectionState.RUNNING

        if device_state == DeviceConnectionState.STOPPED:
            return ConnectionState.STOPPED

        # Unsupported state
        return None


class DataTypeHelpers:
    """
    Register data type helpers

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         utilities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @staticmethod
    def transform_for_gateway(  # pylint: disable=too-many-return-statements
        data_type: DeviceDataType,
    ) -> DataType:
        """Transform connector data type representation to application data type"""
        if data_type == DeviceDataType.INT8:
            return DataType.CHAR

        if data_type == DeviceDataType.UINT8:
            return DataType.UCHAR

        if data_type == DeviceDataType.INT16:
            return DataType.SHORT

        if data_type == DeviceDataType.UINT16:
            return DataType.USHORT

        if data_type == DeviceDataType.INT32:
            return DataType.INT

        if data_type == DeviceDataType.UINT32:
            return DataType.UINT

        if data_type == DeviceDataType.FLOAT32:
            return DataType.FLOAT

        if data_type == DeviceDataType.BOOLEAN:
            return DataType.BOOLEAN

        if data_type == DeviceDataType.STRING:
            return DataType.STRING

        if data_type == DeviceDataType.BUTTON:
            return DataType.BUTTON

        if data_type == DeviceDataType.SWITCH:
            return DataType.SWITCH

        raise InvalidArgumentException("Gateway item data type is not supported by this connector")

    # -----------------------------------------------------------------------------

    @staticmethod
    def transform_for_device(  # pylint: disable=too-many-return-statements
        data_type: DataType,
    ) -> DeviceDataType:
        """Transform application data type representation to connector data type"""
        if data_type == DataType.CHAR:
            return DeviceDataType.INT8

        if data_type == DataType.UCHAR:
            return DeviceDataType.UINT8

        if data_type == DataType.SHORT:
            return DeviceDataType.INT16

        if data_type == DataType.USHORT:
            return DeviceDataType.UINT16

        if data_type == DataType.INT:
            return DeviceDataType.INT32

        if data_type == DataType.UINT:
            return DeviceDataType.UINT32

        if data_type == DataType.FLOAT:
            return DeviceDataType.FLOAT32

        if data_type == DataType.BOOLEAN:
            return DeviceDataType.BOOLEAN

        if data_type == DataType.STRING:
            return DeviceDataType.STRING

        if data_type == DataType.BUTTON:
            return DeviceDataType.BUTTON

        if data_type == DataType.SWITCH:
            return DeviceDataType.SWITCH

        raise InvalidArgumentException("Connector item data type is not supported by this connector")


class DataTransformHelpers:
    """
    Value transformers helpers

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         utilities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @staticmethod
    def transform_value_from_bytes(  # pylint: disable=too-many-return-statements,too-many-branches
        data_type: DeviceDataType,
        value: List[int],
    ) -> Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None]:
        """Transform value from received bytes to plain number"""
        if data_type == DeviceDataType.FLOAT32:
            [transformed] = struct.unpack("<f", bytearray(value[0:4]))  # pylint: disable=no-member

            return fast_float(transformed)

        if data_type in (DeviceDataType.UINT8, DeviceDataType.UINT16, DeviceDataType.UINT32):
            [transformed] = struct.unpack("<I", bytearray(value[0:4]))  # pylint: disable=no-member

            return fast_int(transformed)

        if data_type in (DeviceDataType.INT8, DeviceDataType.INT16, DeviceDataType.INT32):
            [transformed] = struct.unpack("<i", bytearray(value[0:4]))  # pylint: disable=no-member

            return fast_int(transformed)

        if data_type == DeviceDataType.BOOLEAN:
            [transformed] = struct.unpack("<I", bytearray(value[0:4]))  # pylint: disable=no-member

            return fast_int(transformed) == 0xFF00

        if data_type == DeviceDataType.BUTTON:
            [transformed] = struct.unpack("<I", bytearray(value[0:4]))  # pylint: disable=no-member

            if ButtonPayloadType.has_value(fast_int(transformed)):
                return ButtonPayloadType(fast_int(transformed))

        if data_type == DeviceDataType.SWITCH:
            [transformed] = struct.unpack("<I", bytearray(value[0:4]))  # pylint: disable=no-member

            if SwitchPayloadType.has_value(fast_int(transformed)):
                return SwitchPayloadType(fast_int(transformed))

        if data_type == DeviceDataType.STRING:
            return TextHelpers.extract_text_from_payload(payload=bytearray(value), start_pointer=0)

        if data_type == DeviceDataType.DATE:
            date = TextHelpers.extract_text_from_payload(payload=bytearray(value), start_pointer=0)

            try:
                return datetime.strptime(date, "%Y-%m-%d")

            except ValueError:
                return None

        if data_type == DeviceDataType.TIME:
            time = TextHelpers.extract_text_from_payload(payload=bytearray(value), start_pointer=0)

            try:
                return datetime.strptime(time, "%H:%M:%S%z")

            except ValueError:
                return None

        if data_type == DeviceDataType.DATETIME:
            date_time = TextHelpers.extract_text_from_payload(payload=bytearray(value), start_pointer=0)

            try:
                return datetime.strptime(date_time, r"%Y-%m-%d\T%H:%M:%S%z")

            except ValueError:
                return None

        return None

    # -----------------------------------------------------------------------------

    @staticmethod
    def transform_value_to_bytes(  # pylint: disable=too-many-return-statements,too-many-branches
        data_type: DeviceDataType,
        value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime],
    ) -> Optional[bytes]:
        """Transform value to bytes representation"""
        if data_type == DeviceDataType.FLOAT32:
            return struct.pack(  # pylint: disable=no-member
                "<f",
                (value if isinstance(value, float) else fast_float(str(value))),  # type: ignore[arg-type]
            )

        if data_type in (
            DeviceDataType.UINT8,
            DeviceDataType.UINT16,
            DeviceDataType.UINT32,
        ):
            return struct.pack(  # pylint: disable=no-member
                "<I",
                (value if isinstance(value, int) else fast_int(str(value))),  # type: ignore[arg-type]
            )

        if data_type in (DeviceDataType.INT8, DeviceDataType.INT16, DeviceDataType.INT32):
            return struct.pack(  # pylint: disable=no-member
                "<i",
                (value if isinstance(value, int) else fast_int(str(value))),  # type: ignore[arg-type]
            )

        if data_type == DeviceDataType.BOOLEAN:
            return struct.pack("<I", 0xFF00 if bool(value) is True else 0x0000)  # pylint: disable=no-member

        if data_type == DeviceDataType.BUTTON:
            return struct.pack(  # pylint: disable=no-member
                "<I",
                (value if isinstance(value, int) else fast_int(str(value))),  # type: ignore[arg-type]
            )

        if data_type == DeviceDataType.SWITCH:
            return struct.pack(  # pylint: disable=no-member
                "<I",
                (value if isinstance(value, int) else fast_int(str(value))),  # type: ignore[arg-type]
            )

        if data_type == DeviceDataType.STRING:
            return bytearray(str(value).encode())

        if data_type == DeviceDataType.DATE:
            if isinstance(value, datetime):
                return bytearray(value.strftime("%Y-%m-%d").encode())

            try:
                return bytearray(datetime.strptime(str(value), "%Y-%m-%d").strftime("%Y-%m-%d").encode())

            except ValueError:
                return None

        if data_type == DeviceDataType.TIME:
            if isinstance(value, datetime):
                return bytearray(value.strftime("%H:%M:%S%z").encode())

            try:
                return bytearray(datetime.strptime(str(value), "%H:%M:%S%z").strftime("%H:%M:%S%z").encode())

            except ValueError:
                return None

        if data_type == DeviceDataType.DATETIME:
            if isinstance(value, datetime):
                return bytearray(value.strftime(r"%Y-%m-%d\T%H:%M:%S%z").encode())

            try:
                return bytearray(
                    datetime.strptime(str(value), r"%Y-%m-%d\T%H:%M:%S%z").strftime(r"%Y-%m-%d\T%H:%M:%S%z").encode()
                )

            except ValueError:
                return None

        return None

    # -----------------------------------------------------------------------------

    @staticmethod
    def transform_for_device(  # pylint: disable=too-many-branches,too-many-return-statements
        data_type: DeviceDataType, value: Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime, None]
    ) -> Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None]:
        """Transform gateway value to device value"""
        if value is None:
            return None

        if data_type == DeviceDataType.FLOAT32:
            return value if isinstance(value, float) else fast_float(str(value))  # type: ignore[arg-type]

        if data_type in (
            DeviceDataType.UINT8,
            DeviceDataType.INT8,
            DeviceDataType.UINT16,
            DeviceDataType.INT16,
            DeviceDataType.UINT32,
            DeviceDataType.INT32,
        ):
            return value if isinstance(value, int) else fast_int(str(value))  # type: ignore[arg-type]

        if data_type == DeviceDataType.BOOLEAN:
            return value if isinstance(value, bool) else bool(value)

        if data_type == DeviceDataType.STRING:
            return value if isinstance(value, str) else str(value)

        if data_type == DeviceDataType.DATE:
            try:
                return value if isinstance(value, datetime) else datetime.strptime(str(value), "%Y-%m-%d")

            except ValueError:
                return None

        if data_type == DeviceDataType.DATETIME:
            try:
                return value if isinstance(value, datetime) else datetime.strptime(str(value), r"%Y-%m-%d\T%H:%M:%S%z")

            except ValueError:
                return None

        if data_type == DeviceDataType.TIME:
            try:
                return value if isinstance(value, datetime) else datetime.strptime(str(value), "%H:%M:%S%z")

            except ValueError:
                return None

        if data_type == DeviceDataType.BUTTON:
            if ButtonPayloadType.has_value(int(str(value))):
                return ButtonPayloadType(int(str(value)))

        if data_type == DeviceDataType.SWITCH:
            if SwitchPayloadType.has_value(int(str(value))):
                return SwitchPayloadType(int(str(value)))

        return None


class PacketsHelpers:  # pylint: disable=too-few-public-methods
    """
    Packets helpers

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         utilities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    PACKET_NAMES: Dict[Packet, str] = {
        Packet.PING: "FB_PACKET_PING",
        Packet.PONG: "FB_PACKET_PONG",
        Packet.EXCEPTION: "FB_PACKET_EXCEPTION",
        Packet.DISCOVER: "FB_PACKET_DISCOVER",
        Packet.READ_SINGLE_REGISTER: "FB_PACKET_READ_SINGLE_REGISTER",
        Packet.READ_MULTIPLE_REGISTERS: "FB_PACKET_READ_MULTIPLE_REGISTERS",
        Packet.WRITE_SINGLE_REGISTER: "FB_PACKET_WRITE_SINGLE_REGISTER",
        Packet.WRITE_MULTIPLE_REGISTERS: "FB_PACKET_WRITE_MULTIPLE_REGISTERS",
        Packet.REPORT_SINGLE_REGISTER: "FB_PACKET_REPORT_SINGLE_REGISTER",
        Packet.READ_STATE: "FB_PACKET_READ_STATE",
        Packet.WRITE_STATE: "FB_PACKET_WRITE_STATE",
        Packet.REPORT_STATE: "FB_PACKET_REPORT_STATE",
        Packet.PUB_SUB_READ_REGISTER_KEY: "FB_PACKET_PUB_SUB_READ_REGISTER_KEY",
        Packet.PUB_SUB_WRITE_REGISTER_KEY: "FB_PACKET_PUB_SUB_WRITE_REGISTER_KEY",
        Packet.PUB_SUB_BROADCAST_REGISTER_VALUE: "FB_PACKET_PUB_SUB_BROADCAST_REGISTER_VALUE",
        Packet.PUB_SUB_SUBSCRIBE: "FB_PACKET_PUB_SUB_SUBSCRIBE",
        Packet.PUB_SUB_UNSUBSCRIBE: "FB_PACKET_PUB_SUB_UNSUBSCRIBE",
    }

    @classmethod
    def get_packet_name(cls, packet: Packet) -> str:
        """Transform packet value to text representation"""
        if packet in cls.PACKET_NAMES:
            return cls.PACKET_NAMES[packet]

        return "UNKNOWN"
