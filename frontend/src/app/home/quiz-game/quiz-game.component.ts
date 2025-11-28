import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, IonCardContent,
  IonButton, IonList, IonItem, IonLabel, IonRadioGroup, IonRadio,
  IonProgressBar, IonBadge, IonIcon, IonText
} from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { checkmarkCircle, closeCircle } from 'ionicons/icons';
import { Question } from '../../services/quiz.service';

@Component({
  selector: 'app-quiz-game',
  template: `
    <div class="game-container">
      <div class="progress-section ion-padding-bottom">
        <ion-progress-bar [value]="(currentIndex + 1) / questions.length" color="primary"></ion-progress-bar>
        <div class="ion-text-end ion-padding-top">
          <ion-badge color="medium">Pendientes: {{ questions.length - (currentIndex + 1) }}</ion-badge>
        </div>
      </div>

      <ion-card>
        <ion-card-header>
          <ion-card-subtitle color="primary">Pregunta {{ currentIndex + 1 }} de {{ questions.length }}</ion-card-subtitle>
          <ion-card-title class="ion-text-wrap question-title">
            {{ currentQuestion.pregunta }}
          </ion-card-title>
        </ion-card-header>

        <ion-card-content>
          <ion-list>
            <ion-radio-group [value]="selectedOption" (ionChange)="onOptionSelect($event)">
              @for (opt of currentQuestion.opciones; track opt.letra) {
                <ion-item class="option-item" lines="full"
                  [class.correct-answer]="isAnswered && opt.letra === currentQuestion.respuesta_correcta"
                  [class.wrong-answer]="isAnswered && selectedOption === opt.letra && selectedOption !== currentQuestion.respuesta_correcta">
                  <ion-radio slot="start" [value]="opt.letra" [disabled]="isAnswered"></ion-radio>
                  <ion-label class="ion-text-wrap">
                    <strong>{{ opt.letra }})</strong> {{ opt.texto }}
                  </ion-label>
                </ion-item>
              }
            </ion-radio-group>
          </ion-list>

          @if (isAnswered) {
            <div class="feedback-section ion-padding-top">
              @if (isCorrect) {
                <ion-item color="success" lines="none" class="feedback-item rounded">
                  <ion-icon name="checkmark-circle" slot="start"></ion-icon>
                  <ion-label><strong>¡Correcto!</strong></ion-label>
                </ion-item>
              } @else {
                <ion-item color="danger" lines="none" class="feedback-item rounded">
                  <ion-icon name="close-circle" slot="start"></ion-icon>
                  <ion-label><strong>Incorrecto.</strong> La respuesta correcta es {{ currentQuestion.respuesta_correcta }}</ion-label>
                </ion-item>
              }

              @if (currentQuestion.explicacion) {
                <div class="explanation-box ion-margin-top">
                  <ion-text color="dark">
                    <h3>Explicación:</h3>
                    <p>{{ currentQuestion.explicacion }}</p>
                  </ion-text>
                </div>
              }
            </div>
          }
        </ion-card-content>
      </ion-card>

      <div class="ion-padding">
        @if (!isAnswered) {
          <ion-button expand="block" size="large" (click)="checkAnswer()" [disabled]="!selectedOption">
            Verificar Respuesta
          </ion-button>
        } @else {
          <ion-button expand="block" size="large" (click)="next()">
            {{ isLastQuestion ? 'Finalizar Examen' : 'Siguiente Pregunta' }}
          </ion-button>
        }
      </div>
    </div>
  `,
  styles: [`
    .game-container {
      max-width: 800px;
      margin: 0 auto;
      padding-bottom: 50px;
    }
    .question-title {
      font-size: 1.2rem;
      line-height: 1.4;
    }
    .option-item {
      --padding-start: 0;
      margin-bottom: 10px;
    }
    .correct-answer {
      --background: var(--ion-color-success-tint);
      --border-color: var(--ion-color-success);
    }
    .wrong-answer {
      --background: var(--ion-color-danger-tint);
      --border-color: var(--ion-color-danger);
    }
    .rounded {
      border-radius: 8px;
    }
    .explanation-box {
      background-color: var(--ion-color-light);
      padding: 15px;
      border-radius: 8px;
      border-left: 5px solid var(--ion-color-primary);
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, IonCardContent,
    IonButton, IonList, IonItem, IonLabel, IonRadioGroup, IonRadio,
    IonProgressBar, IonBadge, IonIcon, IonText
  ]
})
export class QuizGameComponent implements OnChanges {
  @Input() questions: Question[] = [];
  @Output() finish = new EventEmitter<Question[]>();

  currentIndex = 0;
  currentQuestion!: Question;
  selectedOption: string | null = null;
  isAnswered = false;
  isCorrect = false;

  constructor() {
    addIcons({ checkmarkCircle, closeCircle });
  }

  get isLastQuestion(): boolean {
    return this.currentIndex === this.questions.length - 1;
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['questions'] && this.questions.length > 0) {
      this.currentIndex = 0;
      this.loadQuestion();
    }
  }

  loadQuestion() {
    this.currentQuestion = this.questions[this.currentIndex];
    this.selectedOption = null;
    this.isAnswered = false;
    this.isCorrect = false;
  }

  onOptionSelect(event: any) {
    this.selectedOption = event.detail.value;
  }

  checkAnswer() {
    if (!this.selectedOption) return;

    this.isAnswered = true;
    this.questions[this.currentIndex].userSelected = this.selectedOption;
    this.isCorrect = this.selectedOption === this.currentQuestion.respuesta_correcta;
  }

  next() {
    if (this.isLastQuestion) {
      this.finish.emit(this.questions);
    } else {
      this.currentIndex++;
      this.loadQuestion();
    }
  }
}
