import { useEffect, useRef } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";

interface Props {
  value: number;
  duration?: number;
  className?: string;
}

/** شمارندهٔ انیمیشنی نرم — برای KPIها (میکرو-ترنزیشن). */
export function AnimatedCounter({ value, duration = 1.1, className }: Props) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v).toLocaleString("fa-IR"));
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const controls = animate(count, value, { duration, ease: "easeOut" });
    return () => controls.stop();
  }, [value, duration, count]);

  return (
    <motion.span ref={ref} className={className} dir="ltr">
      {rounded}
    </motion.span>
  );
}
