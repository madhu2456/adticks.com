import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageErrorBoundary } from "@/components/PageErrorBoundary";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <PageErrorBoundary>
      <DashboardLayout>{children}</DashboardLayout>
    </PageErrorBoundary>
  );
}
