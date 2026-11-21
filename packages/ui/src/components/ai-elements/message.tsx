import { cn } from "@repo/ui/lib/utils";
import type { ComponentProps } from "react";

export type MessageRole = "activity" | "assistant" | "system" | "user";

export function Message({
  className,
  from,
  ...props
}: ComponentProps<"article"> & { from: MessageRole }) {
  return (
    <article
      className={cn(
        "group flex w-full flex-col gap-2",
        from === "user" ? "items-end" : "items-start",
        className,
      )}
      data-role={from}
      {...props}
    />
  );
}

export function MessageContent({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "max-w-[90%] text-sm leading-6 group-data-[role=user]:rounded-xl group-data-[role=user]:bg-secondary group-data-[role=user]:px-4 group-data-[role=user]:py-3",
        className,
      )}
      {...props}
    />
  );
}

export function MessageResponse({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("whitespace-pre-wrap text-pretty", className)} {...props} />;
}

export function MessageMeta({ className, ...props }: ComponentProps<"span">) {
  return (
    <span className={cn("font-mono text-[11px] text-muted-foreground", className)} {...props} />
  );
}
