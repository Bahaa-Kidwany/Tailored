import { apiFetch, apiFetchRaw } from './apiClient';

export interface WalletBalance {
  user_id: string;
  available_credits: number;
  held_credits: number;
  low_balance_threshold: number;
}

export interface ServerLedgerEntry {
  id: string;
  date: string;
  created_at: string;
  action: string;
  job_target: string;
  delta: number;
  balance_after: number;
  doc_id?: string | null;
  order_id?: string | null;
}

export const BillingAPI = {
  async getBalance(): Promise<WalletBalance> {
    return apiFetch('/credits/balance');
  },

  async listPacks(currency: string = 'EGP') {
    return apiFetch<Array<Record<string, unknown>>>(`/credits/packs?currency=${encodeURIComponent(currency)}`, {
      skipAuth: true,
    });
  },

  async getLedger(): Promise<ServerLedgerEntry[]> {
    return apiFetch('/credits/ledger');
  },

  async createCheckout(pack_id: string, currency: string, payment_method: string) {
    return apiFetch<{
      id: string;
      provider: string;
      provider_order_id: string;
      fawry_ref_code?: string | null;
      checkout_url: string;
      status: string;
    }>('/credits/checkout', {
      method: 'POST',
      body: { pack_id, currency, payment_method },
      featureKey: 'billing.checkout.create',
      idempotencyKey: `chk_${pack_id}_${Date.now()}`,
    });
  },

  async downloadInvoicePdf(orderId: string): Promise<Blob> {
    const res = await apiFetchRaw(`/credits/invoices/${orderId}/pdf`);
    if (!res.ok) throw new Error(`Invoice download failed (${res.status})`);
    return res.blob();
  },
};
