import { FormEvent, useState } from "react";
import { createAccount } from "@/lib/api";

type Props = {
  onSuccess?: () => void;
};

export default function AccountForm({ onSuccess }: Props) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const formData = new FormData(event.currentTarget);
    const provider_slug = formData.get("provider_slug") as string;
    const label = formData.get("label") as string;
    const api_key = formData.get("api_key") as string;
    const api_secret = (formData.get("api_secret") as string) || undefined;
    const namecheap_api_user = formData.get("namecheap_api_user") as string;
    const namecheap_client_ip = formData.get("namecheap_client_ip") as string;

    setIsSubmitting(true);
    try {
      await createAccount({
        provider_slug,
        label,
        api_key,
        api_secret,
        extra_config:
          provider_slug === "namecheap"
            ? {
                api_user: namecheap_api_user,
                client_ip: namecheap_client_ip
              }
            : undefined
      });
      event.currentTarget.reset();
      onSuccess?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "建立帳號失敗");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <label className="text-sm text-slate-600">
          Provider
          <select name="provider_slug" className="mt-1 w-full rounded border px-3 py-2" required defaultValue="godaddy">
            <option value="godaddy">GoDaddy</option>
            <option value="namecheap">Namecheap</option>
          </select>
        </label>
        <label className="text-sm text-slate-600">
          顯示名稱
          <input name="label" className="mt-1 w-full rounded border px-3 py-2" placeholder="ex: GoDaddy 主帳號" required />
        </label>
        <label className="text-sm text-slate-600">
          API Key
          <input name="api_key" className="mt-1 w-full rounded border px-3 py-2" required />
        </label>
        <label className="text-sm text-slate-600">
          API Secret (GoDaddy)
          <input name="api_secret" className="mt-1 w-full rounded border px-3 py-2" />
        </label>
        <label className="text-sm text-slate-600">
          Namecheap API User
          <input name="namecheap_api_user" className="mt-1 w-full rounded border px-3 py-2" placeholder="NAMECHEAPUSER" />
        </label>
        <label className="text-sm text-slate-600">
          Namecheap Client IP
          <input name="namecheap_client_ip" className="mt-1 w-full rounded border px-3 py-2" placeholder="220.1.1.1" />
        </label>
      </div>
      {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-4 rounded bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {isSubmitting ? "建立中..." : "新增帳號"}
      </button>
    </form>
  );
}

