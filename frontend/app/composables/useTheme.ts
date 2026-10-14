export const useTheme = () => {
  const themeStore = useThemeStore();

  const setMode = (mode: 'light' | 'dark' | 'system'): void => {
    themeStore.setMode(mode);
  };

  const setPreset = (preset: string): void => {
    themeStore.setPreset(preset as any);
  };

  const setDensity = (density: 'compact' | 'default' | 'comfortable'): void => {
    themeStore.setDensity(density);
  };

  const exportTheme = (): string => {
    const state = {
      findrTheme: 1,
      mode: themeStore.mode,
      preset: themeStore.preset,
      density: themeStore.density,
      colors: themeStore.colors,
    };
    return JSON.stringify(state, null, 2);
  };

  const importTheme = (json: string): void => {
    try {
      const state = JSON.parse(json);
      if (state.findrTheme === 1) {
        themeStore.mode = state.mode ?? 'system';
        themeStore.preset = state.preset ?? 'teal';
        themeStore.density = state.density ?? 'default';
        if (state.colors) {
          themeStore.colors = state.colors;
        }
        themeStore.applyAll();
        themeStore.persistTheme();
      }
    } catch (e) {
      console.error('Failed to import theme:', e);
    }
  };

  return {
    mode: computed(() => themeStore.mode),
    preset: computed(() => themeStore.preset),
    density: computed(() => themeStore.density),
    colors: computed(() => themeStore.colors),
    setMode,
    setPreset,
    setDensity,
    exportTheme,
    importTheme,
  };
};
