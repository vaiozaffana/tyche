import { Button } from "@repo/ui/components/button";
import { cn } from "@repo/ui/lib/utils";
import { ArrowDownIcon } from "lucide-react";
import type { ComponentProps } from "react";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";

export const Conversation = ({ className, ...props }: ComponentProps<typeof StickToBottom>) => (
  <StickToBottom
    className={cn("relative min-h-0 flex-1 overflow-y-hidden", className)}
    initial="instant"
    resize="smooth"
    role="log"
    {...props}
  />
);

export const ConversationContent = ({
  className,
  ...props
}: ComponentProps<typeof StickToBottom.Content>) => (
  <StickToBottom.Content className={cn("flex flex-col gap-5 p-4", className)} {...props} />
);

export function ConversationEmptyState({
  className,
  description,
  title,
  ...props
}: ComponentProps<"div"> & { description: string; title: string }) {
  return (
    <div
      className={cn("grid min-h-64 place-content-center gap-2 text-center", className)}
      {...props}
    >
      <p className="font-display text-2xl font-semibold tracking-tight">{title}</p>
      <p className="max-w-sm text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}

export function ConversationScrollButton(props: ComponentProps<typeof Button>) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();
  if (isAtBottom) return null;
  return (
    <Button
      aria-label="Scroll to latest message"
      className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full"
      onClick={() => scrollToBottom()}
      size="icon"
      type="button"
      variant="outline"
      {...props}
    >
      <ArrowDownIcon className="size-4" />
    </Button>
  );
}
