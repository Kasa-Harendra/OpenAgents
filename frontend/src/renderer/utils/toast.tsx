import React, { useState, useEffect } from 'react';
import SwipeToast from '../components/SwipeToast/SwipeToast';
import { CheckmarkCircle01Icon, Alert01Icon, InformationCircleIcon, Loading01Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

type ToastType = 'success' | 'error' | 'info' | 'loading' | 'default';

interface ToastItem {
  id: string;
  message: React.ReactNode;
  type: ToastType;
  options?: any;
}

class ToastManager {
  private toasts: ToastItem[] = [];
  private listeners: Set<(toasts: ToastItem[]) => void> = new Set();

  subscribe(listener: (toasts: ToastItem[]) => void) {
    this.listeners.add(listener);
    return () => { this.listeners.delete(listener); };
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.toasts]));
  }

  show(message: React.ReactNode, type: ToastType = 'default', options?: any) {
    const id = options?.id || Date.now().toString() + Math.random().toString();
    const existingIndex = this.toasts.findIndex(t => t.id === id);
    
    const newToast = { id, message, type, options };
    
    if (existingIndex >= 0) {
      this.toasts[existingIndex] = newToast;
    } else {
      this.toasts.push(newToast);
    }
    
    this.notify();
    return id;
  }

  remove(id: string) {
    this.toasts = this.toasts.filter(t => t.id !== id);
    this.notify();
  }
}

export const toastManager = new ToastManager();

export const toast = Object.assign(
  (message: React.ReactNode, options?: any) => toastManager.show(message, 'default', options),
  {
    success: (message: React.ReactNode, options?: any) => toastManager.show(message, 'success', options),
    error: (message: React.ReactNode, options?: any) => toastManager.show(message, 'error', options),
    info: (message: React.ReactNode, options?: any) => toastManager.show(message, 'info', options),
    loading: (message: React.ReactNode, options?: any) => toastManager.show(message, 'loading', options),
    dismiss: (id: string) => toastManager.remove(id),
  }
);

export function SwipeToastProvider() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    return toastManager.subscribe(setToasts);
  }, []);

  return (
    <div style={{ position: 'fixed', bottom: 20, right: 20, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10, zIndex: 9999 }}>
      {toasts.map(t => {
        let icon = undefined;
        let fuseColor = '#f5a524';
        
        if (t.type === 'success') {
          icon = <HugeiconsIcon icon={CheckmarkCircle01Icon} size={18} color="#10b981" />;
          fuseColor = '#10b981';
        } else if (t.type === 'error') {
          icon = <HugeiconsIcon icon={Alert01Icon} size={18} color="#ef4444" />;
          fuseColor = '#ef4444';
        } else if (t.type === 'info') {
          icon = <HugeiconsIcon icon={InformationCircleIcon} size={18} color="#3b82f6" />;
          fuseColor = '#3b82f6';
        } else if (t.type === 'loading') {
          icon = <HugeiconsIcon icon={Loading01Icon} size={18} color="#3b82f6" className="animate-spin" />;
          fuseColor = '#3b82f6';
        }

        return (
          <SwipeToast
            key={t.id}
            inline
            title={t.message as any}
            icon={icon}
            fuseColor={fuseColor}
            duration={t.type === 'loading' ? 0 : (t.options?.duration || 4000)}
            onClose={() => toastManager.remove(t.id)}
            onAction={() => {}}
          />
        );
      })}
    </div>
  );
}

export default toast;
