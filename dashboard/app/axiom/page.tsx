"use client";

import { useEffect } from "react";
import { useAxiomStore } from "@/lib/store/axiom-store";
import AXIOMInterface from "@/components/axiom/AXIOMInterface";

export default function AxiomPage() {
  const { setActiveWorkstation, setActiveView } = useAxiomStore();

  useEffect(() => {
    setActiveWorkstation("axiom");
    setActiveView("workspace");
  }, [setActiveWorkstation, setActiveView]);

  return <AXIOMInterface />;
}