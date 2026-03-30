import React, { useState } from 'react';
import { LogIn, ShieldCheck, Globe } from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-hot-toast';

interface AuthPopupProps {
  onAuthenticated: () => void;
}

const BASE_URL = 'http://localhost:8000';

const AuthPopup: React.FC<AuthPopupProps> = ({ onAuthenticated }) => {
  const [loading, setLoading] = useState(false);

  const handleSignIn = async () => {
    setLoading(true);
    const toastId = toast.loading('Opening browser for Google Sign-In...');
    try {
      await axios.post(`${BASE_URL}/auth/login`);
      
      // Poll for authentication status
      const pollAuth = setInterval(async () => {
        try {
          const response = await axios.get(`${BASE_URL}/auth/status`);
          if (response.data.authenticated) {
            clearInterval(pollAuth);
            toast.success('Successfully authenticated!', { id: toastId });
            onAuthenticated();
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 2000);

      // Timeout after 2 minutes
      setTimeout(() => {
        clearInterval(pollAuth);
        if (loading) {
          setLoading(false);
          toast.error('Authentication timed out. Please try again.', { id: toastId });
        }
      }, 120000);

    } catch (error) {
      console.error('Sign-in error:', error);
      toast.error('Failed to start sign-in flow', { id: toastId });
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl overflow-hidden animate-scale-in">
        <div className="relative h-32 bg-gradient-to-br from-primary/20 via-primary/10 to-transparent flex items-center justify-center">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(var(--primary),0.1),transparent)]" />
          <div className="w-16 h-16 bg-background rounded-2xl shadow-lg border border-primary/20 flex items-center justify-center z-10 animate-bounce-subtle">
            <ShieldCheck className="text-primary" size={32} />
          </div>
        </div>
        
        <div className="p-8 text-center space-y-6">
          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">Authentication Required</h1>
            <p className="text-muted-foreground text-sm">
              Please sign in with your Google account to access OpenAgents. 
              This ensures your data and sessions are securely managed.
            </p>
          </div>

          <button
            onClick={handleSignIn}
            disabled={loading}
            className="w-full group relative flex items-center justify-center gap-3 px-6 py-3.5 bg-primary text-primary-foreground rounded-xl font-medium transition-all hover:ring-4 hover:ring-primary/20 active:scale-[0.98] disabled:opacity-70 disabled:pointer-events-none"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                <span>Waiting for authorization...</span>
              </div>
            ) : (
              <>
                <LogIn size={20} className="transition-transform group-hover:translate-x-1" />
                <span>Sign in with Google</span>
              </>
            )}
          </button>

          <div className="pt-4 flex items-center justify-center gap-6 border-t border-border/50">
             <div className="flex flex-col items-center gap-1 text-[10px] text-muted-foreground uppercase tracking-widest">
                <Globe size={14} className="mb-1" />
                <span>Secure</span>
             </div>
             <div className="flex flex-col items-center gap-1 text-[10px] text-muted-foreground uppercase tracking-widest">
                <ShieldCheck size={14} className="mb-1" />
                <span>Privacy</span>
             </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes bounceSubtle {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
        .animate-scale-in { animation: scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        .animate-bounce-subtle { animation: bounceSubtle 3s ease-in-out infinite; }
      `}</style>
    </div>
  );
};

export default AuthPopup;
