import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export interface Caption {
  text: string;
  at: number;          // seconds from scene start
  duration?: number;   // seconds; defaults to remainder of scene
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'top' | 'bottom';
  color?: string;      // accent | white | red | cyan | <css>
  size?: 'sm' | 'md' | 'lg';
}

const COLORS: Record<string, string> = {
  accent: '#e8a020',
  white: '#f5f0d8',
  red: '#e05050',
  cyan: '#5fc8e8',
  default: '#f5f0d8',
};

const SIZES: Record<string, number> = {
  sm: 28,
  md: 40,
  lg: 56,
};

const POSITIONS: Record<string, React.CSSProperties> = {
  'top-left':     {top: 70, left: 70, textAlign: 'left'},
  'top-right':    {top: 70, right: 70, textAlign: 'right'},
  'bottom-left':  {bottom: 90, left: 70, textAlign: 'left'},
  'bottom-right': {bottom: 90, right: 70, textAlign: 'right'},
  'top':          {top: 70, left: 0, right: 0, textAlign: 'center'},
  'bottom':       {bottom: 90, left: 0, right: 0, textAlign: 'center'},
};

export const Captions: React.FC<{captions?: Caption[]}> = ({captions}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!captions || captions.length === 0) return null;

  return (
    <>
      {captions.map((cap, i) => {
        const startF = Math.round(cap.at * fps);
        const dur = cap.duration ?? 999;
        const endF = startF + Math.round(dur * fps);
        if (frame < startF || frame > endF) return null;

        // Fade-in over 4 frames, fade-out over 4 frames
        const opacity = interpolate(
          frame,
          [startF, startF + 4, endF - 4, endF],
          [0, 1, 1, 0],
          {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
        );
        // Slide-in from below by 12px over 4 frames
        const dy = interpolate(frame, [startF, startF + 4], [12, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        const color = COLORS[cap.color ?? 'default'] ?? cap.color ?? COLORS.default;
        const size = SIZES[cap.size ?? 'md'];
        const pos = POSITIONS[cap.position ?? 'bottom'];

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              ...pos,
              fontFamily: '"VT323", Consolas, monospace',
              fontSize: size,
              color,
              opacity,
              transform: `translateY(${dy}px)`,
              letterSpacing: 1,
              textShadow: '2px 2px 0 rgba(0,0,0,0.85)',
              pointerEvents: 'none',
              zIndex: 50,
              padding: '4px 12px',
            }}
          >
            {cap.text}
          </div>
        );
      })}
    </>
  );
};
