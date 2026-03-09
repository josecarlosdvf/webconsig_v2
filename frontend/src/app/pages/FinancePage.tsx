import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const formSchema = z.object({
  centroCusto: z.string().min(2, "Centro de custo obrigatório"),
  limite: z.coerce.number().positive("Limite deve ser maior que zero")
});

type FinanceForm = z.infer<typeof formSchema>;

export function FinancePage() {
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<FinanceForm>({ resolver: zodResolver(formSchema), defaultValues: { centroCusto: "Comercial", limite: 50000 } });

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">ERP • Financeiro</h2>
      <form onSubmit={handleSubmit(() => undefined)} className="max-w-xl rounded-xl bg-white p-4 shadow-sm">
        <div className="grid gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Centro de custo</label>
            <input className="w-full rounded-lg border border-slate-300 px-3 py-2" {...register("centroCusto")} />
            {errors.centroCusto ? <p className="mt-1 text-xs text-red-600">{errors.centroCusto.message}</p> : null}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Limite operacional</label>
            <input type="number" className="w-full rounded-lg border border-slate-300 px-3 py-2" {...register("limite")} />
            {errors.limite ? <p className="mt-1 text-xs text-red-600">{errors.limite.message}</p> : null}
          </div>
          <button className="rounded-lg bg-slate-900 px-4 py-2 text-white hover:bg-slate-700" type="submit">
            Salvar parâmetros
          </button>
        </div>
      </form>
    </section>
  );
}
