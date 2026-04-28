import React from 'react';
import {Composition} from 'remotion';
import {Episode, type EpisodeProps} from './Episode';

const DEFAULT_PROPS: EpisodeProps = {
  scenes: [],
  total_duration: 10,
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Episode"
      component={Episode}
      fps={30}
      width={1920}
      height={1080}
      durationInFrames={300}
      defaultProps={DEFAULT_PROPS}
      calculateMetadata={async ({props}) => ({
        durationInFrames: Math.round((props as EpisodeProps).total_duration * 30),
      })}
    />
  );
};
