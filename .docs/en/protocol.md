# Pairing process

1. Gateway send `SEARCH_DEVICES - 0x01` packet
2. Device in pairing mode send reply `SEARCH_DEVICES - 0x01` packet with its current address and serial number/unique identifier
3. Gateway will check received address and serial number/unique identifier against database:
