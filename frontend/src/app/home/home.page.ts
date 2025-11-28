import { Component, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonFab, IonFabButton, IonIcon, IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonSpinner, IonItem, IonLabel, IonInput } from '@ionic/angular/standalone';
import { HeaderComponent } from '../components/header/header.component';
import { NgxExtendedPdfViewerModule } from 'ngx-extended-pdf-viewer';
import { MarkdownModule } from 'ngx-markdown';
import { addIcons } from 'ionicons';
import { languageOutline, closeOutline, searchOutline } from 'ionicons/icons';
import { QuizService } from '../services/quiz.service';

@Component({
  selector: 'app-home',
  template: `
    <app-header title="ITQS Capacitaciones"></app-header>

    <ion-content [fullscreen]="true">
      <div class="main-layout">
        <div class="pdf-section">
          <ngx-extended-pdf-viewer
            [src]="pdfSrc"
            [height]="'100%'"
            [textLayer]="true"
            [showHandToolButton]="true"
            (pageChange)="onPageChange($event)">
          </ngx-extended-pdf-viewer>
        </div>

        <!-- Side Panel for Desktop -->
        <div class="side-panel" *ngIf="isDesktop">
          <ion-toolbar color="light">
            <ion-title size="small">Traductor</ion-title>
          </ion-toolbar>
          <div class="ion-padding">
            <ng-container *ngTemplateOutlet="translationControls"></ng-container>
          </div>
        </div>
      </div>

      <!-- FAB for Mobile -->
      <ion-fab vertical="bottom" horizontal="end" slot="fixed" *ngIf="!isDesktop">
        <ion-fab-button (click)="openTranslationModal()">
          <ion-icon name="language-outline"></ion-icon>
        </ion-fab-button>
      </ion-fab>

      <!-- Modal for Mobile -->
      <ion-modal [isOpen]="showTranslation" (didDismiss)="showTranslation = false" *ngIf="!isDesktop">
        <ng-template>
          <ion-header>
            <ion-toolbar>
              <ion-title>Traductor</ion-title>
              <ion-buttons slot="end">
                <ion-button (click)="showTranslation = false">
                  <ion-icon name="close-outline"></ion-icon>
                </ion-button>
              </ion-buttons>
            </ion-toolbar>
          </ion-header>
          <ion-content class="ion-padding">
            <ng-container *ngTemplateOutlet="translationControls"></ng-container>
          </ion-content>
        </ng-template>
      </ion-modal>

      <!-- Reusable Translation Controls Template -->
      <ng-template #translationControls>
        <div class="input-container">
          <ion-item>
            <ion-label position="stacked">Número de Pregunta</ion-label>
            <ion-input [(ngModel)]="questionNumber" placeholder="Ej: 51" type="number" (keyup.enter)="translateQuestion()"></ion-input>
          </ion-item>

          <div class="page-range-inputs">
            <ion-item class="half-width">
              <ion-label position="stacked">Pág. Inicio (Opcional)</ion-label>
              <ion-input [(ngModel)]="startPage" type="number" placeholder="{{currentPage}}"></ion-input>
            </ion-item>
            <ion-item class="half-width">
              <ion-label position="stacked">Pág. Fin (Opcional)</ion-label>
              <ion-input [(ngModel)]="endPage" type="number" placeholder="{{currentPage}}"></ion-input>
            </ion-item>
          </div>
          <p class="hint-small">Si indicas las páginas, la traducción será más rápida y precisa.</p>

          <ion-button expand="block" (click)="translateQuestion()" [disabled]="translating || !questionNumber" class="ion-margin-top">
            <ion-icon name="search-outline" slot="start"></ion-icon>
            Traducir
          </ion-button>
          <p class="hint">Página actual del visor: {{ currentPage }}</p>
        </div>

        @if (translating) {
          <div class="loading-container">
            <ion-spinner name="crescent"></ion-spinner>
            <p>Analizando imágenes y traduciendo pregunta #{{ questionNumber }}...</p>
          </div>
        } @else if (translatedText) {
          <div class="translation-result markdown-body">
            <markdown [data]="translatedText"></markdown>
          </div>
        }
      </ng-template>
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
      border-left: 1px solid #e0e0e0;
      background: #fff;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      box-shadow: -2px 0 5px rgba(0,0,0,0.05);
    }
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      margin-top: 2rem;
      color: #666;
    }
    .input-container {
      background: #f8f9fa;
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 1rem;
    }
    .page-range-inputs {
      display: flex;
      gap: 10px;
      margin-top: 10px;
    }
    .half-width {
      flex: 1;
    }
    .hint {
      font-size: 0.8rem;
      color: #888;
      margin-top: 0.5rem;
      text-align: center;
    }
    .hint-small {
      font-size: 0.75rem;
      color: #666;
      margin-top: 5px;
      margin-bottom: 0;
      font-style: italic;
    }
    /* Markdown Styles */
    .translation-result {
      padding: 0.5rem;
      line-height: 1.6;
      color: #333;
    }
    ::ng-deep .markdown-body h2 {
      font-size: 1.4rem;
      border-bottom: 1px solid #eee;
      padding-bottom: 0.3rem;
      margin-top: 1.5rem;
      margin-bottom: 1rem;
      color: #2c3e50;
      font-weight: 600;
    }
    ::ng-deep .markdown-body p {
      margin-bottom: 1rem;
    }
    ::ng-deep .markdown-body strong {
      color: #2c3e50;
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
    IonContent, IonFab, IonFabButton, IonIcon, IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonSpinner, IonItem, IonLabel, IonInput,
    HeaderComponent,
    NgxExtendedPdfViewerModule,
    MarkdownModule
  ]
})
export class HomePage implements OnInit {
  currentPage = 1;
  showTranslation = false;
  translating = false;
  translatedText = '';
  questionNumber = '';
  startPage: number | undefined;
  endPage: number | undefined;
  pdfSrc = 'http://localhost:8000/pdfs/az-204.pdf';
  isDesktop = false;

  constructor(private quizService: QuizService) {
    addIcons({ languageOutline, closeOutline, searchOutline });
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
    // Optional: Auto-update start/end page if user hasn't manually typed?
    // Better to leave it manual to avoid confusion.
  }

  openTranslationModal() {
    this.showTranslation = true;
    // Pre-fill with current page as a suggestion
    if (!this.startPage) this.startPage = this.currentPage;
    if (!this.endPage) this.endPage = this.currentPage;
  }

  translateQuestion() {
    if (!this.questionNumber) return;

    this.translating = true;
    this.translatedText = '';

    // Ensure questionNumber is a string
    const qNum = String(this.questionNumber);

    this.quizService.translateQuestion(qNum, this.currentPage, 'az-204.pdf', this.startPage, this.endPage).subscribe({
      next: (res) => {
        this.translatedText = res.translation;
        this.translating = false;
      },
      error: (err) => {
        console.error('Translation error', err);
        this.translatedText = 'Error: ' + (err.error?.detail || 'No se pudo traducir la pregunta. Verifica que el número sea correcto.');
        this.translating = false;
      }
    });
  }
}
