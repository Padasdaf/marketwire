import { Bell, Command, Menu, Search } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Image from "next/image";
import { createClient } from "@/utils/supabase/server";
import DashboardHeaderProfileDropdown from "./DashboardHeaderProfileDropdown";
import { Badge } from "@/components/ui/badge";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { SidebarTrigger } from "./ui/sidebar";
import { StockSearch } from "./StockSearch";
import {
  CommandGroup,
  CommandShortcut,
  CommandItem,
  CommandInput,
  CommandList,
  CommandSeparator,
  CommandEmpty,
} from "./ui/command";

export default async function DashboardHeader() {
  const supabase = createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();
  // Get the user's plan from Stripe
  // const stripePlan = getStripePlan(user!.email!)

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <SidebarTrigger className="mr-2" />

        <div className="mr-4 hidden md:flex">
          {/* <Link className="mr-2 flex items-center space-x-2" href="">
                        <Image src="/logo.png" alt="logo" width={25} height={25} />
                    </Link> */}
          <Suspense
            fallback={
              <Badge variant="outline" className="mr-2">
                <Skeleton className="w-[50px] h-[20px] rounded-full" />
              </Badge>
            }
          >
            {/* <Badge variant="outline" className="mr-2">{stripePlan}</Badge> */}
          </Suspense>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link
              className="transition-colors hover:text-foreground/80 text-foreground"
              href="/dashboard"
            >
              Home
            </Link>
            {/* <Link
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="#"
            >
              Projects
            </Link>
            <Link
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="#"
            >
              Tasks
            </Link>
            <Link
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="#"
            >
              Reports
            </Link> */}
          </nav>
        </div>
        <Button variant="outline" size="icon" className="mr-2 md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle Menu</span>
        </Button>

        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            <StockSearch />
          </div>
          <DashboardHeaderProfileDropdown />
        </div>
      </div>
    </header>
  );
}
