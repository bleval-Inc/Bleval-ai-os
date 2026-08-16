"use client";

import { useEffect } from "react";
import { useAxiomStore } from "@/lib/store/axiom-store";
import WorkstationRouter from "@/components/workspace/WorkstationRouter";

export default function SettingsPage() {
  const { setActiveWorkstation, setActiveView } = useAxiomStore();

  useEffect(() => {
    setActiveWorkstation("settings");
    setActiveView("settings");
  }, [setActiveWorkstation, setActiveView]);

  return <WorkstationRouter />;
}