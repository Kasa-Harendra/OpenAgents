interface ElectronBridge {
  platform: NodeJS.Platform;
  selectDirectory: () => Promise<string | null>;
}

declare global {
  interface Window {
    electron?: ElectronBridge;
  }
}

export {};
