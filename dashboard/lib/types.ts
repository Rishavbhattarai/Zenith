export type TelemetryReading = {
  asset_id: string;
  metric: string;
  value: number;
  status: string;
  timestamp: string;
};

export type AssetState = {
  asset_id: string;
  latest: TelemetryReading;
  history: TelemetryReading[];
};

export type Metrics = {
  received: number;
  valid: number;
  invalid: number;
  dropped: number;
};

export type AgentEvent = {
  note_id: string;
  stage: string;
  message: string;
  timestamp: string;
};

export type Part = {
  id: number;
  part_name: string;
  unit_price: string;
  stock_quantity: number;
  reorder_threshold: number;
  reorder_quantity: number;
};

export type ReorderRequest = {
  id: number;
  part_id: number;
  part_name: string;
  quantity: number;
  status: string;
};

export type DashboardData = {
  assets: AssetState[];
  metrics: Metrics | null;
  events: AgentEvent[];
  parts: Part[];
  reorderRequests: ReorderRequest[];
  errors: string[];
};

export type SupportAnswer = {
  answer: string;
  sources: string[];
};
