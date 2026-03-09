import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../../features/auth/AuthProvider";

const loginSchema = z.object({
  username: z.string().min(3, "Usuário obrigatório"),
  password: z.string().min(6, "Senha obrigatória")
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isSsoMode } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema), defaultValues: { username: "admin", password: "" } });

  async function onSubmit(values: LoginForm) {
    const ok = await login(values.username, values.password);
    if (!ok) {
      setError("root", { message: "Credenciais inválidas" });
      return;
    }
    navigate("/");
  }

  async function onSsoLogin() {
    await login("", "");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 to-slate-700 p-4">
      <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <h1 className="text-2xl font-semibold text-slate-900">Webconsig Admin</h1>
        <p className="mt-1 text-sm text-slate-600">Acesso administrativo ERP/CRM</p>

        {isSsoMode ? (
          <div className="mt-6 space-y-4">
            <button
              type="button"
              onClick={onSsoLogin}
              disabled={isSubmitting}
              className="w-full rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-60"
            >
              Entrar com Keycloak
            </button>
          </div>
        ) : (
        <div className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Usuário</label>
            <input {...register("username")} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
            {errors.username ? <p className="mt-1 text-xs text-red-600">{errors.username.message}</p> : null}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Senha</label>
            <input type="password" {...register("password")} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
            {errors.password ? <p className="mt-1 text-xs text-red-600">{errors.password.message}</p> : null}
          </div>
          {errors.root ? <p className="text-sm text-red-600">{errors.root.message}</p> : null}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-60"
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </div>
        )}
      </form>
    </div>
  );
}
