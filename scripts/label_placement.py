from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    def intersects(self, other: "Rect", pad: float = 0.0) -> bool:
        return not (
            self.x1 + pad < other.x0
            or self.x0 - pad > other.x1
            or self.y1 + pad < other.y0
            or self.y0 - pad > other.y1
        )

    def expanded(self, pad_x: float, pad_y: float | None = None) -> "Rect":
        pad_y = pad_x if pad_y is None else pad_y
        return Rect(self.x0 - pad_x, self.y0 - pad_y, self.x1 + pad_x, self.y1 + pad_y)

    def contains_point(self, x: float, y: float, pad: float = 0.0) -> bool:
        return (
            self.x0 - pad <= x <= self.x1 + pad
            and self.y0 - pad <= y <= self.y1 + pad
        )


@dataclass
class LabelPlacement:
    text_x: float
    text_y: float
    anchor: str
    use_line: bool
    line_end_x: float
    line_end_y: float
    box: Rect


def estimate_label_width(text: str, font_size: int) -> float:
    return max(len(text) * font_size * 0.62, 72)


def rect_from_segment(x0: float, y0: float, x1: float, y1: float, pad: float) -> Rect:
    return Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)).expanded(pad)


def polyline_obstacles(
    points: list[tuple[float, float]],
    *,
    segment_window: int,
    stroke_pad_px: float,
) -> list[Rect]:
    if len(points) < 2:
        return []
    start = max(0, len(points) - 1 - segment_window)
    obstacles: list[Rect] = []
    for i in range(start, len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        obstacles.append(rect_from_segment(x0, y0, x1, y1, stroke_pad_px))
    return obstacles


def candlestick_obstacles(
    *,
    candles: list[tuple[float, float, float, float, float]],
    body_half_width: float,
    pad_px: float = 4.0,
) -> list[Rect]:
    obstacles: list[Rect] = []
    for x, open_y, close_y, high_y, low_y in candles:
        body_top = min(open_y, close_y)
        body_bottom = max(open_y, close_y)
        obstacles.append(
            Rect(
                x - body_half_width,
                min(high_y, body_top),
                x + body_half_width,
                max(low_y, body_bottom),
            ).expanded(pad_px)
        )
    return obstacles


def choose_latest_label_placement(
    *,
    point_x: float,
    point_y: float,
    text: str,
    font_size: int,
    plot_x0: float,
    plot_y0: float,
    plot_x1: float,
    plot_y1: float,
    obstacles: list[Rect],
    gap_px: float,
    vertical_offset_px: float,
    prefer_inside_only: bool = True,
    min_line_length_px: float = 44.0,
    single_label_use_line: bool = False,
) -> LabelPlacement:
    width = estimate_label_width(text, font_size)
    height = font_size + 8

    left_x = point_x - gap_px
    far_left_x = point_x - gap_px - width * 0.38
    farther_left_x = point_x - gap_px - width * 0.72
    candidates = [
        ("end", left_x, point_y + vertical_offset_px),
        ("end", left_x, point_y - (height + 6)),
        ("end", left_x, point_y + (height + 4)),
        ("end", far_left_x, point_y - (height * 0.45)),
        ("end", far_left_x, point_y + (height * 0.55)),
        ("end", farther_left_x, point_y - (height * 0.95)),
        ("end", farther_left_x, point_y + (height * 1.05)),
    ]
    if not prefer_inside_only:
        candidates.extend(
            [
                ("start", point_x + gap_px, point_y + vertical_offset_px),
                ("start", point_x + gap_px, point_y - (height + 6)),
                ("start", point_x + gap_px, point_y + (height + 4)),
            ]
        )

    best: LabelPlacement | None = None
    best_penalty: tuple[int, int, int, float] | None = None

    for anchor, text_x, text_y in candidates:
        if anchor == "end":
            box = Rect(text_x - width, text_y - height, text_x, text_y)
        else:
            box = Rect(text_x, text_y - height, text_x + width, text_y)

        inside = box.x0 >= plot_x0 and box.x1 <= plot_x1 and box.y0 >= plot_y0 and box.y1 <= plot_y1
        collision_count = sum(1 for r in obstacles if box.intersects(r, pad=6))
        point_overlap = 1 if box.contains_point(point_x, point_y, pad=8) else 0
        distance = abs(text_x - point_x) + abs(text_y - point_y)
        penalty = (collision_count, point_overlap, 0 if inside else 1, distance)

        if best_penalty is None or penalty < best_penalty:
            best_penalty = penalty
            line_end_x = box.x1 + 6 if anchor == "end" else box.x0 - 6
            line_end_y = text_y - 6
            line_length = abs(line_end_x - point_x) + abs(line_end_y - point_y)
            use_line = ((not box.contains_point(point_x, point_y, pad=8)) and line_length >= min_line_length_px) or (
                single_label_use_line and line_length >= min_line_length_px
            )
            best = LabelPlacement(
                text_x=text_x,
                text_y=text_y,
                anchor=anchor,
                use_line=use_line,
                line_end_x=line_end_x,
                line_end_y=line_end_y,
                box=box,
            )

    assert best is not None
    return best


def stack_external_labels(
    *,
    items: list[tuple[str, float, str]],
    text_x: float,
    point_x: float,
    gutter_gap_px: float,
    min_separation_px: float,
    plot_y0: float,
    plot_y1: float,
    font_size: int,
) -> list[LabelPlacement]:
    height = font_size + 8
    prepared: list[tuple[str, float, str, float]] = []
    for key, point_y, text in items:
        prepared.append((key, point_y, text, estimate_label_width(text, font_size)))
    prepared.sort(key=lambda item: item[1])

    placements: list[LabelPlacement] = []
    previous_text_y: float | None = None
    for key, point_y, text, width in prepared:
        text_y = min(max(point_y + 5, plot_y0 + height), plot_y1)
        if previous_text_y is not None and text_y - previous_text_y < min_separation_px:
            text_y = previous_text_y + min_separation_px
        text_y = min(text_y, plot_y1)
        box = Rect(text_x, text_y - height, text_x + width, text_y)
        placements.append(
            LabelPlacement(
                text_x=text_x,
                text_y=text_y,
                anchor="start",
                use_line=True,
                line_end_x=text_x - gutter_gap_px,
                line_end_y=text_y - 6,
                box=box,
            )
        )
        previous_text_y = text_y

    overflow = placements[-1].text_y - plot_y1 if placements else 0
    if overflow > 0:
        for placement in placements:
            placement.text_y -= overflow
            placement.line_end_y -= overflow
            placement.box = Rect(
                placement.box.x0,
                placement.box.y0 - overflow,
                placement.box.x1,
                placement.box.y1 - overflow,
            )

    return placements
