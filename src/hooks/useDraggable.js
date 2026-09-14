import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * useDraggable hook
 * Provides smooth pointer / mouse / touch drag percentage handling within a container element.
 */
export function useDraggable({
  initialValue = 50,
  min = 0,
  max = 100,
  orientation = 'horizontal',
  onChange
} = {}) {
  const [value, setValue] = useState(initialValue);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const updateValueFromPointer = useCallback((clientX, clientY) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    let pct;
    
    if (orientation === 'horizontal') {
      const offsetX = clientX - rect.left;
      pct = (offsetX / rect.width) * (max - min) + min;
    } else {
      const offsetY = clientY - rect.top;
      pct = (offsetY / rect.height) * (max - min) + min;
    }

    const clamped = Math.max(min, Math.min(max, pct));
    setValue(clamped);
    if (onChange) onChange(clamped);
  }, [min, max, orientation, onChange]);

  const handlePointerDown = useCallback((e) => {
    if (e.button !== undefined && e.button !== 0) return; // Only left click
    e.preventDefault();
    if (e.stopPropagation) e.stopPropagation();
    setIsDragging(true);
    updateValueFromPointer(e.clientX, e.clientY);
  }, [updateValueFromPointer]);

  const handleTouchStart = useCallback((e) => {
    if (!e.touches[0]) return;
    if (e.stopPropagation) e.stopPropagation();
    setIsDragging(true);
    updateValueFromPointer(e.touches[0].clientX, e.touches[0].clientY);
  }, [updateValueFromPointer]);

  useEffect(() => {
    if (!isDragging) return;

    const handlePointerMove = (e) => {
      e.preventDefault();
      updateValueFromPointer(e.clientX, e.clientY);
    };

    const handleTouchMove = (e) => {
      if (e.touches[0]) {
        updateValueFromPointer(e.touches[0].clientX, e.touches[0].clientY);
      }
    };

    const handlePointerUp = () => {
      setIsDragging(false);
    };

    window.addEventListener('mousemove', handlePointerMove, { passive: false });
    window.addEventListener('mouseup', handlePointerUp);
    window.addEventListener('touchmove', handleTouchMove, { passive: false });
    window.addEventListener('touchend', handlePointerUp);

    return () => {
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handlePointerUp);
    };
  }, [isDragging, updateValueFromPointer]);

  return {
    value,
    setValue,
    isDragging,
    containerRef,
    handlePointerDown,
    handleTouchStart
  };
}
