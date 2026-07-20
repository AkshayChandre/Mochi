# Mochi Shell v1 — Printable CAD

NOVA-style desk companion shell. Parametric OpenSCAD: every real-part
dimension is a variable in `params.scad`.

## CRITICAL — before final printing

Values marked `MEASURE` in `params.scad` are **placeholders**. When the real
parts arrive: measure with calipers, update `params.scad`, re-export every
STL. Cosmetic parts (ears, arms, pods, heart) have no dependency on
electronics and can be printed today.

## Exporting STLs

1. Install [OpenSCAD](https://openscad.org) (free).
2. Open `mochi.scad`, set `part = "head_back"` (etc.), press F6, then
   File → Export → STL.
3. Or CLI, all parts at once:

```powershell
foreach ($p in "head_front","head_back","ear","servo_cradle","neck_post",
               "body_shell","base_plate","pod","arm","heart_inlay") {
  openscad -o "stl/$p.stl" -D "part=""$p""" mochi.scad
}
```

## Print plan

| Part | Qty | Material | Notes |
|------|-----|----------|-------|
| head_front | 1 | PLA/PETG dark | flat side down, no supports |
| head_back | 1 | PLA/PETG white | opening down, supports for ear sockets |
| ear | 2 | **TPU** | rigid PLA snaps — TPU survives desk life |
| servo_cradle | 1 | PETG | |
| neck_post | 1 | PETG, 5 walls | strength part — print solid-ish |
| body_shell | 1 | PLA/PETG white | opening down, supports for windows |
| base_plate | 1 | PETG | flat, no supports |
| pod | 2 | PLA dark | flat face down |
| arm | 2 | PLA white | supports; print one mirrored in slicer |
| heart_inlay | 1 | translucent PETG | LED glows through it |

0.2 mm layers, 3 walls, 15–20% infill unless noted.

## Fasteners (order with the electronics)

M2 x 8 self-tapping (~14): faceplate, servo flanges, cradle, horn screws use
the ones bundled with servos. M2.5 x 6 (~4): Pi to standoffs. M3 x 10 (~4):
base plate. Rubber feet 10 mm (4).

## Assembly order

base_plate + Pi → pan servo into body top → body_shell onto base → neck_post
onto pan horn → tilt servo + cradle into head_back → head onto neck horn →
display + camera into head_front → faceplate screws → ears, arms, pods,
heart press in.
