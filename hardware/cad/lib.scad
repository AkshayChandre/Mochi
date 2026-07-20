// shared modules — include after params.scad

module rrect(w, h, r) {
    offset(r) offset(-r) square([w, h], center = true);
}

module rbox3(w, h, d, r) {
    // fully rounded box, centred in x/y, spans z = 0..d
    hull()
        for (x = [-1, 1], y = [-1, 1], z = [0, 1])
            translate([x * (w / 2 - r), y * (h / 2 - r), z == 0 ? r : d - r])
                sphere(r);
}

module boss(h, pilot) {
    difference() {
        cylinder(d = boss_d, h = h);
        translate([0, 0, 2]) cylinder(d = pilot, h = h);
    }
}

module csk_hole(d_through, plate_t, head_d = 5.6) {
    // countersunk through-hole along +z from 0
    translate([0, 0, -0.01]) cylinder(d = d_through, h = plate_t + 0.02);
    translate([0, 0, plate_t - 1.4]) cylinder(d1 = d_through, d2 = head_d, h = 1.45);
}

module horn_holes(r = 7, d = 1.8) {
    // screw pattern for a standard micro-servo cross horn
    for (a = [0 : 90 : 270])
        rotate(a) translate([r, 0, -6]) cylinder(d = d, h = 20);
    translate([0, 0, -6]) cylinder(d = 5.4, h = 20);   // hub clearance
}

module heart2d(s) {
    translate([0, -s * 0.3]) rotate(225) {
        square(s);
        translate([s / 2, s]) circle(d = s);
        translate([s, s / 2]) circle(d = s);
    }
}

module slot2d(l, w) {
    hull() {
        translate([-l / 2 + w / 2, 0]) circle(d = w);
        translate([ l / 2 - w / 2, 0]) circle(d = w);
    }
}
