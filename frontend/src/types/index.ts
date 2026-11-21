export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  department: string;
  region: string;
  branch: string;
  expertise: string;
}

export interface ImportUploadResult {
  status: string;
  batch_id: string;
  filename: string;
  checksum: string;
  quality_report: {
    total_imported_records: number;
    valid_records: number;
    successful_records: number;
    duplicate_candidates: number;
    rejected_records: number;
    missing_mobile_numbers: number;
    invalid_emails: number;
    invalid_budget_values: number;
    unmatched_locations: number;
    data_completeness_pct: number;
  };
}

export interface ExecutiveOverview {
  total_customers: number;
  total_leads: number;
  active_leads: number;
  active_projects: number;
  available_units: number;
  reserved_units: number;
  sold_units: number;
  total_deals: number;
  total_pipeline_value: number;
  closed_revenue: number;
  conversion_rate: number;
  pending_followups: number;
  overdue_tasks: number;
  crm_sync_health: string;
  security_alerts_7d: number;
}

export interface LeadRecord {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_phone?: string;
  customer_email?: string;
  project_id?: string;
  project_name?: string;
  region: string;
  branch?: string;
  status: string;
  priority: string;
  source: string;
  budget: number;
  assignee_id?: string;
  assignee_name?: string;
  created_at: string;
}

export interface OperationalEvent {
  event_id: string;
  event_type: string;
  actor: { id: string; name: string };
  target: { type: string; id: string };
  action: { description: string; status: string };
  timestamp: string;
  correlation_id: string;
  crm_sync_status: string;
  payload: Record<string, any>;
}

export interface AIAgentResponse {
  execution_id: string;
  agent_name: string;
  intent: string;
  message: string;
  interpreted_filters?: Record<string, any>;
  evidence?: Array<{
    title: string;
    data_points: string[];
    supporting_record_ids?: string[];
  }>;
  proposed_action?: {
    action_type: string;
    summary: string;
    details: Record<string, any>;
    requires_approval: boolean;
  };
  execution_status: string;
}
