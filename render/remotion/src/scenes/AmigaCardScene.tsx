import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const AMBER = '#e8a020';
const CYAN = '#5fc8e8';
const DIRTY_WHITE = '#f5f0d8';

interface AmigaCardVisual {
  scene_type?: 'card';
  headline?: string;
  subtitle?: string;
  amiga_title?: string;
  amiga_icons?: Array<'disk' | 'folder' | 'caution' | 'arrow'>;
}

interface Props {
  visual: AmigaCardVisual;
  enter?: string;
}

const Icon: React.FC<{name: string}> = ({name}) => {
  // Chunky pixel-art icons drawn as nested boxes
  const common: React.CSSProperties = {
    width: 80,
    height: 80,
    display: 'inline-grid',
    placeItems: 'center',
    border: '3px solid #000',
    boxShadow: 'inset 3px 3px 0 0 rgba(255,255,255,0.35), inset -3px -3px 0 0 rgba(0,0,0,0.55)',
  };
  if (name === 'disk') {
    return (
      <div style={{...common, background: AMBER}}>
        <div style={{width: 40, height: 18, background: '#0a0a10'}} />
      </div>
    );
  }
  if (name === 'folder') {
    return (
      <div style={{...common, background: CYAN}}>
        <div style={{width: 50, height: 30, background: '#0a0a10'}} />
      </div>
    );
  }
  if (name === 'caution') {
    return (
      <div style={{...common, background: '#cc3a3a', color: DIRTY_WHITE, fontFamily: '"Press Start 2P", monospace', fontSize: 36}}>!</div>
    );
  }
  return (
    <div style={{...common, background: DIRTY_WHITE, color: '#0a0a10', fontFamily: '"Press Start 2P", monospace', fontSize: 32}}>►</div>
  );
};

export const AmigaCardScene: React.FC<Props> = ({visual, enter = 'fade'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {headline, subtitle, amiga_icons} = visual;

  const headlineProgress = spring({
    frame,
    fps,
    config: {damping: 20, stiffness: 220, mass: 0.7},
  });

  const headlineY = interpolate(headlineProgress, [0, 1], [40, 0]);
  const headlineOpacity = interpolate(frame, [0, 5], [0, 1], {extrapolateRight: 'clamp'});
  const subtitleOpacity = interpolate(frame, [10, 20], [0, 1], {extrapolateRight: 'clamp'});
  const cursorVisible = Math.floor(frame / 12) % 2 === 0;

  const sceneOpacity =
    enter === 'fade' ? interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'}) : 1;

  // Adaptive headline size — Press Start 2P is much wider per char than Consolas
  const charCount = (headline ?? '').length;
  const headlineSize = charCount > 14 ? Math.max(36, 80 - (charCount - 14) * 3) : 80;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 60px',
        opacity: sceneOpacity,
        position: 'relative',
        gap: 36,
      }}
    >
      {amiga_icons && amiga_icons.length > 0 && (
        <div style={{display: 'flex', gap: 28, marginBottom: 16}}>
          {amiga_icons.map((name, i) => (
            <Icon key={i} name={name} />
          ))}
        </div>
      )}

      {headline && (
        <div
          style={{
            fontFamily: '"Press Start 2P", monospace',
            fontSize: headlineSize,
            color: AMBER,
            textAlign: 'center',
            transform: `translateY(${headlineY}px)`,
            opacity: headlineOpacity,
            lineHeight: 1.3,
            textShadow: '4px 4px 0 #000',
            letterSpacing: 2,
          }}
        >
          {headline}
        </div>
      )}

      {subtitle && (
        <div
          style={{
            fontFamily: '"VT323", monospace',
            fontSize: 56,
            color: DIRTY_WHITE,
            textAlign: 'center',
            opacity: subtitleOpacity,
            lineHeight: 1.1,
            letterSpacing: 1,
          }}
        >
          {subtitle}
          <span style={{opacity: cursorVisible ? 1 : 0, color: AMBER}}>_</span>
        </div>
      )}
    </div>
  );
};
