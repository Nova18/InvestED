import { motion } from 'framer-motion'

// Source geometry (236x232 viewBox). Big triangle is a fixed outline - the
// "track." Small triangle is a fixed solid piece that never moves. A second
// copy of the small triangle, drawn as an outline, is the animated piece:
// while thinking, it travels around the big triangle's perimeter and back.
const VIEW_W = 236
const VIEW_H = 232
const PAD = 40 // the traveling piece pokes past the original bounds at several waypoints

const APEX = [115.181, 20.2217]
const BOTTOM_RIGHT = [215.84, 222.75]
const BOTTOM_LEFT = [14.5232, 222.75]

const BIG_TRIANGLE = `${APEX} ${BOTTOM_RIGHT} ${BOTTOM_LEFT}`
const SMALL_TRIANGLE = '199.681,125 235.621,197 163.741,197'
const REST = [199.681, 173] // the small triangle's centroid

// How far outside each edge the traveling piece's centroid sits while
// gliding along it (perpendicular distance, same for all 3 edges so the
// gap "looks" consistent), and how far from each corner the flat part of
// the glide starts/ends (as a fraction of the edge's length).
const GAP = 8
const MARGIN = 0.15

// For an edge from `a` to `b`, return the two points `MARGIN`/`1-MARGIN`
// of the way along it, each pushed `GAP` units outward (away from the
// triangle's interior) - i.e. the entry and exit points of a segment that
// runs exactly parallel to that edge at a constant distance from it.
function edgeGlidePoints(a, b, interior) {
  const d = [b[0] - a[0], b[1] - a[1]]
  const len = Math.hypot(d[0], d[1])
  const unit = [d[0] / len, d[1] / len]
  // Two perpendicular candidates; keep whichever points away from the interior.
  let normal = [-unit[1], unit[0]]
  const towardInterior = [interior[0] - a[0], interior[1] - a[1]]
  if (normal[0] * towardInterior[0] + normal[1] * towardInterior[1] > 0) {
    normal = [-normal[0], -normal[1]]
  }
  const point = (t) => [
    a[0] + d[0] * t + normal[0] * GAP,
    a[1] + d[1] * t + normal[1] * GAP,
  ]
  return [point(MARGIN), point(1 - MARGIN)]
}

const CENTER = [
  (APEX[0] + BOTTOM_RIGHT[0] + BOTTOM_LEFT[0]) / 3,
  (APEX[1] + BOTTOM_RIGHT[1] + BOTTOM_LEFT[1]) / 3,
]

// Right edge only needs its entry point - its "exit" is rest itself (rest
// already sits right by this edge, so a second computed point there tends
// to land slightly past rest and overshoot on the final approach).
const [rightEntry] = edgeGlidePoints(APEX, BOTTOM_RIGHT, CENTER)
const [bottomEntry, bottomExit] = edgeGlidePoints(BOTTOM_RIGHT, BOTTOM_LEFT, CENTER)
const [leftEntry, leftExit] = edgeGlidePoints(BOTTOM_LEFT, APEX, CENTER)

const offsetFromRest = ([x, y]) => [x - REST[0], y - REST[1]]

// Rest -> across the bottom edge -> up the left edge -> across the right
// edge (which passes right by rest) -> back to rest.
const WAYPOINTS = [
  [0, 0],
  offsetFromRest(bottomEntry),
  offsetFromRest(bottomExit),
  offsetFromRest(leftEntry),
  offsetFromRest(leftExit),
  offsetFromRest(rightEntry),
  [0, 0],
]
const TIMES = [0, 0.06, 0.3, 0.36, 0.58, 0.64, 1]

// Glow intensity per waypoint (0-1), from each point's actual distance out
// of the resting position - so the glow genuinely tracks "how far from
// home," using the same keyframe/times mechanism as the movement itself
// rather than computing anything per-frame at runtime.
const distances = WAYPOINTS.map(([x, y]) => Math.hypot(x, y))
const maxDistance = Math.max(...distances)
const INTENSITY = distances.map((d) => d / maxDistance)

const INK_RGB = [16, 9, 37] // #100925
const GLOW_RGB = [66, 133, 255] // bright, clear blue

const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t))
const COLOR_KEYFRAMES = INTENSITY.map((t) => `rgb(${mix(INK_RGB, GLOW_RGB, t).join(',')})`)
const REST_COLOR = COLOR_KEYFRAMES[0]

// A drop-shadow around the whole group, not any single shape - blur radius
// and opacity both ramp with distance-from-rest, so the entire logo reads
// as "softly energized" together rather than just the traveling piece.
const GROUP_FILTER_KEYFRAMES = INTENSITY.map(
  (t) => `drop-shadow(0 0 ${(t * 11).toFixed(1)}px rgba(${GLOW_RGB.join(',')},${(t * 0.85).toFixed(2)}))`
)

const MOTION_TRANSITION = { type: 'tween', duration: 2.4, repeat: Infinity, ease: 'easeInOut', times: TIMES }
const IDLE_TRANSITION = { duration: 0.5, ease: 'easeOut' }

export default function Logo({ thinking = false, size = 96, className = '' }) {
  return (
    <svg
      viewBox={`${-PAD} ${-PAD} ${VIEW_W + PAD * 2} ${VIEW_H + PAD * 2}`}
      width={size}
      height={size * ((VIEW_H + PAD * 2) / (VIEW_W + PAD * 2))}
      className={className}
    >
      <motion.g
        animate={{ filter: thinking ? GROUP_FILTER_KEYFRAMES : GROUP_FILTER_KEYFRAMES[0] }}
        transition={thinking ? MOTION_TRANSITION : IDLE_TRANSITION}
      >
        <motion.polygon
          points={BIG_TRIANGLE}
          fill="none"
          strokeWidth="18"
          animate={{ stroke: thinking ? COLOR_KEYFRAMES : REST_COLOR }}
          transition={thinking ? MOTION_TRANSITION : IDLE_TRANSITION}
        />
        <motion.polygon
          points={SMALL_TRIANGLE}
          animate={{ fill: thinking ? COLOR_KEYFRAMES : REST_COLOR }}
          transition={thinking ? MOTION_TRANSITION : IDLE_TRANSITION}
        />
        <motion.polygon
          points={SMALL_TRIANGLE}
          fill="none"
          strokeWidth="4"
          animate={
            thinking
              ? {
                  x: WAYPOINTS.map((p) => p[0]),
                  y: WAYPOINTS.map((p) => p[1]),
                  stroke: COLOR_KEYFRAMES,
                }
              : { x: 0, y: 0, stroke: REST_COLOR }
          }
          transition={thinking ? MOTION_TRANSITION : IDLE_TRANSITION}
        />
      </motion.g>
    </svg>
  )
}
