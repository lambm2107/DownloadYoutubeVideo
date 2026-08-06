/**
 * Router dành riêng cho desktop (Electron).
 * Dùng memory history để hoạt động với file:// protocol.
 */
import { QueryClient } from "@tanstack/react-query";
import { createRouter, createMemoryHistory } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

export const getRouter = () => {
  const queryClient = new QueryClient();
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: ["/"] }),
    context: { queryClient },
    defaultPreloadStaleTime: 0,
  });
  return { router, queryClient };
};
