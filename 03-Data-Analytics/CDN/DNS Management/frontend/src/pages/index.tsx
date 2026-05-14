import Layout from "@/components/Layout";
import { fetchAccounts, fetchSyncJobs } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export default function DashboardPage() {
  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: fetchAccounts
  });

  const syncHistoryQuery = useQuery({
    queryKey: ["sync-jobs"],
    queryFn: fetchSyncJobs
  });

  return (
    <Layout>
      <div className="grid gap-4 md:grid-cols-3">
        <Card label="帳號數量" value={accountsQuery.data?.length ?? 0} />
        <Card label="同步紀錄" value={syncHistoryQuery.data?.items.length ?? 0} />
        <Card label="最新狀態" value={syncHistoryQuery.data?.items[0]?.status ?? "N/A"} />
      </div>
      <section className="mt-10 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">同步歷史</h2>
        <ul className="mt-4 space-y-2 text-sm text-slate-600">
          {(syncHistoryQuery.data?.items?.slice(0, 5) ?? []).map((job) => (
            <li key={job.id} className="flex items-center justify-between border-b border-slate-100 pb-2 last:border-b-0">
              <span>
                #{job.id} - {job.provider_slug} / acct {job.account_id}
              </span>
              <span className="text-xs uppercase text-slate-500">{job.status}</span>
            </li>
          ))}
          {!syncHistoryQuery.data?.items?.length && <li>目前沒有同步紀錄</li>}
        </ul>
      </section>
    </Layout>
  );
}

function Card({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-center shadow-sm">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

