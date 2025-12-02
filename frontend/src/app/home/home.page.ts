import { Component, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonIcon, IonToolbar, IonTitle, IonButton, IonLabel, IonInput, IonToast, IonSegment, IonSegmentButton, IonCard, IonCardContent, IonNote, IonText, IonSkeletonText } from '@ionic/angular/standalone';
import { HeaderComponent } from '../components/header/header.component';
import { NgxExtendedPdfViewerModule } from 'ngx-extended-pdf-viewer';
import { MarkdownModule } from 'ngx-markdown';
import { addIcons } from 'ionicons';
import { languageOutline, closeOutline, searchOutline, saveOutline, createOutline, eyeOutline, documentTextOutline } from 'ionicons/icons';
import { ExamService } from '../services/exam.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  template: `
    <app-header title="ITQS Capacitaciones">
      <ion-button fill="clear" (click)="goToReport()">
        <ion-icon name="document-text-outline" slot="icon-only"></ion-icon>
      </ion-button>
    </app-header>

    <ion-content [fullscreen]="true">
      <!-- Segment for Mobile -->
      @if (!isDesktop) {
        <ion-segment [(ngModel)]="selectedSegment" (ionChange)="onSegmentChange($event)">
          <ion-segment-button value="pdf">
            <ion-label>PDF</ion-label>
          </ion-segment-button>
          <ion-segment-button value="translator">
            <ion-label>Traductor</ion-label>
          </ion-segment-button>
        </ion-segment>
      }

      <div class="main-layout">
        <div class="pdf-section" [style.display]="(isDesktop || selectedSegment === 'pdf') ? 'block' : 'none'">
          @if (pdfLoading) {
            <div class="pdf-skeleton ion-padding">
              <ion-skeleton-text animated style="width: 100%; height: 100%; border-radius: 8px;"></ion-skeleton-text>
            </div>
          }
          <ngx-extended-pdf-viewer
            [src]="pdfSrc"
            [height]="'100%'"
            [textLayer]="true"
            [showHandToolButton]="true"
            [language]="'es'"
            (pageChange)="onPageChange($event)"
            (pagesLoaded)="onPdfLoaded()">
          </ngx-extended-pdf-viewer>
        </div>

        <!-- Side Panel for Desktop -->
        @if (isDesktop) {
          <div class="side-panel">
            <ion-toolbar>
              <ion-title size="small">Traductor</ion-title>
            </ion-toolbar>
            <div class="ion-padding">
              <ng-container *ngTemplateOutlet="translationControls"></ng-container>
            </div>
          </div>
        }

        <!-- Mobile Translator View -->
        @if (!isDesktop && selectedSegment === 'translator') {
          <div class="mobile-translator">
            <div class="ion-padding">
              <ng-container *ngTemplateOutlet="translationControls"></ng-container>
            </div>
          </div>
        }
      </div>

      <!-- Reusable Translation Controls Template -->
      <ng-template #translationControls>
        <ion-card class="control-card">
          <ion-card-content>
            <ion-input
              label="Número de Pregunta"
              labelPlacement="stacked"
              [(ngModel)]="questionNumber"
              placeholder="Ej: 51"
              type="number"
              (keyup.enter)="translateQuestion()"
              class="ion-margin-bottom">
            </ion-input>

            <div class="page-range-inputs">
              <div class="half-width">
                <ion-input
                  label="Pág. Inicio (Opcional)"
                  labelPlacement="stacked"
                  [(ngModel)]="startPage"
                  type="number"
                  placeholder="{{currentPage}}">
                </ion-input>
              </div>
              <div class="half-width">
                <ion-input
                  label="Pág. Fin (Opcional)"
                  labelPlacement="stacked"
                  [(ngModel)]="endPage"
                  type="number"
                  placeholder="{{currentPage}}">
                </ion-input>
              </div>
            </div>
            <ion-note color="medium" class="ion-margin-top d-block">Si indicas las páginas, la traducción será más rápida.</ion-note>

            <ion-button expand="block" (click)="translateQuestion()" [disabled]="translating || !questionNumber" class="ion-margin-top">
              <ion-icon name="search-outline" slot="start"></ion-icon>
              Traducir
            </ion-button>
            <ion-note color="medium" class="ion-text-center d-block ion-margin-top">Página actual del visor: {{ currentPage }}</ion-note>
          </ion-card-content>
        </ion-card>

        @if (translating) {
          <div class="skeleton-container ion-padding">
            <!-- Segment Skeleton -->
            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
              <ion-skeleton-text animated style="width: 25%; height: 30px; border-radius: 16px;"></ion-skeleton-text>
              <ion-skeleton-text animated style="width: 25%; height: 30px; border-radius: 16px;"></ion-skeleton-text>
              <ion-skeleton-text animated style="width: 25%; height: 30px; border-radius: 16px;"></ion-skeleton-text>
              <ion-skeleton-text animated style="width: 25%; height: 30px; border-radius: 16px;"></ion-skeleton-text>
            </div>

            <!-- Title Skeleton -->
            <ion-skeleton-text animated style="width: 60%; height: 28px; margin-bottom: 15px; border-radius: 4px;"></ion-skeleton-text>

            <!-- Content Skeleton -->
            <ion-skeleton-text animated style="width: 100%; height: 16px; margin-bottom: 8px;"></ion-skeleton-text>
            <ion-skeleton-text animated style="width: 95%; height: 16px; margin-bottom: 8px;"></ion-skeleton-text>
            <ion-skeleton-text animated style="width: 90%; height: 16px; margin-bottom: 8px;"></ion-skeleton-text>
            <ion-skeleton-text animated style="width: 98%; height: 16px; margin-bottom: 20px;"></ion-skeleton-text>

            <!-- Options Skeleton -->
            <ion-skeleton-text animated style="width: 40%; height: 20px; margin-bottom: 10px; border-radius: 4px;"></ion-skeleton-text>
            <ion-skeleton-text animated style="width: 80%; height: 16px; margin-bottom: 8px; margin-left: 10px;"></ion-skeleton-text>
            <ion-skeleton-text animated style="width: 85%; height: 16px; margin-bottom: 8px; margin-left: 10px;"></ion-skeleton-text>
            <ion-skeleton-text animated style="width: 75%; height: 16px; margin-bottom: 8px; margin-left: 10px;"></ion-skeleton-text>

            <div class="loading-text ion-text-center ion-margin-top">
              <ion-text color="medium">
                <small>Analizando imágenes y traduciendo pregunta #{{ questionNumber }}...</small>
              </ion-text>
            </div>
          </div>
        } @else if (markdownEs) {
          <div class="result-container">
            <ion-segment [(ngModel)]="selectedTranslationView" scrollable mode="md">
              <ion-segment-button value="es_summary">
                <ion-label>ES Resumen</ion-label>
              </ion-segment-button>
              <ion-segment-button value="es_full">
                <ion-label>ES Completo</ion-label>
              </ion-segment-button>
              <ion-segment-button value="en_summary">
                <ion-label>EN Summary</ion-label>
              </ion-segment-button>
              <ion-segment-button value="en_full">
                <ion-label>EN Full</ion-label>
              </ion-segment-button>
            </ion-segment>

            <div class="translation-result markdown-body">
              <markdown [data]="currentMarkdown"></markdown>
            </div>
          </div>
        }
      </ng-template>

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
      position: relative;
    }
    .side-panel {
      width: 450px;
      min-width: 350px;
      border-left: 1px solid var(--ion-border-color);
      background: var(--ion-background-color);
      display: flex;
      flex-direction: column;
      overflow-y: auto;
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
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      margin-top: 2rem;
      color: var(--ion-color-medium);
    }
    .control-card {
      margin: 0;
      margin-bottom: 1rem;
      --background: var(--ion-item-background, var(--ion-card-background));
    }
    .page-range-inputs {
      display: flex;
      gap: 10px;
      margin-top: 10px;
    }
    .half-width {
      flex: 1;
    }
    .d-block {
      display: block;
    }

    /* Markdown Styles */
    .translation-result {
      padding: 1rem;
      line-height: 1.6;
      color: var(--ion-text-color);
      background: var(--ion-background-color);
    }
    ::ng-deep .markdown-body {
      color: var(--ion-text-color) !important;
      background-color: transparent !important;
    }
    ::ng-deep .markdown-body h2 {
      font-size: 1.4rem;
      border-bottom: 1px solid var(--ion-border-color);
      padding-bottom: 0.3rem;
      margin-top: 1.5rem;
      margin-bottom: 1rem;
      color: var(--ion-text-color);
      font-weight: 600;
    }
    ::ng-deep .markdown-body p {
      margin-bottom: 1rem;
    }
    ::ng-deep .markdown-body strong {
      color: var(--ion-text-color);
      font-weight: 600;
    }
    ::ng-deep .markdown-body ul {
      padding-left: 1.5rem;
      margin-bottom: 1rem;
    }
    ::ng-deep .markdown-body li {
      margin-bottom: 0.5rem;
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonContent, IonIcon, IonToolbar, IonTitle, IonButton, IonLabel, IonInput, IonToast, IonSegment, IonSegmentButton, IonCard, IonCardContent, IonNote, IonText, IonSkeletonText,
    HeaderComponent,
    NgxExtendedPdfViewerModule,
    MarkdownModule
  ]
})
export class HomePage implements OnInit {
  currentPage = 1;
  selectedSegment = 'pdf';
  selectedTranslationView = 'es_summary';
  translating = false;
  saving = false;
  pdfLoading = true;

  // Translation results
  markdownEs = '';
  markdownEsFull = '';
  markdownEn = '';
  markdownEnFull = '';

  questionNumber = '';
  startPage: number | undefined;
  endPage: number | undefined;
  pdfSrc = '/pdfs/az-204.pdf';
  isDesktop = false;
  toastMessage = '';

  constructor(private examService: ExamService, private router: Router) {
    addIcons({ languageOutline, closeOutline, searchOutline, saveOutline, createOutline, eyeOutline, documentTextOutline });
  }

  ngOnInit() {
    this.checkScreen();
  }

  @HostListener('window:resize')
  onResize() {
    this.checkScreen();
  }

  checkScreen() {
    this.isDesktop = window.innerWidth >= 992;
  }

  onPageChange(page: number) {
    this.currentPage = page;
  }

  onPdfLoaded() {
    this.pdfLoading = false;
  }

  onSegmentChange(event: any) {
    this.selectedSegment = event.detail.value;
  }

  translateQuestion() {
    if (!this.questionNumber) return;

    this.translating = true;
    this.markdownEs = '';
    this.markdownEsFull = '';
    this.markdownEn = '';
    this.markdownEnFull = '';

    const qNum = String(this.questionNumber);

    this.examService.translateQuestion(qNum, this.currentPage, 'az-204.pdf', this.startPage, this.endPage).subscribe({
      next: (res) => {
        this.markdownEs = res.markdown || '';
        this.markdownEsFull = res.markdown_full || '';
        this.markdownEn = res.markdown_en || '';
        this.markdownEnFull = res.markdown_full_en || '';

        this.translating = false;
      },
      error: (err) => {
        console.error('Translation error', err);
        this.markdownEs = 'Error: ' + (err.error?.detail || 'No se pudo traducir la pregunta. Verifica que el número sea correcto.');
        this.translating = false;
      }
    });
  }

  get currentMarkdown(): string {
    switch (this.selectedTranslationView) {
      case 'es_summary': return this.markdownEs;
      case 'es_full': return this.markdownEsFull;
      case 'en_summary': return this.markdownEn;
      case 'en_full': return this.markdownEnFull;
      default: return this.markdownEs;
    }
  }

  goToReport() {
    this.router.navigate(['/report']);
  }
}
