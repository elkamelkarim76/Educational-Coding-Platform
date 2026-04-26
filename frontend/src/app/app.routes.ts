import { Routes } from '@angular/router';
import { Dashboard } from './pages/dashboard/dashboard';
import { ExerciseCreate } from './pages/exercise-create/exercise-create';
import { ExerciseRun } from './pages/exercise-run/exercise-run';
import { UnitInfo } from './pages/unit-info/unit-info';
import { Analytics } from './pages/analytics/analytics';

export const routes: Routes = [
    { path: 'dashboard', component: Dashboard },
    { path: 'analytics', component: Analytics },
    { path: 'exercise-create/:unitId/:courseId', component: ExerciseCreate },
    { path: 'exercise-edit/:unitId/:courseId/:exerciseId', component: ExerciseCreate },
    { path: 'unit/:unitId', component: UnitInfo },
    { path: 'unit/:unitId/course/:courseId/exercise/:exerciseId', component: ExerciseRun },
    { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
    { path: '**', redirectTo: '/dashboard' }
];
