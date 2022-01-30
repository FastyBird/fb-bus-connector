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
FastyBird BUS connector DI container
"""

# pylint: disable=no-value-for-parameter

# Python base dependencies
import logging

# Library dependencies
from kink import di
from whistle import EventDispatcher

# Library libs
from fastybird_fb_bus_connector.api.v1parser import V1Parser
from fastybird_fb_bus_connector.clients.client import Client
from fastybird_fb_bus_connector.connector import FbBusConnector
from fastybird_fb_bus_connector.entities import FbBusConnectorEntity
from fastybird_fb_bus_connector.events.listeners import EventsListener
from fastybird_fb_bus_connector.logger import Logger
from fastybird_fb_bus_connector.pairing.apiv1 import ApiV1Pairing
from fastybird_fb_bus_connector.pairing.pairing import Pairing
from fastybird_fb_bus_connector.publishers.apiv1 import ApiV1Publisher
from fastybird_fb_bus_connector.publishers.publisher import Publisher
from fastybird_fb_bus_connector.receivers.device import (
    DeviceItemReceiver,
    DiscoverReceiver,
    RegisterItemReceiver,
)
from fastybird_fb_bus_connector.receivers.receiver import Receiver
from fastybird_fb_bus_connector.registry.model import DevicesRegistry, RegistersRegistry


def create_connector(
    connector: FbBusConnectorEntity,
    logger: logging.Logger = logging.getLogger("dummy"),
) -> FbBusConnector:
    """Create FB BUS connector services"""
    if isinstance(logger, logging.Logger):
        connector_logger = Logger(connector_id=connector.id, logger=logger)

        di[Logger] = connector_logger
        di["fb-bus-connector_logger"] = di[Logger]

    else:
        connector_logger = logger

    di[EventDispatcher] = EventDispatcher()
    di["fb-bus-connector_events-dispatcher"] = di[EventDispatcher]

    # Registers
    di[RegistersRegistry] = RegistersRegistry(event_dispatcher=di[EventDispatcher])
    di["fb-bus-connector_registers-registry"] = di[RegistersRegistry]
    di[DevicesRegistry] = DevicesRegistry(
        registers_registry=di[RegistersRegistry],
        event_dispatcher=di[EventDispatcher],
    )
    di["fb-bus-connector_devices-registry"] = di[DevicesRegistry]

    # API utils
    di[V1Parser] = V1Parser(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
    )
    di["fb-bus-connector_api-v1-parser"] = di[V1Parser]

    # Communication client
    di[Client] = Client(logger=connector_logger)
    di["fb-bus-connector_data-client-proxy"] = di[Client]

    # Devices pairing
    di[ApiV1Pairing] = ApiV1Pairing(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        client=di[Client],
        logger=connector_logger,
    )
    di["fb-bus-connector_devices-pairing-api-v1"] = di[ApiV1Pairing]

    di[Pairing] = Pairing(
        pairing=[
            di[ApiV1Pairing],
        ],
    )
    di["fb-bus-connector_devices-pairing-proxy"] = di[Pairing]

    # Communication receivers
    di[RegisterItemReceiver] = RegisterItemReceiver(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        logger=connector_logger,
    )
    di["fb-bus-connector_registers-receiver"] = di[RegisterItemReceiver]

    di[DeviceItemReceiver] = DeviceItemReceiver(devices_registry=di[DevicesRegistry], logger=connector_logger)
    di["fb-bus-connector_device-receiver"] = di[DeviceItemReceiver]

    di[DiscoverReceiver] = DiscoverReceiver(device_pairing=di[ApiV1Pairing])
    di["fb-bus-connector_discovery-receiver"] = di[DiscoverReceiver]

    di[Receiver] = Receiver(
        receivers=[
            di[DeviceItemReceiver],
            di[RegisterItemReceiver],
            di[DiscoverReceiver],
        ],
        parser=di[V1Parser],
        logger=connector_logger,
    )
    di["fb-bus-connector_receiver-proxy"] = di[Receiver]

    # Data publishers
    di[ApiV1Publisher] = ApiV1Publisher(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        client=di[Client],
        logger=connector_logger,
    )
    di["fb-bus-connector_api-v1-publisher"] = di[ApiV1Publisher]

    di[Publisher] = Publisher(
        publishers=[di[ApiV1Publisher]],
        devices_registry=di[DevicesRegistry],
    )
    di["fb-bus-connector_publisher-proxy"] = di[Publisher]

    # Inner events system
    di[EventsListener] = EventsListener(  # type: ignore[call-arg]
        connector_id=connector.id,
        event_dispatcher=di[EventDispatcher],
        logger=connector_logger,
    )
    di["fb-bus-connector_events-listener"] = di[EventsListener]

    # Main connector service
    connector_service = FbBusConnector(  # type: ignore[call-arg]
        connector_id=connector.id,
        receiver=di[Receiver],
        publisher=di[Publisher],
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        client=di[Client],
        pairing=di[Pairing],
        logger=connector_logger,
    )
    di[FbBusConnector] = connector_service
    di["fb-bus-connector_connector"] = connector_service

    return connector_service
