import { Button } from "@repo/ui/components/button";
import { Textarea } from "@repo/ui/components/textarea";
import { cn } from "@repo/ui/lib/utils";
import { ArrowUpIcon, SquareIcon } from "lucide-react";
import type { ComponentProps, FormEvent } from "react";

export function PromptInput({ className, ...props }: ComponentProps<"form">) {
  return (
    <form
      className={cn(
        "grid gap-3 border border-foreground bg-background p-3 shadow-[4px_4px_0_#111111]",
        className,
      )}
      {...props}
    />
  );
}

export function PromptInputTextarea({ className, ...props }: ComponentProps<typeof Textarea>) {
  return (
    <Textarea
      className={cn(
        "min-h-24 resize-none border-0 bg-transparent px-1 py-1 text-base shadow-none focus-visible:ring-0",
        className,
      )}
      {...props}
    />
  );
}

export function PromptInputFooter({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("flex items-center justify-between gap-3", className)} {...props} />;
}

export function PromptInputHint({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("font-mono text-[10px] text-muted-foreground", className)} {...props} />;
}

export function PromptInputSubmit({
  isStreaming = false,
  onStop,
  ...props
}: ComponentProps<typeof Button> & { isStreaming?: boolean; onStop?: () => void }) {
  return (
    <Button
      aria-label={isStreaming ? "Stop agent" : "Send message"}
      onClick={isStreaming ? onStop : undefined}
      size="icon"
      type={isStreaming ? "button" : "submit"}
      {...props}
    >
      {isStreaming ? (
        <SquareIcon className="size-3.5 fill-current" />
      ) : (
        <ArrowUpIcon className="size-4" />
      )}
    </Button>
  );
}

export function submitPrompt(
  event: FormEvent<HTMLFormElement>,
  value: string,
  send: (prompt: string) => void,
) {
  event.preventDefault();
  const prompt = value.trim();
  if (prompt) send(prompt);
}
