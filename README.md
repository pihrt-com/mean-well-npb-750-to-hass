# Mean Well NPB-750 to Home Assistant

Custom integration for a MEAN WELL NPB-750-24 charger connected to Home Assistant OS through a Waveshare USB-CAN-A adapter.

The adapter is a serial USB-CAN bridge, not SocketCAN. Use the stable HA OS path:

```text
/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
```

## Defaults

- Charger: MEAN WELL NPB-750-24
- CAN protocol: CAN 2.0B extended frame
- CAN bitrate: 250 kbit/s
- Charger address: `0x03`
- Adapter serial bitrate: `2000000`
- Adapter protocol: Waveshare variable-length serial protocol

## Install

Copy `custom_components/mean_well_npb_750` into:

```text
/config/custom_components/mean_well_npb_750
```

Restart Home Assistant and add `Mean Well NPB-750` from Devices & services.

Recommended settings:

```text
Serial device: /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0
CAN address: 3
CAN bitrate: 250000
Serial baudrate: 2000000
```

## Entities

- Sensors: input voltage, output voltage, output current, internal temperature, fault status, charge status, system status
- Switch: output operation on/off
- Numbers: output voltage set, output current set

The setpoint entities use `VOUT_SET` and `IOUT_SET`. The Mean Well manual says these commands can be invalid in charging mode; they are mainly useful in power-supply mode.

## Protocol Notes

Mean Well CAN IDs:

```text
Controller -> charger: 0x000C01XX
Charger -> controller: 0x000C00XX
Broadcast -> charger: 0x000C01FF
```

Waveshare variable-length serial frame:

```text
AA TYPE ID... DATA... 55
```

For extended CAN data frames, `TYPE = 0xC0 | 0x20 | DLC` and the CAN ID is little-endian.

## Sources

- Local `NPB,NPP-E.pdf`: Mean Well NPB/NPP user manual, CANBus protocol section.
- Local `CANBus_MW_PS.pdf`: Mean Well CANBus command list.
- Local `nabijec 230v-24v NPB-750-spec.pdf`: NPB-750 datasheet.
- Waveshare wiki: USB-CAN-A and serial conversion protocol.
