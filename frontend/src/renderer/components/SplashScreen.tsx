import React, { useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

interface SplashScreenProps {
  onComplete: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLHeadingElement>(null);

  useGSAP(() => {
    const tl = gsap.timeline({
      onComplete: onComplete
    });

    // 0s - 2s: Text emerges from deep blur and opacity 0
    tl.fromTo(textRef.current, 
      { filter: 'blur(30px)', opacity: 0, scale: 0.9 },
      { filter: 'blur(0px)', opacity: 1, scale: 1, duration: 2, ease: "power2.out" }
    );

    // 2s - 4.5s: Text holds focus and breathes slightly
    tl.to(textRef.current, {
      scale: 1.05,
      duration: 2.5,
      ease: "sine.inOut"
    });

    // 4.5s - 5s: Dissolve smoothly
    tl.to(containerRef.current, {
      opacity: 0,
      duration: 0.5,
      ease: "power2.inOut"
    });

  }, { scope: containerRef });

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 h-screen w-screen z-50 flex items-center justify-center noise-bg bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-secondary/60 via-background/95 to-background pointer-events-none"
    >
      <h1 
        ref={textRef}
        className="font-display font-bold text-[clamp(4rem,8vw,8rem)] tracking-tighter text-foreground"
      >
        OpenAgents
      </h1>
    </div>
  );
};

export default SplashScreen;
