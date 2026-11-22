/** Concept A — "Amfiteatrul deschis" (Open Hemicycle).
 *
 * Original in-repo brand mark. Painted only with currentColor so it follows
 * the surrounding theme class in both dark and light themes. This component
 * returns the SVG *contents* so callers own the `<svg>` element, viewBox and
 * accessibility semantics (the hero wrapper is labelled, the header copy is).
 */
export default function BrandMark() {
  return (
    <>
      {/* Outer hemicycle arc (sweep=1 → upper semicircle) */}
      <path
        d="M36 150 A64 64 0 0 1 164 150"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        opacity={0.5}
      />
      {/* Middle seating arc (the seven seat dots sit on this r=50 arc) */}
      <path
        d="M50 150 A50 50 0 0 1 150 150"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity={0.35}
      />
      {/* Inner presidium arc */}
      <path
        d="M66 150 A34 34 0 0 1 134 150"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity={0.25}
      />
      {/* Seven seat dots on the middle arc (apex emphasised) */}
      <circle cx="54" cy="131" r="4.5" fill="currentColor" opacity={0.55} />
      <circle cx="65" cy="115" r="4.5" fill="currentColor" opacity={0.55} />
      <circle cx="81" cy="104" r="4.5" fill="currentColor" opacity={0.55} />
      <circle cx="100" cy="100" r="4.5" fill="currentColor" opacity={0.6} />
      <circle cx="119" cy="104" r="4.5" fill="currentColor" opacity={0.55} />
      <circle cx="135" cy="115" r="4.5" fill="currentColor" opacity={0.55} />
      <circle cx="146" cy="131" r="4.5" fill="currentColor" opacity={0.55} />
      {/* Broken floor — the 20-unit gap is the "open door" negative space */}
      <path d="M36 150 L90 150" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity={0.45} />
      <path d="M110 150 L164 150" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity={0.45} />
      {/* Doorway posts */}
      <path d="M90 144 L90 156" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity={0.4} />
      <path d="M110 144 L110 156" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity={0.4} />
    </>
  );
}
