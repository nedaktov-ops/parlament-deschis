
## Browser Support Policy

This project follows modern web best practices per [Chrome's modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance).

### Baseline Support
Features marked as "Baseline widely available" are safe to use without fallbacks:
- **`popover` attribute**: Baseline since Chrome 116 (Aug 2023), Edge 116, Firefox 125 (Apr 2024), Safari 17 (Sep 2023), Safari iOS 18.3 (Jan 2025)
- **Invoker Commands** (`command`/`commandfor`): Baseline since Chrome 135 (Apr 2025), Edge 135, Firefox 144 (Oct 2025), Safari 26.2 (Dec 2025)
- **`overscroll-behavior`**: Supported Chrome 144 (Jan 2026), Edge 144, Firefox 150 (Apr 2026). Not supported in Safari — treated as progressive enhancement.
- **Native `<dialog>`**: Supported in all modern browsers

### Progressive Enhancement
- **`overscroll-behavior` on non-scrollable containers**: Not feature-detectable. Treat as progressive enhancement — in supporting browsers, scrolling is fully contained. In non-supporting browsers, scrolling is contained when the modal's own content overflows.
- **`popover` attribute**: Requires `@oddbird/popover-polyfill` for older browsers. Must feature-detect via `HTMLElement.prototype.popover` and load polyfill only when missing — never load unconditionally.

### Project-Specific Notes
- `overscroll-behavior: contain` is used on modal overlays (About.tsx, PersonDrawer.tsx)
- `popover` attribute is used on CitationPopover — note that older browsers require the polyfill
- Button `type="button"` is required per HTML guide — all buttons in the codebase should have this attribute
- Color contrast should be verified against WCAG AA for all text/background combinations

For new features, consult the [modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) before implementation.
