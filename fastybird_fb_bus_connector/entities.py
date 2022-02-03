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
FastyBird BUS connector entities module
"""

# Python base dependencies
from typing import Dict, List, Optional, Union

# Library dependencies
from fastybird_devices_module.entities.connector import ConnectorEntity
from fastybird_devices_module.entities.device import DeviceEntity

# Library libs
from fastybird_fb_bus_connector.types import (
    CONNECTOR_NAME,
    DEVICE_NAME,
    MASTER_ADDRESS,
    ProtocolVersion,
)


class FbBusConnectorEntity(ConnectorEntity):  # pylint: disable=too-few-public-methods
    """
    FB BUS connector entity

    @package        FastyBird:FbBusConnector!
    @module         entities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __mapper_args__ = {"polymorphic_identity": CONNECTOR_NAME}

    # -----------------------------------------------------------------------------

    @property
    def type(self) -> str:
        """Connector type"""
        return CONNECTOR_NAME

    # -----------------------------------------------------------------------------

    @property
    def address(self) -> int:
        """Connector communication master address"""
        return (
            int(str(self.params.get("address", MASTER_ADDRESS)))
            if self.params is not None and self.params.get("address", MASTER_ADDRESS) is not None
            else MASTER_ADDRESS
        )

    # -----------------------------------------------------------------------------

    @address.setter
    def address(self, address: Optional[int]) -> None:
        """Connector communication master address setter"""
        if self.params is not None and bool(self.params) is True:
            self.params["address"] = address

        else:
            self.params = {"address": address}

    # -----------------------------------------------------------------------------

    @property
    def interface(self) -> str:
        """Connector serial interface"""
        return (
            str(self.params.get("interface", None))
            if self.params is not None and self.params.get("interface") is not None
            else "/dev/ttyAMA0"
        )

    # -----------------------------------------------------------------------------

    @interface.setter
    def interface(self, interface: Optional[str]) -> None:
        """Connector serial interface setter"""
        if self.params is not None and bool(self.params) is True:
            self.params["interface"] = interface

        else:
            self.params = {"interface": interface}

    # -----------------------------------------------------------------------------

    @property
    def baud_rate(self) -> int:
        """Connector communication baud rate"""
        return (
            int(str(self.params.get("baud_rate", 38400)))
            if self.params is not None and self.params.get("baud_rate", 38400) is not None
            else 38400
        )

    # -----------------------------------------------------------------------------

    @baud_rate.setter
    def baud_rate(self, baud_rate: Optional[int]) -> None:
        """Connector communication baud rate setter"""
        if self.params is not None and bool(self.params) is True:
            self.params["baud_rate"] = baud_rate

        else:
            self.params = {"baud_rate": baud_rate}

    # -----------------------------------------------------------------------------

    @property
    def protocol(self) -> ProtocolVersion:
        """Connector communication protocol version"""
        return (
            ProtocolVersion(int(str(self.params.get("protocol"))))
            if self.params is not None and self.params.get("protocol") is not None
            else ProtocolVersion.V1
        )

    # -----------------------------------------------------------------------------

    @protocol.setter
    def protocol(self, protocol: Optional[ProtocolVersion]) -> None:
        """Connector communication protocol version setter"""
        if self.params is not None and bool(self.params) is True:
            self.params["protocol"] = protocol.value if protocol is not None else None

        else:
            self.params = {"protocol": (protocol.value if protocol is not None else None)}

    # -----------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Union[str, int, bool, List[str], None]]:
        """Transform entity to dictionary"""
        return {
            **super().to_dict(),
            **{
                "address": self.address,
                "interface": self.interface,
                "baud_rate": self.baud_rate,
                "protocol": self.protocol.value,
            },
        }


class FbBusDeviceEntity(DeviceEntity):  # pylint: disable=too-few-public-methods
    """
    FB BUS device entity

    @package        FastyBird:FbBusConnector!
    @module         entities

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __mapper_args__ = {"polymorphic_identity": DEVICE_NAME}

    # -----------------------------------------------------------------------------

    @property
    def type(self) -> str:
        """Device type"""
        return DEVICE_NAME
