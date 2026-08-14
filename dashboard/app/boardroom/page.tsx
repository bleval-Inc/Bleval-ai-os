"use client";

import { useEffect } from "react";
import { useAxiomStore } from "@/lib/store/axiom-store";
import WorkstationRouter from "@/components/workspace/WorkstationRouter";

export default function BoardroomPage() {
  const { setActiveWorkstation, setActiveView } = useAxiomStore();

  useEffect(() => {
    setActiveWorkstation("boardroom");
    setActiveView("boardroom");
  }, [setActiveWorkstation, setActiveView]);

  return <WorkstationRouter />;
}