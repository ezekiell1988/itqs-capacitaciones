import { Component, HostListener, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonIcon, IonToolbar, IonTitle, IonButton, IonLabel, IonSelect, IonSelectOption, IonToast, IonCard, IonCardContent, IonNote, IonText, IonSkeletonText } from '@ionic/angular/standalone';
import { HeaderComponent } from '../components/header/header.component';
import { NgxExtendedPdfViewerModule } from 'ngx-extended-pdf-viewer';
import { MarkdownModule } from 'ngx-markdown';
import { addIcons } from 'ionicons';
import { documentTextOutline, refreshOutline, homeOutline } from 'ionicons/icons';
import { ExamService } from '../services/exam.service';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

interface QuestionMapping {
  numero: string;
  startPage: number;
  endPage: number;
}

@Component({
  selector: 'app-report',
  template: `
    <app-header title="Reporte de Preguntas">
      <ion-button fill="clear" (click)="goToHome()">
        <ion-icon name="home-outline" slot="icon-only"></ion-icon>
      </ion-button>
    </app-header>

    <ion-content [fullscreen]="true">
      <div class="main-layout">
        <!-- PDF Section -->
        <div class="pdf-section">
          @if (pdfLoading) {
            <div class="pdf-skeleton ion-padding">
              <ion-skeleton-text animated style="width: 100%; height: 100%; border-radius: 8px;"></ion-skeleton-text>
            </div>
          }
          @if (pdfReady) {
            <ngx-extended-pdf-viewer
              [src]="pdfSrc"
              [height]="'100%'"
              [textLayer]="true"
              [showHandToolButton]="true"
              [language]="'es'"
              (pageChange)="onPageChange($event)"
              (pagesLoaded)="onPdfLoaded()">
            </ngx-extended-pdf-viewer>
          }
        </div>

        <!-- Side Panel -->
        <div class="side-panel">
          <ion-toolbar>
            <ion-title size="small">Preguntas</ion-title>
          </ion-toolbar>

          <div class="ion-padding">
            <ion-card class="control-card">
              <ion-card-content>
                <ion-select
                  label="Selecciona Examen"
                  labelPlacement="stacked"
                  [(ngModel)]="selectedExam"
                  (ionChange)="loadQuestionsMarkdown()"
                  class="ion-margin-bottom">
                  <ion-select-option value="az-204">AZ-204</ion-select-option>
                </ion-select>

                <ion-button expand="block" (click)="loadQuestionsMarkdown()" [disabled]="loading || !selectedExam">
                  <ion-icon name="refresh-outline" slot="start"></ion-icon>
                  Cargar Preguntas
                </ion-button>
              </ion-card-content>
            </ion-card>

            @if (loading) {
              <div class="skeleton-container ion-padding">
                <ion-skeleton-text animated style="width: 100%; height: 20px; margin-bottom: 10px;"></ion-skeleton-text>
                <ion-skeleton-text animated style="width: 90%; height: 16px; margin-bottom: 8px;"></ion-skeleton-text>
                <ion-skeleton-text animated style="width: 95%; height: 16px; margin-bottom: 20px;"></ion-skeleton-text>
                <ion-skeleton-text animated style="width: 100%; height: 20px; margin-bottom: 10px;"></ion-skeleton-text>
                <ion-skeleton-text animated style="width: 85%; height: 16px; margin-bottom: 8px;"></ion-skeleton-text>
              </div>
            } @else if (markdownContent) {
              <div class="markdown-container" #markdownContainer>
                <div class="markdown-body">
                  <markdown [data]="markdownContent"></markdown>
                </div>
              </div>
            }
          </div>
        </div>
      </div>

      <ion-toast [isOpen]="!!toastMessage" [message]="toastMessage" [duration]="3000" (didDismiss)="toastMessage = ''"></ion-toast>
    </ion-content>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    .main-layout {
      display: flex;
      height: 100%;
      width: 100%;
    }
    .pdf-section {
      flex: 1;
      height: 100%;
      min-height: 500px;
      min-width: 400px;
      position: relative;
    }
    .side-panel {
      width: 500px;
      min-width: 400px;
      border-left: 1px solid var(--ion-border-color);
      background: var(--ion-background-color);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: -2px 0 5px rgba(0,0,0,0.05);
    }
    .pdf-skeleton {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 10;
      background: var(--ion-background-color);
    }
    .control-card {
      margin: 0;
      margin-bottom: 1rem;
      --background: var(--ion-item-background, var(--ion-card-background));
    }
    .markdown-container {
      overflow-y: auto;
      max-height: calc(100vh - 250px);
      padding: 0.5rem;
    }
    .markdown-body {
      padding: 1rem;
      line-height: 1.6;
      color: var(--ion-text-color);
      background: var(--ion-background-color);
    }

    /* Markdown Styles */
    ::ng-deep .markdown-body {
      color: var(--ion-text-color) !important;
      background-color: transparent !important;
    }
    ::ng-deep .markdown-body h2 {
      font-size: 1.3rem;
      border-bottom: 1px solid var(--ion-border-color);
      padding-bottom: 0.3rem;
      margin-top: 1.5rem;
      margin-bottom: 1rem;
      color: var(--ion-color-primary);
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    ::ng-deep .markdown-body h2:hover {
      background-color: var(--ion-color-light);
      padding-left: 0.5rem;
    }
    ::ng-deep .markdown-body p {
      margin-bottom: 1rem;
    }
    ::ng-deep .markdown-body strong {
      color: var(--ion-text-color);
      font-weight: 600;
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonContent, IonIcon, IonToolbar, IonTitle, IonButton, IonSelect, IonSelectOption, IonToast, IonCard, IonCardContent, IonSkeletonText,
    HeaderComponent,
    NgxExtendedPdfViewerModule,
    MarkdownModule
  ]
})
export class ReportPage implements OnInit {
  @ViewChild('markdownContainer') markdownContainer?: ElementRef;

  currentPage = 1;
  selectedExam = 'az-204';
  loading = false;
  pdfLoading = true;
  pdfReady = false;
  markdownContent = '';
  questionMappings: QuestionMapping[] = [];

  pdfSrc = '/pdfs/az-204.pdf';
  toastMessage = '';

  constructor(
    private examService: ExamService,
    private http: HttpClient,
    private router: Router
  ) {
    addIcons({ documentTextOutline, refreshOutline, homeOutline });
  }

  ngOnInit() {
    // Wait for the view to be fully initialized before rendering PDF
    setTimeout(() => {
      this.pdfReady = true;
    }, 100);

    this.loadQuestionsMarkdown();

    // Add click listener to markdown headings after content loads
    setTimeout(() => {
      this.setupMarkdownClickHandlers();
    }, 500);
  }

  onPageChange(page: number) {
    this.currentPage = page;
    this.highlightQuestionForPage(page);
  }

  onPdfLoaded() {
    this.pdfLoading = false;
  }

  loadQuestionsMarkdown() {
    if (!this.selectedExam) return;

    this.loading = true;
    this.markdownContent = '';
    this.questionMappings = [];

    // Load questions from backend
    this.examService.getQuestions(this.selectedExam, 'es', 1000, false).subscribe({
      next: (questions) => {
        // Build markdown content
        let md = '# Reporte de Preguntas\n\n';

        questions.forEach((q) => {
          md += `## Pregunta ${q.numero}\n\n`;
          md += `**Resumen:** ${q.pregunta}\n\n`;
          md += `**Respuesta Correcta:** ${q.respuesta_correcta}\n\n`;
          md += `---\n\n`;
        });

        this.markdownContent = md;
        this.loading = false;

        // Load page mappings
        this.loadPageMappings();

        // Setup click handlers after render
        setTimeout(() => {
          this.setupMarkdownClickHandlers();
        }, 300);
      },
      error: (err) => {
        console.error('Error loading questions', err);
        this.toastMessage = 'Error al cargar preguntas';
        this.loading = false;
      }
    });
  }

  loadPageMappings() {
    // Call the analyze-pages endpoint to get page mappings
    // Analyze questions 1-200 to build the mapping
    this.http.get<any[]>(`/analyze-pages?start_question=1&end_question=200&pdf_filename=az-204.pdf`).subscribe({
      next: (mappings) => {
        this.questionMappings = mappings.map((m: any) => ({
          numero: m.question.toString(),
          startPage: m.start_page,
          endPage: m.end_page
        }));
        console.log('Loaded page mappings:', this.questionMappings.length);
      },
      error: (err) => {
        console.warn('Could not load page mappings, will use fallback', err);
        // Fallback: create approximate mappings (assuming ~2 pages per question)
        this.createFallbackMappings();
      }
    });
  }

  createFallbackMappings() {
    // Create approximate mappings assuming questions start at page 18
    // and take about 2-3 pages each
    const startPage = 18;
    const avgPagesPerQuestion = 2.5;

    for (let i = 1; i <= 200; i++) {
      const start = Math.floor(startPage + (i - 1) * avgPagesPerQuestion);
      const end = Math.floor(start + avgPagesPerQuestion);
      this.questionMappings.push({
        numero: i.toString(),
        startPage: start,
        endPage: end
      });
    }
  }

  setupMarkdownClickHandlers() {
    if (!this.markdownContainer) return;

    const container = this.markdownContainer.nativeElement;
    const headings = container.querySelectorAll('h2');

    headings.forEach((heading: HTMLElement) => {
      heading.addEventListener('click', () => {
        const text = heading.textContent || '';
        const match = text.match(/Pregunta (\d+)/);
        if (match) {
          const questionNum = match[1];
          this.navigateToQuestion(questionNum);
        }
      });
    });
  }

  navigateToQuestion(questionNum: string) {
    const mapping = this.questionMappings.find(m => m.numero === questionNum);
    if (mapping) {
      // Navigate PDF to the start page
      this.goToPdfPage(mapping.startPage);
      this.toastMessage = `Navegando a pregunta ${questionNum} (página ${mapping.startPage})`;
    } else {
      this.toastMessage = `No se encontró la página para la pregunta ${questionNum}`;
    }
  }

  goToPdfPage(pageNumber: number) {
    // Use the ngx-extended-pdf-viewer API to navigate
    const pdfViewer = (window as any).PDFViewerApplication;
    if (pdfViewer) {
      pdfViewer.page = pageNumber;
    }
  }

  highlightQuestionForPage(page: number) {
    // Find which question corresponds to this page
    const mapping = this.questionMappings.find(
      m => page >= m.startPage && page <= m.endPage
    );

    if (mapping && this.markdownContainer) {
      const container = this.markdownContainer.nativeElement;
      const headings = container.querySelectorAll('h2');

      // Remove previous highlights
      headings.forEach((h: HTMLElement) => {
        h.style.backgroundColor = '';
        h.style.paddingLeft = '';
      });

      // Highlight the current question
      headings.forEach((heading: HTMLElement) => {
        const text = heading.textContent || '';
        if (text.includes(`Pregunta ${mapping.numero}`)) {
          heading.style.backgroundColor = 'var(--ion-color-light)';
          heading.style.paddingLeft = '0.5rem';

          // Scroll to the heading
          heading.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }
  }

  goToHome() {
    this.router.navigate(['/home']);
  }
}
