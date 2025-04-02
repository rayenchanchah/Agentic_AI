export interface WebReference {
  url: string;
  title: string;
  relevance: number;
}

export interface TeamJob {
  title: string;
  description: string;
  assignedTo: string;
  deadline: Date;
  references?: string[];
  aiEnhanced?: boolean;
  sourceDocument?: string;
  webReferences?: WebReference[];
  status?: 'pending' | 'in_progress' | 'completed';
  priority?: 'low' | 'medium' | 'high';
  tags?: string[];
  aiConfidence?: number;
  lastUpdated?: Date;
}

export interface AIProcessingStatus {
  isProcessing: boolean;
  currentJob?: string;
  progress: number;
  stage: 'document_analysis' | 'web_search' | 'knowledge_enhancement' | 'complete';
  error?: string;
  startTime?: Date;
  estimatedCompletion?: Date;
}

export interface DocumentSource {
  type: 'pdf' | 'html' | 'csv' | 'database';
  name: string;
  path: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'error';
  extractedJobCount?: number;
  lastProcessed?: Date;
}

export interface AIEnhancementResult {
  originalJob: TeamJob;
  enhancedJob: TeamJob;
  changes: {
    field: string;
    original: any;
    enhanced: any;
    confidence: number;
  }[];
  webSearchResults: WebReference[];
  processingTime: number;
} 