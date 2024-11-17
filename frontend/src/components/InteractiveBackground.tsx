'use client';

import React, { useState, useEffect } from 'react';

interface BackgroundElement {
  id: number;
  x: string;
  y: string;
  size: number;
  animationDelay: string;
}

const InteractiveBackground = () => {
  const [elements, setElements] = useState<BackgroundElement[]>([]);
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  useEffect(() => {
    const generatedElements = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: `${Math.random() * 100}%`,
      y: `${Math.random() * 100}%`,
      size: Math.random() * (80 - 20) + 20,
      animationDelay: `${Math.random() * -8}s`,
    }));
    setElements(generatedElements);
  }, []);

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-800 overflow-hidden">
      {elements.map((element) => (
        <div
          key={element.id}
          className="absolute transition-all duration-700 ease-in-out"
          style={{
            left: element.x,
            top: element.y,
            animationDelay: element.animationDelay,
          }}
          onMouseEnter={() => setHoveredId(element.id)}
          onMouseLeave={() => setHoveredId(null)}
        >
          <div
            className={`
                backdrop-blur-sm rounded-full transition-all duration-1000
                animate-float animate-pulse-soft
                ${hoveredId === element.id 
                ? 'bg-purple-400/20 scale-125 animate-rotate-slow' 
                : 'bg-purple-300/10'
                }
            `}
            style={{
              width: element.size,
              height: element.size,
              animationDelay: element.animationDelay,
            }}
          />
        </div>
      ))}
    </div>
  );
};

export default InteractiveBackground;