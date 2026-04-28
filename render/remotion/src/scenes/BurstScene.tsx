import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {LGTMLabel} from '../LGTMLabel';
import {Scanlines} from '../Scanlines';

const ACCENT = '#e8a020';
const WHITE = '#f5f0d8';
const RED = '#e05050';
const CYAN = '#5fc8e8';
const BG = '#0a0a10';

const COLORS: Record<string, string> = {
  accent: ACCENT,
  white: WHITE,
  red: RED,
  cyan: CYAN,
};

const SIZES: Record<string, number> = {
  sm: 56,
  md: 92,
  lg: 140,
  xl: 180,
};

interface BurstItem {
  text: string;
  delay?: number;             // seconds
  color?: 'accent' | 'white' | 'red' | 'cyan' | string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  from?: 'left' | 'right' | 'top' | 'bottom' | 'scale';
  rotate?: number;            // degrees, light tilt for visual variety
  position?: {x: number; y: number}; // 0..100 percent of frame
}

interface BurstVisual {
  scene_type: 'burst';
  items: BurstItem[];
}

const offsetForFrom = (from?: string): {dx: number; dy: number} => {
  switch (from) {
    case 'left':   return {dx: -200, dy: 0};
    case 'right':  return {dx: +200, dy: 0};
    case 'top':    return {dx: 0,    dy: -200};
    case 'bottom': return {dx: 0,    dy: +200};
    default:       return {dx: 0,    dy: 0};
  }
};

export const BurstScene: React.FC<{visual: BurstVisual}> = ({visual}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {items} = visual;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: BG,
        fontFamily: 'Consolas, monospace',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Scanlines />
      <LGTMLabel />

      {items.map((item, i) => {
        const delayF = Math.round((item.delay ?? i * 0.15) * fps);
        const localFrame = Math.max(0, frame - delayF);
        const visible = frame >= delayF;
        if (!visible) return null;

        const progress = spring({
          frame: localFrame,
          fps,
          config: {damping: 14, stiffness: 240, mass: 0.7},
        });

        const offset = offsetForFrom(item.from);
        const scale = item.from === 'scale'
          ? interpolate(progress, [0, 1], [0.4, 1.0])
          : 1;
        const dx = interpolate(progress, [0, 1], [offset.dx, 0]);
        const dy = interpolate(progress, [0, 1], [offset.dy, 0]);

        const opacity = interpolate(localFrame, [0, 5], [0, 1], {
          extrapolateRight: 'clamp',
        });

        const color = COLORS[item.color ?? 'white'] ?? item.color ?? WHITE;
        const fontSize = SIZES[item.size ?? 'md'];
        const rotation = item.rotate ?? 0;

        // Default layout: vertical stack, centered, evenly spaced
        const defaultX = 50;
        const defaultY = items.length > 1
          ? 18 + (i / Math.max(1, items.length - 1)) * 64
          : 50;
        const px = item.position?.x ?? defaultX;
        const py = item.position?.y ?? defaultY;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${px}%`,
              top: `${py}%`,
              transform: `translate(-50%, -50%) translate(${dx}px, ${dy}px) scale(${scale}) rotate(${rotation}deg)`,
              opacity,
              color,
              fontSize,
              fontWeight: 'bold',
              letterSpacing: 2,
              whiteSpace: 'nowrap',
              textShadow: '4px 4px 0 rgba(0,0,0,0.85)',
            }}
          >
            {item.text}
          </div>
        );
      })}
    </div>
  );
};
