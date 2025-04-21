'use client';

import { useEffect, useState } from 'react';

interface TypeAnimationProps {
  text: string;
  delay?: number;
  speed?: number;
}

export function TypeAnimation({ text, delay = 0, speed = 50 }: TypeAnimationProps) {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let timeout: NodeJS.Timeout;
    
    // Initial delay
    if (currentIndex === 0) {
      timeout = setTimeout(() => {
        setCurrentIndex(1);
      }, delay);
      return () => clearTimeout(timeout);
    }
    
    // Type each character
    if (currentIndex <= text.length) {
      timeout = setTimeout(() => {
        setDisplayText(text.substring(0, currentIndex));
        setCurrentIndex(prevIndex => prevIndex + 1);
        
        if (currentIndex === text.length) {
          setIsComplete(true);
        }
      }, speed);
      
      return () => clearTimeout(timeout);
    }
    
    return undefined;
  }, [currentIndex, delay, speed, text]);

  return (
    <span>
      {displayText}
      {!isComplete && <span className="animate-pulse">|</span>}
    </span>
  );
}