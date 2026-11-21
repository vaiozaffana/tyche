import { Badge } from "@repo/ui/components/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@repo/ui/components/collapsible";
import { cn } from "@repo/ui/lib/utils";
import { CheckIcon, ChevronDownIcon, ClockIcon, WrenchIcon, XIcon } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";

export type ToolStatus =
  | "approval-requested"
  | "approval-responded"
  | "awaiting-input"
  | "complete"
  | "error"
  | "input-complete"
  | "input-streaming";

const labels: Record<ToolStatus, string> = {
  "approval-requested": "Approval needed",
  "approval-responded": "Approval recorded",
  "awaiting-input": "Preparing",
  complete: "Complete",
  error: "Failed",
  "input-complete": "Running",
  "input-streaming": "Preparing",
};

export function Tool({ className, ...props }: ComponentProps<typeof Collapsible>) {
  return (
    <Collapsible
      className={cn("group w-full border-l-2 border-primary bg-secondary/40", className)}
      {...props}
    />
  );
}

export function ToolHeader({
  className,
  name,
  status,
  ...props
}: ComponentProps<typeof CollapsibleTrigger> & { name: string; status: ToolStatus }) {
  const Icon = status === "complete" ? CheckIcon : status === "error" ? XIcon : ClockIcon;
  return (
    <CollapsibleTrigger
      className={cn("flex w-full items-center gap-3 px-4 py-3 text-left", className)}
      {...props}
    >
      <WrenchIcon className="size-4 text-primary" />
      <span className="min-w-0 flex-1 truncate font-mono text-xs">{name}</span>
      <Badge className="gap-1 rounded-sm font-mono text-[10px]" variant="outline">
        <Icon className="size-3" />
        {labels[status]}
      </Badge>
      <ChevronDownIcon className="size-4 transition-transform group-data-[state=open]:rotate-180" />
    </CollapsibleTrigger>
  );
}

export function ToolContent({ className, ...props }: ComponentProps<typeof CollapsibleContent>) {
  return <CollapsibleContent className={cn("px-4 pb-4", className)} {...props} />;
}

export function ToolSection({ children, label }: { children: ReactNode; label: string }) {
  return (
    <div className="grid gap-1.5 border-t pt-3">
      <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <div className="text-sm">{children}</div>
    </div>
  );
}
