---
title: Extension bar half-width on flex-container pages
date: 2026-06-12
category: ui-bugs
module: browser-extension
problem_type: ui_bug
component: tooling
symptoms:
  - Extension bar rendered at half viewport width on flex-container pages
  - Bar width did not span full page when body was a flex container
root_cause: wrong_api
resolution_type: code_fix
severity: medium
tags: [css, position-fixed, browser-extension, flexbox]
---

# Extension bar half-width on flex-container pages

## Problem

The robots.txt browser extension bar rendered at half viewport width on pages where `body` is a flex container. `width: 100%` with `position: relative` resolves to the parent's content width, not the viewport, causing half-width rendering in flex layouts.

## Symptoms

- Bar appears half-width on flex-container pages
- `width: 100%` does not fill viewport
- Only visible on sites with `display: flex` on `body` or a wrapper

## What Didn't Work

- `width: 100vw` — still broken on flex layouts because `vw` units can behave unexpectedly with scrollbars
- `calc(-50vw + 50%)` — complex, fragile, and still failed on certain flex configurations
- Looking up spacer via `getElementById` before it was inserted into the DOM — the spacer div existed but wasn't findable

## Solution

Switched the bar from `position: relative` to `position: fixed`:

```css
position: fixed; top: 0; left: 0; width: 100%;
```

Added a spacer div as a property on the bar object (`bar.spacer`) rather than looking it up by DOM ID, so `injectBar` and `defendBar` can reliably access it before DOM insertion:

```javascript
bar.spacer = document.createElement('div')
bar.spacer.id = BAR_ID + '-spacer'
bar.spacer.style.cssText = 'height: 40px;'

function injectBar(bar) {
    document.body.insertBefore(bar.spacer, document.body.firstChild)
    document.body.insertBefore(bar, bar.spacer)
}
```

Updated `defendBar` (MutationObserver) and the close handler to also manage the spacer.

## Why This Works

`position: fixed` removes the element from normal document flow and establishes the viewport as its containing block. `width: 100%` then resolves to 100% of the viewport width, regardless of the parent element's layout mode (flex, grid, block, etc.). The spacer div compensates for the bar being removed from flow, preventing content from rendering underneath it.

## Prevention

- Use `position: fixed` (not `relative`) for viewport-spanning overlays, bars, and banners
- Attach related DOM nodes as JS object properties rather than looking them up by ID after insertion — the spacer needs to exist before it can be found
