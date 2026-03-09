import { useUISettings } from "../../features/ui/UISettingsProvider";

export function SettingsPage() {
  const { settings, setTheme, setBrandColor, setMenuMode, setMenuPosition } = useUISettings();

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">Admin • Configurações</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">Tema e identidade visual</h3>

          <div className="mb-3">
            <label className="mb-1 block text-sm">Tema</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              value={settings.theme}
              onChange={(e) => setTheme(e.target.value as "light" | "dark")}
            >
              <option value="light">Claro</option>
              <option value="dark">Escuro</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm">Cor primária</label>
            <input
              type="color"
              value={settings.brandColor}
              onChange={(e) => setBrandColor(e.target.value)}
              className="h-10 w-20 rounded border border-slate-300"
            />
          </div>
        </div>

        <div className="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-semibold">Menu e navegação</h3>

          <div className="mb-3">
            <label className="mb-1 block text-sm">Tipo de menu</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              value={settings.menuMode}
              onChange={(e) => setMenuMode(e.target.value as "sidebar" | "compact" | "top")}
            >
              <option value="sidebar">Lateral completo</option>
              <option value="compact">Lateral compacto</option>
              <option value="top">Superior</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm">Posição do menu</label>
            <select
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              value={settings.menuPosition}
              onChange={(e) => setMenuPosition(e.target.value as "left" | "right")}
              disabled={settings.menuMode === "top"}
            >
              <option value="left">Esquerda</option>
              <option value="right">Direita</option>
            </select>
          </div>
        </div>
      </div>
    </section>
  );
}
