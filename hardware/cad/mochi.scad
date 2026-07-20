// Mochi shell v1 — NOVA-style desk companion.
// Set `part` below (or via -D on the CLI), render (F6), export STL.
// parts: head_front | head_back | ear | servo_cradle | neck_post |
//        body_shell | base_plate | pod | arm | heart_inlay | assembly

part = "assembly";

include <params.scad>
include <lib.scad>

face_t = wall + 1.5;

/* ------------------------------------------------ head ---- */

module head_front() {
    // faceplate: screen aperture, camera hole, countersunk corner screws
    difference() {
        linear_extrude(face_t) rrect(head_w, head_hh, head_r);
        // display active-area aperture
        translate([disp_act_dx, disp_act_dy - 4, -1])
            linear_extrude(face_t + 2) rrect(disp_act_w + 1, disp_act_h + 1, 3);
        // display PCB recess from the back
        translate([0, -4, -0.01])
            linear_extrude(disp_t) rrect(disp_w + clr, disp_h + clr, 3);
        // camera lens hole, top-centre
        translate([0, head_hh / 2 - 11, -1]) cylinder(d = cam_lens_d + 0.6, h = face_t + 2);
        // camera pcb screw pilots
        for (sx = [-1, 1])
            translate([sx * cam_hole_dx / 2, head_hh / 2 - 11 - cam_hole_dy / 2, disp_t])
                cylinder(d = m2_pilot, h = face_t);
        // faceplate screws into head_back bosses (mid-edges)
        for (sx = [-1, 1])
            translate([sx * (head_w / 2 - wall - boss_d / 2 - 1), 0, 0])
                csk_hole(m2_through, face_t);
        for (sy = [-1, 1])
            translate([0, sy * (head_hh / 2 - wall - boss_d / 2 - 1), 0])
                csk_hole(m2_through, face_t);
    }
}

module head_back() {
    difference() {
        union() {
            rbox3(head_w, head_hh, head_d, head_r);
            // faceplate bosses live inside; added after hollowing below
        }
        // hollow, open toward the front (z < 0 side)
        translate([0, 0, -wall])
            rbox3(head_w - 2 * wall, head_hh - 2 * wall, head_d, head_r - wall / 2);
        // ear sockets, top wall
        for (sx = [-1, 1])
            translate([sx * head_w * 0.28, head_hh / 2 - 6, head_d * 0.55])
                cube([ear_t + 0.5 + 8, 14, 6.5], center = true);
        // neck slot, bottom wall (tilt-servo shaft + clearance)
        translate([0, -head_hh / 2 - 1, head_d * 0.55])
            cube([30, 2 * wall + 4, 20], center = true);
    }
    // faceplate screw bosses (mid-edges), fused to side walls
    for (sx = [-1, 1])
        translate([sx * (head_w / 2 - wall - boss_d / 2 - 1), 0, 0])
            rotate([180, 0, 0]) translate([0, 0, -12]) boss(12, m2_pilot);
    for (sy = [-1, 1])
        translate([0, sy * (head_hh / 2 - wall - boss_d / 2 - 1), 0])
            rotate([180, 0, 0]) translate([0, 0, -12]) boss(12, m2_pilot);
    // servo-cradle bosses on the back wall, bottom centre
    for (sx = [-1, 1])
        translate([sx * 14, -head_hh / 2 + 22, head_d - wall - 8])
            boss(8, m2_pilot);
}

module ear() {
    // print in TPU; peg glues/press-fits into the head socket
    linear_extrude(ear_t) hull() {
        translate([-8, 0]) circle(r = 3);
        translate([8, 0]) circle(r = 3);
        translate([2, ear_h]) circle(r = 2.5);
    }
    translate([0, -6, ear_t / 2 - 3]) cube([8, 12, 6], center = true);
}

module servo_cradle() {
    // clamps the tilt servo against the head back wall
    difference() {
        linear_extrude(3.5) rrect(40, 26, 4);
        translate([0, 0, -1]) linear_extrude(6)
            square([servo_w + clr, servo_d + clr], center = true);
        for (sx = [-1, 1])
            translate([sx * servo_hole_dx / 2, 0, -1]) cylinder(d = m2_through, h = 6);
        for (sx = [-1, 1])
            translate([sx * 14, 0, 0]) csk_hole(m2_through, 3.5);
    }
}

/* ------------------------------------------------ neck ---- */

module neck_post() {
    difference() {
        union() {
            linear_extrude(45) rrect(30, 24, 6);          // column
            translate([0, 0, 45]) linear_extrude(4) rrect(30, 24, 6);
        }
        // bottom: pan-servo horn recess + screw pattern
        translate([0, 0, 1.6]) rotate([180, 0, 0]) horn_holes();
        translate([0, 0, -0.01]) cylinder(d = 23, h = 1.6);
        // top face: tilt-servo horn pattern on the front vertical face
        translate([0, -12 + 1.6, 49 - 12]) rotate([90, 0, 0]) horn_holes();
        translate([0, -12 - 0.01, 49 - 12]) rotate([-90, 0, 0]) cylinder(d = 23, h = 1.6);
        // lighten the column
        translate([0, 0, 8]) linear_extrude(30) rrect(18, 12, 4);
    }
}

/* ------------------------------------------------ body ---- */

module body_shell() {
    difference() {
        rbox3(body_w, body_hh, body_d, body_r);
        // hollow, open bottom (y < 0 side)
        translate([0, -wall, 0])
            rotate([-90, 0, 0]) translate([0, -body_d / 2 - wall, -body_hh / 2 - wall])
            rbox3(body_w - 2 * wall, body_d - 2 * wall, body_hh, body_r - wall / 2);
        // heart window, front wall
        translate([0, body_hh * 0.12, -1])
            linear_extrude(wall + 2) heart2d(heart_s);
        // heart inlay lip pocket (from inside, leaves 1.2 mm front lip)
        translate([0, body_hh * 0.12, 1.2])
            linear_extrude(wall + 2) heart2d(heart_s + 4);
        // speaker grille, lower front
        translate([0, -body_hh * 0.22, -1]) {
            cylinder(d = 2.6, h = wall + 2);
            for (a = [0 : 45 : 359], r = [spk_hole_r1, spk_hole_r2])
                rotate([0, 0, a + (r == spk_hole_r2 ? 22.5 : 0)])
                    translate([r, 0, 0]) cylinder(d = 2.6, h = wall + 2);
        }
        // mic holes, top wall
        for (sx = [-1, 1])
            translate([sx * mic_dx / 2, body_hh / 2 - wall - 1, body_d * 0.4])
                rotate([-90, 0, 0]) cylinder(d = 2.2, h = wall + 2);
        // pan-servo window, top wall centre
        translate([0, body_hh / 2 - wall - 1, body_d * 0.5])
            rotate([-90, 0, 0]) linear_extrude(wall + 2)
                square([servo_w + clr, servo_d + clr], center = true);
        for (sx = [-1, 1])
            translate([sx * servo_hole_dx / 2, body_hh / 2 - wall - 1, body_d * 0.5])
                rotate([-90, 0, 0]) cylinder(d = m2_pilot, h = wall + 2);
        // rear cable port + vents
        translate([0, -body_hh * 0.28, body_d - wall - 1])
            linear_extrude(wall + 2) slot2d(32, 14);
        for (i = [0 : 4])
            translate([0, body_hh * 0.05 + i * 8, body_d - wall - 1])
                linear_extrude(wall + 2) slot2d(40, 3);
        // arm peg holes, upper sides
        for (sx = [-1, 1])
            translate([sx * (body_w / 2 - wall - 1), body_hh * 0.18, body_d * 0.5])
                rotate([0, sx * 90, 0]) cylinder(d = 6.3, h = wall + 3);
        // pod peg holes, lower sides
        for (sx = [-1, 1], dz = [-20, 20])
            translate([sx * (body_w / 2 - wall - 1), -body_hh * 0.15, body_d * 0.5 + dz])
                rotate([0, sx * 90, 0]) cylinder(d = 4.3, h = wall + 3);
    }
    // base-plate bosses at bottom rim, fused to side walls
    for (sx = [-1, 1])
        translate([sx * (body_w / 2 - wall - boss_d / 2 - 1), -body_hh / 2 + 10, body_d / 2])
            rotate([90, 0, 0]) boss(10, m3_pilot);
    for (sz = [-1, 1])
        translate([0, -body_hh / 2 + 10, body_d / 2 + sz * (body_d / 2 - wall - boss_d / 2 - 1)])
            rotate([90, 0, 0]) boss(10, m3_pilot);
}

module base_plate() {
    difference() {
        linear_extrude(3) rrect(body_w - 2 * wall - clr, body_d - 2 * wall - clr, body_r - wall);
        // screws up into body bosses
        for (sx = [-1, 1])
            translate([sx * (body_w / 2 - wall - boss_d / 2 - 1), 0, 0])
                csk_hole(m3_through, 3);
        for (sy = [-1, 1])
            translate([0, sy * (body_d / 2 - wall - boss_d / 2 - 1), 0])
                csk_hole(m3_through, 3);
        // rear cable slot
        translate([0, body_d / 2 - 14, -1]) linear_extrude(5) slot2d(25, 8);
        // rubber-feet recesses
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (body_w / 2 - 18), sy * (body_d / 2 - 18), -0.01])
                cylinder(d = 11, h = 1);
    }
    // pi standoffs (ports toward the rear)
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * pi_hole_dx / 2, sy * pi_hole_dy / 2 + 4, 3])
            boss(pi_standoff_h, m25_pilot);
}

/* ------------------------------------------ cosmetics ---- */

module pod() {
    rotate([0, 90, 0]) rbox3(pod_w, pod_d, pod_l, 8);
    // wheel discs on the outer face
    for (dx = [-28, 0, 28])
        translate([pod_l / 2 + dx, 0, pod_w - 0.5]) cylinder(d = 22, h = 2);
    // pegs on the inner face
    for (dx = [-20, 20])
        translate([pod_l / 2 + dx, 0, 0.5]) rotate([180, 0, 0]) cylinder(d = 4, h = 8);
}

module arm() {
    hull() { sphere(6); translate([2, -26, 0]) sphere(5); }
    hull() { translate([2, -26, 0]) sphere(5); translate([12, -46, 0]) sphere(6.5); }
    rotate([0, 90, 0]) translate([0, 0, -9]) cylinder(d = 6, h = 10);
}

module heart_inlay() {
    // print in translucent filament; status LED sits behind it
    linear_extrude(wall) heart2d(heart_s + 3.4);
}

/* ------------------------------------------ assembly ---- */

module assembly() {
    color("WhiteSmoke") translate([0, 158, 30]) rotate([90, 0, 0]) head_back();
    color("DimGray") translate([0, 158, 29]) rotate([90, 0, 0]) head_front();
    color("WhiteSmoke") translate([0, 60, 42]) neck_post();
    color("WhiteSmoke") translate([0, 55, 0]) rotate([90, 0, 0]) body_shell();
    color("Crimson") translate([0, 66.5, -1]) rotate([90, 0, 0]) heart_inlay();
    for (sx = [-1, 1]) {
        color("DimGray") translate([sx * (body_w / 2 + pod_w / 2), 22, -pod_l / 2 + 42])
            rotate([0, sx * 90 + 90, 0]) pod();
        color("WhiteSmoke") translate([sx * (body_w / 2 + 6), 72, 42])
            rotate([0, sx * 90 - 90, 0]) arm();
        color("WhiteSmoke") translate([sx * head_w * 0.28, 195, 30]) rotate([0, 0, sx * -8]) ear();
    }
}

if (part == "head_front") head_front();
else if (part == "head_back") head_back();
else if (part == "ear") ear();
else if (part == "servo_cradle") servo_cradle();
else if (part == "neck_post") neck_post();
else if (part == "body_shell") body_shell();
else if (part == "base_plate") base_plate();
else if (part == "pod") pod();
else if (part == "arm") arm();
else if (part == "heart_inlay") heart_inlay();
else assembly();
