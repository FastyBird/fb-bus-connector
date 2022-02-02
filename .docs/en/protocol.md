# Discovery process

This connector has implemented semi-automatic auto discovery proces. Discovery mode could be enabled via user interface. 

### Discovery of new devices

When discovery is enabled triggered, connector start broadcasting of `DISCOVER - 0x04` packet. Each device in discovery mode should reply to this packet with its own description

When new device is discovered by connector, device details are processed and prepared for pairing.

TBD...