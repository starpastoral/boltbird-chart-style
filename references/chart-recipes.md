# Boltbird Chart Recipes

Apply the global style spec first, then use the rules below for the requested chart type.

## Candlestick / K-Line

- Use wick strokes in the same neutral family as the candle body.
- Default body convention:
  - Up candle: hollow body with neutral outline
  - Down candle: solid body with darker neutral fill
- Keep all candlesticks themselves in grayscale by default.
- Reserve accent color for the latest-price marker, latest-price label, or a deliberately highlighted annotation.
- Do not use red/green trading defaults unless the user explicitly asks for them.
- Keep wick width slender and body width moderate; do not let bodies visually merge in weekly or daily charts.
- When placing the latest-price label, treat the recent candle cluster as one obstacle field. Do not only avoid the endpoint dot; avoid the last several bodies and wicks around it.
- Use event markers sparingly and prefer geometry over color:
  - Earnings/report: circle
  - Product launch: square
  - Conference/event: triangle
- If three event families are insufficient, use direct text labels instead of adding more colors.
- Reserve extra headroom above the price range for event labels so they do not collide with the watermark band.
- If volume is shown, place it in a subdued lower strip using the same neutral ladder at lower opacity.

## Line

- Use the `single-accent-first` system:
  - 1 series: primary accent only
  - 2 series: primary accent plus one neutral companion
  - 3 series: primary accent plus cool and warm reserves
  - 4 series: use the full editorial quartet
  - more than 4 series: switch to `highlight-plus-muted`
- Prefer endpoint labels over large legends when series count is three or fewer.
- Latest-value labels should run through the shared dynamic-placement helper and avoid recent line segments, not just the endpoint dot.
- For more than three series, move the latest-value labels into a right-side external stack instead of letting them fight inside the plot.
- When the legend has more than three items, render it outside the plot in the same right-side column family as the label stack.
- Avoid smoothing that changes the story of the data.
- If one series is the story and the others are context, keep only the focal series in accent and mute the rest to neutral grays.

## Area

- Use one dominant stroke plus a restrained fill at `0.10` to `0.16` opacity.
- Keep fills monochrome unless the user explicitly needs stacked categories.
- If stacked, stop at three layers and use lightness steps within one hue family whenever possible.
- Treat the accent stroke as the main carrier; the fill should never compete with it.

## Bar / Column

- Default to `one accent + neutral ladder`, not a per-bar categorical palette.
- Use a single neutral fill when nothing deserves emphasis.
- Highlight at most one comparison target or one current period with the primary accent.
- If a second emphasis layer is truly necessary, use a lighter accent variant or a warmer reserve once, then stop.
- Sort descending for ranking charts unless the x-axis is temporal.
- Direct-label the highlighted bar when it removes the need for a legend.

## Grouped or Stacked Bar

- Use no more than three real identities before muting or reconsidering the chart form.
- Start with primary accent, then cool reserve, then warm reserve only if the third identity is necessary.
- Prefer lightness steps over unrelated hues.
- If four or more series are required, reconsider the chart form before forcing the style.

## Scatter / Bubble

- Use hollow or lightly filled markers with controlled alpha.
- Keep most marks neutral and reserve accent for the focal cluster, threshold violators, or a selected cohort.
- Label only outliers, clusters of interest, or the latest observation.
- Bubble size should never be the only carrier of meaning if labels can clarify the largest few marks.

## Heatmap

- Use a monochrome sequential ramp only.
- Keep the highest values brightest and the lowest values faintest.
- Add cell labels only when the matrix is small enough to remain readable.
- Never use rainbow or diverging scales unless the data truly has a midpoint semantic that the user asks to emphasize.

## Histogram / Distribution

- Use one neutral fill and a slightly stronger outline.
- If a benchmark or current-period marker is needed, give that line the primary accent and leave the bars neutral.
- If a reference line is needed, use one accent hue or a dashed neutral line, not both.
- Label key percentiles directly instead of adding dense legends.

## Box Plot

- Keep box, whisker, and median line in the same hue family.
- Use one stronger accent stroke for the median line only when it helps the comparison.
- Show outliers with small hollow markers.

## Pie / Donut

- Avoid unless the user explicitly asks for it.
- In `consulting_safe`, default to a sorted bar chart once the slice count exceeds the mode threshold.
- In `editorial`, you may keep pie slightly longer, but only if label density remains manageable.
- If the slice count is above 4, treat pie as a compromised format.
- If the slice count is above 6, the consulting-style default is to switch to a sorted bar chart or another rank-friendly form instead of forcing the pie.
- If forced and the slice count is high, do not switch to a rainbow palette. Use a single-hue ladder derived from the primary accent, and move all labels outside the wedges.
- For high-slice pie stress cases, do not rely on color alone. Use numbered callouts or external labels so the chart remains readable even when adjacent hues are close.
- Prefer legend or external labels over text crammed into wedges.
- For more than four slices, treat the chart as a stress case and prioritize harmony over categorical fireworks.

## Small Multiples

- Reuse identical scales, padding, and annotation logic across panels.
- One shared title, subtitle, and source line should govern the whole sheet.
- Watermark once per sheet, not once per panel.
