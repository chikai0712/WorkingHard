import AccountForm from "@/components/AccountForm";
import Layout from "@/components/Layout";
import { fetchAccounts } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export default function AccountsPage() {
  const { data, refetch, isFetching } = useQuery({
    queryKey: ["accounts"],
    queryFn: fetchAccounts
  });

  return (
    <Layout>
      <div className="flex flex-col gap-6">
        <section>
          <h2 className="text-lg font-semibold text-slate-900">新增帳號</h2>
          <p className="text-sm text-slate-500">支援 GoDaddy / Namecheap，請填入 API 凭證並測試連線。</p>
          <AccountForm onSuccess={refetch} />
        </section>
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">已設定帳號</h2>
            {isFetching && <span className="text-xs text-slate-500">重新整理中...</span>}
          </div>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Label</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Provider</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">建立時間</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.map((account) => (
                  <tr key={account.id}>
                    <td className="px-4 py-2 font-medium text-slate-900">{account.label}</td>
                    <td className="px-4 py-2 text-slate-600">{account.provider_name ?? account.provider_slug}</td>
                    <td className="px-4 py-2 text-slate-500">
                      {account.created_at ? new Date(account.created_at).toLocaleString() : "-"}
                    </td>
                  </tr>
                )) ?? (
                  <tr>
                    <td className="px-4 py-3 text-center text-slate-500" colSpan={3}>
                      目前沒有資料
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </Layout>
  );
}

