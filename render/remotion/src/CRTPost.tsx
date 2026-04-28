import React from 'react';

/**
 * Full-screen CRT post-processing overlay.
 * Stacks: scanlines + vignette + soft chromatic aberration tint.
 * Render this AFTER scene content so it sits on top.
 */
export const CRTPost: React.FC = () => {
  return (
    <>
      {/* Scanlines: 4px period horizontal lines */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: `repeating-linear-gradient(
            0deg,
            rgba(0,0,0,0) 0 2px,
            rgba(0,0,0,0.28) 2px 4px
          )`,
          mixBlendMode: 'multiply',
          zIndex: 100,
        }}
      />
      {/* Soft RGB shift on edges via two tinted vignettes */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at 48% 50%, transparent 60%, rgba(255,40,80,0.10) 100%)',
          mixBlendMode: 'screen',
          zIndex: 101,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at 52% 50%, transparent 60%, rgba(40,140,255,0.10) 100%)',
          mixBlendMode: 'screen',
          zIndex: 102,
        }}
      />
      {/* Dark vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.55) 100%)',
          zIndex: 103,
        }}
      />
    </>
  );
};
