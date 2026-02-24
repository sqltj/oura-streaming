import { Suspense, useMemo } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useWebSocket } from "@/hooks/use-websocket";
import type { WebSocketEvent } from "@/hooks/use-websocket";
import { StatusIndicator } from "@/components/apx/status-indicator";
import { MetricChart } from "@/components/apx/metric-chart";
import { EventsTable } from "@/components/apx/events-table";
import {
  useGetHealthSuspense,
  useListEventsSuspense,
  type EventOut,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/_sidebar/dashboard")({
  component: DashboardPage,
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Normalize a WebSocket event into the EventOut shape used by the REST API. */
function wsEventToEventOut(ws: WebSocketEvent): EventOut {
  return {
    id: ws.id,
    received_at: ws.received_at,
    data_type: ws.event.data_type,
    event_type: ws.event.event_type,
    user_id: ws.event.user_id,
    timestamp: ws.event.timestamp,
    data: ws.event.data,
  };
}

interface ChartPoint {
  label: string;
  value: number;
}

/** Derive chart-ready arrays from a merged event list. */
function useChartData(events: EventOut[]) {
  return useMemo(() => {
    function extractScores(dataType: string): ChartPoint[] {
      return events
        .filter((e) => e.data_type === dataType && e.data?.score != null)
        .map((e) => ({
          label: e.timestamp
            ? new Date(e.timestamp).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              })
            : new Date(e.received_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              }),
          value: Number(e.data!.score),
        }))
        .reverse();
    }

    return {
      sleep: extractScores("daily_sleep"),
      readiness: extractScores("daily_readiness"),
      activity: extractScores("daily_activity"),
    };
  }, [events]);
}

// ---------------------------------------------------------------------------
// Skeleton Fallbacks
// ---------------------------------------------------------------------------

function StatsCardsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4">
      {[1, 2].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <Skeleton className="h-3 w-20" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-16" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ChartsSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <Skeleton className="h-3 w-24" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[200px] w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-32" />
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stats Cards (suspense-aware)
// ---------------------------------------------------------------------------

function StatsCards() {
  const { data: health } = useGetHealthSuspense({
    refetchInterval: 15_000,
  });

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Total Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <span className="font-mono text-3xl font-light tabular-nums">
            {health.events_stored}
          </span>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Auth Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <span
            className={`inline-flex items-center gap-1.5 text-sm font-medium ${
              health.authenticated
                ? "text-emerald-700"
                : "text-zinc-500"
            }`}
          >
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                health.authenticated ? "bg-emerald-500" : "bg-zinc-400"
              }`}
            />
            {health.authenticated ? "Authenticated" : "Not Connected"}
          </span>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard Content (suspense-aware)
// ---------------------------------------------------------------------------

function DashboardContent({
  liveEvents,
}: {
  liveEvents: WebSocketEvent[];
}) {
  const { data: eventList } = useListEventsSuspense(
    { limit: 50 },
    { refetchInterval: 30_000 },
  );

  // Merge live WebSocket events with fetched events, deduplicating by id.
  const mergedEvents = useMemo(() => {
    const seen = new Set<string>();
    const combined: EventOut[] = [];

    // Live events first (newest)
    for (const ws of liveEvents) {
      const ev = wsEventToEventOut(ws);
      if (!seen.has(ev.id)) {
        seen.add(ev.id);
        combined.push(ev);
      }
    }

    // Then fetched events
    for (const ev of eventList.events) {
      if (!seen.has(ev.id)) {
        seen.add(ev.id);
        combined.push(ev);
      }
    }

    return combined;
  }, [liveEvents, eventList.events]);

  const chartData = useChartData(mergedEvents);
  const recentEvents = mergedEvents.slice(0, 10);

  return (
    <>
      {/* Metric Charts */}
      <section>
        <div className="grid gap-6 md:grid-cols-3">
          <MetricChart
            title="Sleep Score"
            data={chartData.sleep}
            color="#6366f1"
          />
          <MetricChart
            title="Readiness Score"
            data={chartData.readiness}
            color="#10b981"
          />
          <MetricChart
            title="Activity Score"
            data={chartData.activity}
            color="#f97316"
          />
        </div>
      </section>

      {/* Recent Events */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium tracking-wide text-muted-foreground uppercase">
          Recent Events
        </h2>
        <EventsTable events={recentEvents} />
      </section>
    </>
  );
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

function DashboardPage() {
  const { status, events: liveEvents } = useWebSocket("/ws/events");

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-8">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Real-time health metrics from your Oura Ring
          </p>
        </div>
        <StatusIndicator status={status} />
      </header>

      {/* Stats Cards */}
      <Suspense fallback={<StatsCardsSkeleton />}>
        <StatsCards />
      </Suspense>

      {/* Charts + Events Table */}
      <Suspense
        fallback={
          <div className="space-y-8">
            <ChartsSkeleton />
            <TableSkeleton />
          </div>
        }
      >
        <DashboardContent liveEvents={liveEvents} />
      </Suspense>
    </div>
  );
}
