import { Component, HostListener } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { TeamJob, AIProcessingStatus, DocumentSource, AIEnhancementResult, KnowledgeArticle } from './interfaces/job.interface';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, HttpClientModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title(title: any) {
    throw new Error('Method not implemented.');
  }
  isProcessingFile = false;
  isDragOver = false;
  teamJobs: TeamJob[] = [];
  
  // Upload error properties
  uploadError = false;
  uploadErrorMessage = '';
  
  // Article management properties
  knowledgeArticles: KnowledgeArticle[] = [];
  showArticleForm = false;
  isSubmittingArticle = false;
  newArticle: KnowledgeArticle = this.getEmptyArticle();
  articleTagsInput = '';
  
  aiStatus: AIProcessingStatus = {
    isProcessing: false,
    progress: 0,
    stage: 'document_analysis',
    startTime: new Date()
  };
  currentDocument?: DocumentSource;
  private apiUrl = 'http://localhost:3000/api';

  constructor(private http: HttpClient) {
    this.loadKnowledgeArticles();
  }

  // Clear upload error
  clearError() {
    this.uploadError = false;
    this.uploadErrorMessage = '';
  }

  // Article management methods
  toggleArticleForm() {
    this.showArticleForm = !this.showArticleForm;
    if (this.showArticleForm) {
      this.newArticle = this.getEmptyArticle();
      this.articleTagsInput = '';
    }
  }

  submitArticle() {
    if (!this.newArticle.title || !this.newArticle.content) {
      alert('Please provide both title and content for the article');
      return;
    }

    // Process tags
    if (this.articleTagsInput) {
      this.newArticle.tags = this.articleTagsInput
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);
    }

    this.newArticle.dateAdded = new Date();
    this.isSubmittingArticle = true;

    this.http.post<KnowledgeArticle>(`${this.apiUrl}/knowledge-articles`, this.newArticle)
      .subscribe({
        next: (article) => {
          this.knowledgeArticles.push(article);
          this.isSubmittingArticle = false;
          this.toggleArticleForm();
          
          // Update AI status to show knowledge integration
          this.aiStatus = {
            isProcessing: true,
            progress: 0,
            stage: 'knowledge_enhancement',
            startTime: new Date()
          };
          
          // Simulate AI processing the new knowledge
          setTimeout(() => {
            this.aiStatus.progress = 100;
            this.aiStatus.isProcessing = false;
            this.aiStatus.stage = 'complete';
          }, 3000);
        },
        error: (error) => {
          console.error('Error submitting article:', error);
          this.isSubmittingArticle = false;
          alert('Error submitting article. Please try again.');
        }
      });
  }

  deleteArticle(id?: string) {
    if (!id) return;
    
    if (confirm('Are you sure you want to remove this article from the knowledge base?')) {
      this.http.delete(`${this.apiUrl}/knowledge-articles/${id}`)
        .subscribe({
          next: () => {
            this.knowledgeArticles = this.knowledgeArticles.filter(article => article.id !== id);
          },
          error: (error) => {
            console.error('Error deleting article:', error);
            alert('Error removing article. Please try again.');
          }
        });
    }
  }

  private loadKnowledgeArticles() {
    this.http.get<KnowledgeArticle[]>(`${this.apiUrl}/knowledge-articles`)
      .subscribe({
        next: (articles) => {
          this.knowledgeArticles = articles;
        },
        error: (error) => {
          console.error('Error loading knowledge articles:', error);
        }
      });
  }

  private getEmptyArticle(): KnowledgeArticle {
    return {
      title: '',
      content: '',
      source: '',
      author: '',
      dateAdded: new Date(),
      tags: [],
      usageCount: 0
    };
  }

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
    // Clear any previous errors
    this.clearError();
    
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    const allowedTypes = ['csv', 'db', 'sqlite', 'sqlite3', 'pdf', 'html', 'txt'];
    
    if (!allowedTypes.includes(fileExt || '')) {
      this.uploadError = true;
      this.uploadErrorMessage = 'File type not supported. Please upload a CSV, SQLite DB, PDF, HTML, or TXT file.';
      return;
    }
    
    this.isProcessingFile = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Log that we're sending the request
    console.log('Sending file upload request to:', `${this.apiUrl}/upload`);
    
    this.http.post<any>(`${this.apiUrl}/upload`, formData)
      .subscribe({
        next: (response) => {
          console.log('File upload response:', response);
          this.isProcessingFile = false;
          
          // Handle job data from response
          if (response.jobs && response.jobs.length > 0) {
            // Convert string dates to Date objects
            response.jobs.forEach((job: any) => {
              if (typeof job.deadline === 'string') {
                try {
                  job.deadline = new Date(job.deadline);
                } catch (e) {
                  job.deadline = new Date();
                }
              }
            });
            
            // Set team jobs to display them
            this.teamJobs = response.jobs;
            console.log(`Successfully loaded ${this.teamJobs.length} jobs`);
          } else {
            console.warn('No jobs were found in the uploaded file');
          }
          
          // Show AI processing animation regardless of response
          this.startAIProcessingAnimation();
        },
        error: (error) => {
          console.error('Error uploading file:', error);
          this.isProcessingFile = false;
          this.uploadError = true;
          
          if (error.status === 400) {
            this.uploadErrorMessage = `Invalid file: ${error.error?.detail || 'File type not supported'}`;
          } else if (error.status === 413) {
            this.uploadErrorMessage = 'File is too large. Please upload a smaller file.';
          } else if (error.status === 500) {
            this.uploadErrorMessage = `Server error: ${error.error?.detail || 'An internal server error occurred'}`;
          } else {
            this.uploadErrorMessage = 'Error uploading file. Please try again.';
          }
          
          // For debugging - force showing jobs even on error
          this.teamJobs = [
            {
              title: "Emergency Backup Job",
              description: "This job was created automatically when an error occurred during file upload.",
              assignedTo: "System",
              deadline: new Date(),
              aiEnhanced: true,
              references: ["Error Recovery Documentation"],
              webReferences: [
                { url: "https://example.com/help", title: "Troubleshooting Guide", relevance: 100 }
              ]
            }
          ];
          this.startAIProcessingAnimation();
        }
      });
  }
  
  private startAIProcessingAnimation() {
    // Set initial AI processing status
    this.aiStatus = {
      isProcessing: true,
      progress: 0,
      stage: 'document_analysis',
      startTime: new Date()
    };
    
    // Simulate progress over time
    const totalSteps = 5;
    const stageNames: ('document_analysis' | 'content_extraction' | 'ai_enhancement' | 'web_search' | 'finalizing' | 'complete')[] = 
      ['document_analysis', 'content_extraction', 'ai_enhancement', 'web_search', 'finalizing'];
    const timePerStep = 1500; // milliseconds
    
    for (let step = 0; step < totalSteps; step++) {
      setTimeout(() => {
        this.aiStatus.progress = (step + 1) * (100 / totalSteps);
        this.aiStatus.stage = stageNames[step];
        
        // Complete processing after last step
        if (step === totalSteps - 1) {
          setTimeout(() => {
            this.aiStatus.isProcessing = false;
            this.aiStatus.progress = 100;
            this.aiStatus.stage = 'complete';
          }, 1000);
        }
      }, step * timePerStep);
    }
  }

  private processJobsWithAI(jobs: TeamJob[]) {
    this.aiStatus = {
      isProcessing: true,
      progress: 0,
      stage: 'document_analysis',
      startTime: new Date(),
      estimatedCompletion: new Date(Date.now() + (jobs.length * 30000)) 
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
    const stages: {[key: string]: string} = {
      'document_analysis': 'Analyzing document structure',
      'content_extraction': 'Extracting job content',
      'ai_enhancement': 'Enhancing with AI knowledge',
      'web_search': 'Searching web for relevant information',
      'knowledge_enhancement': 'Integrating knowledge articles',
      'finalizing': 'Finalizing results'
    };
    return stages[stage] || 'Processing';
  }
}