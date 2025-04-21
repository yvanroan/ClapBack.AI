'use client';

import { useEffect, useState } from 'react';
import { motion } from '@/lib/motion';

const emojis = ['😎', '🔥', '💯', '👀', '💬', '👋', '😂', '🥰', '🙌', '✨', '🤔', '🫡', '🤩'];

export function FloatingEmojis() {
  const [particles, setParticles] = useState<{ id: number; emoji: string; x: number; y: number; scale: number; rotate: number; duration: number }[]>([]);

  useEffect(() => {
    // Generate initial particles
    const newParticles = Array.from({ length: 15 }, (_, i) => ({
      id: i,
      emoji: emojis[Math.floor(Math.random() * emojis.length)],
      x: Math.random() * 100,
      y: Math.random() * 100,
      scale: 0.5 + Math.random() * 1.5,
      rotate: Math.random() * 360,
      duration: 15 + Math.random() * 30
    }));
    
    setParticles(newParticles);
    
    // Update particles periodically
    const interval = setInterval(() => {
      setParticles(current => {
        const updated = [...current];
        const randomIndex = Math.floor(Math.random() * updated.length);
        
        updated[randomIndex] = {
          ...updated[randomIndex],
          emoji: emojis[Math.floor(Math.random() * emojis.length)],
          x: Math.random() * 100,
          y: Math.random() * 100,
          rotate: Math.random() * 360
        };
        
        return updated;
      });
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute text-4xl blur-[0.5px] opacity-20 select-none"
          initial={{ 
            x: `${particle.x}vw`, 
            y: `${particle.y}vh`, 
            scale: particle.scale,
            rotate: 0
          }}
          animate={{ 
            x: `${(particle.x + 20) % 100}vw`, 
            y: `${(particle.y + 20) % 100}vh`,
            rotate: particle.rotate
          }}
          transition={{ 
            duration: particle.duration, 
            ease: "linear", 
            repeat: Infinity,
            repeatType: "reverse"
          }}
        >
          {particle.emoji}
        </motion.div>
      ))}
    </div>
  );
}