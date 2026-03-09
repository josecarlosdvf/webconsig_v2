import { Switch, Tab } from "@headlessui/react";
import { useState } from "react";
import { AuditTrail } from "./components/AuditTrail";
import { PluginManager } from "./components/PluginManager";
import { TransactionForm } from "./components/TransactionForm";
import { logFrontend } from "./lib/logger";

export default function App() {
  const [debugMode, setDebugMode] = useState(true);

  async function toggleDebug(value: boolean) {
    setDebugMode(value);
    await logFrontend("debug", "Debug mode alterado", { enabled: value });
  }

  return (
    <main className="mx-auto mt-10 max-w-5xl rounded-xl bg-white p-8 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Webconsig Modern Stack</h1>
          <p className="mt-1 text-sm text-slate-600">Experiência moderna, auditável e orientada a contratos.</p>
        </div>

        <div className="flex items-center gap-3">
          <Switch
            checked={debugMode}
            onChange={toggleDebug}
            className={`${debugMode ? "bg-emerald-600" : "bg-slate-300"} relative inline-flex h-6 w-11 items-center rounded-full`}
          >
            <span className="sr-only">Debug mode</span>
            <span
              className={`${debugMode ? "translate-x-6" : "translate-x-1"} inline-block h-4 w-4 transform rounded-full bg-white transition`}
            />
          </Switch>
          <span className="text-sm text-slate-700">Debug frontend: {debugMode ? "ON" : "OFF"}</span>
        </div>
      </div>

      <Tab.Group>
        <Tab.List className="mt-8 flex gap-2 border-b border-slate-200 pb-2">
          <Tab className="rounded-md px-4 py-2 text-sm font-medium ui-selected:bg-slate-900 ui-selected:text-white ui-not-selected:bg-slate-100 ui-not-selected:text-slate-700">
            Transações
          </Tab>
          <Tab className="rounded-md px-4 py-2 text-sm font-medium ui-selected:bg-slate-900 ui-selected:text-white ui-not-selected:bg-slate-100 ui-not-selected:text-slate-700">
            Auditoria
          </Tab>
          <Tab className="rounded-md px-4 py-2 text-sm font-medium ui-selected:bg-slate-900 ui-selected:text-white ui-not-selected:bg-slate-100 ui-not-selected:text-slate-700">
            Plugins
          </Tab>
        </Tab.List>
        <Tab.Panels className="mt-6">
          <Tab.Panel>
            <TransactionForm />
          </Tab.Panel>
          <Tab.Panel>
            <AuditTrail />
          </Tab.Panel>
          <Tab.Panel>
            <PluginManager />
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </main>
  );
}
