import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export type ThemeMode = 'light' | 'dark' | 'system';
export type ThemePreset = 'teal' | 'indigo' | 'graphite' | 'copper' | 'plum';
export type ThemeDensity = 'compact' | 'default' | 'comfortable';

export interface ThemeColors {
  accent: string;
  ground: string;
  surface: string;
  ink: string;
  add: string;
  edit: string;
  del: string;
  info: string;
}

export interface ThemeState {
  mode: ThemeMode;
  preset: ThemePreset;
  density: ThemeDensity;
  colors: {
    light: ThemeColors;
    dark: ThemeColors;
  };
}

const DEFAULT_PRESETS: Record<ThemePreset, { light: ThemeColors; dark: ThemeColors }> = {
  teal: {
    light: {
      accent: '#0a6b60',
      ground: '#edf0ef',
      surface: '#fafbfa',
      ink: '#16201e',
      add: '#1f8a4c',
      edit: '#c98a00',
      del: '#cc3b3b',
      info: '#2f6fcb',
    },
    dark: {
      accent: '#3fc1ae',
      ground: '#0e1413',
      surface: '#151d1b',
      ink: '#e3ebe8',
      add: '#4cc37a',
      edit: '#e3b341',
      del: '#ef6b6f',
      info: '#6fa3ea',
    },
  },
  indigo: {
    light: {
      accent: '#4338ca',
      ground: '#f3f2f7',
      surface: '#faf9fc',
      ink: '#1f1d35',
      add: '#1f8a4c',
      edit: '#c98a00',
      del: '#cc3b3b',
      info: '#4338ca',
    },
    dark: {
      accent: '#8e9bff',
      ground: '#0f0e1a',
      surface: '#1a1829',
      ink: '#e8e6f5',
      add: '#4cc37a',
      edit: '#e3b341',
      del: '#ef6b6f',
      info: '#8e9bff',
    },
  },
  graphite: {
    light: {
      accent: '#2f4b66',
      ground: '#eef1f3',
      surface: '#f9f9fa',
      ink: '#1a1d20',
      add: '#1f8a4c',
      edit: '#c98a00',
      del: '#cc3b3b',
      info: '#2f4b66',
    },
    dark: {
      accent: '#9db9d6',
      ground: '#0d0f11',
      surface: '#161819',
      ink: '#e2e4e7',
      add: '#4cc37a',
      edit: '#e3b341',
      del: '#ef6b6f',
      info: '#9db9d6',
    },
  },
  copper: {
    light: {
      accent: '#b04e16',
      ground: '#f5f2f0',
      surface: '#faf8f7',
      ink: '#251e1a',
      add: '#1f8a4c',
      edit: '#c98a00',
      del: '#cc3b3b',
      info: '#b04e16',
    },
    dark: {
      accent: '#e8935a',
      ground: '#0f0c0a',
      surface: '#1a1612',
      ink: '#f0ebe7',
      add: '#4cc37a',
      edit: '#e3b341',
      del: '#ef6b6f',
      info: '#e8935a',
    },
  },
  plum: {
    light: {
      accent: '#8a2b77',
      ground: '#f6f2f7',
      surface: '#faf8fc',
      ink: '#2a1a2e',
      add: '#1f8a4c',
      edit: '#c98a00',
      del: '#cc3b3b',
      info: '#8a2b77',
    },
    dark: {
      accent: '#d98bcb',
      ground: '#0f0a11',
      surface: '#1a1220',
      ink: '#f2e8f5',
      add: '#4cc37a',
      edit: '#e3b341',
      del: '#ef6b6f',
      info: '#d98bcb',
    },
  },
};

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('system');
  const preset = ref<ThemePreset>('teal');
  const density = ref<ThemeDensity>('default');
  const colors = ref<ThemeState['colors']>(JSON.parse(JSON.stringify(DEFAULT_PRESETS.teal)));

  const effectiveMode = computed(() => {
    if (mode.value === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return mode.value;
  });

  const setMode = (newMode: ThemeMode): void => {
    mode.value = newMode;
    applyTheme();
    persistTheme();
  };

  const setPreset = (newPreset: ThemePreset): void => {
    preset.value = newPreset;
    colors.value = JSON.parse(JSON.stringify(DEFAULT_PRESETS[newPreset]));
    applyTheme();
    persistTheme();
  };

  const setDensity = (newDensity: ThemeDensity): void => {
    density.value = newDensity;
    applyDensity();
    persistTheme();
  };

  const setColor = (colorKey: keyof ThemeColors, colorMode: 'light' | 'dark', value: string): void => {
    colors.value[colorMode][colorKey] = value;
    applyTheme();
    persistTheme();
  };

  const applyTheme = (): void => {
    const root = document.documentElement;
    const currentMode = effectiveMode.value;
    const currentColors = colors.value[currentMode];

    root.style.setProperty('--accent', currentColors.accent);
    root.style.setProperty('--ground', currentColors.ground);
    root.style.setProperty('--surface', currentColors.surface);
    root.style.setProperty('--ink', currentColors.ink);
    root.style.setProperty('--add', currentColors.add);
    root.style.setProperty('--edit', currentColors.edit);
    root.style.setProperty('--del', currentColors.del);
    root.style.setProperty('--info', currentColors.info);
  };

  const applyDensity = (): void => {
    const root = document.documentElement;
    root.setAttribute('data-density', density.value);
  };

  const applyAll = (): void => {
    const root = document.documentElement;

    if (mode.value !== 'system') {
      root.setAttribute('data-theme', mode.value);
    } else {
      root.removeAttribute('data-theme');
    }

    applyDensity();
    applyTheme();
  };

  const persistTheme = (): void => {
    const state: ThemeState = {
      mode: mode.value,
      preset: preset.value,
      density: density.value,
      colors: colors.value,
    };
    localStorage.setItem('findr-theme', JSON.stringify(state));
  };

  const loadTheme = (): void => {
    const saved = localStorage.getItem('findr-theme');
    if (saved) {
      try {
        const state: ThemeState = JSON.parse(saved);
        mode.value = state.mode;
        preset.value = state.preset;
        density.value = state.density;
        colors.value = state.colors;
      } catch (e) {
        console.error('Failed to load theme from localStorage:', e);
      }
    }
    applyAll();
  };

  const resetToPreset = (): void => {
    colors.value = JSON.parse(JSON.stringify(DEFAULT_PRESETS[preset.value]));
    applyTheme();
    persistTheme();
  };

  const resetAll = (): void => {
    mode.value = 'system';
    preset.value = 'teal';
    density.value = 'default';
    colors.value = JSON.parse(JSON.stringify(DEFAULT_PRESETS.teal));
    applyAll();
    persistTheme();
  };

  return {
    mode,
    preset,
    density,
    colors,
    effectiveMode,
    setMode,
    setPreset,
    setDensity,
    setColor,
    applyAll,
    loadTheme,
    resetToPreset,
    resetAll,
  };
});
