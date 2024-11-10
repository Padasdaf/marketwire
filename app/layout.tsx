import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Marketwire",
  description: "The warren buffet way of investing now at your finger tips research companies and invest in stocks",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    
    <html lang="en">

      {/* Required for pricing table */}
        {" "}
        <body className={inter.className}>
        {children}</body>
    </html>
  );
}
