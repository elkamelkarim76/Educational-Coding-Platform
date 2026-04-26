import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';

export interface ExerciseStatApi {
  id: number;
  name: string;
  courseName: string;
  unitName: string;
  lang: string;
  attempts: number;
  success: number;
  avgTry: number;
  hints: number;
}

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  constructor(private http: HttpClient) {}

  getExerciseStats(): Observable<ExerciseStatApi[]> {
    return this.http.get<ExerciseStatApi[]>(
      `${environment.apiUrl}analytics/exercises`
    );
  }
}