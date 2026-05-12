import DomainTable from "@/components/DomainTable";
import Layout from "@/components/Layout";
import { fetchAccounts, fetchDomains, syncDomains } from "@/lib/api";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function DomainsPage() {
  const [selectedAccount, setSelectedAccount] = useState<number | undefined>(undefined);
  const [search, setSearch] = useState("");

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: fetchAccounts
  });

  const domainsQuery = useQuery({
    queryKey: ["domains", selectedAccount, search],
    queryFn: () => fetchDomains({ accountId: selectedAccount, search }),
    keepPreviousData: true
  });

  const syncMutation = useMutation({
    mutationFn: (accountId: number) => syncDomains(accountId),
    onSuccess: () => domainsQuery.refetch()
  });

  const selectedAccountLabel = useMemo(() => {
    const target = accountsQuery.data?.find((account) => account.id === selectedAccount);
    return target?.label ?? "全部帳號";
  }, [accountsQuery.data, selectedAccount]);

  return (
    <Layout>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <label className="text-sm text-slate-600">
            選擇帳號
            <select
              className="mt-1 rounded border px-3 py-2"
              value={selectedAccount ?? ""}
              onChange={(event) => setSelectedAccount(event.target.value ? Number(event.target.value) : undefined)}
            >
              <option value="">全部</option>
              {accountsQuery.data?.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm text-slate-600">
            搜尋
            <input
              className="mt-1 rounded border px-3 py-2"
              placeholder="example.com"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          {selectedAccount && (
            <button
              onClick={() => syncMutation.mutate(selectedAccount)}
              className="rounded bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:opacity-70"
              disabled={syncMutation.isLoading}
            >
              {syncMutation.isLoading ? "同步中..." : "手動同步"}
            </button>
          )}
        </div>
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">域名列表 - {selectedAccountLabel}</h2>
            <span className="text-sm text-slate-500">{domainsQuery.data?.total ?? 0} 筆</span>
          </div>
          <DomainTable domains={domainsQuery.data?.items ?? []} isLoading={domainsQuery.isLoading} />
        </div>
      </div>
    </Layout>
  );
}

