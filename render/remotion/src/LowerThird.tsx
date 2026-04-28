import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const ACCENT = 'rgb(232, 160, 32)';

interface LowerThirdProps {
  headline: string;
  subtitle?: string;
}

export const LowerThird: React.FC<LowerThirdProps> = ({headline, subtitle}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Slide up from below
  const slideY = spring({
    frame,
    fps,
    config: {damping: 22, stiffness: 220, mass: 0.8},
    from: 80,
    to: 0,
  });

  const opacity = interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'});

  // Slide back down before scene ends
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames - 2],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  // Accent bar width draws in
  const barWidth = interpolate(frame, [4, 24], [0, 100], {extrapolateRight: 'clamp'});

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        transform: `translateY(${slideY}px)`,
        opacity: opacity * exitOpacity,
        zIndex: 8,
      }}
    >
      {/* Accent bar */}
      <div
        style={{
          width: `${barWidth}%`,
          height: 3,
          background: ACCENT,
        }}
      />
      {/* Text panel */}
      <div
        style={{
          background: 'rgba(0,0,0,0.72)',
          padding: '18px 72px 22px',
          fontFamily: 'Consolas, monospace',
        }}
      >
        <div style={{color: ACCENT, fontSize: 30, letterSpacing: '0.02em'}}>{headline}</div>
        {subtitle && (
          <div style={{color: 'rgba(255,255,255,0.8)', fontSize: 22, marginTop: 4}}>
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};
