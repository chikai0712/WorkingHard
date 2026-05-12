import { Domain } from "@/lib/api";

type Props = {
  domains: Domain[];
  isLoading?: boolean;
};

export default function DomainTable({ domains, isLoading }: Props) {
  if (isLoading) {
    return <p className="text-sm text-slate-500">載入中...</p>;
  }

  if (!domains.length) {
    return <p className="text-sm text-slate-500">目前沒有資料</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Domain</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Expires</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Auto Renew</th>
            <th className="px-4 py-3 text-left font-medium text-slate-600">Nameservers</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {domains.map((domain) => (
            <tr key={domain.id}>
              <td className="px-4 py-2 font-medium text-slate-900">{domain.name}</td>
              <td className="px-4 py-2 text-slate-600">{domain.status ?? "-"}</td>
              <td className="px-4 py-2 text-slate-600">{domain.expires_at ? new Date(domain.expires_at).toLocaleDateString() : "-"}</td>
              <td className="px-4 py-2 text-slate-600">{domain.auto_renew ? "Yes" : "No"}</td>
              <td className="px-4 py-2 text-slate-500">{domain.nameservers?.join(", ") ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

