export type Dashboard = {
  nodeTotal: number;
  nodeOnline: number;
  lineTotal: number;
  lineActive: number;
  socksTotal: number;
  socksOnline: number;
  socksOffline: number;
  alertOpen: number;
  socksAlertOpen: number;
};

export type NodeRow = {
  id: number;
  nodeKey: string;
  name: string;
  region: string;
  country: string;
  publicIp: string | null;
  isActive: boolean;
  online: boolean;
  lastSeenAt: string | null;
  currentConfigVersion: string | null;
  createdAt: string | null;
};

export type LineListItem = {
  id: number;
  tid: string;
  name: string;
  nodeId: number;
  nodeName: string;
  country: string;
  bandwidthMbps: number;
  channel: string;
  remark: string | null;
  isEnabled: boolean;
  status: string;
  createdAt: string;
  socksProfileId: number;
  socksName: string;
};

export type PaginatedLines = {
  total: number;
  items: LineListItem[];
};

export type LineDetail = LineListItem & {
  sourceCidrs: string[];
  socksRemark: string | null;
  createdBy: string;
  socksHost: string;
  socksPort: number;
  socksUsername: string | null;
  socksPassword: string | null;
  clientSocksDisplay: string;
  currentConfigVersion: string | null;
};

export type StaticRoute = {
  prefix: string;
  next_hop?: string | null;
  device?: string | null;
  comment?: string | null;
};

export type SocksProfile = {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string | null;
  password: string | null;
  country: string | null;
  channel: string | null;
  remark: string | null;
  addressDisplay: string;
  isHealthy: boolean;
  createdAt: string | null;
};

export type AlertEvent = {
  id: number;
  nodeId: number | null;
  lineId: number | null;
  level: string;
  type: string;
  message: string;
  createdAt: string;
};

export type FlowStat = {
  id: number;
  nodeId: number;
  lineId: number | null;
  windowStart: string;
  windowSeconds: number;
  bytesIn: number;
  bytesOut: number;
  activeConns: number;
};

export type PlatformUser = {
  id: number;
  username: string;
  role: string;
  isActive: boolean;
  createdAt: string;
};

export type OperationLog = {
  id: number;
  username: string;
  action: string;
  target: string;
  detail: string | null;
  createdAt: string;
};

/** API returns snake_case; map to camelCase for UI */
export function mapLineItem(raw: Record<string, unknown>): LineListItem {
  return {
    id: raw.id as number,
    tid: raw.tid as string,
    name: raw.name as string,
    nodeId: raw.node_id as number,
    nodeName: raw.node_name as string,
    country: raw.country as string,
    bandwidthMbps: raw.bandwidth_mbps as number,
    channel: raw.channel as string,
    remark: raw.remark as string | null,
    isEnabled: raw.is_enabled as boolean,
    status: raw.status as string,
    createdAt: raw.created_at as string,
    socksProfileId: raw.socks_profile_id as number,
    socksName: raw.socks_name as string,
  };
}

export function mapLineDetail(raw: Record<string, unknown>): LineDetail {
  const base = mapLineItem(raw);
  return {
    ...base,
    sourceCidrs: raw.source_cidrs as string[],
    socksRemark: raw.socks_remark as string | null,
    createdBy: raw.created_by as string,
    socksHost: raw.socks_host as string,
    socksPort: raw.socks_port as number,
    socksUsername: raw.socks_username as string | null,
    socksPassword: raw.socks_password as string | null,
    clientSocksDisplay: (raw.client_socks_display as string) || "N/A",
    currentConfigVersion: raw.current_config_version as string | null,
  };
}

export function mapNode(raw: Record<string, unknown>): NodeRow {
  return {
    id: raw.id as number,
    nodeKey: (raw.nodeKey as string) || "",
    name: raw.name as string,
    region: raw.region as string,
    country: (raw.country as string) || raw.region as string,
    publicIp: (raw.publicIp as string) || null,
    isActive: raw.isActive as boolean,
    online: raw.online as boolean,
    lastSeenAt: (raw.lastSeenAt as string) || null,
    currentConfigVersion: (raw.currentConfigVersion as string) || null,
    createdAt: (raw.createdAt as string) || null,
  };
}

export function nodeOptionLabel(n: NodeRow): string {
  const ip = n.publicIp ? ` ${n.publicIp}` : "";
  const st = n.online ? "在线" : "离线";
  return `#${n.id} ${n.name} (${n.region})${ip} [${st}]`;
}

export function mapDashboard(raw: Record<string, unknown>): Dashboard {
  return {
    nodeTotal: raw.node_total as number,
    nodeOnline: raw.node_online as number,
    lineTotal: raw.line_total as number,
    lineActive: raw.line_active as number,
    socksTotal: raw.socks_total as number,
    socksOnline: (raw.socks_online as number) ?? 0,
    socksOffline: (raw.socks_offline as number) ?? 0,
    alertOpen: raw.alert_open as number,
    socksAlertOpen: (raw.socks_alert_open as number) ?? 0,
  };
}

export function alertCategory(type: string): "socks" | "node" | "other" {
  if (type.startsWith("socks_down_")) return "socks";
  if (type.startsWith("service_down_") || type === "node_offline" || type === "config_apply_failed") {
    return "node";
  }
  return "other";
}

export function mapSocks(raw: Record<string, unknown>): SocksProfile {
  return {
    id: raw.id as number,
    name: raw.name as string,
    host: raw.host as string,
    port: raw.port as number,
    username: raw.username as string | null,
    password: raw.password as string | null,
    country: (raw.country as string) || null,
    channel: (raw.channel as string) || null,
    remark: raw.remark as string | null,
    addressDisplay: (raw.address_display as string) || "",
    isHealthy: raw.is_healthy as boolean,
    createdAt: raw.created_at as string | null,
  };
}
