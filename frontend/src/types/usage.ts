export interface UsageStatus {
  tokens_used: number;
  tokens_limit: number;
  requests_used: number;
  requests_limit: number;
  reset_at: string;
}
