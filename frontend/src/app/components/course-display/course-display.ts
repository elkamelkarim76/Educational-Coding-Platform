import { Component, Input, Output, EventEmitter } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { CourseNav, CourseUpdatePayload } from '../../models/exercise.models';
import { validateEntityForm } from '../../utils/utils';

@Component({
  selector: 'app-course-display',
  imports: [RouterLink, FormsModule, ReactiveFormsModule, CommonModule],
  templateUrl: './course-display.html',
  styleUrl: './course-display.css',
})
export class CourseDisplay {
  @Input() courses: CourseNav[] = [];
  @Input() unitId!: number;

  @Output() deleteCourseRequest = new EventEmitter<number>();
  @Output() deleteExerciseRequest = new EventEmitter<{courseId: number, exerciseId: number}>();
  @Output() updateCourseRequest = new EventEmitter<{courseId: number, payload: CourseUpdatePayload}>();

  // Course edit state
  editingCourseId: number | null = null;
  editedCourse = {
    name: '',
    description: '',
    difficulty: 1,
    visibility: 'private'
  };

  errorMessage = '';

  onDeleteClick(courseId: number) {
    // "confirm" function will open a pop up and "ask" a question to the user
    if (confirm('Voulez-vous vraiment supprimer ce cours et tous ses exercices ?')) {
      this.deleteCourseRequest.emit(courseId);
    }
  }

  onDeleteExerciseClick(courseId: number, exerciseId: number, event: Event) {
    // Don' allow the click to propagate 
    event.preventDefault();
    event.stopPropagation();

    if (confirm('Voulez-vous vraiment supprimer cet exercice ?')) {
      this.deleteExerciseRequest.emit({ courseId, exerciseId });
    }
  }

  // Course Edit Methods
  startEditingCourse(course: CourseNav, event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.editingCourseId = course.id;
    this.editedCourse = {
      name: course.name,
      description: course.description,
      difficulty: course.difficulty,
      visibility: course.visibility
    };
  }

  cancelEditingCourse(): void {
    this.editingCourseId = null;
    this.errorMessage = '';
  }

  saveCourseChanges(courseId: number): void {
    this.errorMessage = '';

    const validationError = validateEntityForm(this.editedCourse);
    if (validationError) {
      this.errorMessage = validationError;
      return;
    }

    this.updateCourseRequest.emit({
      courseId,
      payload: { ...this.editedCourse }
    });
    this.editingCourseId = null;
  }
}
