export const calibrationCurve = [
  { threshold: 10, changePercent: 35.18 },
  { threshold: 15, changePercent: 14.13 },
  { threshold: 20, changePercent: 7.06, isDefault: true },
  { threshold: 25, changePercent: 4.00 },
  { threshold: 30, changePercent: 2.19 }
];

export function interpolateSensitivity(th) {
  if (th <= calibrationCurve[0].threshold) return calibrationCurve[0].changePercent;
  if (th >= calibrationCurve[calibrationCurve.length - 1].threshold) {
    return calibrationCurve[calibrationCurve.length - 1].changePercent;
  }
  for (let i = 0; i < calibrationCurve.length - 1; i++) {
    const p1 = calibrationCurve[i];
    const p2 = calibrationCurve[i + 1];
    if (th >= p1.threshold && th <= p2.threshold) {
      const ratio = (th - p1.threshold) / (p2.threshold - p1.threshold);
      return p1.changePercent + ratio * (p2.changePercent - p1.changePercent);
    }
  }
  return 7.06;
}
