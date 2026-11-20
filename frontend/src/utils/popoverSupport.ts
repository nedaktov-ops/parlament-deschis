// src/utils/popoverSupport.ts
/**
 * Dynamically ensures that the native Popover API is available.
 * If the browser does not support it, the @oddbird/popover-polyfill
 * is imported (which registers the polyfill globally).
 */
export async function ensurePopoverSupport(): Promise<void> {
  // In the build environment (Node) HTMLElement may be undefined.
  if (typeof HTMLElement !== 'undefined' && 'popover' in HTMLElement.prototype) {
    // Native support – nothing to do.
    return;
  }
  // Load the polyfill dynamically – it attaches itself to the global scope.
  // This import is only evaluated when needed, keeping bundle size minimal.
  await import('@oddbird/popover-polyfill');
}
