import React from 'react';

/** Subtle CRT scanline texture overlay — applied to all scenes for broadcast feel. */
export const Scanlines: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      backgroundImage:
        'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.06) 3px, rgba(0,0,0,0.06) 4px)',
      pointerEvents: 'none',
      zIndex: 10,
    }}
  />
);
