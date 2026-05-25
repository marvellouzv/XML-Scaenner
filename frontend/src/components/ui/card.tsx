import { HTMLAttributes, PropsWithChildren } from "react";
import { cn } from "../../lib/utils";

export function Card({ className, children, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("rounded-xl border border-border bg-card/80 backdrop-blur", className)} {...props}>
      {children}
    </div>
  );
}

