import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {LGTMLabel} from '../LGTMLabel';
import {Scanlines} from '../Scanlines';

interface MockupVisual {
  scene_type: 'mockup';
  mockup_image: string; // injected by remotion_renderer.py, e.g. "mockups/s06.png"
}

export const MockupScene: React.FC<{visual: MockupVisual; enter?: string}> = ({visual, enter = 'fade'}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  const opacity =
    enter === 'fade'
      ? interpolate(frame, [0, 7], [0, 1], {extrapolateRight: 'clamp'})
      : 1;

  // Subtle Ken Burns: slow zoom in over scene duration
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{width: '100%', height: '100%', position: 'relative', overflow: 'hidden', opacity}}>
      <Img
        src={staticFile(visual.mockup_image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${zoom})`,
          transformOrigin: 'center center',
        }}
      />
      <Scanlines />
      <LGTMLabel />
    </div>
  );
};
