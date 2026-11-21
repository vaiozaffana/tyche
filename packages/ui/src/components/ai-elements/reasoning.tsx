import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@repo/ui/components/collapsible";
import { cn } from "@repo/ui/lib/utils";
import { BrainIcon, ChevronDownIcon } from "lucide-react";
import type { ComponentProps } from "react";

export function Reasoning({
  isStreaming = false,
  ...props
}: ComponentProps<typeof Collapsible> & { isStreaming?: boolean }) {
  return <Collapsible defaultOpen={isStreaming} {...props} />;
}

export function ReasoningTrigger({
  className,
  ...props
}: ComponentProps<typeof CollapsibleTrigger>) {
  return (
    <CollapsibleTrigger
      className={cn(
        "group flex items-center gap-2 font-mono text-xs text-muted-foreground hover:text-foreground",
        className,
      )}
      {...props}
    >
      <BrainIcon className="size-3.5" />
      <span>Reasoning</span>
      <ChevronDownIcon className="size-3.5 transition-transform group-data-[state=open]:rotate-180" />
    </CollapsibleTrigger>
  );
}

export function ReasoningContent({
  className,
  ...props
}: ComponentProps<typeof CollapsibleContent>) {
  return (
    <CollapsibleContent
      className={cn("mt-2 max-w-2xl whitespace-pre-wrap text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}
