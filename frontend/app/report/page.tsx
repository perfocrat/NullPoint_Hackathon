import type { Metadata } from "next";
import { ReportPage } from "@/components/report-page";

export const metadata: Metadata = {
  title: "Your career report",
};

export default function ReportRoute() {
  return <ReportPage />;
}
