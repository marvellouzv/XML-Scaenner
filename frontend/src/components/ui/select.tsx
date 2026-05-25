import * as SelectPrimitive from "@radix-ui/react-select";
import { ChevronDown } from "lucide-react";
import { PropsWithChildren } from "react";

export function Select({
  value,
  onValueChange,
  children
}: PropsWithChildren<{ value: string; onValueChange: (value: string) => void }>) {
  return (
    <SelectPrimitive.Root value={value} onValueChange={onValueChange}>
      {children}
    </SelectPrimitive.Root>
  );
}

export function SelectTrigger({ children }: PropsWithChildren) {
  return (
    <SelectPrimitive.Trigger className="inline-flex h-10 items-center justify-between rounded-md border border-border bg-card px-3 text-sm text-foreground">
      {children}
      <ChevronDown className="ml-2 h-4 w-4" />
    </SelectPrimitive.Trigger>
  );
}

export function SelectValue({ placeholder }: { placeholder: string }) {
  return <SelectPrimitive.Value placeholder={placeholder} />;
}

export function SelectContent({ children }: PropsWithChildren) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content className="overflow-hidden rounded-md border border-border bg-card text-foreground shadow-lg">
        <SelectPrimitive.Viewport>{children}</SelectPrimitive.Viewport>
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

export function SelectItem({ value, children }: PropsWithChildren<{ value: string }>) {
  return (
    <SelectPrimitive.Item value={value} className="cursor-pointer px-3 py-2 text-sm hover:bg-muted">
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}

