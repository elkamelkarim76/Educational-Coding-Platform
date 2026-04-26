import { Routes } from '@angular/router';

import { Dashboard } from './pages/dashboard/dashboard';
import { ExerciseCreate } from './pages/exercise-create/exercise-create';
import { ExerciseRun } from './pages/exercise-run/exercise-run';
import { UnitInfo } from './pages/unit-info/unit-info';
import { Login } from './pages/login/login';

import { authGuard } from './guards/auth-guard';
import { teacherGuard } from './guards/teacher-guard';

export const routes: Routes = [
  { path: 'login', component: Login },

  { path: 'dashboard', component: Dashboard, canActivate: [authGuard] },

  {
    path: 'exercise-create/:unitId/:courseId',
    component: ExerciseCreate,
    canActivate: [authGuard, teacherGuard],
  },

  {
    path: 'exercise-edit/:unitId/:courseId/:exerciseId',
    component: ExerciseCreate,
    canActivate: [authGuard, teacherGuard],
  },

  { path: 'unit/:unitId', component: UnitInfo, canActivate: [authGuard] },

  {
    path: 'unit/:unitId/course/:courseId/exercise/:exerciseId',
    component: ExerciseRun,
    canActivate: [authGuard],
  },

  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' },
];