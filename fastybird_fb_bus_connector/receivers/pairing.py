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
FastyBird BUS connector receivers module receiver for pairing messages
"""

# Library dependencies
from kink import inject

# Library libs
from fastybird_fb_bus_connector.pairing.apiv1 import ApiV1Pairing
from fastybird_fb_bus_connector.receivers.base import IReceiver
from fastybird_fb_bus_connector.receivers.entities import (
    BaseEntity,
    DeviceDiscoveryEntity,
    RegisterStructureEntity,
)
from fastybird_fb_bus_connector.types import RegisterType


@inject(alias=IReceiver)
class PairingReceiver(IReceiver):  # pylint: disable=too-few-public-methods
    """
    BUS messages receiver for pairing messages

    @package        FastyBird:FbBusConnector!
    @module         receivers/pairing

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __device_pairing: ApiV1Pairing

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        device_pairing: ApiV1Pairing,
    ) -> None:
        self.__device_pairing = device_pairing

    # -----------------------------------------------------------------------------

    def receive(self, entity: BaseEntity) -> None:
        """Handle received message"""
        if isinstance(entity, DeviceDiscoveryEntity):
            self.__receive_set_device_discovery(entity=entity)

            return

        if isinstance(entity, RegisterStructureEntity):
            self.__receive_register_structure(entity=entity)

            return

    # -----------------------------------------------------------------------------

    def __receive_set_device_discovery(self, entity: DeviceDiscoveryEntity) -> None:
        self.__device_pairing.append_device(
            # Device description
            device_address=entity.device_address,
            device_max_packet_length=entity.device_max_packet_length,
            device_serial_number=entity.device_serial_number,
            device_state=entity.device_state,
            device_hardware_version=entity.device_hardware_version,
            device_hardware_model=entity.device_hardware_model,
            device_hardware_manufacturer=entity.device_hardware_manufacturer,
            device_firmware_version=entity.device_firmware_version,
            device_firmware_manufacturer=entity.device_firmware_manufacturer,
            # Registers sizes info
            input_registers_size=entity.input_registers_size,
            output_registers_size=entity.output_registers_size,
            attributes_registers_size=entity.attributes_registers_size,
        )

    # -----------------------------------------------------------------------------

    def __receive_register_structure(self, entity: RegisterStructureEntity) -> None:
        if entity.register_type in (RegisterType.INPUT, RegisterType.OUTPUT, RegisterType.ATTRIBUTE):
            if entity.register_type == RegisterType.INPUT:
                # Update register record
                self.__device_pairing.append_input_register(
                    register_address=entity.register_address,
                    # Configure register data type
                    register_data_type=entity.register_data_type,
                )

            elif entity.register_type == RegisterType.OUTPUT:
                # Update register record
                self.__device_pairing.append_output_register(
                    register_address=entity.register_address,
                    # Configure register data type
                    register_data_type=entity.register_data_type,
                )

            elif entity.register_type == RegisterType.ATTRIBUTE:
                # Update register record
                self.__device_pairing.append_attribute_register(
                    register_address=entity.register_address,
                    # Configure register details
                    register_data_type=entity.register_data_type,
                    register_name=entity.register_name,
                    register_settable=entity.register_settable,
                    register_queryable=entity.register_queryable,
                )
