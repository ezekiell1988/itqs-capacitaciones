import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Option {
  letra: string;
  texto: string;
  es_correcta: boolean;
}

export interface Question {
  numero: string;
  pregunta: string;
  opciones: Option[];
  respuesta_correcta: string;
  explicacion: string;
  userSelected?: string; // Para guardar la respuesta del usuario
}

export interface Exam {
  id: string;
  name: string;
}

@Injectable({
  providedIn: 'root'
})
export class QuizService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  checkHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  getExams(): Observable<Exam[]> {
    return this.http.get<Exam[]>(`${this.apiUrl}/exams`);
  }

  getQuestions(examId: string, lang: string, limit: number, randomize: boolean): Observable<Question[]> {
    let params = new HttpParams()
      .set('lang', lang)
      .set('limit', limit.toString())
      .set('randomize', randomize.toString());

    return this.http.get<Question[]>(`${this.apiUrl}/questions/${examId}`, { params });
  }
}
