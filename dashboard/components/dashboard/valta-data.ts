// HOUSE OF VALTA demo data — isolated placeholder trading values.
// Replace these with live workstation/trading data in a later step.
// No MT5, broker, TradingView, or market-feed connections are involved.

export interface ValtaPoint {
  label: string;
  value: number;
}

export interface ValtaKPI {
  key: string;
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down";
  series: number[];
}

export interface Trade {
  id: string;
  instrument: "GOLD" | "US30";
  lot: string;
  pnl: number;
  time: string;
}

export interface ValtaData {
  identity: string;
  kpis: ValtaKPI[];
  equity: ValtaPoint[];
  equityStart: string;
  equityEnd: string;
  equityDelta: string;
  trades: Trade[];
  closedTotal: number;
}

export const valtaData: ValtaData = {
  identity: "GOLD",
  kpis: [
    {
      key: "total-profit",
      label: "Total Profit",
      value: "+$8,420",
      delta: "+68.4%",
      trend: "up",
      series: [5000, 5240, 5180, 5620, 6100, 6420, 7050, 7480, 8420],
    },
    {
      key: "pnl",
      label: "PNL",
      value: "+$1,240",
      delta: "+12.4%",
      trend: "up",
      series: [220, 310, -140, 480, 95, 540, -60, 690, 1240],
    },
    {
      key: "profit-factor",
      label: "Profit Factor",
      value: "2.18",
      delta: "+0.31",
      trend: "up",
      series: [1.2, 1.4, 1.3, 1.6, 1.8, 1.7, 2.0, 2.1, 2.18],
    },
    {
      key: "win-rate",
      label: "Win Rate",
      value: "68.4%",
      delta: "+4.2%",
      trend: "up",
      series: [58, 60, 59, 62, 64, 63, 66, 67, 68.4],
    },
  ],
  equity: [
    { label: "W1", value: 5000 },
    { label: "W2", value: 5240 },
    { label: "W3", value: 5180 },
    { label: "W4", value: 5620 },
    { label: "W5", value: 6100 },
    { label: "W6", value: 6420 },
    { label: "W7", value: 7050 },
    { label: "W8", value: 7480 },
    { label: "W9", value: 8420 },
  ],
  equityStart: "$5,000",
  equityEnd: "$8,420",
  equityDelta: "+68.4%",
  trades: [
    { id: "t1", instrument: "GOLD", lot: "0.20", pnl: 420, time: "09:42" },
    { id: "t2", instrument: "US30", lot: "0.10", pnl: 280, time: "09:11" },
    { id: "t3", instrument: "GOLD", lot: "0.05", pnl: -110, time: "08:57" },
    { id: "t4", instrument: "US30", lot: "0.30", pnl: 365, time: "08:34" },
    { id: "t5", instrument: "GOLD", lot: "0.10", pnl: 190, time: "08:02" },
    { id: "t6", instrument: "US30", lot: "0.01", pnl: 95, time: "07:48" },
    { id: "t7", instrument: "GOLD", lot: "0.01", pnl: -60, time: "07:19" },
    { id: "t8", instrument: "US30", lot: "0.30", pnl: 540, time: "06:55" },
    { id: "t9", instrument: "GOLD", lot: "0.05", pnl: 75, time: "06:20" },
    { id: "t10", instrument: "US30", lot: "0.10", pnl: -130, time: "05:44" },
    { id: "t11", instrument: "GOLD", lot: "0.20", pnl: 230, time: "05:09" },
    { id: "t12", instrument: "GOLD", lot: "0.30", pnl: 310, time: "04:36" },
  ],
  closedTotal: 12,
};