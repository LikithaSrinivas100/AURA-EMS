---
name: Calculated Caliber
colors:
  surface: '#f9f9ff'
  surface-dim: '#d8dae2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3fc'
  surface-container: '#ecedf6'
  surface-container-high: '#e6e8f0'
  surface-container-highest: '#e1e2eb'
  on-surface: '#191c22'
  on-surface-variant: '#3e4947'
  inverse-surface: '#2d3037'
  inverse-on-surface: '#eff0f9'
  outline: '#6e7977'
  outline-variant: '#bdc9c6'
  surface-tint: '#006a63'
  primary: '#005c55'
  on-primary: '#ffffff'
  primary-container: '#0f766e'
  on-primary-container: '#a3faef'
  inverse-primary: '#80d5cb'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#54504d'
  on-tertiary: '#ffffff'
  tertiary-container: '#6d6865'
  on-tertiary-container: '#f0e8e4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9cf2e8'
  primary-fixed-dim: '#80d5cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#00504a'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#e8e1dd'
  tertiary-fixed-dim: '#ccc5c1'
  on-tertiary-fixed: '#1e1b19'
  on-tertiary-fixed-variant: '#4a4643'
  background: '#f9f9ff'
  on-background: '#191c22'
  surface-variant: '#e1e2eb'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
  telemetry-display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.03em
  telemetry-display-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  telemetry-value:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.25rem
  margin: 1rem
  margin-tablet: 1.5rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system serves campus facilities directors, sustainability engineers, and university administrators who manage power distribution, peak shaving, and demand modeling. The emotional response is centered on clarity, operational composure, and quiet authority. Interfaces must reject visual noise, gratuitous embellishments, and distracting micro-interactions in favor of high-density utility, predictable interactions, and precision data handling.

The design movement is **Utilitarian Modernism**—drawing the structural exactness of Linear, the structural typographic pacing of Stripe's reporting suites, and the dense visual telemetry of Grafana. Information density remains high without feeling congested. The tone is deliberate, institutional, and metric-first.

## Colors

The palette employs a restrained, warm-neutral foundation that eliminates visual fatigue during prolonged operational monitoring sessions:

- **Canvas & Surface**: 
  - Application Canvas: Warm off-white `#F5F4F0`.
  - Cards, Containers, and Data Panels: Pure white `#FFFFFF`.
  - Structural Borders: Hairline `#E7E5E0`.
  - Subdued Hover/Active Tints: `#ECEAE4`.
- **Typography & Structure**:
  - Ink (Primary Text & Headings): `#15181E`.
  - Muted (Secondary Metadata, Units, Labels): `#6B7280`.
  - Inactive/Placeholder: `#9CA3AF`.
- **Primary Operational Accent**: Deep Teal `#0F766E` denotes selection states, primary actions, and primary prediction paths. Muted background tint for teal states is `#F0FDFA`.
- **Telemetry & Metric Plotting**:
  - Actual Recorded Load: Ink `#15181E` (solid, weighted).
  - Primary Prediction (Best Fit / ML Output): Deep Teal `#0F766E` (solid).
  - Baseline/Historical Model: Slate Blue `#64748B` (dashed or fine stroke).
  - Ambient Weather / Secondary Trend: Amber Gray `#A8A29E`.
- **Operational Risk & Threshold System**:
  - Strict allocation: Risk colors must never be applied decoratively.
  - Critical Threshold (High Load/Fault): Crimson `#B91C1C` (background tint `#FEF2F2`).
  - Warning Threshold (Mid Load/Approaching Cap): Amber Orange `#C2410C` (background tint `#FFF7ED`).
  - Optimal / Nominal (Low Demand/Normal): Deep Green `#15803D` (background tint `#F0FDF4`).

## Typography

Typography prioritizes tabular precision, immediate scannability, and hierarchical rhythm:

- **Typeface**: Inter across all UI layers.
- **Tabular Figures**: Every numeric data point, metric counter, chart tooltip, timestamp, and table cell must declare `font-variant-numeric: tabular-nums` to guarantee aligned columns and prevent layout shifting during telemetry updates.
- **Letter Casing**: Standard sentence case across all headings, metric titles, and actions. Avoid uppercase tracking except for technical units (e.g., `kW`, `MWh`, `kVA`).
- **Telemetry Scale**: Large numerical callouts (`telemetry-display` and `telemetry-value`) anchor overview cards, allowing operators to parse energy usage instantly across high-density dashboards.

## Layout & Spacing

The layout model is a structured fluid grid optimized for high-density analytical dashboards:

- **Canvas Organization**: A fixed side-rail navigation (240px wide on desktop, collapsible to 56px icon mode) paired with a fluid main workspace spanning 12-column modules.
- **Breakpoints**:
  - Mobile (`< 768px`): 4 columns, single-card vertical flow, margin `1rem`, gutter `1rem`. Secondary analytical charts collapse into selectable tabbed views.
  - Tablet (`768px - 1199px`): 8 columns, 2-column card layouts, margin `1.5rem`, gutter `1rem`.
  - Desktop (`≥ 1200px`): 12 columns, 3 to 4-card metric strips, margin `2rem`, gutter `1.25rem`. Maximum layout bounds capped at `1600px` for ultra-wide displays to maintain ergonomic line tracking.
- **Spacing Cadence**: Tight, linear increments (`4px`, `8px`, `12px`, `16px`, `24px`). Panel internals stick strictly to `space-lg` (16px) or `space-xl` (24px) padding to maximize chart real estate while guaranteeing clean separation.

## Elevation & Depth

This system avoids ambient shadows, blur effects, skeuomorphic depths, and multi-tier drop shadows entirely. Depth and visual hierarchy are created strictly through low-contrast outlines and tonal surface stratification:

- **Base Elevation**: Canvas sits at `#F5F4F0`.
- **Card Elevation**: Surfaces rise via color shift to `#FFFFFF`, delineated by a crisp `1px solid #E7E5E0` border. Shadows are set to `none` (`box-shadow: none`).
- **Interactive Layers & Flyouts**: Contextual menus, tooltips, and flyout date/filter selectors use a `#FFFFFF` surface with a slightly darker boundary `1px solid #D6D3CD` and an ultra-subtle, non-diffused keyline border rather than a blurred shadow.
- **Table and Row Hierarchy**: Row division lines use hairline `#E7E5E0` borders. Hover states on interactive rows apply background `#FBFBFA` without elevation changes.

## Shapes

The interface balances sharp architectural discipline with soft corner transitions:

- **Cards and Panels**: Hard fixed to `10px` (`rounded-lg` token variant calibrated to 10px).
- **Controls & Form Elements**: Buttons, text input boxes, dropdown selectors, and segmented tabs use a uniform `6px` radius (`0.375rem`) for a precise, compact feel.
- **Status Tags & Badges**: Small threshold indicators and risk chips use a `4px` corner radius. Full pill shapes are prohibited to avoid an informal, consumer-app aesthetic.

## Components

### Buttons
- **Primary**: Background Deep Teal `#0F766E`, text `#FFFFFF`, border `none`, radius `6px`, height `32px` (compact) or `36px` (standard), weight `500`. Hover state `#0D655E`.
- **Secondary / Ghost**: Background `#FFFFFF`, text `#15181E`, border `1px solid #E7E5E0`, radius `6px`. Hover state: background `#F5F4F0`, border `#D6D3CD`.
- **Destructive**: Background `#FFFFFF`, text `#B91C1C`, border `1px solid #FECACA`. Hover: background `#FEF2F2`.

### Cards & Telemetry Panels
- Background `#FFFFFF`, border `1px solid #E7E5E0`, radius `10px`, drop shadow `none`.
- Internal structure comprises a header row (12px uppercase or medium label, secondary metric badge, optional time range selector), primary metric stack (tabular numeric text), and a lower telemetry/sparkline slot.

### Input Fields & Selectors
- Background `#FFFFFF`, border `1px solid #E7E5E0`, height `34px`, font size `13px`, text `#15181E`, border-radius `6px`, padding `0 10px`.
- Focus ring: `1px solid #0F766E` with an outer outline offset of `0px` (crisp outline, no fuzzy glow).

### Risk & Status Chips
- Height `20px`, padding `2px 8px`, border-radius `4px`, font-size `11px`, font-weight `500`, tabular numbers.
- High Risk: Background `#FEF2F2`, border `1px solid #FCA5A5`, text `#B91C1C`.
- Medium Risk: Background `#FFF7ED`, border `1px solid #FDBA74`, text `#C2410C`.
- Low / Nominal Risk: Background `#F0FDF4`, border `1px solid #86EFAC`, text `#15803D`.

### Checkboxes & Segmented Controls
- Checkbox: `14px x 14px`, radius `3px`, border `1px solid #D1D5DB`. Checked: `#0F766E` background with white checkmark.
- Segmented Control (Time Range Switcher: 1H, 24H, 7D, 30D): Canvas container `#ECEAE4`, padding `2px`, radius `6px`. Selected item: `#FFFFFF` fill, `1px solid #E7E5E0`, text `#15181E`, font-weight `500`. Inactive item: transparent fill, text `#6B7280`.

### Data Tables
- Headers: Background `#FAFAF8`, text `#6B7280`, font-size `11px`, font-weight `500`, uppercase tracking `0.02em`, height `32px`, bottom border `1px solid #E7E5E0`.
- Cells: Text `#15181E`, font-size `13px`, height `40px`, bottom border `1px solid #E7E5E0`, numeric columns right-aligned with `font-variant-numeric: tabular-nums`.

### Timeseries Charts & Legend
- Chart area canvas: `#FFFFFF`, zero drop shadow.
- Grid lines: Hairline `#F0EFEA` (horizontal only, dashed `2px 2px`).
- Chart Legends: Horizontal list below or top-right of panel. Dot indicators (`6px` circular or line dashes matching trace styles) with `12px` font `#6B7280`. Actual (`#15181E`), ML Best Fit (`#0F766E`), Slate Baseline (`#64748B`), Ambient Factor (`#A8A29E`).