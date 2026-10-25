// Chart.js visualization wrappers for Multimodal Classroom Intelligence Dashboard

class DashboardCharts {
  constructor() {
    this.engagementChart = null;
    this.signalsChart = null;
    this.modesChart = null;
  }

  // Format seconds to MM:SS string
  formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  // 1. Multimodal Engagement Timeline (Line + Area)
  renderEngagementTimeline(canvasId, intervals) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.engagementChart) {
      this.engagementChart.destroy();
    }

    if (!intervals || intervals.length === 0) {
      return;
    }

    const labels = intervals.map(it => this.formatTime(it.start_seconds));
    const scores = intervals.map(it => it.composite_engagement_score);
    const modes = intervals.map(it => it.inferred_mode);

    this.engagementChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Composite Engagement Score (0 - 100)',
          data: scores,
          borderColor: '#4f46e5',
          backgroundColor: 'rgba(79, 70, 229, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#4f46e5',
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const idx = context.dataIndex;
                return `Mode: ${modes[idx]}\nRule: ${intervals[idx].rule_applied}`;
              }
            }
          }
        },
        scales: {
          y: {
            min: 0,
            max: 100,
            grid: { color: '#f1f5f9' },
            ticks: {
              callback: val => val + ' pts'
            }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // 2. Headcount & Acoustic Signal Alignment (Dual Axis)
  renderMultimodalSignals(canvasId, intervals) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.signalsChart) {
      this.signalsChart.destroy();
    }

    if (!intervals || intervals.length === 0) {
      return;
    }

    const labels = intervals.map(it => this.formatTime(it.start_seconds));
    const headcount = intervals.map(it => it.visible_participants);
    const speech = intervals.map(it => Math.round(it.speech_activity_ratio * 100));
    const motion = intervals.map(it => Math.round(it.motion_intensity * 100));

    this.signalsChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'bar',
            label: 'Headcount (Attendees)',
            data: headcount,
            backgroundColor: 'rgba(14, 165, 233, 0.45)',
            borderColor: '#0ea5e9',
            borderWidth: 1.5,
            yAxisID: 'y'
          },
          {
            type: 'line',
            label: 'Speech Activity (%)',
            data: speech,
            borderColor: '#10b981',
            backgroundColor: 'transparent',
            tension: 0.3,
            borderWidth: 2,
            yAxisID: 'y1'
          },
          {
            type: 'line',
            label: 'Motion Intensity (%)',
            data: motion,
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            tension: 0.3,
            borderWidth: 2,
            borderDash: [4, 4],
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
        },
        scales: {
          y: {
            type: 'linear',
            position: 'left',
            beginAtZero: true,
            ticks: { precision: 0 },
            title: { display: true, text: 'Visible Attendees' },
            grid: { color: '#f1f5f9' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 100,
            grid: { drawOnChartArea: false },
            title: { display: true, text: 'Signal Ratio (%)' }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 3. Interaction Mode Distribution (Doughnut)
  renderModeDistribution(canvasId, modeDistribution) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.modesChart) {
      this.modesChart.destroy();
    }

    if (!modeDistribution || Object.keys(modeDistribution).length === 0) {
      return;
    }

    const labels = Object.keys(modeDistribution);
    const data = Object.values(modeDistribution);

    // Color mapping by dynamic mode
    const colorMap = {
      'Active Discussion': '#4f46e5',
      'Attentive Listening / Lecture': '#0ea5e9',
      'Collaborative Group Work': '#10b981',
      'Passive / Lull': '#f59e0b',
      'Transition / Restlessness': '#f43f5e'
    };

    const bgColors = labels.map(l => colorMap[l] || '#94a3b8');

    this.modesChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: bgColors,
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } },
          tooltip: {
            callbacks: {
              label: context => ` ${context.label}: ${context.raw}%`
            }
          }
        },
        cutout: '65%'
      }
    });
  }
}

window.dashboardCharts = new DashboardCharts();
