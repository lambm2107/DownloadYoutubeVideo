/**
 * Desktop SPA entry point — dùng cho Electron build.
 * Khác với SSR entry (src/start.ts), file này mount React trực tiếp vào DOM.
 * Dùng TanStack Router (hash-based) để hoạt động với file:// protocol.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { getRouter } from "./router.desktop";
import "./styles.css";

const { router, queryClient: routerQueryClient } = getRouter();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={routerQueryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
);
