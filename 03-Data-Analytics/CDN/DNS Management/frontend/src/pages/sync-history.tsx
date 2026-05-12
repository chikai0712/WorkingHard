import Layout from "@/components/Layout";
import { fetchSyncJobs } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export default function SyncHistoryPage() {
  const { data, isFetching } = useQuery({
    queryKey: ["sync-jobs"],
    queryFn: fetchSyncJobs
  });

  return (
    <Layout>
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">同步歷史</h2>
          {isFetching && <span className="text-xs text-slate-500">更新中...</span>}
        </div>
        <ul className="space-y-3 text-sm text-slate-600">
          {data?.items.map((job) => (
            <li key={job.id} className="rounded border border-slate-100 p-3">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-900">
                  #{job.id} / {job.provider_slug} / Account {job.account_id}
                </span>
                <span className="text-xs uppercase text-slate-500">{job.status}</span>
              </div>
              <p className="text-xs text-slate-500">
                {job.started_at && `開始：${new Date(job.started_at).toLocaleString()} `}
                {job.finished_at && `結束：${new Date(job.finished_at).toLocaleString()}`}
              </p>
              {job.message && <p className="mt-1 text-slate-600">{job.message}</p>}
            </li>
          )) ?? <li>目前沒有同步紀錄</li>}
        </ul>
      </div>
    </Layout>
  );
}

