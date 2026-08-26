"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// SETTINGS was consolidated into the SYSTEM workstation. Keep the old
// /settings URL as an alias so bookmarked links land on the unified AXIOM
// control centre instead of 404ing or reaching a removed route.
export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/system");
  }, [router]);

  return null;
}