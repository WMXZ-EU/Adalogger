# CircuitPython microPAM code for rp2040 Adalogger

![microPAM](./microPAM.jpg)

Special issue:

The Passive Acoustic Monitoring (PAM) uses an ICS43434 I2S microphone, which has the following Timing diagram
![I2S timing](./image.png)
that is, the MSB is fetched on bit #2 and not on bit #1. This requires a custom I2S protocol.

See microPAM.pdf for more details