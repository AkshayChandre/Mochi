# Mochi v0.1 — Bill of Materials

Cheap-route target: **~$150–190**. All parts commodity, Amazon-orderable.

| # | Part | Spec / pick | ~Cost | Notes |
|---|------|-------------|-------|-------|
| 1 | Raspberry Pi 5 | 4GB + official 27W USB-C PSU | $75 | Pi 4 works if you own one |
| 2 | microSD | 64GB, A2 rated | $10 | |
| 3 | Display | Waveshare 4" round DSI, 720x720 | $40 | The blob's face — worth it |
| 4 | Camera | Pi Camera Module 3 | $25 | Face ID + look-at-you |
| 5 | Audio in | ReSpeaker 2-Mic HAT | $15 | Hardware AEC → barge-in |
| 6 | Speaker | 3W 4Ω mini | $4 | Drives off ReSpeaker out |
| 7 | Neck | 2x MG90S metal-gear servo + pan-tilt kit | $12 | Metal gear, not SG90 plastic |
| 8 | Servo driver | PCA9685 16-ch PWM | $5 | Pi GPIO alone jitters |
| 9 | Status LED | WS2812 ring (12–16 px) | $3 | Heart = camera/mic indicator |
| 10 | Fasteners | M2/M2.5 assortment, jumper wires | $8 | |

Deferred (later versions): touch sensors (TTP223), IMU, arm servos,
N20 motors + TB6612 + VL53L0X cliff sensors + 18650 pack (v2.0 wheels).

## 3D printing (after parts arrive — measure real components first)

- Front face ring / display bezel
- Back shell (blob silhouette, two-piece)
- Internal neck mount for pan-tilt + PCA9685
- Weighted base plate
- Ears/nubs in TPU if included (rigid PLA snaps)
