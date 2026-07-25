import { motion } from 'framer-motion'

// Source geometry (236x232 viewBox). Big triangle is a fixed outline - the
// "track." Small triangle is a fixed solid piece that never moves. A second
// copy of the small triangle, drawn as an outline, is the animated piece:
// while thinking, it travels from its resting spot (overlapping the solid
// triangle, near the big triangle's bottom-right vertex) around the other
// two vertices and back, tracing the big triangle's perimeter.
const VIEW_W = 236
const VIEW_H = 232
const PAD = 40 // the traveling piece pokes past the original bounds at two waypoints

const BIG_TRIANGLE = '115.181,20.2217 215.84,222.75 14.5232,222.75'
const SMALL_TRIANGLE = '199.681,125 235.621,197 163.741,197'

// Offsets (from rest) for the traveling piece's centroid: rest -> bottom-left
// vertex -> top apex -> back to rest. The rest->bottom-left leg holds y at 0
// (matching rest's height) so it glides flat along the bottom edge instead
// of drifting toward the vertex's exact (lower) y-position.
const WAYPOINTS = [
  [0, 0],
  [-185.16, 0],
  [-84.5, -152.78],
  [0, 0],
]

export default function Logo({ thinking = false, size = 96, className = '' }) {
  return (
    <svg
      viewBox={`${-PAD} ${-PAD} ${VIEW_W + PAD * 2} ${VIEW_H + PAD * 2}`}
      width={size}
      height={size * ((VIEW_H + PAD * 2) / (VIEW_W + PAD * 2))}
      className={className}
    >
      <polygon points={BIG_TRIANGLE} fill="none" stroke="var(--color-ink)" strokeWidth="18" />
      <polygon points={SMALL_TRIANGLE} fill="var(--color-ink)" />
      <motion.polygon
        points={SMALL_TRIANGLE}
        fill="none"
        stroke="var(--color-ink)"
        strokeWidth="4"
        animate={
          thinking
            ? { x: WAYPOINTS.map((p) => p[0]), y: WAYPOINTS.map((p) => p[1]) }
            : { x: 0, y: 0 }
        }
        transition={
          thinking
            ? { duration: 2.4, repeat: Infinity, ease: 'easeInOut', times: [0, 0.33, 0.66, 1] }
            : { duration: 0.5, ease: 'easeOut' }
        }
      />
    </svg>
  )
}
