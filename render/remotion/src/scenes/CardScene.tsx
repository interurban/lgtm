import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentLine} from '../AccentLine';
import {LGTMLabel} from '../LGTMLabel';
import {Scanlines} from '../Scanlines';

const ACCENT = 'rgb(232, 160, 32)';
const BG = 'rgb(10, 10, 16)';

interface CardVisual {
  scene_type: 'card';
  headline?: string;
  subtitle?: string;
  headline_size?: number;
}

interface CardSceneProps {
  visual: CardVisual;
  enter?: string;
}

export const CardScene: React.FC<CardSceneProps> = ({visual, enter = 'fade'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {headline, subtitle, headline_size} = visual;

  // Headline: spring up from below
  const headlineProgress = spring({
    frame,
    fps,
    config: {damping: 20, stiffness: 180, mass: 0.9},
  });

  const headlineY = interpolate(headlineProgress, [0, 1], [48, 0]);
  const headlineOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Subtitle: fades in after headline settles
  const subtitleOpacity = interpolate(frame, [14, 24], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Scene-level entry (for snap/scale enter modes)
  let sceneScale = 1;
  if (enter === 'scale') {
    sceneScale = spring({frame, fps, config: {damping: 16, stiffness: 260, mass: 0.7}, from: 0.6, to: 1.0});
  } else if (enter === 'snap') {
    sceneScale = spring({frame, fps, config: {damping: 28, stiffness: 400, mass: 0.5}, from: 0.85, to: 1.0});
  }

  const sceneOpacity = enter === 'fade'
    ? interpolate(frame, [0, 7], [0, 1], {extrapolateRight: 'clamp'})
    : 1;

  const baseSize = headline_size ?? (subtitle ? 120 : 148);
  // Scale down for longer headlines to keep on one line
  const charCount = (headline ?? '').length;
  const fontSize = charCount > 20 ? Math.max(72, baseSize - (charCount - 20) * 3) : baseSize;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: BG,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Consolas, monospace',
        position: 'relative',
        transform: `scale(${sceneScale})`,
        opacity: sceneOpacity,
      }}
    >
      <Scanlines />
      <AccentLine />
      <LGTMLabel />

      {headline && (
        <div
          style={{
            color: ACCENT,
            fontSize,
            lineHeight: 1.1,
            textAlign: 'center',
            transform: `translateY(${headlineY}px)`,
            opacity: headlineOpacity,
            marginBottom: subtitle ? 20 : 0,
            maxWidth: '80%',
          }}
        >
          {headline}
        </div>
      )}

      {subtitle && (
        <div
          style={{
            color: 'rgba(255,255,255,0.88)',
            fontSize: 56,
            textAlign: 'center',
            opacity: subtitleOpacity,
            maxWidth: '80%',
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};
