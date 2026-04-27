import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';

import { UnitSummary, UnitNav } from '../../models/exercise.models';
import { environment } from '../../../environments/environment.development';

@Injectable({
  providedIn: 'root',
})
export class NavigationInformationService {

  // cache simple pour éviter de refaire les mêmes appels API
  private UnitId: number | null = null;
  private Structure: UnitNav | null = null;
  private DashboardList: UnitSummary[] | null = null;

  constructor(private http: HttpClient) {}

  // récupère les unités depuis le backend
  // le backend sait qui est connecté grâce au token JWT
  getDashboardUnits(): Observable<UnitSummary[]> {
    if (this.DashboardList) {
      return of(this.DashboardList);
    }

    return this.http.get<UnitSummary[]>(`${environment.apiUrl}units`).pipe(
      tap((data) => {
        this.DashboardList = data;
      })
    );
  }

  // récupère les cours + exercices d'une unité
  // plus besoin de user_id dans l'URL, le token suffit
  getUnitStructure(unitId: number): Observable<UnitNav> {
    if (this.Structure && this.UnitId === unitId) {
      console.log('Data from cache');
      return of(this.Structure);
    }

    return this.http.get<UnitNav>(`${environment.apiUrl}unit/${unitId}/courses`).pipe(
      tap((data) => {
        this.UnitId = unitId;
        this.Structure = data;
      })
    );
  }

  // vide seulement le cache de l'unité
  clearUnitCache(): void {
    this.UnitId = null;
    this.Structure = null;
  }

  // vide tout le cache après ajout/suppression/modif
  clearAllCache(): void {
    this.UnitId = null;
    this.Structure = null;
    this.DashboardList = null;
  }
}