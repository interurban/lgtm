import React from 'react';
import {staticFile, continueRender, delayRender} from 'remotion';

// Inject @font-face for VT323 + Press Start 2P, served from /public/fonts/
const fontFaces = `
  @font-face {
    font-family: 'VT323';
    src: url(${staticFile('fonts/VT323.woff2')}) format('woff2');
    font-display: block;
  }
  @font-face {
    font-family: 'Press Start 2P';
    src: url(${staticFile('fonts/PressStart2P.woff2')}) format('woff2');
    font-display: block;
  }
`;

let injected = false;
const injectFonts = () => {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const style = document.createElement('style');
  style.textContent = fontFaces;
  document.head.appendChild(style);

  // Force fonts to load before render proceeds
  if (document.fonts && document.fonts.load) {
    const handle = delayRender('Loading pixel fonts');
    Promise.all([
      document.fonts.load('16px "VT323"'),
      document.fonts.load('16px "Press Start 2P"'),
    ])
      .then(() => continueRender(handle))
      .catch(() => continueRender(handle));
  }
};

export const PixelFonts: React.FC = () => {
  injectFonts();
  return null;
};
