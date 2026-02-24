import type { EventOut } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const dataTypeColors: Record<string, string> = {
  daily_sleep: "bg-indigo-100 text-indigo-800",
  daily_readiness: "bg-emerald-100 text-emerald-800",
  daily_activity: "bg-orange-100 text-orange-800",
  sleep: "bg-violet-100 text-violet-800",
  workout: "bg-rose-100 text-rose-800",
  daily_spo2: "bg-sky-100 text-sky-800",
  daily_stress: "bg-amber-100 text-amber-800",
  session: "bg-teal-100 text-teal-800",
};

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function EventsTable({ events }: { events: EventOut[] }) {
  if (events.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
        No events recorded yet. Events will appear here when received via webhook or polling.
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[180px]">Time</TableHead>
            <TableHead>Data Type</TableHead>
            <TableHead>Event</TableHead>
            <TableHead className="font-mono text-xs">ID</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id}>
              <TableCell className="font-mono text-xs tabular-nums">
                {formatTime(event.received_at)}
              </TableCell>
              <TableCell>
                <Badge
                  className={
                    dataTypeColors[event.data_type] ??
                    "bg-zinc-100 text-zinc-800"
                  }
                >
                  {event.data_type.replace(/_/g, " ")}
                </Badge>
              </TableCell>
              <TableCell className="text-sm">{event.event_type}</TableCell>
              <TableCell className="font-mono text-xs text-muted-foreground">
                {event.id.slice(0, 8)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
