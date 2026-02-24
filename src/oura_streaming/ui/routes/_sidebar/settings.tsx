import { Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  useGetAuthStatusSuspense,
  useListSubscriptionsSuspense,
  useLogout,
  useDeleteSubscription,
} from "@/lib/api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

export const Route = createFileRoute("/_sidebar/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">
          Manage authentication and webhook subscriptions.
        </p>
      </div>

      <Separator />

      <Suspense fallback={<AuthSkeleton />}>
        <AuthSection />
      </Suspense>

      <Suspense fallback={<SubscriptionsSkeleton />}>
        <SubscriptionsErrorBoundary>
          <SubscriptionsSection />
        </SubscriptionsErrorBoundary>
      </Suspense>
    </div>
  );
}

// ─── Authentication Section ───────────────────────────────────

function AuthSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-4 w-48" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-4 w-36" />
        <Skeleton className="h-9 w-28" />
      </CardContent>
    </Card>
  );
}

function AuthSection() {
  const { data: authStatus } = useGetAuthStatusSuspense();
  const logout = useLogout();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Authentication</CardTitle>
        <CardDescription>Oura Ring OAuth2 connection status.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Status:</span>
          {authStatus.authenticated ? (
            <Badge variant="default" className="bg-green-600 hover:bg-green-700">
              Authenticated
            </Badge>
          ) : (
            <Badge variant="destructive">Not authenticated</Badge>
          )}
        </div>

        {authStatus.authenticated && authStatus.token_expired !== null && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Token expired:</span>
            {authStatus.token_expired ? (
              <Badge variant="destructive">Yes</Badge>
            ) : (
              <Badge variant="outline">No</Badge>
            )}
          </div>
        )}

        <div className="pt-2">
          {authStatus.authenticated ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
            >
              {logout.isPending ? "Logging out..." : "Logout"}
            </Button>
          ) : (
            <a
              href="/api/auth/login"
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-3"
            >
              Login with Oura
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Subscriptions Section ────────────────────────────────────

function SubscriptionsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-64" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </CardContent>
    </Card>
  );
}

import { Component, type ReactNode, type ErrorInfo } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class SubscriptionsErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("SubscriptionsSection error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card>
          <CardHeader>
            <CardTitle>Webhook Subscriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Authenticate to view subscriptions.
            </p>
          </CardContent>
        </Card>
      );
    }
    return this.props.children;
  }
}

function truncateUrl(url: string, maxLength = 40): string {
  if (url.length <= maxLength) return url;
  return url.slice(0, maxLength) + "...";
}

function SubscriptionsSection() {
  const { data: subscriptions } = useListSubscriptionsSuspense();
  const deleteSub = useDeleteSubscription();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Webhook Subscriptions</CardTitle>
        <CardDescription>
          Active Oura webhook subscriptions. Manage subscriptions via the API or
          CLI.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {subscriptions.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No active subscriptions. Create subscriptions via the API or CLI.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data Type</TableHead>
                <TableHead>Event Type</TableHead>
                <TableHead>Callback URL</TableHead>
                <TableHead>Expiration</TableHead>
                <TableHead className="w-[80px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {subscriptions.map((sub) => (
                <TableRow key={sub.id}>
                  <TableCell className="font-mono text-sm">
                    {sub.data_type ?? "—"}
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {sub.event_type ?? "—"}
                  </TableCell>
                  <TableCell
                    className="text-sm text-muted-foreground"
                    title={sub.callback_url ?? undefined}
                  >
                    {sub.callback_url ? truncateUrl(sub.callback_url) : "—"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {sub.expiration_time
                      ? new Date(sub.expiration_time).toLocaleDateString()
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => deleteSub.mutate(sub.id)}
                      disabled={deleteSub.isPending}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
