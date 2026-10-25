export type NavTab = 
  | 'profile' 
  | 'simulator' 
  | 'counterfactual' 
  | 'history';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'loading' | 'error';
  service?: string;
  version?: string;
  environment?: string;
  timestamp?: string;
  latencyMs?: number;
  errorMessage?: string;
}
