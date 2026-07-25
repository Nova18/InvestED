import { motion } from 'framer-motion'

// Idle-state coordinates taken directly from the source logo file (538x510
// viewBox). Each triangle also has a "mergeOffset" - how far it needs to
// translate to sit in a perfectly tessellated (gapless) 3-row triangle grid
// centered on the same point. Corner pieces travel much farther than inner
// ones, which is intentional (that's what makes the "thinking" merge read
// as pieces converging rather than just wobbling).
const TRIANGLES = [
  { points: '269.844,0 344.755,128.25 194.933,128.25', mergeOffset: [-1.0, 83.0] },
  { points: '139.844,155 214.755,283.25 64.933,283.25', mergeOffset: [54.0, 56.25] },
  { points: '272.844,297 197.933,168.75 347.755,168.75', mergeOffset: [-4.0, 42.5] },
  { points: '405.844,155 480.755,283.25 330.933,283.25', mergeOffset: [-62.0, 56.25] },
  { points: '75.3442,381 150.688,509.25 0,509.25', mergeOffset: [43.5, -41.5] },
  { points: '180.844,450 105.933,321.75 255.755,321.75', mergeOffset: [13.0, 17.75] },
  { points: '268.844,381 343.755,509.25 193.933,509.25', mergeOffset: [0, -41.5] },
  { points: '354.844,450 279.933,321.75 429.755,321.75', mergeOffset: [-11.0, 17.75] },
  { points: '462.344,381 537.688,509.25 387,509.25', mergeOffset: [-43.5, -41.5] },
]

const VIEW_W = 538
const VIEW_H = 510

export default function Logo({ thinking = false, size = 96, className = '' }) {
  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      width={size}
      height={size * (VIEW_H / VIEW_W)}
      className={className}
    >
      {TRIANGLES.map(({ points, mergeOffset: [dx, dy] }, i) => (
        <motion.polygon
          key={i}
          points={points}
          fill="var(--color-ink)"
          animate={
            thinking
              ? { x: [0, dx, 0], y: [0, dy, 0] }
              : { x: 0, y: 0 }
          }
          transition={
            thinking
              ? { duration: 1.4, repeat: Infinity, ease: 'easeInOut' }
              : { duration: 0.6, ease: 'easeOut' }
          }
        />
      ))}
    </svg>
  )
}
