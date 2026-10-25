import { registerPlugin } from '@capacitor/core';

export interface NotificationAccessStatus {
  accessGranted: boolean;
  connected: boolean;
  preDisplayInterception: false;
}

export interface LocalNotificationEvent {
  id: string;
  packageName: string;
  appLabel?: string;
  postedAt: number;
  updatedAt: number;
  removedAt?: number;
  deferredUntil?: number;
  removalReason?: number;
  deferOrigin?: 'user' | 'automatic';
  transitions?: Array<{ state: string; at: number; reason?: number; deferOrigin?: 'user' | 'automatic' }>;
  clearable: boolean;
  state: 'active' | 'removed' | 'deferred';
}

export interface AutomationSettings {
  enabled: boolean;
  focusWindows: string;
  packages: string;
}

interface AttentionListenerPlugin {
  getStatus(): Promise<NotificationAccessStatus>;
  requestAccess(): Promise<void>;
  getEvents(): Promise<{ events: LocalNotificationEvent[] }>;
  clearHistory(): Promise<void>;
  getBreakSchedule(): Promise<{ times: string }>;
  saveBreakSchedule(options: { times: string }): Promise<void>;
  getAutomationSettings(): Promise<AutomationSettings>;
  saveAutomationSettings(options: AutomationSettings): Promise<void>;
  deferUntilNextBreak(options: { id: string }): Promise<void>;
}

export const attentionListener = registerPlugin<AttentionListenerPlugin>('AttentionListener');
