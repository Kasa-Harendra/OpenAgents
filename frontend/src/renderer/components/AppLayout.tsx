import React, { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import SplashScreen from '@/components/SplashScreen';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [showSplash, setShowSplash] = useState(true);

  if (showSplash) {
    return <SplashScreen onComplete={() => setShowSplash(false)} />;
  }

  return (
    <div className="noise-bg flex h-screen w-screen overflow-hidden bg-background text-foreground uppercase-none">
      <Sidebar />
      <main className="relative flex-1 flex flex-col min-w-0 overflow-hidden">
        {children}
      </main>
    </div>
  );
};

export default AppLayout;
