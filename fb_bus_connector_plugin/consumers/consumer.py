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
FastyBird BUS connector plugin messages consumers module proxy
"""

# Python base dependencies
from abc import ABC, abstractmethod
from queue import Full as QueueFull
from queue import Queue
from typing import Set

# Library dependencies
from kink import inject

# Library libs
from fb_bus_connector_plugin.consumers.entities import (
    AttributeRegisterActualValueEntity,
    AttributeRegisterEntity,
    BaseEntity,
    DeviceEntity,
    DeviceStateEntity,
    InputRegisterActualValueEntity,
    InputRegisterEntity,
    OutputRegisterActualValueEntity,
    OutputRegisterEntity,
    SettingRegisterActualValueEntity,
    SettingRegisterEntity,
)
from fb_bus_connector_plugin.exceptions import InvalidStateException
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.registry.records import DeviceRecord, RegisterRecord
from fb_bus_connector_plugin.types import RegisterType
from fb_bus_connector_plugin.utilities.helpers import (
    DataTransformHelpers,
    DataTypeHelpers,
    StateHelpers,
)


class IConsumer(ABC):  # pylint: disable=too-few-public-methods
    """
    Entity consumer interface

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @abstractmethod
    def consume(self, entity: BaseEntity) -> None:
        """Consume entity"""


@inject
class Consumer:
    """
    Messages entities consumer

    @package        FastyBird:FbBusConnectorPlugin!
    @module         consumers

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    __consumers: Set[IConsumer]
    __queue: Queue

    __logger: Logger

    # -----------------------------------------------------------------------------

    @inject
    def __init__(
        self,
        logger: Logger,
    ) -> None:
        self.__consumers = set()

        self.__logger = logger

        self.__queue = Queue(maxsize=1000)

    # -----------------------------------------------------------------------------

    def loop(self) -> None:
        """Consume message"""
        try:
            if not self.__queue.empty():
                entity = self.__queue.get()

                if isinstance(entity, BaseEntity):
                    for consumer in self.__consumers:
                        consumer.consume(entity=entity)

        except InvalidStateException as ex:
            self.__logger.error("Received message could not be consumed")
            self.__logger.exception(ex)

    # -----------------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Check if all messages are handled"""
        return self.__queue.empty()

    # -----------------------------------------------------------------------------

    def register_consumer(
        self,
        consumer: IConsumer,
    ) -> None:
        """Register new consumer to proxy"""
        self.__consumers.add(consumer)

    # -----------------------------------------------------------------------------

    def propagate_device_record(self, device_record: DeviceRecord) -> None:
        """Propagate repository device record"""
        self.__append(
            entity=DeviceEntity(
                client_id=device_record.client_id,
                device_id=device_record.id,
                device_serial_number=device_record.serial_number,
                device_address=device_record.address,
                device_max_packet_length=device_record.max_packet_length,
                device_state=StateHelpers.transform_state_for_gateway(device_record.state),
                device_pub_sub_pub_support=device_record.pub_sub_pub_support,
                device_pub_sub_sub_support=device_record.pub_sub_sub_support,
                device_pub_sub_sub_max_subscriptions=device_record.pub_sub_sub_max_subscriptions,
                device_pub_sub_sub_max_conditions=device_record.pub_sub_sub_max_conditions,
                device_pub_sub_sub_max_actions=device_record.pub_sub_sub_max_actions,
                hardware_manufacturer=device_record.hardware_manufacturer,
                hardware_model=device_record.hardware_model,
                hardware_version=device_record.hardware_version,
                firmware_manufacturer=device_record.firmware_manufacturer,
                firmware_version=device_record.firmware_version,
            ),
        )

    # -----------------------------------------------------------------------------

    def propagate_device_record_state(self, device_record: DeviceRecord) -> None:
        """Propagate repository device record state"""
        self.__append(
            entity=DeviceStateEntity(
                device_id=device_record.id,
                device_state=StateHelpers.transform_state_for_gateway(device_record.state),
            ),
        )

    # -----------------------------------------------------------------------------

    def propagate_register_record(self, register_record: RegisterRecord) -> None:
        """Propagate repository register record"""
        if register_record.type == RegisterType.INPUT:
            self.__append(
                entity=InputRegisterEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_data_type=DataTypeHelpers.transform_for_gateway(register_record.data_type),
                    register_address=register_record.address,
                    register_key=register_record.key,
                    register_is_settable=register_record.settable,
                    register_is_queryable=register_record.queryable,
                ),
            )

        elif register_record.type == RegisterType.OUTPUT:
            self.__append(
                entity=OutputRegisterEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_data_type=DataTypeHelpers.transform_for_gateway(register_record.data_type),
                    register_address=register_record.address,
                    register_key=register_record.key,
                    register_is_settable=register_record.settable,
                    register_is_queryable=register_record.queryable,
                ),
            )

        elif register_record.type == RegisterType.ATTRIBUTE:
            self.__append(
                entity=AttributeRegisterEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_data_type=DataTypeHelpers.transform_for_gateway(register_record.data_type),
                    register_address=register_record.address,
                    register_key=register_record.key,
                    register_is_settable=register_record.settable,
                    register_is_queryable=register_record.queryable,
                ),
            )

        elif register_record.type == RegisterType.SETTING:
            self.__append(
                entity=SettingRegisterEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_data_type=DataTypeHelpers.transform_for_gateway(register_record.data_type),
                    register_address=register_record.address,
                    register_key=register_record.key,
                    register_is_settable=register_record.settable,
                    register_is_queryable=register_record.queryable,
                ),
            )

    # -----------------------------------------------------------------------------

    def propagate_register_record_value(self, register_record: RegisterRecord) -> None:
        """Propagate repository register record value"""
        if register_record.type == RegisterType.INPUT:
            self.__append(
                entity=InputRegisterActualValueEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_value=DataTransformHelpers.transform_for_gateway(
                        data_type=register_record.data_type,
                        value=register_record.actual_value,
                    ),
                ),
            )

        elif register_record.type == RegisterType.OUTPUT:
            self.__append(
                entity=OutputRegisterActualValueEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_value=DataTransformHelpers.transform_for_gateway(
                        data_type=register_record.data_type,
                        value=register_record.actual_value,
                    ),
                ),
            )

        elif register_record.type == RegisterType.ATTRIBUTE:
            self.__append(
                entity=AttributeRegisterActualValueEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_value=DataTransformHelpers.transform_for_gateway(
                        data_type=register_record.data_type,
                        value=register_record.actual_value,
                    ),
                ),
            )

        elif register_record.type == RegisterType.SETTING:
            self.__append(
                entity=SettingRegisterActualValueEntity(
                    device_id=register_record.device_id,
                    register_id=register_record.id,
                    register_value=DataTransformHelpers.transform_for_gateway(
                        data_type=register_record.data_type,
                        value=register_record.actual_value,
                    ),
                ),
            )

    # -----------------------------------------------------------------------------

    def __append(self, entity: BaseEntity) -> None:
        """Append new entity for consume"""
        try:
            self.__queue.put(item=entity)

        except QueueFull:
            self.__logger.error("Consumer processing queue is full. New messages could not be added")
