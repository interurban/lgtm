import React from 'react';
import {Series} from 'remotion';
import {AmigaCardScene} from './scenes/AmigaCardScene';
import {BrollScene} from './scenes/BrollScene';
import {BurstScene} from './scenes/BurstScene';
import {CardScene} from './scenes/CardScene';
import {KineticScene} from './scenes/KineticScene';
import {MockupScene} from './scenes/MockupScene';
import {Captions, type Caption} from './Captions';
import {CRTPost} from './CRTPost';
import {PixelFonts} from './PixelFonts';
import {Workbench} from './Workbench';

export interface Scene {
  scene_id: string;
  type: string;
  start: number;
  duration: number;
  enter?: string;
  style?: string; // "amiga" wraps the scene in Workbench + CRT overlay
  visual: Record<string, unknown>;
  captions?: Caption[];
  vo?: {text: string; duration_hint: number};
  sfx?: Array<{at: number; name: string; vol?: number}>;
  notes?: string;
}

export interface EpisodeProps {
  scenes: Scene[];
  total_duration: number;
}

export const Episode: React.FC<EpisodeProps> = ({scenes}) => {
  return (
    <>
      <PixelFonts />
      <Series>
        {scenes.map((scene) => {
          const frames = Math.round(scene.duration * 30);
          return (
            <Series.Sequence key={scene.scene_id} durationInFrames={frames}>
              {wrapScene(scene)}
            </Series.Sequence>
          );
        })}
      </Series>
    </>
  );
};

function wrapScene(scene: Scene): React.ReactNode {
  const captions = <Captions captions={scene.captions} />;

  if (scene.style === 'amiga') {
    const visual = scene.visual as {amiga_title?: string};
    const title = visual.amiga_title || `LGTM:DH0/${scene.scene_id}.run`;
    const inner =
      scene.type === 'card' ? (
        <AmigaCardScene
          visual={scene.visual as Parameters<typeof AmigaCardScene>[0]['visual']}
          enter={scene.enter}
        />
      ) : (
        renderScene(scene)
      );
    return (
      <>
        <Workbench title={title}>{inner}</Workbench>
        <CRTPost />
        {captions}
      </>
    );
  }
  return (
    <>
      {renderScene(scene)}
      {captions}
    </>
  );
}

function renderScene(scene: Scene): React.ReactNode {
  const visual = scene.visual as Record<string, unknown>;
  const enter = scene.enter;

  switch (scene.type) {
    case 'card':
      return <CardScene visual={visual as Parameters<typeof CardScene>[0]['visual']} enter={enter} />;
    case 'kinetic':
      return <KineticScene visual={visual as Parameters<typeof KineticScene>[0]['visual']} />;
    case 'broll':
      return <BrollScene visual={visual as Parameters<typeof BrollScene>[0]['visual']} enter={enter} />;
    case 'mockup':
      return <MockupScene visual={visual as Parameters<typeof MockupScene>[0]['visual']} enter={enter} />;
    case 'burst':
      return <BurstScene visual={visual as Parameters<typeof BurstScene>[0]['visual']} />;
    default:
      return (
        <CardScene
          visual={{scene_type: 'card', headline: `[${scene.type}]`, subtitle: scene.scene_id}}
          enter={enter}
        />
      );
  }
}
