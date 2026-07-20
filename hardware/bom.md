# Mochi v0.1 — Bill of Materials

Matches shell v1 (`hardware/cad`, NOVA-style, rectangular face).
Cheap-and-best target: **~$175**. All parts commodity, Amazon-orderable.

| # | Part | Spec / pick | ~Cost | Notes |
|---|------|-------------|-------|-------|
| 1 | Raspberry Pi 5 | 4GB + official 27W USB-C PSU | $75 | Pi 4 works if you own one |
| 2 | microSD | 64GB, A2 rated | $10 | |
| 3 | Display | 4" rectangular IPS **DSI**, 800x480 (Waveshare 4inch DSI LCD) | $30 | The NOVA face. DSI, not SPI — SPI is too slow for 60fps animation. Measure before printing the head |
| 4 | Camera | Pi Camera Module 3 | $25 | Autofocus + low light for face ID. Budget alt: OV5647 board ~$9, worse face ID |
| 5 | Audio in | ReSpeaker 2-Mic HAT | $15 | Hardware AEC → barge-in later |
| 6 | Speaker | 3W 4Ω mini, ~40mm | $4 | Behind the front grille, drives off ReSpeaker out |
| 7 | Neck | 2x MG90S metal-gear servo (pan + tilt) | $10 | Metal gear, not SG90 plastic. Shell mounts them directly — no bracket kit needed |
| 8 | Servo driver | PCA9685 16-ch PWM | $5 | Pi GPIO alone jitters |
| 9 | Status LED | WS2812 ring (8–12 px) | $3 | Sits behind the translucent heart inlay |
| 10 | Fasteners | M2 x8 self-tap (~14), M2.5 x6 (4), M3 x10 (4), rubber feet, jumper wires | $8 | Matches cad/README screw plan |

Filament (friend's printer): ~500g PLA/PETG white + dark, small TPU spool
for the ears, a few meters translucent PETG for the heart.

Deferred (later versions): touch sensors (TTP223), IMU, arm servos,
N20 motors + TB6612 + VL53L0X cliff sensors + 18650 pack (v2.0 wheels).

## 3D printing

All parts in `hardware/cad/mochi.scad` — see `hardware/cad/README.md` for
the print plan. Cosmetics (ears, arms, pods, heart, neck post) print now;
head, body, and base only after measuring real parts into `params.scad`.
