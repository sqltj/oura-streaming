import { createFileRoute } from "@tanstack/react-router";
import SidebarRoute from "./_sidebar/-layout";

export const Route = createFileRoute("/_sidebar")({
  component: SidebarRoute,
});
