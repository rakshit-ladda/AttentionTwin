export type NavTab = 
  | 'profile' 
  | 'simulator' 
  | 'counterfactual' 
  | 'history';

export type ConnectionState = 'checking' | 'connected' | 'offline' | 'not_configured';

export interface HealthStatus {
  status: ConnectionState;
  service?: string;
  version?: string;
  environment?: string;
  timestamp?: string;
  latencyMs?: number;
  errorMessage?: string;
  baseUrl?: string;
}

