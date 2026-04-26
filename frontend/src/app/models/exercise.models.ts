//Type of a hint sent to the backend 
export interface Hint{
  id ?: number; 
  body: string;
  unlock_after_attempts: number;
  position: number;
}

export interface HintDisplay extends Hint {
  isRevealed: boolean; 
}

export interface Test {
  id ?: number;
  argv: string;
  expected_output: string;
  comment: string;
  position: number;
}

export interface TestDisplay extends Test {
  actualOutput?: string;  // Student output
  status: 'pending' | 'success' | 'failure'; 
} 

export interface File {
  id ?: number;
  name: string;
  content: string;
  extension: string;
  is_main: boolean;
  editable: boolean;
  position: number;
}

export interface Exercise {
  course_id: number;
  name: string;
  description: string;
  visibility: string;
  language: string; 
  difficulty: number;
  position: number;
  
  files: File[];
  tests: Test[];
  hints: Hint[];
}

// Full exercise update (replaces files, tests, hints entirely)
export interface ExerciseFull extends Exercise {
  id: number;
}

//

export interface CodePayload {
  files: File[];
  language: string;
}

export interface TestRunPayload extends CodePayload{
  argv: string;
}

export interface StudentSubmissionPayload extends CodePayload{
  user_id : number; 
}

// Respond from the back

export interface ApiResponse<T> {
  status: boolean;
  message: string;
  data: T;
}

export interface RunResponse {
  stdout: string;
  stderr: string;
  exit_code: number;
}

export interface TestRespond {
  id: number;
  actual_output: string;  // Student output
  status: 'pending' | 'success' | 'failure';
  error_log: string;
}

// Structure of error response data from the backend when a student do an exercise.

export interface ErrorResponseData {
  format_error?: string;
  stderr?: string;
  exit_code?: number;
}

export interface TestRespondList {
  test_responses: TestRespond[];
}

// EDITOR CONFIGURATION 

export interface EditorConfig {
  canAddFiles: boolean;
  canDeleteFiles: boolean;
  canRenameFiles: boolean;
  canCompile: boolean;
  canTest: boolean; // Button "Test" to test the user code with the exercise test (written by the teacher)
  canEditStructure: boolean; // Allow to change main and editable for a file
  respectEditableFlag: boolean; // If true, files that are readonly will be in the editor
}

export const STUDENT_CONFIG: EditorConfig = {
  canAddFiles: false,
  canDeleteFiles: false,
  canRenameFiles: false,
  canCompile: false,
  canTest: true,
  canEditStructure: false,
  respectEditableFlag: true
};

export const TEACHER_CONFIG: EditorConfig = {
  canAddFiles: true,
  canDeleteFiles: true,
  canRenameFiles: true,
  canCompile: true,
  canTest: false,
  canEditStructure: true,
  respectEditableFlag: false
};

// Light information about an exercise, course or unit 


//Commun base for exercise, course and unit

export interface BaseNav {
  id: number;
  name: string;
  description: string;
  visibility: string;
  difficulty: number; 
  author_id: number;
}

// # Ligth information of an exercice (without his files, etc...)
export interface ExerciseNav extends BaseNav {
  position: number;
  //  Can be good in the futur to add attemps count or other info 
}

export interface CourseNav extends BaseNav {
  position: number;
  exercises: ExerciseNav[]; 
}

export interface UnitNav extends BaseNav {
  courses: CourseNav[]; 
}

// Ligth information of all the unit a student need to do
export interface UnitSummary extends BaseNav {
  // No new information, just for the readability of the type
}

export interface CourseCreatePayload {
  name: string;
  description: string;
  difficulty: number;
  visibility: string;
  unit_id: number;
}

// Unit

export interface UnitCreatePayload {
  name: string;
  description: string;
  difficulty: number;
  visibility: string;
}

export interface UnitUpdatePayload {
  name?: string;
  description?: string;
  difficulty?: number;
  visibility?: string;
}

export interface CourseUpdatePayload {
  name?: string;
  description?: string;
  difficulty?: number;
  visibility?: string;
}



