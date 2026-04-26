import { Component, OnInit, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';
import { NavigationInformationService } from '../../services/navigationInformation/navigation-information-service';
import { AnalyticsService } from '../../services/analyticsService/analytics.service';

Chart.register(...registerables);

interface ExerciseStat {
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

interface DailyStat {
  label: string;
  success: number;
  failure: number;
}

@Component({
  selector: 'app-analytics',
  imports: [RouterLink, CommonModule, FormsModule],
  templateUrl: './analytics.html',
  styleUrl: './analytics.css',
})
export class Analytics implements OnInit, AfterViewInit {

  @ViewChild('chartLine')  chartLineRef!:  ElementRef<HTMLCanvasElement>;
  @ViewChild('chartDonut') chartDonutRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('chartBar')   chartBarRef!:   ElementRef<HTMLCanvasElement>;

  // Derived stats
  allExercises: ExerciseStat[] = [];
  filteredExercises: ExerciseStat[] = [];
  dailyStats: DailyStat[] = [];

  // Metrics
  totalStudents    = 0;
  totalSubmissions = 0;
  successRate      = 0;
  avgAttempts      = 0;

  // Filter
  selectedLang = 'all';

  // Chart instances
  private lineChart:  Chart | null = null;
  private donutChart: Chart | null = null;
  private barChart:   Chart | null = null;

  private chartsReady = false;
  private dataReady   = false;

  isLoading = true;

  constructor(
    private navigationService: NavigationInformationService,
    private analyticsService: AnalyticsService
  ) {}

  ngOnInit(): void {
    this.buildMockDailyStats();
    this.loadRealStats();
  }

  ngAfterViewInit(): void {
    this.chartsReady = true;
    if (this.dataReady) this.renderCharts();
  }

  // ── Data loading ────────────────────────────────────────────────

  private loadRealStats(): void {
    this.analyticsService.getExerciseStats().subscribe({
      next: (stats) => {
        this.allExercises = stats;
        this.applyFilter();
        this.isLoading = false;
        this.dataReady = true;
        if (this.chartsReady) this.renderCharts();
      },
      error: () => { this.isLoading = false; }
    });
  }

  private buildMockDailyStats(): void {
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const label = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
      const seed  = d.getDate() + d.getMonth() * 5;
      this.dailyStats.push({ label, success: 8 + (seed % 18), failure: 3 + (seed % 11) });
    }
  }

  // ── Filtering ────────────────────────────────────────────────────

  // CORRECTIF : filterData() appelait throw new Error(...) — maintenant il délègue à applyFilter()
  filterData(): void {
    this.applyFilter();
  }

  applyFilter(): void {
    this.filteredExercises = this.selectedLang === 'all'
      ? [...this.allExercises]
      : this.allExercises.filter(e => e.lang === this.selectedLang);

    const total = this.filteredExercises.reduce((a, e) => a + e.attempts, 0);
    const ok    = this.filteredExercises.reduce((a, e) => a + e.success,  0);

    this.totalSubmissions = total;
    this.successRate      = total > 0 ? Math.round(ok / total * 100) : 0;
    this.avgAttempts      = this.filteredExercises.length > 0
      ? parseFloat((this.filteredExercises.reduce((a, e) => a + e.avgTry, 0) / this.filteredExercises.length).toFixed(1))
      : 0;
    this.totalStudents = this.allExercises.length > 0 ? Math.max(1, Math.round(total / 3)) : 0;

    if (this.chartsReady) this.renderCharts();
  }

  // ── Chart rendering ──────────────────────────────────────────────

  private renderCharts(): void {
    this.renderLineChart();
    this.renderDonutChart();
    this.renderBarChart();
  }

  private renderLineChart(): void {
    if (this.lineChart) { this.lineChart.destroy(); }
    const ctx = this.chartLineRef?.nativeElement;
    if (!ctx) return;
    this.lineChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.dailyStats.map(d => d.label),
        datasets: [
          { label: 'Succès', data: this.dailyStats.map(d => d.success),
            borderColor: '#22c55e', backgroundColor: '#22c55e20', fill: true,
            tension: 0.35, pointRadius: 0, borderWidth: 2 },
          { label: 'Échecs', data: this.dailyStats.map(d => d.failure),
            borderColor: '#ef4444', backgroundColor: '#ef444415', fill: true,
            tension: 0.35, pointRadius: 0, borderWidth: 2, borderDash: [4, 3] },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
        scales: {
          x: { ticks: { autoSkip: true, maxRotation: 0, maxTicksLimit: 8, font: { size: 10 }, color: '#9ca3af' }, grid: { display: false } },
          y: { ticks: { font: { size: 10 }, color: '#9ca3af' }, grid: { color: 'rgba(156,163,175,0.15)' } }
        }
      }
    });
  }

  private renderDonutChart(): void {
    if (this.donutChart) { this.donutChart.destroy(); }
    const ctx = this.chartDonutRef?.nativeElement;
    if (!ctx) return;
    const cCount = this.allExercises.filter(e => e.lang === 'c').reduce((a, e) => a + e.attempts, 0);
    const jCount = this.allExercises.filter(e => e.lang === 'java').reduce((a, e) => a + e.attempts, 0);
    const pCount = this.allExercises.filter(e => e.lang === 'python').reduce((a, e) => a + e.attempts, 0);
    this.donutChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['C', 'Java', 'Python'],
        datasets: [{ data: [cCount || 1, jCount || 1, pCount || 1],
          backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'], borderWidth: 0 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '70%',
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx: any) => ` ${ctx.label}: ${ctx.parsed}` } }
        }
      }
    });
  }

  private renderBarChart(): void {
    if (this.barChart) { this.barChart.destroy(); }
    const ctx = this.chartBarRef?.nativeElement;
    if (!ctx) return;
    const hard = [...this.filteredExercises]
      .sort((a, b) => (a.success / (a.attempts || 1)) - (b.success / (b.attempts || 1)))
      .slice(0, 5);
    const rates   = hard.map(e => Math.round(e.success / (e.attempts || 1) * 100));
    const colors  = rates.map(r => r >= 70 ? '#22c55e44' : r >= 45 ? '#f59e0b44' : '#ef444444');
    const borders = rates.map(r => r >= 70 ? '#22c55e'   : r >= 45 ? '#f59e0b'   : '#ef4444');
    this.barChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: hard.map(e => e.name.length > 18 ? e.name.slice(0, 16) + '…' : e.name),
        datasets: [{ label: 'Réussite (%)', data: rates,
          backgroundColor: colors, borderColor: borders, borderWidth: 1.5, borderRadius: 4 }]
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { max: 100, ticks: { callback: (v: any) => v + '%', font: { size: 10 }, color: '#9ca3af' }, grid: { color: 'rgba(156,163,175,0.15)' } },
          y: { ticks: { font: { size: 11 }, color: '#9ca3af' }, grid: { display: false } }
        }
      }
    });
  }

  // ── Helpers for template ─────────────────────────────────────────

  getRate(ex: ExerciseStat): number {
    return ex.attempts > 0 ? Math.round(ex.success / ex.attempts * 100) : 0;
  }

  getStatusClass(rate: number): string {
    if (rate >= 70) return 'badge-ok';
    if (rate >= 45) return 'badge-mid';
    return 'badge-bad';
  }

  getStatusLabel(rate: number): string {
    if (rate >= 70) return 'Facile';
    if (rate >= 45) return 'Moyen';
    return 'Difficile';
  }

  getLangColor(lang: string): string {
    const map: Record<string, string> = { c: '#3b82f6', java: '#10b981', python: '#f59e0b' };
    return map[lang] || '#6b7280';
  }

  getHardest(): ExerciseStat[] {
    return [...this.filteredExercises]
      .sort((a, b) => (a.success / (a.attempts || 1)) - (b.success / (b.attempts || 1)))
      .slice(0, 6);
  }

  getMaxHints(): number {
    return Math.max(...this.filteredExercises.map(e => e.hints), 1);
  }

  getLangStats(): { lang: string; label: string; count: number; color: string }[] {
    const all = this.filteredExercises;
    return [
      { lang: 'c',      label: 'C',      count: all.filter(e => e.lang === 'c').reduce((a, e) => a + e.attempts, 0),      color: '#3b82f6' },
      { lang: 'java',   label: 'Java',   count: all.filter(e => e.lang === 'java').reduce((a, e) => a + e.attempts, 0),   color: '#10b981' },
      { lang: 'python', label: 'Python', count: all.filter(e => e.lang === 'python').reduce((a, e) => a + e.attempts, 0), color: '#f59e0b' },
    ];
  }
}