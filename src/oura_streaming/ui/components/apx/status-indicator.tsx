import type { ConnectionStatus } from "@/hooks/use-websocket";

const statusConfig: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: "bg-emerald-500", label: "Live" },
  connecting: { color: "bg-amber-500", label: "Connecting" },
  disconnected: { color: "bg-zinc-400", label: "Offline" },
};

export function StatusIndicator({ status }: { status: ConnectionStatus }) {
  const { color, label } = statusConfig[status];
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {status === "connected" && (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full ${color} opacity-75`}
          />
        )}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${color}`} />
      </span>
      <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
        {label}
      </span>
    </div>
  );
}
