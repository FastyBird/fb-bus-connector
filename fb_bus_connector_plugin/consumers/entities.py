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
FastyBird BUS connector plugin messages consumers module entities
"""

# Python base dependencies
import uuid
from abc import ABC
from datetime import datetime
from typing import Optional, Union

# App dependencies
from modules_metadata.devices_module import DeviceConnectionState
from modules_metadata.types import ButtonPayload, DataType, SwitchPayload


class BaseEntity(ABC):  # pylint: disable=too-few-public-methods
    """
    Base entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __device_id: uuid.UUID

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        device_id: uuid.UUID,
    ) -> None:
        self.__device_id = device_id

    # -----------------------------------------------------------------------------

    @property
    def device_id(self) -> uuid.UUID:
        """Device unique identifier"""
        return self.__device_id


class DeviceEntity(BaseEntity):  # pylint: disable=too-many-instance-attributes
    """
    Device entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __client_id: uuid.UUID

    __serial_number: str
    __address: int
    __max_packet_length: int
    __state: DeviceConnectionState

    __pub_sub_pub_support: bool
    __pub_sub_sub_support: bool
    __pub_sub_sub_max_subscriptions: int
    __pub_sub_sub_max_conditions: int
    __pub_sub_sub_max_actions: int

    __hardware_manufacturer: Optional[str]
    __hardware_model: Optional[str]
    __hardware_version: Optional[str]

    __firmware_manufacturer: Optional[str]
    __firmware_version: Optional[str]

    def __init__(  # pylint: disable=too-many-locals,too-many-arguments
        self,
        client_id: uuid.UUID,
        device_id: uuid.UUID,
        device_serial_number: str,
        device_address: int,
        device_max_packet_length: int,
        device_state: DeviceConnectionState,
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
    ) -> None:
        super().__init__(device_id=device_id)

        self.__client_id = client_id

        self.__serial_number = device_serial_number
        self.__address = device_address
        self.__max_packet_length = device_max_packet_length
        self.__state = device_state

        self.__pub_sub_pub_support = device_pub_sub_pub_support
        self.__pub_sub_sub_support = device_pub_sub_sub_support
        self.__pub_sub_sub_max_subscriptions = device_pub_sub_sub_max_subscriptions
        self.__pub_sub_sub_max_conditions = device_pub_sub_sub_max_conditions
        self.__pub_sub_sub_max_actions = device_pub_sub_sub_max_actions

        self.__hardware_manufacturer = hardware_manufacturer
        self.__hardware_model = hardware_model
        self.__hardware_version = hardware_version

        self.__firmware_manufacturer = firmware_manufacturer
        self.__firmware_version = firmware_version

    # -----------------------------------------------------------------------------

    @property
    def client_id(self) -> uuid.UUID:
        """Connector unique identifier"""
        return self.__client_id

    # -----------------------------------------------------------------------------

    @property
    def serial_number(self) -> str:
        """Device serial number"""
        return self.__serial_number

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Device communication address"""
        return self.__address

    # -----------------------------------------------------------------------------

    @property
    def max_packet_length(self) -> int:
        """Maximum communication packet length"""
        return self.__max_packet_length

    # -----------------------------------------------------------------------------

    @property
    def state(self) -> DeviceConnectionState:
        """Device current state"""
        return self.__state

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_pub_support(self) -> bool:
        """Has device pub/sub publish supported?"""
        return self.__pub_sub_pub_support

    # -----------------------------------------------------------------------------

    @property
    def pub_sub_sub_support(self) -> bool:
        """Has device pub/sub subscribe supported?"""
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


class DeviceStateEntity(BaseEntity):
    """
    Device state entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __state: DeviceConnectionState

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        device_id: uuid.UUID,
        device_state: DeviceConnectionState,
    ) -> None:
        super().__init__(device_id=device_id)

        self.__state = device_state

    # -----------------------------------------------------------------------------

    @property
    def state(self) -> DeviceConnectionState:
        """Device current state"""
        return self.__state


class RegisterEntity(BaseEntity):  # pylint: disable=too-many-instance-attributes
    """
    Register entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __id: uuid.UUID
    __address: int
    __name: Optional[str]
    __key: Optional[str]
    __settable: bool
    __queryable: bool
    __data_type: DataType

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_is_settable: bool,
        register_is_queryable: bool,
        register_data_type: DataType,
        register_name: Optional[str] = None,
    ) -> None:
        super().__init__(device_id=device_id)

        self.__id = register_id
        self.__address = register_address
        self.__name = register_name
        self.__key = register_key
        self.__settable = register_is_settable
        self.__queryable = register_is_queryable
        self.__data_type = register_data_type

    # -----------------------------------------------------------------------------

    @property
    def register_id(self) -> uuid.UUID:
        """Register unique identifier"""
        return self.__id

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Register communication address"""
        return self.__address

    # -----------------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """Register name"""
        return self.__name

    # -----------------------------------------------------------------------------

    @property
    def key(self) -> Optional[str]:
        """Register unique key"""
        return self.__key

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
    def data_type(self) -> DataType:
        """Register data type"""
        return self.__data_type


class InputRegisterEntity(RegisterEntity):
    """
    Input register entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class OutputRegisterEntity(RegisterEntity):
    """
    Output register entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class AttributeRegisterEntity(RegisterEntity):
    """
    Attribute register entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class SettingRegisterEntity(RegisterEntity):
    """
    Setting register entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class RegisterActualValueEntity(BaseEntity):
    """
    Register actual value entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __id: uuid.UUID
    __value: Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime, None]

    # -----------------------------------------------------------------------------

    def __init__(
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_value: Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime, None],
    ) -> None:
        super().__init__(device_id=device_id)

        self.__id = register_id
        self.__value = register_value

    # -----------------------------------------------------------------------------

    @property
    def register_id(self) -> uuid.UUID:
        """Register unique identifier"""
        return self.__id

    # -----------------------------------------------------------------------------

    @property
    def value(self) -> Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime, None]:
        """Register actual value"""
        return self.__value


class InputRegisterActualValueEntity(RegisterActualValueEntity):
    """
    Input register actual value entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class OutputRegisterActualValueEntity(RegisterActualValueEntity):
    """
    Output register actual value entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class AttributeRegisterActualValueEntity(RegisterActualValueEntity):
    """
    Attribute register actual value entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """


class SettingRegisterActualValueEntity(RegisterActualValueEntity):
    """
    Setting register actual value entity

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """
