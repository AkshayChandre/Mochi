"""Mochi face engine: procedural emotions, gaze, blink. Same file on PC and Pi."""

from __future__ import annotations

import math
import os
import random
import sys

import pygame as pg

from mochi.constants import (
    AUTOPILOT_INTERVAL,
    BACKGROUND,
    BEZEL,
    BLINK_INTERVAL,
    BLINK_SPEED,
    BOUNCE_AMP,
    BOUNCE_FREQ,
    BREATH_AMP,
    BREATH_PERIOD,
    DOUBLE_BLINK_CHANCE,
    DOUBLE_BLINK_DELAY,
    EASE_RATE,
    EMOTION_KEYS,
    EMOTIONS,
    EYE_COLOR,
    EYE_GAP,
    EYE_RAISE,
    FPS,
    GAZE_LERP_RATE,
    GAZE_RANGE,
    MOUTH_DEPTH,
    MOUTH_HALF_WIDTH,
    MOUTH_OFFSET_Y,
    MOUTH_THICKNESS,
    MOUTH_VISIBLE_MIN,
    NUMERIC_FIELDS,
    SIZE,
    SQUINT_FACTOR,
    STRETCH_CROSS,
    STRETCH_GAIN,
    STRETCH_LIMITS,
    TALK_AMP,
    TALK_BASE,
    TALK_FREQ,
    WANDER_INTERVAL,
    WANDER_RADIUS,
)


def ease(current: float, target: float, rate: float, dt: float) -> float:
    return current + (target - current) * (1.0 - math.exp(-rate * dt))


class MochiFace:
    def __init__(self) -> None:
        self.emotion = "neutral"
        self.state = {k: getattr(EMOTIONS["neutral"], k) for k in NUMERIC_FIELDS}
        self.gaze = pg.Vector2()
        self.gaze_target = pg.Vector2()
        self.gaze_vel = pg.Vector2()
        self.next_wander = 0.0
        self.blink = 1.0
        self.blink_phase = "idle"
        self.next_blink = random.uniform(*BLINK_INTERVAL)
        self.speaking = False
        self.t = 0.0

    def set_emotion(self, name: str) -> None:
        if name not in EMOTIONS:
            raise ValueError(f"unknown emotion {name!r}")
        self.emotion = name

    def set_speaking(self, speaking: bool) -> None:
        self.speaking = speaking

    def update(self, dt: float, mouse_gaze: pg.Vector2 | None = None) -> None:
        self.t += dt
        spec = EMOTIONS[self.emotion]
        for k in NUMERIC_FIELDS:
            self.state[k] = ease(self.state[k], getattr(spec, k), EASE_RATE, dt)
        self.update_gaze(dt, spec, mouse_gaze)
        self.update_blink(dt, self.emotion == "sleeping")

    def update_gaze(self, dt: float, spec, mouse: pg.Vector2 | None) -> None:
        if mouse is not None:
            self.gaze_target = mouse
        elif spec.gaze_lock is not None:
            self.gaze_target = pg.Vector2(spec.gaze_lock)
        else:
            self.next_wander -= dt
            if self.next_wander <= 0:
                self.next_wander = random.uniform(*WANDER_INTERVAL)
                a = random.uniform(0, math.tau)
                m = random.uniform(0, WANDER_RADIUS)
                self.gaze_target = pg.Vector2(math.cos(a) * m, math.sin(a) * m * 0.6)
        prev = self.gaze.copy()
        self.gaze = self.gaze.lerp(self.gaze_target, min(1.0, GAZE_LERP_RATE * dt))
        self.gaze_vel = (self.gaze - prev) / max(dt, 1e-6)

    def update_blink(self, dt: float, sleeping: bool) -> None:
        if self.blink_phase == "closing":
            self.blink = max(0.0, self.blink - BLINK_SPEED * dt)
            if self.blink == 0.0:
                self.blink_phase = "opening"
        elif self.blink_phase == "opening":
            self.blink = min(1.0, self.blink + BLINK_SPEED * dt)
            if self.blink == 1.0:
                self.blink_phase = "idle"
        else:
            self.next_blink -= dt
            if self.next_blink <= 0 and not sleeping:
                self.blink_phase = "closing"
                double = random.random() < DOUBLE_BLINK_CHANCE
                self.next_blink = DOUBLE_BLINK_DELAY if double else random.uniform(*BLINK_INTERVAL)

    def draw(self, screen: pg.Surface) -> None:
        s = self.state
        cx, cy = SIZE / 2, SIZE / 2
        screen.fill(BACKGROUND)
        pg.draw.circle(screen, BEZEL, (cx, cy), SIZE // 2 - 4, 3)

        breathe = 1.0 + BREATH_AMP * math.sin(self.t * math.tau / BREATH_PERIOD)
        bounce_y = -abs(math.sin(self.t * BOUNCE_FREQ)) * BOUNCE_AMP * s["bounce"]
        color = tuple(int(c * s["dim"]) for c in EYE_COLOR)

        v = self.gaze_vel
        lo, hi = STRETCH_LIMITS
        stretch_x = max(lo, min(hi, 1.0 + abs(v.x) * STRETCH_GAIN - abs(v.y) * STRETCH_CROSS))
        stretch_y = max(lo, min(hi, 1.0 + abs(v.y) * STRETCH_GAIN - abs(v.x) * STRETCH_CROSS))

        gx = self.gaze.x * GAZE_RANGE[0]
        gy = self.gaze.y * GAZE_RANGE[1] + bounce_y

        for side in (-1, 1):
            w = s["w"] * stretch_x * breathe
            h = s["h"] * stretch_y * breathe * max(0.05, self.blink)
            if side == 1:
                h *= 1.0 - SQUINT_FACTOR * s["squint"]
            r = min(s["r"], w / 2, h / 2)
            surf = pg.Surface((int(w) + 4, int(h) + 4), pg.SRCALPHA)
            pg.draw.rect(surf, color, (2, 2, int(w), int(h)), border_radius=int(r))
            if s["crescent"] > 0.02:
                cover_y = 2 + h * (1.08 - 0.78 * s["crescent"])
                cover = (0, cover_y, int(w) + 4, int(h) + 4)
                pg.draw.rect(surf, BACKGROUND, cover, border_radius=int(r))
            if abs(s["tilt"]) > 0.5:
                surf = pg.transform.rotate(surf, -side * s["tilt"])
            rect = surf.get_rect(center=(cx + side * EYE_GAP + gx, cy - EYE_RAISE + gy))
            screen.blit(surf, rect)

        mouth_val = s["mouth"]
        if self.speaking:
            mouth_val = TALK_BASE + TALK_AMP * math.sin(self.t * TALK_FREQ)
        self.draw_mouth(screen, cx, cy + MOUTH_OFFSET_Y + gy * 0.4, mouth_val, color)

    @staticmethod
    def draw_mouth(screen: pg.Surface, cx: float, cy: float, mouth: float, color: tuple) -> None:
        if abs(mouth) < MOUTH_VISIBLE_MIN:
            return
        depth = MOUTH_DEPTH * mouth
        pts = [
            (cx + (u / 8 - 1) * MOUTH_HALF_WIDTH, cy + depth * (1 - (u / 8 - 1) ** 2))
            for u in range(17)
        ]
        pg.draw.lines(screen, color, False, pts, MOUTH_THICKNESS)


def main() -> None:
    pg.init()
    screen = pg.display.set_mode((SIZE, SIZE))
    clock = pg.time.Clock()
    face = MochiFace()
    mouse_follow = autopilot = False
    auto_next = 0.0
    frame_limit = int(os.environ.get("MOCHI_FRAMES", 0))
    frame = 0

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for e in pg.event.get():
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            if e.type == pg.KEYDOWN:
                if pg.K_1 <= e.key <= pg.K_7:
                    face.set_emotion(EMOTION_KEYS[e.key - pg.K_1])
                    autopilot = False
                elif e.key == pg.K_m:
                    mouse_follow = not mouse_follow
                elif e.key == pg.K_a:
                    autopilot = not autopilot

        if autopilot:
            auto_next -= dt
            if auto_next <= 0:
                auto_next = AUTOPILOT_INTERVAL
                face.set_emotion(random.choice(EMOTION_KEYS[:-1]))

        mouse = None
        if mouse_follow:
            mx, my = pg.mouse.get_pos()
            mouse = pg.Vector2((mx - SIZE / 2) / (SIZE / 2), (my - SIZE / 2) / (SIZE / 2))
            if mouse.length() > 1:
                mouse.normalize_ip()

        face.update(dt, mouse)
        face.draw(screen)
        pg.display.set_caption(f"Mochi v0.1 — {face.emotion}  [1-7 emotion | M mouse | A auto]")
        pg.display.flip()

        frame += 1
        if frame_limit and frame >= frame_limit:
            pg.quit()
            return


if __name__ == "__main__":
    main()
