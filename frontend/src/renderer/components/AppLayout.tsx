import React from 'react';
import Sidebar from '@/components/Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground uppercase-none">
      <Sidebar />
      <main className="relative flex-1 flex flex-col min-w-0 overflow-hidden">
        {children}
      </main>
    </div>
  );
};

export default AppLayout;
