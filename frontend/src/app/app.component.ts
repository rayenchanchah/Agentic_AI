import { Component, HostListener } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { TeamJob, AIProcessingStatus, DocumentSource, AIEnhancementResult } from './interfaces/job.interface';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  isProcessingFile = false;
  isDragOver = false;
  teamJobs: TeamJob[] = [];
  aiStatus: AIProcessingStatus = {
    isProcessing: false,
    progress: 0,
    stage: 'document_analysis',
    startTime: new Date()
  };
  currentDocument?: DocumentSource;
  private apiUrl = 'http://localhost:3000/api';

  constructor(private http: HttpClient) {}

  @HostListener('dragover', ['$event'])
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }

  @HostListener('dragleave', ['$event'])
  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  @HostListener('drop', ['$event'])
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.handleFile(file);
    }
  }

  private handleFile(file: File) {
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    const allowedTypes = ['csv', 'db', 'sqlite', 'sqlite3', 'pdf', 'html'];
    
    if (!allowedTypes.includes(fileExt || '')) {
      alert('Please upload a CSV, database, PDF, or HTML file');
      return;
    }

    this.isProcessingFile = true;
    const formData = new FormData();
    formData.append('file', file);

    // Create document source
    this.currentDocument = {
      type: this.getDocumentType(fileExt || ''),
      name: file.name,
      path: URL.createObjectURL(file),
      processingStatus: 'processing',
      lastProcessed: new Date()
    };

    // First upload and process the file
    this.http.post<TeamJob[]>(`${this.apiUrl}/upload`, formData)
      .subscribe({
        next: (jobs) => {
          this.teamJobs = jobs;
          if (this.currentDocument) {
            this.currentDocument.processingStatus = 'completed';
            this.currentDocument.extractedJobCount = jobs.length;
          }
          this.isProcessingFile = false;
          // Start AI processing for each job
          this.processJobsWithAI(jobs);
        },
        error: (error) => {
          console.error('Error uploading file:', error);
          if (this.currentDocument) {
            this.currentDocument.processingStatus = 'error';
          }
          alert('Failed to upload file. Please try again.');
          this.isProcessingFile = false;
        }
      });
  }

  private processJobsWithAI(jobs: TeamJob[]) {
    this.aiStatus = {
      isProcessing: true,
      progress: 0,
      stage: 'document_analysis',
      startTime: new Date(),
      estimatedCompletion: new Date(Date.now() + (jobs.length * 30000)) // Estimate 30 seconds per job
    };

    // Process each job sequentially
    jobs.forEach((job, index) => {
      this.http.post<AIEnhancementResult>(`${this.apiUrl}/enhance-job`, job)
        .subscribe({
          next: (result) => {
            // Update the job with AI-enhanced information
            this.teamJobs[index] = result.enhancedJob;
            this.aiStatus.progress = ((index + 1) / jobs.length) * 100;
            this.aiStatus.currentJob = result.enhancedJob.title;
            
            if (index === jobs.length - 1) {
              this.aiStatus.isProcessing = false;
              this.aiStatus.stage = 'complete';
            }
          },
          error: (error) => {
            console.error(`Error processing job ${job.title}:`, error);
            this.aiStatus.error = `Failed to process job: ${job.title}`;
          }
        });
    });
  }

  private getDocumentType(extension: string): DocumentSource['type'] {
    switch (extension) {
      case 'pdf':
        return 'pdf';
      case 'html':
        return 'html';
      case 'csv':
        return 'csv';
      default:
        return 'database';
    }
  }

  getStageDescription(stage: string): string {
    switch (stage) {
      case 'document_analysis':
        return 'Analyzing document contents...';
      case 'web_search':
        return 'Searching web for additional information...';
      case 'knowledge_enhancement':
        return 'Enhancing job information with AI...';
      case 'complete':
        return 'Processing complete!';
      default:
        return 'Processing...';
    }
  }
}
