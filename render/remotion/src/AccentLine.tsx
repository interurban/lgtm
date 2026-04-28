import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

const ACCENT = 'rgb(232, 160, 32)';

/** Thin amber line that draws across the bottom of a scene over the first ~20 frames. */
export const AccentLine: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const drawIn = interpolate(frame, [0, 20], [0, 100], {extrapolateRight: 'clamp'});
  // Fade out in last 8 frames
  const opacity = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        width: `${drawIn}%`,
        height: 3,
        background: ACCENT,
        opacity: opacity * 0.65,
        zIndex: 9,
      }}
    />
  );
};
