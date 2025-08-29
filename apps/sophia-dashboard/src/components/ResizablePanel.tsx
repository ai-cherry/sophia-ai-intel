'use client';

import { useState, useRef, useEffect, ReactNode } from 'react';
import { motion } from 'framer-motion';

interface ResizablePanelProps {
  children: ReactNode;
  defaultWidth?: number;
  minWidth?: number;
  maxWidth?: number;
  side?: 'left' | 'right';
  onResize?: (width: number) => void;
}

export default function ResizablePanel({
  children,
  defaultWidth = 400,
  minWidth = 300,
  maxWidth = 600,
  side = 'right',
  onResize
}: ResizablePanelProps) {
  const [width, setWidth] = useState(defaultWidth);
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    startX.current = e.clientX;
    startWidth.current = width;
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const diff = side === 'right' 
        ? startX.current - e.clientX
        : e.clientX - startX.current;
      
      const newWidth = Math.max(
        minWidth,
        Math.min(maxWidth, startWidth.current + diff)
      );
      
      setWidth(newWidth);
      onResize?.(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, side, minWidth, maxWidth, onResize]);

  return (
    <motion.div
      ref={panelRef}
      animate={{ width }}
      transition={{ duration: isResizing ? 0 : 0.2 }}
      className="relative flex flex-col h-full bg-gray-900/50 backdrop-blur-sm border-l border-white/10"
      style={{ width }}
    >
      {/* Resize Handle */}
      <div
        onMouseDown={handleMouseDown}
        className={`
          absolute top-0 bottom-0 w-1 cursor-col-resize z-10
          hover:w-2 transition-all duration-200
          ${side === 'right' ? 'left-0' : 'right-0'}
          ${isResizing 
            ? 'bg-cyan-500/50' 
            : 'hover:bg-cyan-500/30'
          }
        `}
      >
        <div className="absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-4" />
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </motion.div>
  );
}