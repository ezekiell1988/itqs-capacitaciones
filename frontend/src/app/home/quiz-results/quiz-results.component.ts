import { Component, EventEmitter, Input, Output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonCard, IonCardHeader, IonCardTitle, IonCardContent,
  IonButton, IonList, IonItem, IonLabel, IonIcon, IonText, IonBadge,
  IonAccordionGroup, IonAccordion
} from '@ionic/angular/standalone';
import { Question } from '../../services/quiz.service';
import { addIcons } from 'ionicons';
import { checkmarkCircle, closeCircle, refresh } from 'ionicons/icons';

@Component({
  selector: 'app-quiz-results',
  template: `
    <div class="results-container">
      <ion-card class="score-card" [color]="passed ? 'success' : 'danger'">
        <ion-card-header>
          <ion-card-title class="ion-text-center">
            {{ passed ? '¡Aprobado!' : 'No Aprobado' }}
          </ion-card-title>
        </ion-card-header>
        <ion-card-content class="ion-text-center">
          <h1 class="score-text">{{ score }}%</h1>
          <p>{{ correctCount }} correctas de {{ totalQuestions }}</p>
          <p>Nota mínima requerida: 70%</p>
        </ion-card-content>
      </ion-card>

      <div class="ion-padding">
        <ion-button expand="block" (click)="restart.emit()">
          <ion-icon slot="start" name="refresh"></ion-icon>
          Jugar de Nuevo
        </ion-button>
      </div>

      <h3 class="ion-padding-start">Detalle de Respuestas</h3>

      <ion-accordion-group>
        @for (q of questions; track q.numero) {
          <ion-accordion [value]="q.numero">
            <ion-item slot="header" [color]="isCorrect(q) ? 'light' : 'light'">
              <ion-icon [name]="isCorrect(q) ? 'checkmark-circle' : 'close-circle'" [color]="isCorrect(q) ? 'success' : 'danger'" slot="start"></ion-icon>
              <ion-label>
                <h2>Pregunta #{{ q.numero }}</h2>
                <p>{{ isCorrect(q) ? 'Correcta' : 'Incorrecta' }}</p>
              </ion-label>
            </ion-item>

            <div class="ion-padding" slot="content">
              <p><strong>Pregunta:</strong> {{ q.pregunta }}</p>

              <div class="options-review">
                @for (opt of q.opciones; track opt.letra) {
                  <div class="option-row"
                       [class.correct-opt]="opt.letra === q.respuesta_correcta"
                       [class.wrong-opt]="opt.letra === q.userSelected && opt.letra !== q.respuesta_correcta">
                    <span class="opt-letter">{{ opt.letra }})</span>
                    <span class="opt-text">{{ opt.texto }}</span>
                    @if (opt.letra === q.respuesta_correcta) {
                      <ion-badge color="success">Correcta</ion-badge>
                    }
                    @if (opt.letra === q.userSelected && opt.letra !== q.respuesta_correcta) {
                      <ion-badge color="danger">Tu elección</ion-badge>
                    }
                  </div>
                }
              </div>

              @if (q.explicacion) {
                <div class="explanation-box">
                  <p><strong>Explicación:</strong></p>
                  <p>{{ q.explicacion }}</p>
                </div>
              }
            </div>
          </ion-accordion>
        }
      </ion-accordion-group>
    </div>
  `,
  styles: [`
    .results-container {
      max-width: 800px;
      margin: 0 auto;
      padding-bottom: 40px;
    }
    .score-text {
      font-size: 4rem;
      font-weight: bold;
      margin: 10px 0;
    }
    .option-row {
      padding: 8px;
      margin: 4px 0;
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .correct-opt {
      background-color: var(--ion-color-success-tint);
      border: 1px solid var(--ion-color-success);
    }
    .wrong-opt {
      background-color: var(--ion-color-danger-tint);
      border: 1px solid var(--ion-color-danger);
    }
    .opt-letter {
      font-weight: bold;
    }
    .explanation-box {
      margin-top: 16px;
      padding: 12px;
      background-color: #f0f0f0;
      border-radius: 8px;
      border-left: 4px solid var(--ion-color-tertiary);
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    IonCard, IonCardHeader, IonCardTitle, IonCardContent,
    IonButton, IonList, IonItem, IonLabel, IonIcon, IonText, IonBadge,
    IonAccordionGroup, IonAccordion
  ]
})
export class QuizResultsComponent implements OnInit {
  @Input() questions: Question[] = [];
  @Output() restart = new EventEmitter<void>();

  score = 0;
  correctCount = 0;
  totalQuestions = 0;
  passed = false;

  constructor() {
    addIcons({ checkmarkCircle, closeCircle, refresh });
  }

  ngOnInit() {
    this.calculateScore();
  }

  calculateScore() {
    this.totalQuestions = this.questions.length;
    this.correctCount = this.questions.filter(q => this.isCorrect(q)).length;
    this.score = Math.round((this.correctCount / this.totalQuestions) * 100);
    this.passed = this.score >= 70;
  }

  isCorrect(q: Question): boolean {
    return q.userSelected === q.respuesta_correcta;
  }
}
