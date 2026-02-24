import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { LayoutDashboard, List, Settings } from "lucide-react";

const navItems = [
  {
    to: "/",
    label: "Dashboard",
    icon: <LayoutDashboard size={16} />,
    match: (path: string) => path === "/",
  },
  {
    to: "/events",
    label: "Events",
    icon: <List size={16} />,
    match: (path: string) => path.startsWith("/events"),
  },
  {
    to: "/settings",
    label: "Settings",
    icon: <Settings size={16} />,
    match: (path: string) => path.startsWith("/settings"),
  },
] as const;

export default function SidebarRoute() {
  const router = useRouterState();
  const currentPath = router.location.pathname;

  return (
    <div className="flex min-h-screen w-full">
      <aside className="w-56 border-r border-sidebar-border bg-sidebar-background p-4 flex flex-col gap-1">
        <div className="px-2 py-3 mb-4">
          <h1 className="text-lg font-semibold tracking-tight">Oura Streaming</h1>
          <p className="text-xs text-muted-foreground">Health metrics dashboard</p>
        </div>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                item.match(currentPath)
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              }`}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
