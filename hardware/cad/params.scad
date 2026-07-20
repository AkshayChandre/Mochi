// Mochi shell v1 — all dimensions in mm.
// Values marked MEASURE are placeholders: verify with calipers against the
// real part, update here, re-export every STL. Do not final-print before that.

wall = 2.5;
clr  = 0.4;

// screws (self-tapping into printed bosses)
m2_pilot   = 1.7;  m2_through  = 2.4;
m25_pilot  = 2.2;  m25_through = 2.9;
m3_pilot   = 2.6;  m3_through  = 3.4;
boss_d     = 7;

// display — MEASURE (placeholder: generic 4" rectangular DSI panel)
disp_w = 97;   disp_h = 59;   disp_t = 5.5;
disp_act_w = 86;  disp_act_h = 52;
disp_act_dx = 0;  disp_act_dy = 0;    // active-area offset from PCB centre

// camera module 3 — MEASURE lens position on your unit
cam_hole_dx = 21;  cam_hole_dy = 12.5;
cam_lens_d  = 7.6;

// raspberry pi 5
pi_w = 85;  pi_h = 56;
pi_hole_dx = 58;  pi_hole_dy = 49;
pi_standoff_h = 6;

// mg90s servo — MEASURE your batch
servo_w = 23.0;  servo_d = 12.4;
servo_hole_dx = 27.8;

// speaker — MEASURE
spk_hole_r1 = 8;  spk_hole_r2 = 15;

// respeaker 2-mic hat: mic-to-mic distance — MEASURE
mic_dx = 58;

// head shell
head_w = 112;  head_hh = 86;  head_d = 58;  head_r = 16;

// body shell
body_w = 118;  body_hh = 95;  body_d = 84;  body_r = 18;

// cosmetics
ear_h = 42;  ear_t = 4;
pod_l = 95;  pod_d = 34;  pod_w = 18;
heart_s = 30;

$fn = 64;
