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
FastyBird BUS connector plugin api module validator for API v1
"""

# Library libs
from fb_bus_connector_plugin.types import Packet, PairingResponse, ProtocolVersion


class V1Validator:
    """
    BUS payload validator

    @package        FastyBird:FastyBirdBusConnectorPlugin!
    @module         api

    @author         Adam Kadlec <adam.kadlec@fastybird.com>
    """

    @classmethod
    def validate(cls, payload: bytearray) -> bool:
        """Validate topic against sets of regular expressions"""
        return True

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_version(cls, payload: bytearray) -> bool:
        """Validate payload against version definition"""
        return ProtocolVersion(int(payload[0])) == ProtocolVersion.V1

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_read_single_register(cls, payload: bytearray) -> bool:
        """Validate payload against read single register packet structure"""
        return Packet(int(payload[1])) == Packet.READ_SINGLE_REGISTER

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_read_multiple_registers(cls, payload: bytearray) -> bool:
        """Validate payload against read multiple registers packet structure"""
        return Packet(int(payload[1])) == Packet.READ_MULTIPLE_REGISTERS

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_write_single_register(cls, payload: bytearray) -> bool:
        """Validate payload against write single register packet structure"""
        return Packet(int(payload[1])) == Packet.WRITE_SINGLE_REGISTER

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_write_multiple_registers(cls, payload: bytearray) -> bool:
        """Validate payload against write multiple registers packet structure"""
        return Packet(int(payload[1])) == Packet.WRITE_MULTIPLE_REGISTERS

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_report_single_register(cls, payload: bytearray) -> bool:
        """Validate payload against report single register packet structure"""
        return Packet(int(payload[1])) == Packet.REPORT_SINGLE_REGISTER

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_get_device_state(cls, payload: bytearray) -> bool:
        """Validate payload against get device state packet structure"""
        return Packet(int(payload[1])) == Packet.READ_STATE

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_set_device_state(cls, payload: bytearray) -> bool:
        """Validate payload against set device state packet structure"""
        return Packet(int(payload[1])) == Packet.WRITE_STATE

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_report_device_state(cls, payload: bytearray) -> bool:
        """Validate payload against report device state packet structure"""
        return Packet(int(payload[1])) == Packet.REPORT_STATE

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pub_sub_write_register_key(cls, payload: bytearray) -> bool:
        """Validate payload against pub/sub write register key packet structure"""
        return Packet(int(payload[1])) == Packet.PUB_SUB_WRITE_REGISTER_KEY

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pub_sub_broadcast(cls, payload: bytearray) -> bool:
        """Validate payload against pub/sub broadcast packet structure"""
        return Packet(int(payload[1])) == Packet.PUB_SUB_BROADCAST_REGISTER_VALUE

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pong_response(cls, payload: bytearray) -> bool:
        """Validate payload against pong response packet structure"""
        return Packet(int(payload[1])) == Packet.PONG

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_discover_device(cls, payload: bytearray) -> bool:
        """Validate payload against pair device packet structure"""
        return Packet(int(payload[1])) == Packet.DISCOVER

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pair_command_search_devices(cls, payload: bytearray) -> bool:
        """Validate payload against search devices response packet structure"""
        return PairingResponse(int(payload[2])) == PairingResponse.SEARCH

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pair_command_write_address(cls, payload: bytearray) -> bool:
        """Validate payload against pair device command write address result packet structure"""
        return PairingResponse(int(payload[2])) == PairingResponse.WRITE_ADDRESS

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pair_command_provide_register_structure(cls, payload: bytearray) -> bool:
        """Validate payload against pair device command provide register structure packet structure"""
        return PairingResponse(int(payload[2])) == PairingResponse.PROVIDE_REGISTER_STRUCTURE

    # -----------------------------------------------------------------------------

    @classmethod
    def validate_pair_command_pairing_finished(cls, payload: bytearray) -> bool:
        """Validate payload against pair device command pairing finished packet structure"""
        return PairingResponse(int(payload[2])) == PairingResponse.PAIRING_FINISHED
