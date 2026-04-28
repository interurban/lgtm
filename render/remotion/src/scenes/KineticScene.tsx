import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {AccentLine} from '../AccentLine';
import {LGTMLabel} from '../LGTMLabel';
import {Scanlines} from '../Scanlines';

const BG = 'rgb(10, 10, 16)';

const COLOR_MAP: Record<string, string> = {
  accent: 'rgb(232, 160, 32)',
  white: 'rgb(255, 255, 255)',
  red: 'rgb(220, 60, 60)',
};

interface KineticVisual {
  scene_type: 'kinetic';
  value: string;
  label?: string;
  color?: string;
  label_color?: string;
}

function isNumericValue(v: string): boolean {
  return /^-?\d+(\.\d+)?$/.test(v.replace(/[$M%,]/g, ''));
}

function parseNumeric(v: string): number {
  return parseFloat(v.replace(/[$M%,]/g, '')) || 0;
}

function formatWithPrefix(original: string, n: number): string {
  const prefix = original.startsWith('$') ? '$' : '';
  const suffix = original.endsWith('M') ? 'M' : original.endsWith('%') ? '%' : '';
  return `${prefix}${Math.round(n)}${suffix}`;
}

export const KineticScene: React.FC<{visual: KineticVisual}> = ({visual}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {value, label, color = 'accent', label_color = 'white'} = visual;

  // Scale bounce: 0.4 → 1.12 → 1.0
  const scaleSpring = spring({
    frame,
    fps,
    config: {damping: 10, stiffness: 280, mass: 0.6},
    from: 0.4,
    to: 1.0,
  });
  // Overshoot clamp: allow up to 1.12
  const scale = Math.min(scaleSpring, 1.12);

  const opacity = interpolate(frame, [0, 5], [0, 1], {extrapolateRight: 'clamp'});
  const labelOpacity = interpolate(frame, [12, 22], [0, 1], {extrapolateRight: 'clamp'});

  // Counter roll-up for numeric values
  let displayValue = value;
  if (isNumericValue(value)) {
    const target = parseNumeric(value);
    const rollProgress = interpolate(frame, [0, Math.round(fps * 0.45)], [0, target], {
      extrapolateRight: 'clamp',
      easing: (t) => 1 - Math.pow(1 - t, 3),
    });
    displayValue = formatWithPrefix(value, rollProgress);
  }

  const valueColor = COLOR_MAP[color] ?? COLOR_MAP.accent;
  const lColor = COLOR_MAP[label_color] ?? 'rgba(255,255,255,0.88)';

  const glowColor = valueColor.replace('rgb', 'rgba').replace(')', ', 0.35)');

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
      }}
    >
      <Scanlines />
      <AccentLine />
      <LGTMLabel />

      <div
        style={{
          color: valueColor,
          fontSize: 360,
          lineHeight: 1,
          transform: `scale(${scale})`,
          opacity,
          textShadow: `0 0 80px ${glowColor}, 0 0 160px ${glowColor}`,
          marginBottom: label ? 8 : 0,
        }}
      >
        {displayValue}
      </div>

      {label && (
        <div
          style={{
            color: lColor,
            fontSize: 52,
            opacity: labelOpacity,
            letterSpacing: '0.04em',
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};
