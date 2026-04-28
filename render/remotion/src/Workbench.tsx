import React from 'react';

interface WorkbenchProps {
  title?: string;
  children: React.ReactNode;
}

const PALETTE = {
  desktop: '#1a1a26',
  desktopAlt: '#0e0e16',
  windowBg: '#0a0a10',
  bevelLight: '#f5f0d8',
  bevelDark: '#2a2030',
  titleBar: '#e8a020',
  titleText: '#0a0a10',
  closeBoxBg: '#0a0a10',
  closeBoxFg: '#f5f0d8',
};

// Window inset within the 1920x1080 frame
const WIN_INSET = {x: 90, y: 70};
const TITLE_BAR_H = 56;

export const Workbench: React.FC<WorkbenchProps> = ({title = 'LGTM:DH0/episode.run', children}) => {
  const winLeft = WIN_INSET.x;
  const winTop = WIN_INSET.y;
  const winW = 1920 - WIN_INSET.x * 2;
  const winH = 1080 - WIN_INSET.y * 2;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        // Dithered Workbench desktop pattern (Bayer-ish 2x2)
        background: `
          repeating-conic-gradient(
            ${PALETTE.desktop} 0 25%,
            ${PALETTE.desktopAlt} 0 50%
          )
        `,
        backgroundSize: '6px 6px',
      }}
    >
      {/* Drop shadow block — solid offset */}
      <div
        style={{
          position: 'absolute',
          left: winLeft + 14,
          top: winTop + 14,
          width: winW,
          height: winH,
          background: 'rgba(0,0,0,0.85)',
        }}
      />

      {/* Window */}
      <div
        style={{
          position: 'absolute',
          left: winLeft,
          top: winTop,
          width: winW,
          height: winH,
          background: PALETTE.windowBg,
          // Beveled frame: light top/left, dark bottom/right
          boxShadow: `
            inset 4px 4px 0 0 ${PALETTE.bevelLight},
            inset -4px -4px 0 0 ${PALETTE.bevelDark}
          `,
          border: `2px solid #000`,
          display: 'flex',
          flexDirection: 'column',
          fontFamily: '"Press Start 2P", "VT323", monospace',
        }}
      >
        {/* Title bar */}
        <div
          style={{
            height: TITLE_BAR_H,
            background: PALETTE.titleBar,
            color: PALETTE.titleText,
            display: 'flex',
            alignItems: 'center',
            paddingLeft: 12,
            paddingRight: 12,
            gap: 14,
            borderBottom: '2px solid #000',
            // Inner bevel on title bar
            boxShadow: 'inset 0 -2px 0 0 rgba(0,0,0,0.25), inset 0 2px 0 0 rgba(255,255,255,0.20)',
          }}
        >
          {/* Close box */}
          <div
            style={{
              width: 32,
              height: 32,
              background: PALETTE.closeBoxBg,
              color: PALETTE.closeBoxFg,
              fontFamily: '"Press Start 2P", monospace',
              fontSize: 14,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'inset 2px 2px 0 0 rgba(255,255,255,0.4), inset -2px -2px 0 0 rgba(0,0,0,0.6)',
            }}
          >
            X
          </div>

          {/* Title text */}
          <div
            style={{
              fontFamily: '"Press Start 2P", monospace',
              fontSize: 16,
              letterSpacing: 1,
              flex: 1,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'clip',
            }}
          >
            {title}
          </div>

          {/* Drag pattern (dotted stripes, classic Amiga title bar) */}
          <div
            style={{
              flex: '0 1 360px',
              height: 18,
              background: `repeating-linear-gradient(
                0deg,
                ${PALETTE.titleText} 0 2px,
                transparent 2px 5px
              )`,
              opacity: 0.55,
            }}
          />

          {/* Depth/zoom gadget squares */}
          <div style={{display: 'flex', gap: 6}}>
            <div
              style={{
                width: 32,
                height: 32,
                background: PALETTE.closeBoxBg,
                color: PALETTE.closeBoxFg,
                fontFamily: '"Press Start 2P", monospace',
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'inset 2px 2px 0 0 rgba(255,255,255,0.4), inset -2px -2px 0 0 rgba(0,0,0,0.6)',
              }}
            >
              □
            </div>
          </div>
        </div>

        {/* Body — children render here */}
        <div style={{flex: 1, position: 'relative', overflow: 'hidden'}}>
          {children}
        </div>
      </div>
    </div>
  );
};
