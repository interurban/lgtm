import React from 'react';
import {interpolate, staticFile, useCurrentFrame, Video} from 'remotion';
import {LGTMLabel} from '../LGTMLabel';
import {LowerThird} from '../LowerThird';
import {Scanlines} from '../Scanlines';

interface BrollVisual {
  scene_type: 'broll';
  clip_file?: string;
  lower_third?: {headline: string; subtitle?: string};
  fallback?: {headline?: string; subtitle?: string};
}

interface BrollSceneProps {
  visual: BrollVisual;
  enter?: string;
}

const BG = 'rgb(10, 10, 16)';
const ACCENT = 'rgb(232, 160, 32)';

/** Fallback card when no clip is available. */
const FallbackCard: React.FC<{headline?: string; subtitle?: string}> = ({headline, subtitle}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        width: '100%', height: '100%', background: BG,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        fontFamily: 'Consolas, monospace', opacity,
      }}
    >
      {headline && <div style={{color: ACCENT, fontSize: 120, textAlign: 'center'}}>{headline}</div>}
      {subtitle && <div style={{color: 'rgba(255,255,255,0.8)', fontSize: 52, textAlign: 'center', marginTop: 16}}>{subtitle}</div>}
    </div>
  );
};

export const BrollScene: React.FC<BrollSceneProps> = ({visual, enter = 'fade'}) => {
  const frame = useCurrentFrame();

  const sceneOpacity = enter === 'fade'
    ? interpolate(frame, [0, 7], [0, 1], {extrapolateRight: 'clamp'})
    : 1;

  // Derive just the filename from clip_file (e.g. "clips/s04.mp4" → "s04.mp4")
  const clipName = visual.clip_file?.split('/').pop() ?? visual.clip_file?.split('\\').pop();

  if (!clipName) {
    return <FallbackCard {...(visual.fallback ?? {})} />;
  }

  const lt = visual.lower_third;

  return (
    <div
      style={{
        width: '100%', height: '100%',
        position: 'relative', overflow: 'hidden',
        background: 'black',
        opacity: sceneOpacity,
      }}
    >
      {/* Full-bleed looping video */}
      <Video
        src={staticFile(`clips/${clipName}`)}
        loop
        muted
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />

      {/* Dim overlay */}
      <div style={{position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.42)'}} />

      <Scanlines />

      {lt && <LowerThird headline={lt.headline} subtitle={lt.subtitle} />}
      <LGTMLabel />
    </div>
  );
};
