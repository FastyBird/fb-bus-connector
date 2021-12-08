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
FastyBird BUS connector
"""

# Python base dependencies
import uuid
from datetime import datetime
from typing import Optional, Union

# Library dependencies
from modules_metadata.types import ButtonPayload, DataType, SwitchPayload

# Library libs
from fb_bus_connector_plugin.clients.client import Client, ClientFactory
from fb_bus_connector_plugin.consumers.consumer import Consumer
from fb_bus_connector_plugin.exceptions import InvalidStateException
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.pairing.pairing import DevicesPairing
from fb_bus_connector_plugin.publishers.publisher import Publisher
from fb_bus_connector_plugin.receivers.receiver import Receiver
from fb_bus_connector_plugin.registry.model import DevicesRegistry, RegistersRegistry
from fb_bus_connector_plugin.registry.records import DeviceRecord
from fb_bus_connector_plugin.types import (
    ButtonPayloadType,
    ClientType,
    ConnectionState,
    ProtocolVersion,
    RegisterType,
    SwitchPayloadType,
)
from fb_bus_connector_plugin.utilities.helpers import (
    DataTransformHelpers,
    DataTypeHelpers,
)


class FbBusConnector:  # pylint: disable=too-many-instance-attributes
    """
    FastyBird BUS connector

    @package        FastyBird:FbBusConnectorPlugin!
    @module         connector

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __stopped: bool = False

    __packets_to_be_sent: int = 0

    __receiver: Receiver
    __publisher: Publisher
    __consumer: Consumer

    __devices_registry: DevicesRegistry
    __registers_registry: RegistersRegistry

    __client: Client
    __client_factory: ClientFactory

    __pairing_helper: DevicesPairing

    __logger: Logger

    # -----------------------------------------------------------------------------

    def __init__(  # pylint: disable=too-many-arguments
        self,
        receiver: Receiver,
        publisher: Publisher,
        consumer: Consumer,
        devices_registry: DevicesRegistry,
        registers_registry: RegistersRegistry,
        client: Client,
        client_factory: ClientFactory,
        pairing_handler: DevicesPairing,
        logger: Logger,
    ) -> None:
        self.__receiver = receiver
        self.__publisher = publisher
        self.__consumer = consumer

        self.__devices_registry = devices_registry
        self.__registers_registry = registers_registry

        self.__client = client
        self.__client_factory = client_factory
        self.__pairing_helper = pairing_handler

        self.__logger = logger

    # -----------------------------------------------------------------------------

    def initialize_client(  # pylint: disable=too-many-arguments
        self,
        client_id: uuid.UUID,
        client_type: ClientType = ClientType.PJON,
        client_address: int = 254,
        client_baud_rate: int = 38400,
        client_interface: str = "/dev/ttyAMA0",
        protocol_version: ProtocolVersion = ProtocolVersion.V1,
    ) -> None:
        """Configure BUS client & append it to client proxy"""
        self.__client_factory.create(
            client_id=client_id,
            client_type=client_type,
            client_address=client_address,
            client_baud_rate=client_baud_rate,
            client_interface=client_interface,
            protocol_version=protocol_version,
        )

    # -----------------------------------------------------------------------------

    def enable_client(self, client_id: uuid.UUID) -> bool:
        """Enable client"""
        return self.__client.enable_client(client_id=client_id)

    # -----------------------------------------------------------------------------

    def disable_client(self, client_id: uuid.UUID) -> bool:
        """Disable client connector"""
        return self.__client.disable_client(client_id=client_id)

    # -----------------------------------------------------------------------------

    def remove_client(self, client_id: uuid.UUID) -> bool:
        """Remove client from connector"""
        return self.__client.remove_client(client_id=client_id)

    # -----------------------------------------------------------------------------

    def initialize_device(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        client_id: uuid.UUID,
        device_id: uuid.UUID,
        device_address: int,
        device_serial_number: str,
        device_max_packet_length: int,
        device_enabled: bool = True,
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
        """Configure device connector record"""
        device_record = self.__devices_registry.get_by_id(device_id=device_id)

        if device_record is not None:
            is_ready = self.__check_device_record_ready(device_record=device_record)

        else:
            is_ready = True

        self.__devices_registry.initialize(
            client_id=client_id,
            device_id=device_id,
            device_address=device_address,
            device_serial_number=device_serial_number,
            device_max_packet_length=device_max_packet_length,
            device_enabled=device_enabled,
            device_pub_sub_pub_support=device_pub_sub_pub_support,
            device_pub_sub_sub_support=device_pub_sub_sub_support,
            device_pub_sub_sub_max_subscriptions=device_pub_sub_sub_max_subscriptions,
            device_pub_sub_sub_max_conditions=device_pub_sub_sub_max_conditions,
            device_pub_sub_sub_max_actions=device_pub_sub_sub_max_actions,
            hardware_manufacturer=hardware_manufacturer,
            hardware_model=hardware_model,
            hardware_version=hardware_version,
            firmware_manufacturer=firmware_manufacturer,
            firmware_version=firmware_version,
            device_ready=is_ready,
        )

    # -----------------------------------------------------------------------------

    def enable_device(self, device_id: uuid.UUID) -> bool:
        """Enable device"""
        device_record = self.__devices_registry.get_by_id(device_id=device_id)

        if device_record is None:
            raise InvalidStateException("Device for given register is not registered. Call 'initialize_device' first")

        return isinstance(self.__devices_registry.enable(device=device_record), DeviceRecord)

    # -----------------------------------------------------------------------------

    def disable_device(self, device_id: uuid.UUID) -> bool:
        """Disable device"""
        device_record = self.__devices_registry.get_by_id(device_id=device_id)

        if device_record is None:
            raise InvalidStateException("Device for given register is not registered. Call 'initialize_device' first")

        return isinstance(self.__devices_registry.disable(device=device_record), DeviceRecord)

    # -----------------------------------------------------------------------------

    def remove_device(self, device_id: uuid.UUID) -> None:
        """Remove device from connector registry"""
        self.__devices_registry.remove(device_id=device_id)

    # -----------------------------------------------------------------------------

    def initialize_device_input_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DataType,
    ) -> None:
        """Configure device input register connector record"""
        self.__initialize_device_register(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_type=RegisterType.INPUT,
        )

    # -----------------------------------------------------------------------------

    def initialize_device_output_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DataType,
    ) -> None:
        """Configure device output register connector record"""
        self.__initialize_device_register(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_type=RegisterType.OUTPUT,
        )

    # -----------------------------------------------------------------------------

    def initialize_device_attribute_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DataType,
        register_name: str,
        register_settable: bool,
        register_queryable: bool,
    ) -> None:
        """Configure device attribute register connector record"""
        self.__initialize_device_register(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_type=RegisterType.ATTRIBUTE,
            register_name=register_name,
            register_settable=register_settable,
            register_queryable=register_queryable,
        )

    # -----------------------------------------------------------------------------

    def initialize_device_setting_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DataType,
        register_name: str,
    ) -> None:
        """Configure device setting register connector record"""
        self.__initialize_device_register(
            device_id=device_id,
            register_id=register_id,
            register_address=register_address,
            register_key=register_key,
            register_data_type=register_data_type,
            register_type=RegisterType.SETTING,
            register_name=register_name,
        )

    # -----------------------------------------------------------------------------

    def remove_register(self, register_id: uuid.UUID) -> None:
        """Remove device register from connector registry"""
        self.__registers_registry.remove(register_id=register_id)

    # -----------------------------------------------------------------------------

    def start(self) -> None:
        """Start connector services"""
        self.__stopped = False

        # When connector is closing...
        for device in self.__devices_registry:
            # ...set device state to disconnected
            self.__devices_registry.set_state(device=device, state=ConnectionState.UNKNOWN)

        self.__logger.info("Connector FB BUS has been started.")

    # -----------------------------------------------------------------------------

    def stop(self) -> None:
        """Close all opened connections & stop connector thread"""
        # When connector is closing...
        for device in self.__devices_registry:
            # ...set device state to disconnected
            self.__devices_registry.set_state(device=device, state=ConnectionState.UNKNOWN)

        self.__logger.info("Connector FB BUS has been stopped.")

        self.__stopped = True

    # -----------------------------------------------------------------------------

    def write_register_value(
        self,
        register_id: uuid.UUID,
        write_value: Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime, None],
    ) -> bool:
        """Write expected value to register"""
        if self.__stopped:
            self.__logger.warning("Connector is stopped, value can't be written")

            return False

        register = self.__registers_registry.get_by_id(register_id=register_id)

        if register is not None:
            expected_value = DataTransformHelpers.transform_for_device(
                data_type=register.data_type,
                value=write_value,
            )

            if isinstance(
                expected_value,
                (str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime),
            ):
                self.__registers_registry.set_expected_value(register=register, value=expected_value)

                return True

        return False

    # -----------------------------------------------------------------------------

    def broadcast_value(
        self,
        broadcast_key: str,
        broadcast_value: Union[str, int, float, bool, ButtonPayload, SwitchPayload, datetime, None],
        broadcast_data_type: DataType,
    ) -> bool:
        """Broadcast value for given register key"""
        transformed_value = DataTransformHelpers.transform_for_device(
            data_type=DataTypeHelpers.transform_for_device(data_type=broadcast_data_type),
            value=broadcast_value,
        )

        if isinstance(
            transformed_value,
            (str, int, float, bool, ButtonPayloadType, SwitchPayloadType, datetime),
        ):
            return self.__publisher.broadcast_value(
                broadcast_key=broadcast_key,
                broadcast_value=transformed_value,
                broadcast_data_type=DataTypeHelpers.transform_for_device(data_type=broadcast_data_type),
            )

        return False

    # -----------------------------------------------------------------------------

    def has_unfinished_tasks(self) -> bool:
        """Check if connector has some unfinished task"""
        return not self.__receiver.is_empty() or not self.__consumer.is_empty()

    # -----------------------------------------------------------------------------

    def loop(self) -> None:
        """Run connector service"""
        if self.__stopped and not self.has_unfinished_tasks():
            self.__logger.warning("Connector FB BUS is stopped")

            return

        self.__receiver.loop()
        self.__consumer.loop()

        if self.__stopped:
            return

        # Check is pairing enabled...
        if self.__pairing_helper.is_enabled() is True:
            self.__pairing_helper.loop()

        # Pairing is not enabled...
        else:
            # Check packets queue...
            if self.__packets_to_be_sent == 0:
                # Continue processing devices
                self.__publisher.loop()

        self.__packets_to_be_sent = self.__client.loop()

    # -----------------------------------------------------------------------------

    def __initialize_device_register(  # pylint: disable=too-many-arguments
        self,
        device_id: uuid.UUID,
        register_id: uuid.UUID,
        register_address: int,
        register_key: Optional[str],
        register_data_type: DataType,
        register_type: RegisterType,
        register_name: Optional[str] = None,
        register_settable: bool = False,
        register_queryable: bool = False,
    ) -> None:
        device_record = self.__devices_registry.get_by_id(device_id=device_id)

        if device_record is None:
            raise InvalidStateException("Device for given register is not registered. Call 'initialize_device' first")

        if register_type == RegisterType.INPUT:
            self.__registers_registry.initialize_input_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=DataTypeHelpers.transform_for_device(data_type=register_data_type),
                register_ready=True,
            )

            return

        if register_type == RegisterType.OUTPUT:
            self.__registers_registry.initialize_output_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=DataTypeHelpers.transform_for_device(data_type=register_data_type),
                register_ready=True,
            )

            return

        if register_type == RegisterType.ATTRIBUTE:
            self.__registers_registry.initialize_attribute_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=DataTypeHelpers.transform_for_device(data_type=register_data_type),
                register_name=register_name,
                register_queryable=register_queryable,
                register_settable=register_settable,
                register_ready=True,
            )

            return

        if register_type == RegisterType.SETTING:
            self.__registers_registry.initialize_setting_register(
                device_id=device_id,
                register_id=register_id,
                register_address=register_address,
                register_key=register_key,
                register_data_type=DataTypeHelpers.transform_for_device(data_type=register_data_type),
                register_name=register_name,
                register_ready=True,
            )

        device_record = self.__devices_registry.get_by_id(device_id=device_id)

        if device_record is not None and not device_record.ready:
            is_ready = self.__check_device_record_ready(device_record=device_record)

            if is_ready:
                self.__devices_registry.set_ready(device=device_record, ready=True)

    # -----------------------------------------------------------------------------

    def __check_device_record_ready(self, device_record: DeviceRecord) -> bool:
        registers_ready = True

        for register in self.__registers_registry.get_all_for_device(device_id=device_record.id):
            if not register.ready:
                registers_ready = False

        return registers_ready
