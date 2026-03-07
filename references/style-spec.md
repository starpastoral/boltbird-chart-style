# Boltbird Style Spec

## Design Intent

Build charts that feel editorial, quiet, and deliberate. Let the data carry contrast; let the styling enforce order.

Default delivery assumes transparent export may land on either a light or dark surface. Use mid-gray typography and restrained neutral strokes that stay readable on both, instead of light-only text or outline-heavy lettering.

Tokens are the shipped source of truth. If this prose gives a range and the tokens specify a concrete value, use the token value.

## Modes

Two explicit operating modes are supported:

- `consulting_safe`
  Use this by default. Prioritize readability and business communication. If a chart form becomes weak under the category count or label density, change the chart form.
- `editorial`
  Preserve the same house style, but allow a bit more compositional freedom before changing chart form.

If the user does not ask for a specific mode, default to `consulting_safe`.

## Typography

- Primary font: `Geist`
- Monospace font: `Google Sans Code`
- Wordmark font: `Source Serif 4`
- Do not mix additional display fonts.
- Use semibold titles and medium-weight support text. Avoid black or ultra-heavy weights.

Fallback stacks:

- primary: `Geist`, `Helvetica Neue`, `Arial`, `sans-serif`
- monospace: `Google Sans Code`, `SFMono-Regular`, `Menlo`, `monospace`
- wordmark: `Source Serif 4`, `Times New Roman`, `serif`

Recommended 1600x900 sizing:

- Title: 34-42 px, `Geist SemiBold`
- Subtitle or date range: 18-22 px, `Geist Medium`
- Source and legend: 15-18 px, `Geist Medium`
- Axis labels: 16-18 px, `Geist Medium`
- Tick labels: 14-16 px, `Geist Medium`
- Compact numeric tags: 13-15 px, `Google Sans Code Medium`
- Footnotes or caveats: 12-13 px, `Geist Medium`

## Palette

Default transparent-safe palette uses mid-gray neutrals:

- `ink-strong`: `rgba(150, 156, 168, 0.96)`
- `ink-base`: `rgba(132, 139, 151, 0.92)`
- `ink-soft`: `rgba(112, 120, 132, 0.88)`
- `ink-faint`: `rgba(92, 100, 112, 0.82)`
- `grid-major`: `rgba(100, 108, 120, 0.26)`
- `grid-minor`: `rgba(100, 108, 120, 0.14)`

Default accent system is `single-accent-first`:

- `primary-accent`: `#34605F`
- reserve cool: `#7C86B6`
- reserve warm: `#D6A15D`
- reserve bridge: `#947BA8`

Rules:

- Start with one hue family: neutral plus one primary accent.
- Only add the second and third accent families when the number of series or categories makes one accent insufficient.
- Prefer lightness changes inside the same hue family before adding another hue.
- Treat accent as a scarce resource. Most charts should read as one brand hue plus a neutral ladder, not as a categorical rainbow.
- For pie or donut charts with many slices, prefer a single-hue ladder derived from the primary accent instead of a rainbow categorical palette.
- Never use rainbow scales, saturated red/green trading defaults, or unrelated category palettes.
- For transparent exports intended for unknown backgrounds, prefer mid-gray text and moderate line weight. Do not rely on text outlines for readability.

Default role mapping by chart family:

- line and area: `single-accent-first`
- bar and column: `accent-plus-neutrals`
- grouped or stacked bar: `single-accent-first`, only up to three real identities before muting the rest
- scatter and bubble: `accent-plus-neutrals`, accent only for focal cohorts or outliers
- histogram: neutral body plus one accent reference line if needed
- box plot: one neutral family, accent only for the median or selected group
- heatmap: monochrome sequential only
- pie and donut: single hue plus structural labels; if density rises, change chart form before adding more hues

## Implementation Boundary

- First-class implementation target: SVG-first workflows.
- Portable layer: tokens, chart-form decisions, color-role logic, metadata layout, and label-placement rules.
- For Matplotlib, Plotly, Vega-Lite, ECharts, or similar stacks, translate the same token values and role rules instead of copying SVG helpers directly.

## Background and Surface

- Export background: transparent
- Canonical source artifact may remain `SVG`, but user-facing preview should prefer `PNG` when available.
- Avoid panel fills, boxed legends, outer frames, drop shadows, bevels, or glossy effects.
- Use anti-aliased strokes and crisp text.
- Do not rely on a background inversion pass. The default transparent theme must already remain legible on both white and dark surfaces.

## Layout

Use a top metadata band so the plot body stays clean.

Recommended 1600x900 layout:

- Outer padding: left 88 px, right 72 px, top 44 px, bottom 76 px
- Metadata band height: 150-180 px
- Plot area begins below the metadata band
- Title block: centered horizontally
- Source line: left-aligned under title block or under the legend, never floating inside the plot
- Legend: single row under title block when needed
- Legend rule:
  - 1 to 3 items: center it under the subtitle in one horizontal row
  - more than 3 items: move it outside the plot on the right side as one vertical column
- When the legend is on the right side, align its top to the plot body's top edge, not to the metadata band. The watermark owns the upper-right metadata area.
- Source line should sit on its own row under the subtitle. Keep it short, for example `Source: Stooq`, instead of repeating ticker lists in parentheses.

Do not over-pack the top band. If title, subtitle, source, and legend exceed the band, reduce legend burden before shrinking fonts.

## Axes and Grid

- Show only the axes and gridlines that improve reading.
- Default to major gridlines only.
- Use `grid-major` for primary reading structure and turn minor grids off unless the data density demands them.
- Start from the sparsest readable grid. If a chart looks busy, remove lines before shrinking type.
- For price charts, default to fewer horizontal guides than you initially think you need.
- Hide top and right plot borders.
- Use tick labels sparingly and align them to meaningful intervals.
- Use `Google Sans Code` only when tick labels are dense numeric values and alignment benefits from monospacing.

## Labels and Annotation

- Label what matters, not everything.
- Prefer endpoint labels, extrema labels, event labels, and the latest value over blanket data labels.
- Use short annotation text. Keep labels to one line where possible.
- Use one marker geometry per event type: circle, square, triangle, or vertical flag.
- Prefer stroke and outline over heavy fill for annotation markers.
- Offset annotations so they do not sit directly on text or bars unless the chart type requires it.
- Keep annotation count low enough that the data remains readable at first glance.
- On line charts, prefer a right-side label gutter or endpoint tags over labels sitting on top of the data path.
- For multi-series line charts with more than three series, do not force latest-value labels inside the plot. Move them to a right-side external stack aligned by endpoint order.
- Add enough outer bleed that edge labels, date ticks, and right-side tags never clip, but keep endpoint labels visually close to the data instead of leaving a large empty gutter.
- Keep x-axis tick labels tucked close to the axis line; do not let them drift downward unless a second row of labels is required.
- Prefer dynamic latest-value labels inside the plot before reserving a large right-side gutter.
- For latest-value labels, try this order:
  - inside-left of the latest point
  - above-left of the latest point
  - below-left of the latest point
- Only fall back to an outside gutter when the in-plot placements would collide with the data or clip.
- For dense multi-series charts, outside placement is the default, not the fallback.
- If there is only one latest-value label, prefer no connector line unless the label would otherwise be ambiguous.
- If a connector line is used, keep it short and visually attached to the marked point.
- Keep chart titles on one line whenever the canvas allows it. Prefer wrapping endpoint labels, legend labels, or secondary tags before wrapping the title.

## Watermark

Use the lockup text `Powered by Boltbird` with the bird icon rendered in a single color. Do not use a full-color emoji. The supplied [`../assets/watermark-lockup.svg`](../assets/watermark-lockup.svg) is the reference lockup.

Typography rules for the lockup:

- Set `Powered by` in `Geist`.
- Set `Boltbird` in `Source Serif 4 Bold`.
- Keep the lockup on one line.
- Make the lockup large enough that the bird mark is clearly legible, but still slightly smaller than the chart title.

Placement rules:

- Default to top-right. If a long centered title makes the metadata band crowded, drop the watermark into the upper-right edge of the plot area instead of letting it sit behind the title.
- Keep at least 32 px away from the canvas edge and 24 px away from title or legend blocks.
- Default opacity: around `0.24`
- Default width: about `268 px` on a 1600x900 canvas
- If top-right metadata is crowded, reduce width first, then shift downward within the metadata band. Do not move into the plot body unless the chart has no top text.
- Never let the watermark cover title text, legend labels, axis labels, or chart annotations.
- For transparent charts, keep the watermark quieter than the legend and subtitle, but large enough that both the wordmark and bird mark are clearly legible.
- Anchor watermark placement from the logo's rightmost edge so the full lockup stays inside the canvas.

## Density and Restraint

- Keep the visual hierarchy obvious from three meters away.
- Keep legends compact; if there are too many series, direct-label the most important lines and mute the rest.
- Use one emphasis layer at a time: either a focal series, a focal region, or focal annotations.
- Remove ornamental borders, glossy fills, gradients, and shadow treatments that do not improve data reading.
- When a chart form becomes unreadable under realistic category counts, change the chart form instead of adding more color. This is the default consulting-style move.
