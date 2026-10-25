import { ReactNode, HTMLAttributes } from "react";
import clsx from "clsx";

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hover?: boolean;
}

export default function GlassCard({ children, className, hover = true, ...rest }: GlassCardProps) {
  return (
    <div
      className={clsx("glass rounded-2xl p-6", hover && "glass-hover", className)}
      {...rest}
    >
      {children}
    </div>
  );
}
