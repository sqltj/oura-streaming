import { Suspense, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  useListEventsSuspense,
  useClearEvents,
  type EventOut,
} from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EventsTable } from "@/components/apx/events-table";
import { useWebSocket } from "@/hooks/use-websocket";
import { StatusIndicator } from "@/components/apx/status-indicator";

const DATA_TYPE_FILTERS = [
  "daily_sleep",
  "daily_readiness",
  "daily_activity",
  "sleep",
  "workout",
  "daily_spo2",
] as const;

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 8 }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}

function EventsContent() {
  const [activeFilter, setActiveFilter] = useState<string | undefined>(
    undefined,
  );
  const { data } = useListEventsSuspense({
    limit: 200,
    data_type: activeFilter,
  });
  const clearEvents = useClearEvents();
  const { status, events: wsEvents } = useWebSocket("/ws/events");

  const mergedEvents = useMemo(() => {
    const liveEvents: EventOut[] = wsEvents
      .filter((ws) => !activeFilter || ws.event.data_type === activeFilter)
      .map((ws) => ({
        id: ws.id,
        received_at: ws.received_at,
        data_type: ws.event.data_type,
        event_type: ws.event.event_type,
        user_id: ws.event.user_id,
        timestamp: ws.event.timestamp,
        data: ws.event.data,
      }));

    const existingIds = new Set(data.events.map((e) => e.id));
    const uniqueLive = liveEvents.filter((e) => !existingIds.has(e.id));
    return [...uniqueLive, ...data.events];
  }, [wsEvents, data.events, activeFilter]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight">Events</h2>
          <Badge variant="secondary">{mergedEvents.length} total</Badge>
        </div>
        <div className="flex items-center gap-4">
          <StatusIndicator status={status} />
          <Button
            variant="destructive"
            size="sm"
            onClick={() => clearEvents.mutate()}
            disabled={clearEvents.isPending || mergedEvents.length === 0}
          >
            {clearEvents.isPending ? "Clearing..." : "Clear All"}
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge
          variant={activeFilter === undefined ? "default" : "outline"}
          className="cursor-pointer select-none"
          onClick={() => setActiveFilter(undefined)}
        >
          All
        </Badge>
        {DATA_TYPE_FILTERS.map((type) => (
          <Badge
            key={type}
            variant={activeFilter === type ? "default" : "outline"}
            className="cursor-pointer select-none"
            onClick={() =>
              setActiveFilter(activeFilter === type ? undefined : type)
            }
          >
            {type.replace(/_/g, " ")}
          </Badge>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {activeFilter
              ? `${activeFilter.replace(/_/g, " ")} events`
              : "All events"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EventsTable events={mergedEvents} />
        </CardContent>
      </Card>
    </div>
  );
}

function EventsPage() {
  return (
    <Suspense fallback={<TableSkeletonFallback />}>
      <EventsContent />
    </Suspense>
  );
}

function TableSkeletonFallback() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>
      <div className="flex gap-2">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} className="h-6 w-20 rounded-full" />
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <TableSkeleton />
        </CardContent>
      </Card>
    </div>
  );
}

export const Route = createFileRoute("/_sidebar/events")({
  component: EventsPage,
});
