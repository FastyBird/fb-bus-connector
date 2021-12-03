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
FastyBird BUS connector plugin DI container
"""

# pylint: disable=no-value-for-parameter

# Python base dependencies
import logging

# Library dependencies
from kink import di

# Library libs
from fb_bus_connector_plugin.api.v1parser import V1Parser
from fb_bus_connector_plugin.api.v1validator import V1Validator
from fb_bus_connector_plugin.clients.client import Client, ClientFactory
from fb_bus_connector_plugin.connector import FbBusConnector
from fb_bus_connector_plugin.consumers.consumer import Consumer
from fb_bus_connector_plugin.handlers.apiv1 import ApiV1Handler
from fb_bus_connector_plugin.handlers.handler import Handler
from fb_bus_connector_plugin.logger import Logger
from fb_bus_connector_plugin.pairing.apiv1 import ApiV1Pairing
from fb_bus_connector_plugin.pairing.pairing import DevicesPairing
from fb_bus_connector_plugin.publishers.apiv1 import ApiV1Publisher
from fb_bus_connector_plugin.publishers.publisher import Publisher
from fb_bus_connector_plugin.receivers.device import DeviceItemReceiver
from fb_bus_connector_plugin.receivers.pairing import PairingReceiver
from fb_bus_connector_plugin.receivers.receiver import Receiver
from fb_bus_connector_plugin.receivers.registers import RegisterItemReceiver
from fb_bus_connector_plugin.registry.model import DevicesRegistry, RegistersRegistry


def create_container(logger: logging.Logger = logging.getLogger("dummy")) -> None:
    """Create FB BUS connector services"""
    di[Logger] = Logger(logger=logger)
    di["fb-bus-connector-plugin_logger"] = di[Logger]

    # Processed messages consumer
    di[Consumer] = Consumer(logger=di[Logger])
    di["fb-bus-connector-plugin_messages-consumer"] = di[Consumer]

    # Registers
    di[RegistersRegistry] = RegistersRegistry(consumer=di[Consumer])
    di["fb-bus-connector-plugin_registers-registry"] = di[RegistersRegistry]
    di[DevicesRegistry] = DevicesRegistry(consumer=di[Consumer])
    di["fb-bus-connector-plugin_devices-registry"] = di[DevicesRegistry]

    # API tools
    di[V1Validator] = V1Validator()
    di["fb-bus-connector-plugin_api-v1-validator"] = di[V1Validator]
    di[V1Parser] = V1Parser(devices_registry=di[DevicesRegistry], registers_registry=di[RegistersRegistry])
    di["fb-bus-connector-plugin_api-v1-parser"] = di[V1Parser]

    # BUS client
    di[Client] = Client()
    di["fb-bus-connector-plugin_data-client-proxy"] = di[Client]

    # Devices pairing
    di[ApiV1Pairing] = ApiV1Pairing(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        client=di[Client],
        logger=di[Logger],
    )
    di["fb-bus-connector-plugin_devices-pairing-api-v1"] = di[ApiV1Pairing]

    di[DevicesPairing] = DevicesPairing()  # type: ignore[call-arg]
    di["fb-bus-connector-plugin_devices-pairing-proxy"] = di[DevicesPairing]

    # Clients receivers
    di[RegisterItemReceiver] = RegisterItemReceiver(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        logger=di[Logger],
    )
    di["fb-bus-connector-plugin_registers-receiver"] = di[RegisterItemReceiver]

    di[DeviceItemReceiver] = DeviceItemReceiver(devices_registry=di[DevicesRegistry], logger=di[Logger])
    di["fb-bus-connector-plugin_device-receiver"] = di[DeviceItemReceiver]

    di[PairingReceiver] = PairingReceiver(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        device_pairing=di[ApiV1Pairing],
        logger=di[Logger],
    )
    di["fb-bus-connector-plugin_pairing-receiver"] = di[PairingReceiver]

    di[Receiver] = Receiver(logger=di[Logger])
    di["fb-bus-connector-plugin_receiver-proxy"] = di[Receiver]

    # Clients handlers
    di[ApiV1Handler] = ApiV1Handler(parser=di[V1Parser], receiver=di[Receiver], logger=di[Logger])
    di["fb-bus-connector-plugin_bus-handler-api-v1"] = di[ApiV1Handler]

    di[Handler] = Handler()  # type: ignore[call-arg]
    di["fb-bus-connector-plugin_bus-handler-proxy"] = di[Handler]

    # Clients publishers
    di[ApiV1Publisher] = ApiV1Publisher(
        devices_registry=di[DevicesRegistry],
        registers_registry=di[RegistersRegistry],
        client=di[Client],
        logger=di[Logger],
    )
    di["fb-bus-connector-plugin_api-v1-publisher"] = di[ApiV1Publisher]

    di[Publisher] = Publisher()  # type: ignore[call-arg]
    di["fb-bus-connector-plugin_publisher-proxy"] = di[Publisher]

    # Connector clients factory
    di[ClientFactory] = ClientFactory(
        client=di[Client],
        handler=di[Handler],
        logger=di[Logger],
    )
    di["fb-bus-connector-plugin_data-client-factory"] = di[ClientFactory]

    # Plugin main connector service
    di[FbBusConnector] = FbBusConnector(
        receiver=di[Receiver],
        publisher=di[Publisher],
        consumer=di[Consumer],
        devices_registry=di[DevicesRegistry],
        client=di[Client],
        client_factory=di[ClientFactory],
        pairing_handler=di[DevicesPairing],
        logger=di[Logger],
    )
    di["fb-bus-connector-plugin_connector"] = di[FbBusConnector]
