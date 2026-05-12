import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api"
});

export type Account = {
  id: number;
  provider_slug: string;
  provider_name?: string;
  label: string;
  created_at?: string;
};

export type Domain = {
  id: number;
  account_id: number;
  name: string;
  status?: string | null;
  expires_at?: string | null;
  auto_renew: boolean;
  nameservers?: string[] | null;
  last_synced_at?: string | null;
};

export type SyncJob = {
  id: number;
  account_id: number;
  provider_slug: string;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  message?: string | null;
};

export async function fetchAccounts() {
  const { data } = await api.get<Account[]>("/accounts");
  return data;
}

export async function createAccount(payload: {
  provider_slug: string;
  label: string;
  api_key: string;
  api_secret?: string;
  extra_config?: Record<string, unknown>;
}) {
  const { data } = await api.post<Account>("/accounts", payload);
  return data;
}

export async function testAccount(accountId: number) {
  const { data } = await api.post<{ success: boolean }>(`/accounts/${accountId}/test`);
  return data;
}

export async function fetchDomains(params?: { accountId?: number; search?: string }) {
  const { data } = await api.get<{ total: number; items: Domain[] }>("/domains", {
    params: {
      account_id: params?.accountId,
      search: params?.search
    }
  });
  return data;
}

export async function syncDomains(accountId: number) {
  const { data } = await api.post("/domains/sync", { account_id: accountId });
  return data;
}

export async function fetchSyncJobs() {
  const { data } = await api.get<{ items: SyncJob[] }>("/sync-jobs");
  return data;
}

