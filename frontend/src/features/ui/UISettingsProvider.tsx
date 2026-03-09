import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";

export type MenuMode = "sidebar" | "compact" | "top";
export type MenuPosition = "left" | "right";
export type ThemeMode = "light" | "dark";

type UISettings = {
  theme: ThemeMode;
  brandColor: string;
  menuMode: MenuMode;
  menuPosition: MenuPosition;
};

type UISettingsContextType = {
  settings: UISettings;
  setTheme: (theme: ThemeMode) => void;
  setBrandColor: (color: string) => void;
  setMenuMode: (mode: MenuMode) => void;
  setMenuPosition: (position: MenuPosition) => void;
};

const UI_SETTINGS_KEY = "webconsig_ui_settings";

const defaultSettings: UISettings = {
  theme: "light",
  brandColor: "#0f172a",
  menuMode: "sidebar",
  menuPosition: "left"
};

const UISettingsContext = createContext<UISettingsContextType | undefined>(undefined);

export function UISettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<UISettings>(() => {
    const saved = localStorage.getItem(UI_SETTINGS_KEY);
    return saved ? ({ ...defaultSettings, ...(JSON.parse(saved) as Partial<UISettings>) } as UISettings) : defaultSettings;
  });

  useEffect(() => {
    localStorage.setItem(UI_SETTINGS_KEY, JSON.stringify(settings));
    document.documentElement.dataset.theme = settings.theme;
    document.documentElement.style.setProperty("--brand-color", settings.brandColor);
  }, [settings]);

  const value = useMemo(
    () => ({
      settings,
      setTheme: (theme: ThemeMode) => setSettings((current) => ({ ...current, theme })),
      setBrandColor: (brandColor: string) => setSettings((current) => ({ ...current, brandColor })),
      setMenuMode: (menuMode: MenuMode) => setSettings((current) => ({ ...current, menuMode })),
      setMenuPosition: (menuPosition: MenuPosition) => setSettings((current) => ({ ...current, menuPosition }))
    }),
    [settings]
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
