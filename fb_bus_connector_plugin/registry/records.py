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
FastyBird BUS connector plugin registry module records
"""

# pylint: disable=too-many-lines

# Python base dependencies
import time
import uuid
from abc import ABC
from datetime import datetime
from typing import Optional, Tuple, Union

# Library libs
from fb_bus_connector_plugin.types import (
    ButtonPayloadType,
    ConnectionState,
    DeviceDataType,
    Packet,
    RegisterType,
    SwitchPayloadType,
    WriteKeyType,
)


class DeviceRecord:  # pylint: disable=too-many-public-methods,too-many-instance-attributes
    """
    Device record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __client_id: uuid.UUID

    __id: uuid.UUID
    __address: int
    __serial_number: str

    __max_packet_length: int

    __pub_sub_pub_support: bool = False
    __pub_sub_sub_support: bool = False
    __pub_sub_sub_max_subscriptions: int = 0
    __pub_sub_sub_max_conditions: int = 0
    __pub_sub_sub_max_actions: int = 0

    __hardware_manufacturer: Optional[str] = None
    __hardware_model: Optional[str] = None
    __hardware_version: Optional[str] = None

    __firmware_manufacturer: Optional[str] = None
    __firmware_version: Optional[str] = None

    __enabled: bool = False
    __ready: bool = False

    __waiting_for_packet: Optional[Packet] = None
    __last_packet_sent_timestamp: float = 0.0  # Timestamp when request was sent to the device

    __attempts: int = 0

    __sampling_time: float = 10.0

    __reading_registers_timestamp: float = 0.0
    __reading_register_address: Optional[int] = None
    __reading_register_type: Optional[RegisterType] = None

    __lost_timestamp: float = 0.0

    __state: ConnectionState = ConnectionState.UNKNOWN

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        client_id: uuid.UUID,
        device_id: uuid.UUID,
        address: int,
        serial_number: str,
        max_packet_length: int,
        enabled: bool = False,
        pub_sub_pub_support: bool = False,
        pub_sub_sub_support: bool = False,
        pub_sub_sub_max_subscriptions: int = 0,
        pub_sub_sub_max_conditions: int = 0,
        pub_sub_sub_max_actions: int = 0,
        hardware_manufacturer: Optional[str] = None,
        hardware_model: Optional[str] = None,
        hardware_version: Optional[str] = None,
        firmware_manufacturer: Optional[str] = None,
        firmware_version: Optional[str] = None,
        ready: bool = False,
    ) -> None:
        self.__client_id = client_id

        self.__id = device_id
        self.__address = address
        self.__serial_number = serial_number
        self.__max_packet_length = max_packet_length
        self.__enabled = enabled

        self.__pub_sub_pub_support = pub_sub_pub_support
        self.__pub_sub_sub_support = pub_sub_sub_support
        self.__pub_sub_sub_max_subscriptions = pub_sub_sub_max_subscriptions
        self.__pub_sub_sub_max_conditions = pub_sub_sub_max_conditions
        self.__pub_sub_sub_max_actions = pub_sub_sub_max_actions

        self.__hardware_manufacturer = hardware_manufacturer
        self.__hardware_model = hardware_model
        self.__hardware_version = hardware_version

        self.__firmware_manufacturer = firmware_manufacturer
        self.__firmware_version = firmware_version

        self.__ready = ready

    # -----------------------------------------------------------------------------

    @property
    def client_id(self) -> uuid.UUID:
        """Connector unique identifier"""
        return self.__client_id

    # -----------------------------------------------------------------------------

    @property
    def id(self) -> uuid.UUID:  # pylint: disable=invalid-name
        """Device unique identifier"""
        return self.__id

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Device communication address"""
        return self.__address

    # -----------------------------------------------------------------------------

    @property
    def serial_number(self) -> str:
        """Device unique serial number"""
        return self.__serial_number

    # -----------------------------------------------------------------------------

    @property
    def max_packet_length(self) -> int:
        """Device maximum communication packet length"""
        return self.__max_packet_length

    # -----------------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Is device enabled?"""
        return self.__enabled

    # -----------------------------------------------------------------------------

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """Enable or disable device"""
        self.__enabled = enabled

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_pub_support(self) -> bool:
        """Has device PUB/SUB publish support?"""
        return self.__pub_sub_pub_support

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_sub_support(self) -> bool:
        """Has device PUB/SUB subscribe support?"""
        return self.__pub_sub_sub_support

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_sub_max_subscriptions(self) -> int:
        """Maximum supported pub/sub subscriptions count"""
        return self.__pub_sub_sub_max_subscriptions

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_sub_max_conditions(self) -> int:
        """Maximum supported pub/sub conditions count"""
        return self.__pub_sub_sub_max_conditions

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_sub_max_actions(self) -> int:
        """Maximum supported pub/sub action count"""
        return self.__pub_sub_sub_max_actions

    # -----------------------------------------------------------------------------

    @property
    def hardware_manufacturer(self) -> Optional[str]:
        """Hardware manufacturer"""
        return self.__hardware_manufacturer

    # -----------------------------------------------------------------------------

    @property
    def hardware_model(self) -> Optional[str]:
        """Hardware model"""
        return self.__hardware_model

    # -----------------------------------------------------------------------------

    @property
    def hardware_version(self) -> Optional[str]:
        """Hardware revision"""
        return self.__hardware_version

    # -----------------------------------------------------------------------------

    @property
    def firmware_manufacturer(self) -> Optional[str]:
        """Firmware manufacturer"""
        return self.__firmware_manufacturer

    # -----------------------------------------------------------------------------

    @property
    def firmware_version(self) -> Optional[str]:
        """Firmware version"""
        return self.__firmware_version

    # -----------------------------------------------------------------------------

    @property
    def ready(self) -> bool:
        """Is device ready for communication?"""
        return self.__ready

    # -----------------------------------------------------------------------------

    @ready.setter
    def ready(self, ready: bool) -> None:
        """Set device ready state"""
        self.__ready = ready

    # -----------------------------------------------------------------------------

    @property
    def last_packet_timestamp(self) -> float:
        """Last packet sent time stamp"""
        return self.__last_packet_sent_timestamp

    # -----------------------------------------------------------------------------

    @property
    def waiting_for_packet(self) -> Optional[Packet]:
        """Packet gateway is waiting from device"""
        return self.__waiting_for_packet

    # -----------------------------------------------------------------------------

    @waiting_for_packet.setter
    def waiting_for_packet(self, waiting_for_packet: Optional[Packet]) -> None:
        """Set that gateway is waiting for specific packet from device"""
        self.__waiting_for_packet = waiting_for_packet

        if waiting_for_packet is not None:
            self.__last_packet_sent_timestamp = time.time()
            self.__attempts = self.__attempts + 1

    # -----------------------------------------------------------------------------

    @property
    def transmit_attempts(self) -> int:
        """Transmit packet attempts count"""
        return self.__attempts

    # -----------------------------------------------------------------------------

    @property
    def lost_timestamp(self) -> float:
        """Time stamp when communication with device was lost"""
        return self.__lost_timestamp

    # -----------------------------------------------------------------------------

    @lost_timestamp.setter
    def lost_timestamp(self, timestamp: float) -> None:
        """Set lost communication time stamp"""
        self.__lost_timestamp = timestamp

    # -----------------------------------------------------------------------------

    @property
    def sampling_time(self) -> float:
        """Device registers reading sampling time"""
        return self.__sampling_time

    # -----------------------------------------------------------------------------

    @property
    def state(self) -> ConnectionState:
        """Device current state"""
        return self.__state

    # -----------------------------------------------------------------------------

    @state.setter
    def state(self, state: ConnectionState) -> None:
        """Set device current state"""
        if state == ConnectionState.RUNNING:
            self.reset_reading_register(True)
            # Reset lost timestamp
            self.lost_timestamp = 0

        if state == ConnectionState.UNKNOWN:
            if state == ConnectionState.UNKNOWN and self.__state != ConnectionState.UNKNOWN:
                # Set lost timestamp
                self.lost_timestamp = time.time()

            # Reset device communication state
            self.reset_communication()

        self.__state = state

    # -----------------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """Is device in running state?"""
        return self.__state == ConnectionState.RUNNING

    # -----------------------------------------------------------------------------

    @property
    def is_lost(self) -> bool:
        """Is device in lost state?"""
        return self.__lost_timestamp != 0

    # -----------------------------------------------------------------------------

    @property
    def is_unknown(self) -> bool:
        """Is device in unknown state?"""
        return self.__state == ConnectionState.UNKNOWN

    # -----------------------------------------------------------------------------

    def set_lost(self) -> None:
        """Set device into lost state"""
        self.state = ConnectionState.UNKNOWN

    # -----------------------------------------------------------------------------

    def set_running(self) -> None:
        """Set device into running state"""
        self.state = ConnectionState.RUNNING

    # -----------------------------------------------------------------------------

    def reset_communication(self) -> None:
        """Reset device communication pointer"""
        self.__waiting_for_packet = None
        self.__attempts = 0

    # -----------------------------------------------------------------------------

    def set_reading_register(self, register_address: int, register_type: RegisterType) -> None:
        """Set reading register pointer"""
        self.__reading_register_address = register_address
        self.__reading_register_type = register_type

    # -----------------------------------------------------------------------------

    def reset_reading_register(self, reset_timestamp: bool = False) -> None:
        """Reset reading register pointer"""
        if reset_timestamp:
            self.__reading_registers_timestamp = 0.0

        else:
            self.__reading_registers_timestamp = time.time()

        self.__reading_register_address = None
        self.__reading_register_type = None

    # -----------------------------------------------------------------------------

    def get_reading_register(self) -> Tuple[Optional[int], Optional[RegisterType]]:
        """Get reading register pointer"""
        return self.__reading_register_address, self.__reading_register_type

    # -----------------------------------------------------------------------------

    def get_last_register_reading_timestamp(self) -> float:
        """Get reading register time stamp"""
        return self.__reading_registers_timestamp

    # -----------------------------------------------------------------------------

    def __hash__(self) -> int:
        return self.__id.__hash__()


class RegisterRecord(ABC):  # pylint: disable=too-many-instance-attributes
    """
    Base register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __device_id: uuid.UUID

    __id: uuid.UUID
    __address: int
    __type: RegisterType
    __data_type: DeviceDataType
    __settable: bool = False
    __queryable: bool = False
    __key: Optional[str] = None
    __ready: bool = False
    __pubsub_key_written: WriteKeyType = WriteKeyType.NO

    __actual_value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None] = None
    __expected_value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None] = None
    __expected_pending: Optional[float] = None

    __waiting_for_data: bool = False

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_type: RegisterType,
        register_data_type: DeviceDataType,
        register_settable: bool = False,
        register_queryable: bool = False,
        register_key: Optional[str] = None,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> None:
        self.__device_id = device_id

        self.__id = register_id
        self.__address = register_address
        self.__type = register_type
        self.__data_type = register_data_type
        self.__settable = register_settable
        self.__queryable = register_queryable
        self.__key = register_key
        self.__ready = register_ready
        self.__pubsub_key_written = register_pubsub_key_written

    # -----------------------------------------------------------------------------

    @property
    def device_id(self) -> uuid.UUID:
        """Device unique identifier"""
        return self.__device_id

    # -----------------------------------------------------------------------------

    @property
    def id(self) -> uuid.UUID:  # pylint: disable=invalid-name
        """Register unique identifier"""
        return self.__id

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Register address"""
        return self.__address

    # -----------------------------------------------------------------------------

    @property
    def key(self) -> Optional[str]:
        """Register unique key"""
        return self.__key

    # -----------------------------------------------------------------------------

    @property
    def type(self) -> RegisterType:
        """Register type"""
        return self.__type

    # -----------------------------------------------------------------------------

    @property
    def data_type(self) -> DeviceDataType:
        """Record data type"""
        return self.__data_type

    # -----------------------------------------------------------------------------

    @property
    def data_type_size(self) -> int:
        """Record data type bytes size"""
        if self.data_type in (DeviceDataType.UINT8, DeviceDataType.INT8):
            return 1

        if self.data_type in (DeviceDataType.UINT16, DeviceDataType.INT16):
            return 2

        if self.data_type in (
            DeviceDataType.UINT32,
            DeviceDataType.INT32,
            DeviceDataType.FLOAT32,
        ):
            return 4

        if self.data_type == DeviceDataType.BOOLEAN:
            return 2

        return 0

    # -----------------------------------------------------------------------------

    @property
    def ready(self) -> bool:
        """Is register ready for communication?"""
        return self.__ready

    # -----------------------------------------------------------------------------

    @ready.setter
    def ready(self, ready: bool) -> None:
        """Set register ready state"""
        self.__ready = ready

    # -----------------------------------------------------------------------------

    @property
    def pubsub_key_written(self) -> WriteKeyType:
        """Is register PUB/SUB key propagated?"""
        return self.__pubsub_key_written

    # -----------------------------------------------------------------------------

    @pubsub_key_written.setter
    def pubsub_key_written(self, pubsub_key_written: WriteKeyType) -> None:
        """Set register PUB/SUB key propagation state"""
        self.__pubsub_key_written = pubsub_key_written

    # -----------------------------------------------------------------------------

    @property
    def settable(self) -> bool:
        """Is register settable?"""
        return self.__settable

    # -----------------------------------------------------------------------------

    @property
    def queryable(self) -> bool:
        """Is register queryable?"""
        return self.__queryable

    # -----------------------------------------------------------------------------

    @property
    def actual_value(self) -> Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None]:
        """Register actual value"""
        return self.__actual_value

    # -----------------------------------------------------------------------------

    @actual_value.setter
    def actual_value(self, value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime]) -> None:
        """Set register actual value"""
        self.__actual_value = value

        if value == self.expected_value:
            self.expected_value = None
            self.expected_pending = None

    # -----------------------------------------------------------------------------

    @property
    def expected_value(self) -> Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None]:
        """Register expected value"""
        return self.__expected_value

    # -----------------------------------------------------------------------------

    @expected_value.setter
    def expected_value(
        self,
        value: Union[str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime, None],
    ) -> None:
        """Set register expected value"""
        self.__expected_value = value

        if value is not None:
            self.expected_pending = None

    # -----------------------------------------------------------------------------

    @property
    def expected_pending(self) -> Optional[float]:
        """Register expected value pending status"""
        return self.__expected_pending

    # -----------------------------------------------------------------------------

    @expected_pending.setter
    def expected_pending(self, timestamp: Optional[float]) -> None:
        """Set register expected value transmit timestamp"""
        self.__expected_pending = timestamp

    # -----------------------------------------------------------------------------

    @property
    def waiting_for_data(self) -> bool:
        """Is register waiting for any data?"""
        return self.__waiting_for_data

    # -----------------------------------------------------------------------------

    @waiting_for_data.setter
    def waiting_for_data(self, waiting_for_data: bool) -> None:
        """Set waiting for data flag"""
        self.__waiting_for_data = waiting_for_data

    # -----------------------------------------------------------------------------

    def __hash__(self) -> int:
        return self.__id.__hash__()


class InputRegisterRecord(RegisterRecord):
    """
    Input register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_key: Optional[str] = None,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> None:
        super().__init__(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.INPUT,
            register_data_type=register_data_type,
            register_key=register_key,
            register_ready=register_ready,
            register_settable=False,
            register_queryable=True,
            register_pubsub_key_written=register_pubsub_key_written,
        )


class OutputRegisterRecord(RegisterRecord):
    """
    Output register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_key: Optional[str] = None,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> None:
        super().__init__(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.OUTPUT,
            register_data_type=register_data_type,
            register_key=register_key,
            register_ready=register_ready,
            register_settable=True,
            register_queryable=True,
            register_pubsub_key_written=register_pubsub_key_written,
        )


class NamedRegisterRecord(RegisterRecord):
    """
    Named register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __name: Optional[str] = None

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_type: RegisterType,
        register_data_type: DeviceDataType,
        register_name: Optional[str],
        register_settable: bool = False,
        register_queryable: bool = False,
        register_key: Optional[str] = None,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> None:
        super().__init__(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_type=register_type,
            register_data_type=register_data_type,
            register_settable=register_settable,
            register_queryable=register_queryable,
            register_key=register_key,
            register_ready=register_ready,
            register_pubsub_key_written=register_pubsub_key_written,
        )

        self.__name = register_name

    # -----------------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """Register name"""
        return self.__name


class AttributeRegisterRecord(NamedRegisterRecord):
    """
    Attribute register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_name: Optional[str],
        register_key: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> None:
        super().__init__(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.ATTRIBUTE,
            register_data_type=register_data_type,
            register_name=register_name,
            register_settable=register_settable,
            register_queryable=register_queryable,
            register_key=register_key,
            register_ready=register_ready,
            register_pubsub_key_written=register_pubsub_key_written,
        )


class SettingRegisterRecord(NamedRegisterRecord):
    """
    Setting register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_name: Optional[str],
        register_key: Optional[str] = None,
        register_ready: bool = False,
        register_pubsub_key_written: WriteKeyType = WriteKeyType.NO,
    ) -> None:
        super().__init__(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.SETTING,
            register_data_type=register_data_type,
            register_name=register_name,
            register_settable=True,
            register_queryable=True,
            register_key=register_key,
            register_ready=register_ready,
            register_pubsub_key_written=register_pubsub_key_written,
        )


class PairingDeviceRecord:  # pylint: disable=too-many-instance-attributes
    """
    Pairing device record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __client_id: uuid.UUID
    __id: uuid.UUID

    __address: int
    __serial_number: str

    __max_packet_length: int

    __hardware_version: str
    __hardware_model: str
    __hardware_manufacturer: str

    __firmware_version: str
    __firmware_manufacturer: str

    __input_registers_size: int
    __output_registers_size: int
    __attributes_registers_size: int
    __settings_registers_size: int

    __pub_sub_pub_support: bool
    __pub_sub_sub_support: bool
    __max_subscriptions: int
    __max_subscription_conditions: int
    __max_subscription_actions: int

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        client_id: uuid.UUID,
        device_id: uuid.UUID,
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
        settings_registers_size: int,
        device_pub_sub_pub_support: bool,
        device_pub_sub_sub_support: bool,
        device_max_subscriptions: int,
        device_max_subscription_conditions: int,
        device_max_subscription_actions: int,
    ) -> None:
        self.__client_id = client_id
        self.__id = device_id
        self.__address = device_address
        self.__max_packet_length = device_max_packet_length
        self.__serial_number = device_serial_number

        self.__hardware_version = device_hardware_version
        self.__hardware_model = device_hardware_model
        self.__hardware_manufacturer = device_hardware_manufacturer

        self.__firmware_version = device_firmware_version
        self.__firmware_manufacturer = device_firmware_manufacturer

        self.__input_registers_size = input_registers_size
        self.__output_registers_size = output_registers_size
        self.__attributes_registers_size = attributes_registers_size
        self.__settings_registers_size = settings_registers_size

        self.__pub_sub_pub_support = device_pub_sub_pub_support
        self.__pub_sub_sub_support = device_pub_sub_sub_support
        self.__max_subscriptions = device_max_subscriptions
        self.__max_subscription_conditions = device_max_subscription_conditions
        self.__max_subscription_actions = device_max_subscription_actions

    # -----------------------------------------------------------------------------

    @property
    def client_id(self) -> uuid.UUID:
        """Client unique identifier"""
        return self.__client_id

    # -----------------------------------------------------------------------------

    @property
    def id(self) -> uuid.UUID:  # pylint: disable=invalid-name
        """Device unique identifier"""
        return self.__id

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Device communication address"""
        return self.__address

    # -----------------------------------------------------------------------------

    @address.setter
    def address(self, address: int) -> None:
        """Set device communication address"""
        self.__address = address

    # -----------------------------------------------------------------------------

    @property
    def max_packet_length(self) -> int:
        """Maximum packet bytes length"""
        return self.__max_packet_length

    # -----------------------------------------------------------------------------

    @property
    def serial_number(self) -> str:
        """Serial number"""
        return self.__serial_number

    # -----------------------------------------------------------------------------

    @property
    def hardware_version(self) -> str:
        """Hardware version number"""
        return self.__hardware_version

    # -----------------------------------------------------------------------------

    @property
    def hardware_model(self) -> str:
        """Hardware model"""
        return self.__hardware_model

    # -----------------------------------------------------------------------------

    @property
    def hardware_manufacturer(self) -> str:
        """Hardware manufacturer"""
        return self.__hardware_manufacturer

    # -----------------------------------------------------------------------------

    @property
    def firmware_version(self) -> str:
        """Firmware version number"""
        return self.__firmware_version

    # -----------------------------------------------------------------------------

    @property
    def firmware_manufacturer(self) -> str:
        """Firmware manufacturer"""
        return self.__firmware_manufacturer

    # -----------------------------------------------------------------------------

    @property
    def input_registers_size(self) -> int:
        """Input registers size"""
        return self.__input_registers_size

    # -----------------------------------------------------------------------------

    @property
    def output_registers_size(self) -> int:
        """Output registers size"""
        return self.__output_registers_size

    # -----------------------------------------------------------------------------

    @property
    def attributes_registers_size(self) -> int:
        """Device attributes registers size"""
        return self.__attributes_registers_size

    # -----------------------------------------------------------------------------

    @property
    def settings_registers_size(self) -> int:
        """Device settings registers size"""
        return self.__settings_registers_size

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_pub_support(self) -> bool:
        """Has device pub/sub publish support"""
        return self.__pub_sub_pub_support

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_sub_support(self) -> bool:
        """Has device pub/sub subscribe support"""
        return self.__pub_sub_sub_support

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_max_subscriptions(self) -> int:
        """Maximum pub/sub subscriptions supported count"""
        return self.__max_subscriptions

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_max_subscription_conditions(self) -> int:
        """Maximum pub/sub conditions supported count"""
        return self.__max_subscription_conditions

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_max_subscription_actions(self) -> int:
        """Maximum pub/sub actions supported count"""
        return self.__max_subscription_actions

    # -----------------------------------------------------------------------------

    def __hash__(self) -> int:
        return self.__id.__hash__()


class PairingRegisterRecord(ABC):
    """
    Pairing base register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __id: uuid.UUID
    __address: int
    __key: Optional[str]
    __type: RegisterType
    __data_type: DeviceDataType
    __settable: bool = False
    __queryable: bool = False

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        register_id: uuid.UUID,
        register_address: int,
        register_type: RegisterType,
        register_data_type: DeviceDataType,
        register_key: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
    ) -> None:
        self.__id = register_id
        self.__address = register_address
        self.__key = register_key
        self.__type = register_type
        self.__data_type = register_data_type

        self.__queryable = register_queryable
        self.__settable = register_settable

    # -----------------------------------------------------------------------------

    @property
    def id(self) -> uuid.UUID:  # pylint: disable=invalid-name
        """Register unique identifier"""
        return self.__id

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Register address"""
        return self.__address

    # -----------------------------------------------------------------------------

    @property
    def key(self) -> Optional[str]:
        """Register unique key"""
        return self.__key

    # -----------------------------------------------------------------------------

    @property
    def type(self) -> RegisterType:
        """Register type"""
        return self.__type

    # -----------------------------------------------------------------------------

    @property
    def data_type(self) -> DeviceDataType:
        """Register data type"""
        return self.__data_type

    # -----------------------------------------------------------------------------

    @property
    def settable(self) -> bool:
        """Is register settable?"""
        return self.__settable

    # -----------------------------------------------------------------------------

    @property
    def queryable(self) -> bool:
        """Is register queryable?"""
        return self.__queryable

    # -----------------------------------------------------------------------------

    def __hash__(self) -> int:
        return self.__id.__hash__()


class PairingInputRegisterRecord(PairingRegisterRecord):
    """
    Pairing input register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    def __init__(
        self,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_key: Optional[str] = None,
    ):
        super().__init__(
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.INPUT,
            register_data_type=register_data_type,
            register_key=register_key,
            register_queryable=True,
            register_settable=False,
        )


class PairingOutputRegisterRecord(PairingRegisterRecord):
    """
    Pairing output register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    def __init__(
        self,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_key: Optional[str] = None,
    ):
        super().__init__(
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.OUTPUT,
            register_data_type=register_data_type,
            register_key=register_key,
            register_queryable=True,
            register_settable=True,
        )


class PairingNamedRegisterRecord(PairingRegisterRecord):
    """
    Pairing named register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __name: Optional[str]

    def __init__(  # pylint: disable=too-many-branches,too-many-arguments
        self,
        register_id: uuid.UUID,
        register_address: int,
        register_type: RegisterType,
        register_data_type: DeviceDataType,
        register_name: Optional[str],
        register_key: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
    ):
        super().__init__(
            register_id=register_id,
            register_address=register_address,
            register_type=register_type,
            register_data_type=register_data_type,
            register_key=register_key,
            register_queryable=register_settable,
            register_settable=register_queryable,
        )

        self.__name = register_name

    # -----------------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """Register name"""
        return self.__name


class PairingAttributeRegisterRecord(PairingNamedRegisterRecord):
    """
    Pairing attribute register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    def __init__(  # pylint: disable=too-many-branches,too-many-arguments
        self,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_name: Optional[str],
        register_key: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
    ):
        super().__init__(
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.ATTRIBUTE,
            register_name=register_name,
            register_data_type=register_data_type,
            register_key=register_key,
            register_queryable=register_settable,
            register_settable=register_queryable,
        )


class PairingSettingRegisterRecord(PairingNamedRegisterRecord):
    """
    Pairing setting register record

    @package        FastyBird:FbBusConnectorPlugin!
    @module         registry

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    def __init__(  # pylint: disable=too-many-branches,too-many-arguments
        self,
        register_id: uuid.UUID,
        register_address: int,
        register_data_type: DeviceDataType,
        register_name: Optional[str],
        register_key: Optional[str] = None,
    ):
        super().__init__(
            register_id=register_id,
            register_address=register_address,
            register_type=RegisterType.SETTING,
            register_data_type=register_data_type,
            register_key=register_key,
            register_name=register_name,
            register_queryable=True,
            register_settable=True,
        )
