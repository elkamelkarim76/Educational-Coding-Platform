import { Component, Input, numberAttribute, SimpleChanges} from '@angular/core';
import { finalize } from 'rxjs/operators'

import { FormsModule } from '@angular/forms';
import { Editor} from '../../components/editor/editor';
import { Console } from '../../components/console/console';
import { TestsDisplay } from '../../components/testsDisplay/tests-display/tests-display';
import { ExerciceStudentService } from '../../services/exerciseStudentService/exercise-student-service';
import { NavigationInformationService } from '../../services/navigationInformation/navigation-information-service';
import { EditorConfig, STUDENT_CONFIG, Exercise, File, Hint, TestDisplay, StudentSubmissionPayload, UnitNav, TestRespondList } from '../../models/exercise.models';
import { HintsDisplay } from '../../components/hintsDisplay/hints-display/hints-display';
import { SideBar } from '../../components/side-bar/side-bar';
import { Chat } from '../../components/chat/chat';
import { appendConsoleMessage } from '../../utils/utils';

@Component({
  selector: 'app-exercise-run',
  imports: [FormsModule, Editor, Console, TestsDisplay, HintsDisplay, SideBar, Chat],
  templateUrl: './exercise-run.html',
  styleUrl: './exercise-run.css',
})
export class ExerciseRun {
  @Input({ transform: numberAttribute }) unitId!: number;
  @Input({ transform: numberAttribute }) courseId!: number;
  @Input({ transform: numberAttribute }) exerciseId!: number;

  options : EditorConfig = STUDENT_CONFIG;
  consoleText = '';

  exerciseData!: Exercise; 
  files : File[] = [];
  tests: TestDisplay[] = [];  
  hints: Hint[] = [];

  description: string = "";
  language: string = "";
  activeTab: string = 'console';
  attemptsCount = 0;
  isSubmitting = false;

  unitNavigation: UnitNav | null = null;

  constructor(
    private exerciseStudentService: ExerciceStudentService,
    private navigationInformation: NavigationInformationService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['exerciseId'] && this.exerciseId) {
        this.fetchExercise(this.unitId, this.courseId, this.exerciseId);
    }
    if (changes['unitId'] && this.unitId) {
        this.fetchSidebarContent(this.unitId);
    }
  }

  private fetchSidebarContent(unitId: number): void {
      this.navigationInformation.getUnitStructure(unitId).subscribe({
          next: (navData: UnitNav) => {
              this.unitNavigation = navData;
              this.onConsoleMessage(this.unitNavigation.name)
          },
          error: (err: any) => console.error('Failed to load sidebar navigation', err)
      });
  }

  private fetchExercise(UnitId: number, CourseId: number, ExerciseId: number): void {
    this.resetExerciseState();
    this.exerciseStudentService.getExerciseForStudent(UnitId, CourseId, ExerciseId).pipe(
      finalize(() => {})
    ).subscribe({
      next: (data: any) => {
        this.exerciseData = data;
        this.files = data.files;
        this.tests = data.tests.map((t: any) => ({ ...t, status: 'pending' as const }));
        this.hints = data.hints;
        this.description = data.description;
        this.language = data.language;
      },
      error: (err: any) => console.error('Failed to load exercise', err)
    });
  }

  private resetExerciseState(): void {
    this.files = [];
    this.tests = [];
    this.hints = [];
    this.description = '';
    this.consoleText = '';
    this.attemptsCount = 0;
  }

  onConsoleMessage(message: string): void {
    this.consoleText = appendConsoleMessage(this.consoleText, message);
  }

  onFilesChange(updatedFiles: File[]): void {
    this.files = updatedFiles;
  }

  onSubmitStudentCode(): void {
    if (this.isSubmitting) return;
    this.isSubmitting = true;

    const payload: StudentSubmissionPayload = {
      files: this.files,
      language: this.language,
      user_id: 1
    };

    this.exerciseStudentService.sendExerciseStudent(this.unitId, this.courseId, this.exerciseId, payload).pipe(
      finalize(() => { this.isSubmitting = false; })
    ).subscribe({
      next: (results: any) => {
        this.attemptsCount++;
        this.tests = results.test_results.map((r: any) => ({
          ...r.test_case,
          actualOutput: r.actual_output,
          status: r.status
        }));
        this.setActiveTab('tests');
      },
      error: (err: any) => {
        this.onConsoleMessage('Erreur lors de la soumission.');
        console.error(err);
      }
    });
  }

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }
}
