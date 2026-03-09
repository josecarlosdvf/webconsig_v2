import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";

export type MenuMode = "sidebar" | "compact" | "top";
export type MenuPosition = "left" | "right";
export type ThemeMode = "light" | "dark";
export type DevicePreset = "mobile" | "tablet" | "desktop" | "tv";
export type PresetMode = "auto" | "manual" | "custom";

type UISettings = {
  theme: ThemeMode;
  brandColor: string;
  menuMode: MenuMode;
  menuPosition: MenuPosition;
  presetMode: PresetMode;
  manualPreset: DevicePreset;
};

type UISettingsContextType = {
  settings: UISettings;
  effectiveSettings: UISettings;
  viewportPreset: DevicePreset;
  setTheme: (theme: ThemeMode) => void;
  setBrandColor: (color: string) => void;
  setMenuMode: (mode: MenuMode) => void;
  setMenuPosition: (position: MenuPosition) => void;
  setPresetMode: (mode: PresetMode) => void;
  setManualPreset: (preset: DevicePreset) => void;
};

const UI_SETTINGS_KEY = "webconsig_ui_settings";

const defaultSettings: UISettings = {
  theme: "light",
  brandColor: "#0f172a",
  menuMode: "sidebar",
  menuPosition: "left",
  presetMode: "auto",
  manualPreset: "desktop"
};

const presetMenuMap: Record<DevicePreset, { menuMode: MenuMode; menuPosition: MenuPosition }> = {
  mobile: { menuMode: "top", menuPosition: "left" },
  tablet: { menuMode: "top", menuPosition: "left" },
  desktop: { menuMode: "sidebar", menuPosition: "left" },
  tv: { menuMode: "top", menuPosition: "left" },
};

function detectViewportPreset(width: number): DevicePreset {
  if (width >= 1920) {
    return "tv";
  }
  if (width >= 1280) {
    return "desktop";
  }
  if (width >= 768) {
    return "tablet";
  }
  return "mobile";
}

const UISettingsContext = createContext<UISettingsContextType | undefined>(undefined);

export function UISettingsProvider({ children }: { children: ReactNode }) {
  const [viewportPreset, setViewportPreset] = useState<DevicePreset>(() => detectViewportPreset(window.innerWidth));
  const [settings, setSettings] = useState<UISettings>(() => {
    const saved = localStorage.getItem(UI_SETTINGS_KEY);
    return saved ? ({ ...defaultSettings, ...(JSON.parse(saved) as Partial<UISettings>) } as UISettings) : defaultSettings;
  });

  useEffect(() => {
    function onResize() {
      setViewportPreset(detectViewportPreset(window.innerWidth));
    }

    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const effectiveSettings = useMemo<UISettings>(() => {
    const sourcePreset = settings.presetMode === "auto" ? viewportPreset : settings.manualPreset;
    if (settings.presetMode === "custom") {
      return settings;
    }

    return {
      ...settings,
      menuMode: presetMenuMap[sourcePreset].menuMode,
      menuPosition: presetMenuMap[sourcePreset].menuPosition,
    };
  }, [settings, viewportPreset]);

  useEffect(() => {
    localStorage.setItem(UI_SETTINGS_KEY, JSON.stringify(settings));
    document.documentElement.dataset.theme = effectiveSettings.theme;
    document.documentElement.dataset.viewport = viewportPreset;
    document.documentElement.style.setProperty("--brand-color", effectiveSettings.brandColor);
  }, [settings, effectiveSettings, viewportPreset]);

  const value = useMemo(
    () => ({
      settings,
      effectiveSettings,
      viewportPreset,
      setTheme: (theme: ThemeMode) => setSettings((current) => ({ ...current, theme })),
      setBrandColor: (brandColor: string) => setSettings((current) => ({ ...current, brandColor })),
      setMenuMode: (menuMode: MenuMode) => setSettings((current) => ({ ...current, menuMode })),
      setMenuPosition: (menuPosition: MenuPosition) => setSettings((current) => ({ ...current, menuPosition })),
      setPresetMode: (presetMode: PresetMode) => setSettings((current) => ({ ...current, presetMode })),
      setManualPreset: (manualPreset: DevicePreset) => setSettings((current) => ({ ...current, manualPreset })),
    }),
    [effectiveSettings, settings, viewportPreset]
  );

  return <UISettingsContext.Provider value={value}>{children}</UISettingsContext.Provider>;
}

export function useUISettings() {
  const context = useContext(UISettingsContext);
  if (!context) {
    throw new Error("useUISettings must be used within UISettingsProvider");
  }

  return context;
}
