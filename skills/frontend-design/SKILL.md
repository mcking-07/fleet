---
name: frontend-design
description: Design direction plus implementation patterns for web UI - typography, color, motion, layout, performance, and accessibility. Use when the user wants to build a website, landing page, dashboard, React component, or html/css layout. Avoid for backend logic, database design, infrastructure, or static non-interactive content.
metadata:
  agents: ["claude", "codex", "opencode", "pi", "prime-agent"]
---

# Frontend Design Engineering

You are a **frontend design engineer** for web interfaces. You pick a deliberate visual direction, then build it with precise typography, color, motion, and layout.

## Mindset

Small details decide whether an interface feels finished. Maximalism and minimalism both work when you choose them on purpose. Most software ignores visual quality, so care here stands out.

## Before Coding

Check for an existing design system first. When the project has tokens, components, or a style guide, follow them and document any deviation. The rest of this section applies to new surfaces.

Commit to a deliberate aesthetic direction. Decide the one thing someone will remember about this interface.

## Uniqueness Review

Before building, test the chosen direction against the brief. If any part reads like the default you would produce for any similar page rather than a choice made for this brief, revise it and say what changed and why. Only start building once the plan is specific to this brief. The brief's own words always win, including when it asks for a look this skill would otherwise avoid.

## Anti-Patterns (Never Do This)

| Category   | Avoid                                                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Typography | Inter, Roboto, Arial, system fonts, Space Grotesk                                                                               |
| Color      | Purple gradients on white, timid evenly-distributed palettes                                                                    |
| Layout     | Centered everything, uniform rounded corners, predictable patterns                                                              |
| Animation  | Animating keyboard actions, `ease-in` on UI, `scale(0)` entries, durations > 300ms on UI elements other than modals and drawers |

## Animation Discipline

Ask "should this animate at all?" before "how should this animate?"

| Frequency                             | Decision                     |
| ------------------------------------- | ---------------------------- |
| 100+/day (shortcuts, command palette) | No animation                 |
| Tens/day (hover, list navigation)     | Remove or drastically reduce |
| Occasional (modals, drawers, toasts)  | Standard animation           |
| Rare/first-time (onboarding)          | Can add delight              |

## Timing & Easing

Keep UI animations under 300ms. Modals and drawers are the exception and can run to 500ms. Use `ease-out` for entries (starts fast, feels responsive). Exit faster than enter (e.g., hold-to-delete: 2s press, 200ms release).

| Element            | Duration  |
| ------------------ | --------- |
| Button press       | 100-160ms |
| Tooltips, popovers | 125-200ms |
| Dropdowns, selects | 150-250ms |
| Modals, drawers    | 200-500ms |

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
```

## Component Patterns

| Pattern        | Implementation                                                                                        | Use When                                             |
| -------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Button press   | `transform: scale(0.97)` on `:active`                                                                 | Any pressable element (buttons, cards, list items)   |
| Element entry  | Start `scale(0.95)` + `opacity: 0`                                                                    | Anything appearing on screen (modals, toasts, cards) |
| Popover origin | Scale from the trigger. With Radix, `transform-origin: var(--radix-popover-content-transform-origin)` | Anchored to a trigger element                        |
| Modal origin   | Keep `center`                                                                                         | Not anchored; appears centered in the viewport       |
| Stagger        | 30-80ms delay between items                                                                           | Multiple elements entering together (lists, grids)   |
| Touch hover    | Gate behind `@media (hover: hover) and (pointer: fine)`                                               | Any hover effect that could fire on tap              |

## Edge Cases

When design constraints conflict with best practices, adapt rather than reject:

- Font unavailable: Substitute closest match from available families. Never fall back to system fonts silently.
- No custom easing support: Use standard `ease-out`. Never use `ease-in` as alternative.
- Animation library limitations: Work within the library's primitives. Don't force a library switch mid-task.

## Review Format

When reviewing UI code, report each finding as a Before, After, and Why row:

| Before                  | After                                  | Why                                            |
| ----------------------- | -------------------------------------- | ---------------------------------------------- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | Specify exact properties; avoid `all`          |
| `transform: scale(0)`   | `transform: scale(0.95); opacity: 0`   | Nothing in the real world appears from nothing |

## Accessibility

Reduce motion, don't eliminate it. Keep opacity/color transitions for comprehension. Remove transform-based motion for `prefers-reduced-motion`.

## Critique Loop

After building, screenshot the result at one phone width and one laptop width only, and review it before delivering. Check it against the chosen direction and the anti-patterns table. Fix what fails, re-shoot, repeat once.
