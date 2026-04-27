import { Routes } from '@angular/router';

import { Dashboard } from './pages/dashboard/dashboard';
import { ExerciseCreate } from './pages/exercise-create/exercise-create';
import { ExerciseRun } from './pages/exercise-run/exercise-run';
import { UnitInfo } from './pages/unit-info/unit-info';
import { Login } from './pages/login/login';
import { Analytics } from './pages/analytics/analytics';

import { authGuard } from './guards/auth-guard';
import { teacherGuard } from './guards/teacher-guard';

export const routes: Routes = [
  // page login
  { path: 'login', component: Login },

  // dashboard (auth obligatoire)
  { path: 'dashboard', component: Dashboard, canActivate: [authGuard] },

  // analytics (auth aussi)
  { path: 'analytics', component: Analytics, canActivate: [authGuard] },

  // create exercise (prof seulement)
  {
    path: 'exercise-create/:unitId/:courseId',
    component: ExerciseCreate,
    canActivate: [authGuard, teacherGuard],
  },

  // edit exercise (prof seulement)
  {
    path: 'exercise-edit/:unitId/:courseId/:exerciseId',
    component: ExerciseCreate,
    canActivate: [authGuard, teacherGuard],
  },

  // page unité
  { path: 'unit/:unitId', component: UnitInfo, canActivate: [authGuard] },

  // execution exercice (student)
  {
    path: 'unit/:unitId/course/:courseId/exercise/:exerciseId',
    component: ExerciseRun,
    canActivate: [authGuard],
  },

  // redirections
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' },
];