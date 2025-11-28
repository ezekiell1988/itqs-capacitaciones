import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonContent, IonSpinner, IonToast } from '@ionic/angular/standalone';
import { HeaderComponent } from '../components/header/header.component';
import { QuizSetupComponent, QuizConfig } from './quiz-setup/quiz-setup.component';
import { QuizGameComponent } from './quiz-game/quiz-game.component';
import { QuizResultsComponent } from './quiz-results/quiz-results.component';
import { QuizService, Question } from '../services/quiz.service';

type GameState = 'setup' | 'playing' | 'results';

@Component({
  selector: 'app-home',
  template: `
    <app-header title="ITQS Capacitaciones"></app-header>

    <ion-content class="ion-padding">
      @if (loading) {
        <div class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Cargando preguntas...</p>
        </div>
      }

      @switch (gameState) {
        @case ('setup') {
          <app-quiz-setup (start)="onStartGame($event)"></app-quiz-setup>
        }
        @case ('playing') {
          <app-quiz-game
            [questions]="questions"
            (finish)="onFinishGame($event)">
          </app-quiz-game>
        }
        @case ('results') {
          <app-quiz-results
            [questions]="questions"
            (restart)="onRestart()">
          </app-quiz-results>
        }
      }

      <ion-toast
        [isOpen]="!!errorMessage"
        [message]="errorMessage"
        [duration]="3000"
        color="danger"
        (didDismiss)="errorMessage = ''">
      </ion-toast>
    </ion-content>
  `,
  styles: [`
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
    }
  `],
  standalone: true,
  imports: [
    CommonModule,
    IonContent, IonSpinner, IonToast,
    HeaderComponent,
    QuizSetupComponent,
    QuizGameComponent,
    QuizResultsComponent
  ]
})
export class HomePage {
  gameState: GameState = 'setup';
  questions: Question[] = [];
  loading = false;
  errorMessage = '';

  constructor(private quizService: QuizService) {}

  onStartGame(config: QuizConfig) {
    this.loading = true;
    this.quizService.getQuestions(config.examId, config.lang, config.limit, config.randomize)
      .subscribe({
        next: (data) => {
          this.questions = data;
          this.loading = false;
          if (this.questions.length > 0) {
            this.gameState = 'playing';
          } else {
            this.errorMessage = 'No se encontraron preguntas para esta configuración.';
          }
        },
        error: (err) => {
          console.error(err);
          this.loading = false;
          this.errorMessage = 'Error al cargar las preguntas. Asegúrate de que el servidor backend esté corriendo.';
        }
      });
  }

  onFinishGame(questionsWithAnswers: Question[]) {
    this.questions = questionsWithAnswers;
    this.gameState = 'results';
  }

  onRestart() {
    this.questions = [];
    this.gameState = 'setup';
  }
}
