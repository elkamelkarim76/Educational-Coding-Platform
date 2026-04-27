import { ComponentFixture, TestBed } from '@angular/core/testing';

/// <reference types="jest" />

import { CourseDisplay } from './course-display';

describe('CourseDisplay', () => {
  let component: CourseDisplay;
  let fixture: ComponentFixture<CourseDisplay>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CourseDisplay]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CourseDisplay);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
