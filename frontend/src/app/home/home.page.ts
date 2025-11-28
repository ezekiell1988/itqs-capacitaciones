import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonContent, IonFab, IonFabButton, IonIcon, IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonSpinner } from '@ionic/angular/standalone';
import { HeaderComponent } from '../components/header/header.component';
import { NgxExtendedPdfViewerModule } from 'ngx-extended-pdf-viewer';
import { addIcons } from 'ionicons';
import { languageOutline, closeOutline } from 'ionicons/icons';
import { QuizService } from '../services/quiz.service';

@Component({
  selector: 'app-home',
  template: `
    <app-header title="ITQS Capacitaciones"></app-header>

    <ion-content [fullscreen]="true">
      <ngx-extended-pdf-viewer
        [src]="pdfSrc"
        [height]="'100%'"
        [textLayer]="true"
        [showHandToolButton]="true"
        (pageChange)="onPageChange($event)">
      </ngx-extended-pdf-viewer>

      <ion-fab vertical="bottom" horizontal="end" slot="fixed">
        <ion-fab-button (click)="translateCurrentPage()" [disabled]="translating">
          <ion-icon name="language-outline"></ion-icon>
        </ion-fab-button>
      </ion-fab>

      <ion-modal [isOpen]="showTranslation" (didDismiss)="showTranslation = false">
        <ng-template>
          <ion-header>
            <ion-toolbar>
              <ion-title>Traducción (Página {{ currentPage }})</ion-title>
              <ion-buttons slot="end">
                <ion-button (click)="showTranslation = false">
                  <ion-icon name="close-outline"></ion-icon>
                </ion-button>
              </ion-buttons>
            </ion-toolbar>
          </ion-header>
          <ion-content class="ion-padding">
            @if (translating) {
              <div class="loading-container">
                <ion-spinner name="crescent"></ion-spinner>
                <p>Traduciendo...</p>
              </div>
            } @else {
              <div class="translation-content" [innerHTML]="translatedText"></div>
            }
          </ion-content>
        </ng-template>
      </ion-modal>
    </ion-content>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    ngx-extended-pdf-viewer {
      flex: 1;
      width: 100%;
      height: 100%;
    }
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
    }
    .translation-content {
      white-space: pre-wrap;
      font-family: sans-serif;
      line-height: 1.5;
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    IonContent, IonFab, IonFabButton, IonIcon, IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonSpinner,
    HeaderComponent,
    NgxExtendedPdfViewerModule
  ]
})
export class HomePage {
  currentPage = 1;
  showTranslation = false;
  translating = false;
  translatedText = '';
  pdfSrc = 'http://localhost:8000/pdfs/az-204.pdf';

  constructor(private quizService: QuizService) {
    addIcons({ languageOutline, closeOutline });
  }

  onPageChange(page: number) {
    this.currentPage = page;
  }

  translateCurrentPage() {
    this.showTranslation = true;
    this.translating = true;
    this.translatedText = '';

    // Use the new image-based translation endpoint
    this.quizService.translatePageImage(this.currentPage).subscribe({
      next: (res) => {
        this.translatedText = res.translation;
        this.translating = false;
      },
      error: (err) => {
        console.error('Translation error', err);
        this.translatedText = 'Error al traducir la página. ' + (err.error?.detail || err.message);
        this.translating = false;
      }
    });
  }
}
