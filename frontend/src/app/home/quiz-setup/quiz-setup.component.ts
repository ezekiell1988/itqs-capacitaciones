import { Component, EventEmitter, Output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  IonCard, IonCardHeader, IonCardTitle, IonCardContent,
  IonItem, IonLabel, IonSelect, IonSelectOption,
  IonInput, IonToggle, IonButton, IonList, IonText
} from '@ionic/angular/standalone';
import { QuizService, Exam } from '../../services/quiz.service';

export interface QuizConfig {
  examId: string;
  lang: string;
  limit: number;
  randomize: boolean;
}

@Component({
  selector: 'app-quiz-setup',
  template: `
    <ion-card>
      <ion-card-header>
        <ion-card-title class="ion-text-center">Configuración del Quiz</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <ion-list>
          <ion-item>
            <ion-select label="Examen" label-placement="floating" [(ngModel)]="config.examId">
              @for (exam of exams; track exam.id) {
                <ion-select-option [value]="exam.id">{{ exam.name }}</ion-select-option>
              }
            </ion-select>
          </ion-item>

          <ion-item>
            <ion-select label="Idioma" label-placement="floating" [(ngModel)]="config.lang">
              <ion-select-option value="es">Español</ion-select-option>
              <ion-select-option value="en">Inglés</ion-select-option>
            </ion-select>
          </ion-item>

          <ion-item>
            <ion-input label="Cantidad de preguntas" type="number" label-placement="floating" [(ngModel)]="config.limit" min="1"></ion-input>
          </ion-item>

          <ion-item>
            <ion-toggle [(ngModel)]="config.randomize">Orden Aleatorio</ion-toggle>
          </ion-item>
        </ion-list>

        <div class="ion-padding-top">
          <ion-button expand="block" (click)="startQuiz()" [disabled]="!config.examId">
            Comenzar Juego
          </ion-button>
        </div>

        @if (loading) {
          <ion-text color="medium" class="ion-text-center">
            <p>Cargando exámenes...</p>
          </ion-text>
        }
      </ion-card-content>
    </ion-card>
  `,
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    IonCard, IonCardHeader, IonCardTitle, IonCardContent,
    IonItem, IonLabel, IonSelect, IonSelectOption,
    IonInput, IonToggle, IonButton, IonList, IonText
  ]
})
export class QuizSetupComponent implements OnInit {
  @Output() start = new EventEmitter<QuizConfig>();

  exams: Exam[] = [];
  loading = false;

  config: QuizConfig = {
    examId: '',
    lang: 'es',
    limit: 10,
    randomize: true
  };

  constructor(private quizService: QuizService) {}

  ngOnInit() {
    this.loading = true;
    this.quizService.getExams().subscribe({
      next: (data) => {
        this.exams = data;
        if (this.exams.length > 0) {
          this.config.examId = this.exams[0].id;
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading exams', err);
        this.loading = false;
      }
    });
  }

  startQuiz() {
    this.start.emit(this.config);
  }
}
