import { registerPlugin } from '@capacitor/core';

export interface NotificationAccessStatus {
  accessGranted: boolean;
  connected: boolean;
  preDisplayInterception: false;
}

export interface LocalNotificationEvent {
  id: string;
  packageName: string;
  postedAt: number;
  updatedAt: number;
  removedAt?: number;
  deferredUntil?: number;
  removalReason?: number;
  clearable: boolean;
  state: 'active' | 'removed' | 'deferred';
}

interface AttentionListenerPlugin {
  getStatus(): Promise<NotificationAccessStatus>;
  requestAccess(): Promise<void>;
  getEvents(): Promise<{ events: LocalNotificationEvent[] }>;
  clearHistory(): Promise<void>;
  getBreakSchedule(): Promise<{ times: string }>;
  saveBreakSchedule(options: { times: string }): Promise<void>;
  deferUntilNextBreak(options: { id: string }): Promise<void>;
}

export const attentionListener = registerPlugin<AttentionListenerPlugin>('AttentionListener');
