from __future__ import annotations

import math
import os
import random
import sys

import pygame as pg

from mochi.constants import (
    AUTOPILOT_INTERVAL,
    BACKGROUND,
    BANNER_MARGIN,
    BANNER_SECONDS,
    BEZEL,
    BLINK_INTERVAL,
    BLINK_SPEED,
    BLUSH_ALPHA,
    BLUSH_COLOR,
    BLUSH_EMOTIONS,
    BOUNCE_AMP,
    BOUNCE_FREQ,
    BREATH_AMP,
    BREATH_PERIOD,
    BROW_ANGLE,
    BROW_LENGTH,
    BROW_LIFT,
    BROW_THICKNESS,
    CARD_LINE_H,
    CARD_MAX_LINES,
    CARD_PANEL_TOP,
    CARD_SCROLL_DELAY,
    CARD_SCROLL_SPEED,
    CARD_SECONDS,
    CARD_WRAP,
    COLOR_EASE_RATE,
    COUNT_FONT,
    DOUBLE_BLINK_CHANCE,
    DOUBLE_BLINK_DELAY,
    EASE_RATE,
    EMOTION_COLORS,
    EMOTION_KEYS,
    EMOTIONS,
    EYE_GAP,
    EYE_RAISE,
    FPS,
    GAZE_LERP_RATE,
    GAZE_RANGE,
    GESTURE_AMP,
    GESTURE_FREQ,
    GESTURE_SECONDS,
    GESTURES,
    GLINT_COLOR,
    IDLE_SLEEP_SECONDS,
    MOUTH_DEPTH,
    MOUTH_HALF_WIDTH,
    MOUTH_OFFSET_Y,
    MOUTH_THICKNESS,
    MOUTH_VISIBLE_MIN,
    NUMERIC_FIELDS,
    PARADE_SECONDS,
    SHADES_BRIDGE,
    SHADES_TILT,
    SHAKE_AMP,
    SHAKE_FREQ,
    SIZE,
    SPARKLE_POINTS,
    SQUINT_FACTOR,
    STRETCH_CROSS,
    STRETCH_GAIN,
    STRETCH_LIMITS,
    TALK_AMP,
    TALK_BASE,
    TALK_FREQ,
    TALK_LIP,
    TALK_NARROW,
    TALK_OPEN,
    TALK_WIDTH,
    TALK_WOBBLE,
    TEAR_COLOR,
    TEAR_FALL,
    TEAR_PERIOD,
    TEAR_RADIUS,
    TERMINAL_BG,
    TERMINAL_FG,
    WANDER_INTERVAL,
    WANDER_RADIUS,
)


def ease(current: float, target: float, rate: float, dt: float) -> float:
    return current + (target - current) * (1.0 - math.exp(-rate * dt))

def heart_points(cx: float, cy: float, w: float, h: float) -> list[tuple[float, float]]:
    pts = []
    for i in range(28):
        t = math.tau * i / 28
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * w / 34, cy - y * h / 30))
    return pts

def spiral_points(cx: float, cy: float, radius: float, turns: float = 2.4) -> list[tuple]:
    steps = 46
    return [
        (
            cx + radius * (i / steps) * math.cos(math.tau * turns * i / steps),
            cy + radius * (i / steps) * math.sin(math.tau * turns * i / steps),
        )
        for i in range(steps + 1)
    ]

def star_points(cx: float, cy: float, size: float, spikes: int = 4) -> list[tuple[float, float]]:
    pts = []
    for i in range(spikes * 2):
        a = math.tau * i / (spikes * 2) - math.pi / 2
        r = size if i % 2 == 0 else size * 0.42
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def talk_openness(t: float) -> float:
    wave = sum(w * math.sin(t * TALK_FREQ * m + p) for m, w, p in TALK_WOBBLE)
    return max(0.0, min(1.0, TALK_BASE + TALK_AMP * wave))

class MochiFace:
    def __init__(self) -> None:
        self.emotion = "neutral"
        self.state = {k: getattr(EMOTIONS["neutral"], k) for k in NUMERIC_FIELDS}
        self.rgb = list(EMOTION_COLORS["neutral"])
        self.gaze = pg.Vector2()
        self.gaze_target = pg.Vector2()
        self.gaze_vel = pg.Vector2()
        self.next_wander = 0.0
        self.blink = 1.0
        self.blink_phase = "idle"
        self.next_blink = random.uniform(*BLINK_INTERVAL)
        self.speaking = False
        self.allowed = False
        self.voice = None
        self.idle_since = 0.0
        self.parade: list[str] = []
        self.parade_t = 0.0
        self.card_lines: list[str] = []
        self.card_until = 0.0
        self.card_started = 0.0
        self.card_scroll = 0.0
        self.count_text = ""
        self.count_until = 0.0
        self.banner_text = ""
        self.banner_until = 0.0
        self.gesture = ""
        self.gesture_until = 0.0
        self.fonts: dict[int, pg.font.Font] = {}
        self.t = 0.0

    def set_emotion(self, name: str) -> None:
        if name not in EMOTIONS:
            raise ValueError(f"unknown emotion {name!r}")
        self.emotion = name
        if name != "sleeping":
            self.idle_since = self.t

    def set_speaking(self, speaking: bool) -> None:
        """Permission to talk. When a real voice is attached the mouth also
        needs actual audio, otherwise it mimes through the long gaps while
        the model is still writing the next sentence."""
        self.allowed = speaking
        if self.voice is None:
            self.speaking = speaking

    def play_parade(self) -> None:
        self.parade = [*EMOTION_KEYS, "neutral"]
        self.parade_t = 0.0

    def play_gesture(self, kind: str) -> None:
        if kind not in GESTURES:
            raise ValueError(f"unknown gesture {kind!r}")
        self.gesture = kind
        self.gesture_until = self.t + GESTURE_SECONDS
        self.idle_since = self.t

    def show_banner(self, text: str) -> None:
        """Big text under the eyes - the face keeps being a face."""
        self.banner_text = " ".join(text.split())[:64]
        self.banner_until = self.t + BANNER_SECONDS
        self.idle_since = self.t

    def show_count(self, text: str) -> None:
        self.count_text = text
        self.count_until = self.t + 1.4
        self.idle_since = self.t

    def show_card(self, text: str) -> None:
        lines: list[str] = []
        for raw in text.splitlines():
            if not raw:
                lines.append("")
            while raw:
                lines.append(raw[:CARD_WRAP])
                raw = raw[CARD_WRAP:]
        self.card_lines = lines[:CARD_MAX_LINES]
        self.card_scroll = 0.0
        self.card_started = self.t
        self.card_until = self.t + CARD_SECONDS + 0.6 * len(self.card_lines)

    def font(self, size: int) -> pg.font.Font:
        if size not in self.fonts:
            self.fonts[size] = pg.font.SysFont("consolas,couriernew,monospace", size)
        return self.fonts[size]

    def update(self, dt: float, mouse_gaze: pg.Vector2 | None = None) -> None:
        self.t += dt
        if self.voice is not None:
            self.speaking = self.allowed and self.voice()
        if self.card_lines:
            if self.t >= self.card_until:
                self.card_lines = []
                self.card_scroll = 0.0
            elif self.t > self.card_started + CARD_SCROLL_DELAY:
                panel_h = SIZE - int(SIZE * CARD_PANEL_TOP) - 40
                max_scroll = max(0.0, len(self.card_lines) * CARD_LINE_H - panel_h)
                self.card_scroll = min(self.card_scroll + CARD_SCROLL_SPEED * dt, max_scroll)
        if (
            self.emotion == "neutral"
            and not self.parade
            and not self.card_lines
            and self.t - self.idle_since > IDLE_SLEEP_SECONDS
        ):
            self.emotion = "sleeping"
        if self.parade:
            self.parade_t -= dt
            if self.parade_t <= 0:
                self.set_emotion(self.parade.pop(0))
                self.parade_t = PARADE_SECONDS
        spec = EMOTIONS[self.emotion]
        for k in NUMERIC_FIELDS:
            self.state[k] = ease(self.state[k], getattr(spec, k), EASE_RATE, dt)
        target = EMOTION_COLORS[self.emotion]
        for i in range(3):
            self.rgb[i] = ease(self.rgb[i], target[i], COLOR_EASE_RATE, dt)
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
        if self.count_text and self.t < self.count_until:
            self.draw_count(screen)
            return
        card = bool(self.card_lines) and self.t < self.card_until
        s = self.state
        scale = 0.5 if card else 1.0
        cx, cy = SIZE / 2, SIZE / 2
        eye_cy = SIZE * 0.18 if card else cy - EYE_RAISE
        color = tuple(int(self.rgb[i] * s["dim"]) for i in range(3))
        screen.fill(BACKGROUND)
        if not card:
            pg.draw.circle(screen, BEZEL, (cx, cy), SIZE // 2 - 4, 3)

        breathe = 1.0 + BREATH_AMP * math.sin(self.t * math.tau / BREATH_PERIOD)
        bounce_y = -abs(math.sin(self.t * BOUNCE_FREQ)) * BOUNCE_AMP * s["bounce"]

        v = self.gaze_vel
        lo, hi = STRETCH_LIMITS
        stretch_x = max(lo, min(hi, 1.0 + abs(v.x) * STRETCH_GAIN - abs(v.y) * STRETCH_CROSS))
        stretch_y = max(lo, min(hi, 1.0 + abs(v.y) * STRETCH_GAIN - abs(v.x) * STRETCH_CROSS))

        gx = self.gaze.x * GAZE_RANGE[0]
        gy = self.gaze.y * GAZE_RANGE[1] + bounce_y
        if s["shake"] > 0.02:
            gx += math.sin(self.t * SHAKE_FREQ) * SHAKE_AMP * s["shake"]
        if self.gesture and self.t < self.gesture_until:
            left = self.gesture_until - self.t
            swing = math.sin(left * GESTURE_FREQ) * GESTURE_AMP * (left / GESTURE_SECONDS)
            if self.gesture == "nod":
                gy += swing
            else:
                gx += swing

        style = EMOTIONS[self.emotion].style
        centers: list[tuple[float, float]] = []
        for side in (-1, 1):
            w = s["w"] * stretch_x * breathe * scale
            h = s["h"] * stretch_y * breathe * max(0.05, self.blink) * scale
            if side == 1:
                h *= 1.0 - SQUINT_FACTOR * s["squint"]
                h *= 1.0 - 0.88 * s["wink"]
            center = (cx + side * EYE_GAP * scale + gx * scale, eye_cy + gy * scale)
            if style == "heart" and self.blink > 0.5:
                pg.draw.polygon(screen, color, heart_points(*center, w, h))
            elif style == "swirl" and self.blink > 0.5:
                pg.draw.lines(screen, color, False, spiral_points(*center, w / 2), 7)
            elif style == "star" and self.blink > 0.5:
                pg.draw.polygon(screen, color, star_points(*center, w / 2, spikes=5))
            elif style == "x":
                self.draw_x_eye(screen, center, w, color, scale)
            elif style == "shades":
                self.draw_lens(screen, center, w, h, s, side, color, scale)
                centers.append(center)
            else:
                self.draw_eye(screen, center, w, h, s, side, color, scale)
            if s["brow"] > 0.02:
                lift = 1.0 if side == -1 else 1.0 - s["brow_asym"] * 1.7
                self.draw_brow(screen, center, h, s["brow"], side, lift, color, scale)

        if len(centers) == 2:
            bridge = max(3, int(SHADES_BRIDGE * scale))
            pg.draw.line(screen, color, centers[0], centers[1], bridge)

        if s["sparkle"] > 0.02:
            self.draw_sparkles(screen, cx, eye_cy + gy * scale, color, s["sparkle"], scale)
        if s["tear"] > 0.02:
            self.draw_tear(screen, cx - EYE_GAP * scale + gx * scale, eye_cy, s["tear"], scale)

        if card:
            self.draw_code_panel(screen, color)
            return

        if self.emotion in BLUSH_EMOTIONS:
            blush = pg.Surface((74, 32), pg.SRCALPHA)
            pg.draw.ellipse(blush, (*BLUSH_COLOR, BLUSH_ALPHA), (0, 0, 74, 32))
            for side in (-1, 1):
                pos = (cx + side * (EYE_GAP + 45), cy + 40 + gy)
                screen.blit(blush, blush.get_rect(center=pos))

        if self.emotion == "sleeping":
            f = self.font(24)
            for i in (0, 1):
                z = f.render("z", True, color)
                bob = math.sin(self.t * 2 + i) * 6
                screen.blit(z, (cx + 118 + i * 24, cy - 70 - i * 30 + bob))

        if self.banner_text and self.t < self.banner_until:
            self.draw_banner(screen, color)

        mouth_y = cy + MOUTH_OFFSET_Y + gy * 0.4
        if self.speaking:
            self.draw_talking(screen, cx, mouth_y, talk_openness(self.t), color)
        elif s["mouth_open"] > 0.05:
            rw = int(MOUTH_HALF_WIDTH * s["mouth_open"])
            rh = int(MOUTH_HALF_WIDTH * 1.3 * s["mouth_open"])
            pg.draw.ellipse(screen, color, (cx - rw / 2, mouth_y - rh / 2, rw, rh))
        else:
            self.draw_mouth(screen, cx, mouth_y, s["mouth"], color)

    def draw_x_eye(self, screen, center, w, color, scale=1.0) -> None:
        arm = w / 2
        cx, cy = center
        thick = max(4, int(16 * scale))
        pg.draw.line(screen, color, (cx - arm, cy - arm), (cx + arm, cy + arm), thick)
        pg.draw.line(screen, color, (cx - arm, cy + arm), (cx + arm, cy - arm), thick)

    def draw_lens(self, screen, center, w, h, s, side, color, scale) -> None:
        surf = pg.Surface((int(w) + 4, int(h) + 4), pg.SRCALPHA)
        r = min(s["r"] * scale, w / 2, h / 2)
        pg.draw.rect(surf, color, (2, 2, int(w), int(h)), border_radius=int(r))
        glint_x = int(w * 0.24)
        pg.draw.line(
            surf,
            GLINT_COLOR,
            (glint_x, int(h * 0.78)),
            (int(w * 0.46), int(h * 0.18)),
            max(2, int(7 * scale)),
        )
        surf = pg.transform.rotate(surf, side * SHADES_TILT)
        screen.blit(surf, surf.get_rect(center=center))

    def draw_eye(self, screen, center, w, h, s, side, color, scale) -> None:
        r = min(s["r"] * scale, w / 2, h / 2)
        surf = pg.Surface((int(w) + 4, int(h) + 4), pg.SRCALPHA)
        pg.draw.rect(surf, color, (2, 2, int(w), int(h)), border_radius=int(r))
        if s["lid"] > 0.02:
            lid_h = 2 + h * s["lid"]
            pg.draw.rect(surf, BACKGROUND, (0, 0, int(w) + 4, int(lid_h)), border_radius=int(r))
        if s["crescent"] > 0.02:
            cover_y = 2 + h * (1.08 - 0.78 * s["crescent"])
            cover = (0, cover_y, int(w) + 4, int(h) + 4)
            pg.draw.rect(surf, BACKGROUND, cover, border_radius=int(r))
        if abs(s["tilt"]) > 0.5:
            surf = pg.transform.rotate(surf, -side * s["tilt"])
        screen.blit(surf, surf.get_rect(center=center))

    def draw_brow(self, screen, center, h, weight, side, lift, color, scale) -> None:
        length = BROW_LENGTH * scale
        thick = int(BROW_THICKNESS * scale * weight)
        bar = pg.Surface((int(length), max(3, thick)), pg.SRCALPHA)
        pg.draw.rect(bar, color, bar.get_rect(), border_radius=thick // 2)
        bar = pg.transform.rotate(bar, side * BROW_ANGLE * weight * lift)
        y = center[1] - h / 2 - BROW_LIFT * scale * (1.0 + 0.35 * max(0.0, lift))
        screen.blit(bar, bar.get_rect(center=(center[0], y)))

    def draw_sparkles(self, screen, cx, cy, color, weight, scale) -> None:
        for i, (ox, oy, size) in enumerate(SPARKLE_POINTS):
            pulse = 0.55 + 0.45 * math.sin(self.t * 5.0 + i * 2.1)
            pts = star_points(
                cx + ox * EYE_GAP * scale, cy + oy * EYE_GAP * scale, size * scale * pulse * weight
            )
            pg.draw.polygon(screen, color, pts)

    def draw_tear(self, screen, x, eye_cy, weight, scale) -> None:
        phase = (self.t % TEAR_PERIOD) / TEAR_PERIOD
        y = eye_cy + 60 * scale + phase * TEAR_FALL * scale
        radius = int(TEAR_RADIUS * scale * weight * (1.0 - phase * 0.35))
        if radius > 1:
            pg.draw.circle(screen, TEAR_COLOR, (int(x), int(y)), radius)

    def fit_font(self, text: str, width: float, largest: int) -> pg.font.Font:
        for size in range(largest, 13, -5):
            if self.font(size).size(text)[0] <= width:
                return self.font(size)
        return self.font(14)

    def draw_banner(self, screen: pg.Surface, color: tuple) -> None:
        left = self.banner_until - self.t
        font = self.fit_font(self.banner_text, SIZE * BANNER_MARGIN, 74)
        glyph = font.render(self.banner_text, True, color)
        if left < 0.4:  # fade out instead of vanishing
            glyph.set_alpha(int(255 * left / 0.4))
        screen.blit(glyph, glyph.get_rect(center=(SIZE / 2, SIZE * 0.84)))

    def draw_count(self, screen: pg.Surface) -> None:
        screen.fill(BACKGROUND)
        left = max(0.0, self.count_until - self.t)
        scale = 1.0 + 0.18 * left  # each number lands with a pop
        color = EMOTION_COLORS["excited"] if self.count_text != "0" else EMOTION_COLORS["happy"]
        glyph = self.font(COUNT_FONT).render(self.count_text, True, color)
        glyph = pg.transform.rotozoom(glyph, 0, min(1.25, scale))
        screen.blit(glyph, glyph.get_rect(center=(SIZE / 2, SIZE / 2)))

    def draw_code_panel(self, screen: pg.Surface, color: tuple) -> None:
        top = int(SIZE * CARD_PANEL_TOP)
        rect = pg.Rect(20, top, SIZE - 40, SIZE - top - 20)
        pg.draw.rect(screen, TERMINAL_BG, rect, border_radius=12)
        pg.draw.rect(screen, color, rect, 2, border_radius=12)
        screen.set_clip(rect.inflate(-10, -18))
        f = self.font(16)
        y0 = rect.y + 12 - int(self.card_scroll)
        for i, line in enumerate(self.card_lines):
            screen.blit(f.render(line, True, TERMINAL_FG), (rect.x + 16, y0 + i * CARD_LINE_H))
        screen.set_clip(None)

    @staticmethod
    def draw_talking(screen: pg.Surface, cx: float, cy: float, wide: float, color: tuple) -> None:
        """A jaw, not a wiggling line: the mouth narrows as it opens, the way
        a real one does, and never shuts fully mid-word."""
        w = MOUTH_HALF_WIDTH * (TALK_WIDTH - TALK_NARROW * wide)
        h = MOUTH_THICKNESS + MOUTH_HALF_WIDTH * TALK_OPEN * wide
        pg.draw.ellipse(screen, color, (cx - w / 2, cy - h / 2, w, h))
        if h > TALK_LIP * 3:  # a darker gap once it is properly open
            gap = (w - TALK_LIP * 2, h - TALK_LIP * 2)
            pg.draw.ellipse(
                screen, BACKGROUND, (cx - gap[0] / 2, cy - gap[1] / 2, gap[0], gap[1])
            )

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
                elif e.key == pg.K_p:
                    face.play_parade()
                elif e.key == pg.K_c:
                    face.show_card("def hello():\n    print('hi from Mochi')")

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
        pg.display.set_caption(f"Mochi - {face.emotion}  [1-7 | M mouse | A auto | P parade]")
        pg.display.flip()

        frame += 1
        if frame_limit and frame >= frame_limit:
            pg.quit()
            return

if __name__ == "__main__":
    main()
