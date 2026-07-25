import { motion } from 'framer-motion'

// Big triangle subdivided into 3 rows of small triangles (1 + 3 + 5 = 9),
// generated from geometry rather than hardcoded so the layout stays exact.
const ROWS = 3
const SIZE = 240
const UNIT = SIZE / ROWS
const TRI_H = (UNIT * Math.sqrt(3)) / 2
const HEIGHT = TRI_H * ROWS
const GAP = 20 // px each triangle sits away from center when idle/separated
const PAD = GAP + 4 // viewBox padding so separated triangles don't clip at the edge

function buildTriangles() {
  const centerX = SIZE / 2
  const triangles = []

  for (let row = 0; row < ROWS; row++) {
    const count = 2 * row + 1
    const rowStartX = centerX - ((row + 1) * UNIT) / 2
    const y0 = row * TRI_H

    for (let i = 0; i < count; i++) {
      const pointsUp = i % 2 === 0
      const x0 = rowStartX + (i * UNIT) / 2

      const points = pointsUp
        ? [
            [x0 + UNIT / 2, y0],
            [x0, y0 + TRI_H],
            [x0 + UNIT, y0 + TRI_H],
          ]
        : [
            [x0, y0],
            [x0 + UNIT, y0],
            [x0 + UNIT / 2, y0 + TRI_H],
          ]

      const centroid = [
        (points[0][0] + points[1][0] + points[2][0]) / 3,
        (points[0][1] + points[1][1] + points[2][1]) / 3,
      ]

      triangles.push({ key: `${row}-${i}`, points, centroid })
    }
  }
  return triangles
}

const TRIANGLES = buildTriangles()
const SHAPE_CENTER = [SIZE / 2, HEIGHT / 2]

export default function Logo({ thinking = false, size = 96, className = '' }) {
  return (
    <svg
      viewBox={`${-PAD} ${-PAD} ${SIZE + PAD * 2} ${HEIGHT + PAD * 2}`}
      width={size}
      height={size * (HEIGHT / SIZE)}
      className={className}
    >
      {TRIANGLES.map(({ key, points, centroid }) => {
        const dx = centroid[0] - SHAPE_CENTER[0]
        const dy = centroid[1] - SHAPE_CENTER[1]
        const dist = Math.hypot(dx, dy) || 1
        const ux = dx / dist
        const uy = dy / dist

        return (
          <motion.polygon
            key={key}
            points={points.map((p) => p.join(',')).join(' ')}
            fill="var(--color-ink)"
            animate={
              thinking
                ? { x: [ux * GAP, 0, ux * GAP], y: [uy * GAP, 0, uy * GAP] }
                : { x: ux * GAP, y: uy * GAP }
            }
            transition={
              thinking
                ? { duration: 1.4, repeat: Infinity, ease: 'easeInOut' }
                : { duration: 0.6, ease: 'easeOut' }
            }
          />
        )
      })}
    </svg>
  )
}
