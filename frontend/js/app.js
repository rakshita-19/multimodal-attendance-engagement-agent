// Main Frontend Application Logic for Multimodal Classroom Intelligence Dashboard

const API_BASE = '/api';

class DashboardApp {
  constructor() {
    this.currentSessionId = null;
    this.currentReport = null;
    this.selectedVideoFile = null;
    this.selectedAudioFile = null;

    this.initElements();
    this.bindEvents();
    this.loadSessions();
  }

  initElements() {
    // Buttons & Inputs
    this.btnNewSession = document.getElementById('btn-new-session');
    this.btnLaunchDemo = document.getElementById('btn-launch-demo');
    this.btnUploadProcess = document.getElementById('btn-upload-process');
    this.sessionTitleInput = document.getElementById('session-title-input');
    this.sessionNotesInput = document.getElementById('session-notes-input');
    this.sessionsListEl = document.getElementById('sessions-list');

    // File inputs & dropzone labels
    this.videoFileInput = document.getElementById('video-file-input');
    this.audioFileInput = document.getElementById('audio-file-input');
    this.videoFilenameLabel = document.getElementById('selected-video-name');
    this.audioFilenameLabel = document.getElementById('selected-audio-name');

    // Export buttons
    this.btnExportAttendance = document.getElementById('btn-export-attendance');
    this.btnExportAnalytics = document.getElementById('btn-export-analytics');

    // Overview KPIs
    this.kpiAttendanceRate = document.getElementById('kpi-attendance-rate');
    this.kpiTotalTracked = document.getElementById('kpi-total-tracked');
    this.kpiEngagementScore = document.getElementById('kpi-engagement-score');
    this.kpiDominantMode = document.getElementById('kpi-dominant-mode');
    this.kpiSessionDuration = document.getElementById('kpi-session-duration');

    // Sections
    this.activeSessionTitle = document.getElementById('active-session-title');
    this.activeSessionStatus = document.getElementById('active-session-status');
    this.attendanceTableBody = document.getElementById('attendance-table-body');
    this.recommendationsContainer = document.getElementById('recommendations-container');
    this.ethicalBannerText = document.getElementById('ethical-banner-text');
    this.emptyStateEl = document.getElementById('dashboard-empty-state');
    this.mainContentEl = document.getElementById('dashboard-main-content');
    this.loadingIndicator = document.getElementById('loading-indicator');

    // Modal
    this.mappingModal = document.getElementById('mapping-modal');
    this.modalTrackIdInput = document.getElementById('modal-track-id');
    this.modalStudentNameInput = document.getElementById('modal-student-name');
    this.modalNotesInput = document.getElementById('modal-notes');
    this.btnSaveMapping = document.getElementById('btn-save-mapping');
    this.btnCloseModal = document.getElementById('btn-close-modal');
  }

  bindEvents() {
    // Launch Demo Session
    this.btnLaunchDemo.addEventListener('click', () => this.handleLaunchDemo());

    // Create New Session
    this.btnNewSession.addEventListener('click', () => this.handleCreateSession());

    // Upload & Process Media
    this.btnUploadProcess.addEventListener('click', () => this.handleUploadAndProcess());

    // File Selection listeners
    this.videoFileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.selectedVideoFile = e.target.files[0];
        this.videoFilenameLabel.textContent = `Selected: ${this.selectedVideoFile.name}`;
      }
    });

    this.audioFileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.selectedAudioFile = e.target.files[0];
        this.audioFilenameLabel.textContent = `Selected: ${this.selectedAudioFile.name}`;
      }
    });

    // CSV Exports
    this.btnExportAttendance.addEventListener('click', () => {
      if (!this.currentSessionId) return;
      window.location.href = `${API_BASE}/sessions/${this.currentSessionId}/export/attendance.csv`;
    });

    this.btnExportAnalytics.addEventListener('click', () => {
      if (!this.currentSessionId) return;
      window.location.href = `${API_BASE}/sessions/${this.currentSessionId}/export/analytics.csv`;
    });

    // Modal controls
    this.btnSaveMapping.addEventListener('click', () => this.handleSaveMapping());
    this.btnCloseModal.addEventListener('click', () => this.closeMappingModal());
    this.mappingModal.addEventListener('click', (e) => {
      if (e.target === this.mappingModal) this.closeMappingModal();
    });
  }

  // Load Sessions List
  async loadSessions() {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      const data = await res.json();
      if (data.status === 'success') {
        this.renderSessionList(data.sessions);
        if (data.sessions.length > 0 && !this.currentSessionId) {
          // Auto-select latest completed or first session
          const completed = data.sessions.find(s => s.status === 'completed') || data.sessions[0];
          this.selectSession(completed.id);
        }
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }

  renderSessionList(sessions) {
    this.sessionsListEl.innerHTML = '';
    if (sessions.length === 0) {
      this.sessionsListEl.innerHTML = '<div style="font-size:0.75rem; color:#64748b; padding:0.5rem;">No recorded sessions yet.</div>';
      return;
    }

    sessions.forEach(sess => {
      const div = document.createElement('div');
      div.className = `session-item ${sess.id === this.currentSessionId ? 'active' : ''}`;
      div.onclick = () => this.selectSession(sess.id);

      const statusBadge = `<span class="badge ${sess.status === 'completed' ? 'badge-present' : 'badge-partial'}">${sess.status}</span>`;

      div.innerHTML = `
        <div class="session-item-header">
          <div class="session-item-title">${this.escapeHtml(sess.title)}</div>
          ${statusBadge}
        </div>
        <div class="session-item-meta">
          ID: ${sess.id} • ${sess.duration_seconds ? sess.duration_seconds + 's' : '0s'}
        </div>
      `;
      this.sessionsListEl.appendChild(div);
    });
  }

  // Select and display session report
  async selectSession(sessionId) {
    this.currentSessionId = sessionId;
    this.showLoading(true);

    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}/analytics`);
      if (res.ok) {
        const data = await res.json();
        this.currentReport = data;
        this.renderDashboard(data);
      } else {
        // If not processed yet, fetch basic session info
        const sRes = await fetch(`${API_BASE}/sessions/${sessionId}`);
        const sData = await sRes.json();
        this.renderUnprocessedSession(sData.session);
      }
    } catch (err) {
      console.error('Error fetching session analytics:', err);
    } finally {
      this.showLoading(false);
      this.loadSessions();
    }
  }

  // Create new session
  async handleCreateSession() {
    const title = this.sessionTitleInput.value.trim() || 'New Classroom Session';
    const notes = this.sessionNotesInput.value.trim();

    try {
      const res = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, notes })
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.sessionTitleInput.value = '';
        this.sessionNotesInput.value = '';
        this.selectSession(data.session.id);
      }
    } catch (err) {
      alert('Failed to create session: ' + err.message);
    }
  }

  // One-Click Interactive Demo Lecture
  async handleLaunchDemo() {
    this.showLoading(true, 'Synthesizing 15s classroom video & audio and executing multimodal agent pipeline...');

    try {
      // 1. Create a demo session
      const createRes = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'CS401: Multimodal AI Demo Lecture',
          notes: 'Automated evaluation demo with 4 classroom participants, whiteboard lecture, and Q&A intervals.'
        })
      });
      const createData = await createRes.json();
      const sessId = createData.session.id;

      // 2. Run /process-demo
      const procRes = await fetch(`${API_BASE}/sessions/${sessId}/process-demo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const procData = await procRes.json();

      if (procData.status === 'success') {
        this.selectSession(sessId);
      } else {
        alert('Demo processing failed: ' + procData.message);
      }
    } catch (err) {
      alert('Error launching demo: ' + err.message);
    } finally {
      this.showLoading(false);
    }
  }

  // Upload and process user-provided video and audio
  async handleUploadAndProcess() {
    if (!this.selectedVideoFile && !this.selectedAudioFile) {
      alert('Please select at least one classroom video or audio file to upload.');
      return;
    }

    this.showLoading(true, 'Uploading media and running local multimodal intelligence pipeline...');

    try {
      // 1. Create session if none selected or if currently selected is completed
      let sessId = this.currentSessionId;
      if (!sessId || (this.currentReport && this.currentReport.session.status === 'completed')) {
        const createRes = await fetch(`${API_BASE}/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: this.sessionTitleInput.value.trim() || 'Custom Uploaded Session',
            notes: this.sessionNotesInput.value.trim()
          })
        });
        const createData = await createRes.json();
        sessId = createData.session.id;
      }

      // 2. Upload FormData
      const formData = new FormData();
      if (this.selectedVideoFile) formData.append('video', this.selectedVideoFile);
      if (this.selectedAudioFile) formData.append('audio', this.selectedAudioFile);

      const upRes = await fetch(`${API_BASE}/sessions/${sessId}/upload`, {
        method: 'POST',
        body: formData
      });
      const upData = await upRes.json();
      if (upData.status !== 'success') {
        throw new Error(upData.message || 'Upload failed');
      }

      // 3. Trigger processing
      const procRes = await fetch(`${API_BASE}/sessions/${sessId}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ min_presence_seconds: 5.0, window_size: 5.0 })
      });
      const procData = await procRes.json();
      if (procData.status !== 'success') {
        throw new Error(procData.message || 'Processing failed');
      }

      // Clear file inputs
      this.selectedVideoFile = null;
      this.selectedAudioFile = null;
      this.videoFilenameLabel.textContent = '';
      this.audioFilenameLabel.textContent = '';

      this.selectSession(sessId);
    } catch (err) {
      alert('Upload & Processing error: ' + err.message);
    } finally {
      this.showLoading(false);
    }
  }

  // Render processed dashboard
  renderDashboard(data) {
    this.emptyStateEl.style.display = 'none';
    this.mainContentEl.style.display = 'flex';

    const sess = data.session;
    this.activeSessionTitle.textContent = sess.title;
    this.activeSessionStatus.textContent = `Status: ${sess.status} • Duration: ${sess.duration_seconds}s`;

    // Overview KPIs
    const kpis = data.kpis || {};
    this.kpiAttendanceRate.textContent = `${kpis.attendance_rate_percentage || 0}%`;
    this.kpiTotalTracked.textContent = `${kpis.present_count || 0} / ${kpis.total_tracked || 0}`;

    // Compute average score from intervals
    const intervals = data.intervals || [];
    const avgScore = intervals.length > 0
      ? Math.round(intervals.reduce((acc, it) => acc + it.composite_engagement_score, 0) / intervals.length)
      : 0;
    this.kpiEngagementScore.textContent = `${avgScore} / 100`;

    // Dominant mode
    const modes = intervals.map(it => it.inferred_mode);
    const dominant = modes.length > 0 ? this.modeCounts(modes) : 'N/A';
    this.kpiDominantMode.textContent = dominant;
    this.kpiSessionDuration.textContent = `${sess.duration_seconds || 0}s`;

    // Render Charts
    if (window.dashboardCharts) {
      window.dashboardCharts.renderEngagementTimeline('chart-engagement-timeline', intervals);
      window.dashboardCharts.renderMultimodalSignals('chart-multimodal-signals', intervals);

      // Mode distribution
      const modeDist = this.computeModeDistribution(modes);
      window.dashboardCharts.renderModeDistribution('chart-mode-doughnut', modeDist);
    }

    // Render Attendance Table
    this.renderAttendanceTable(data.attendance || []);

    // Render Recommendations
    this.renderRecommendations(data.recommendations || []);

    // Render Student-Facing Ethical Summary
    if (data.student_summary) {
      this.ethicalBannerText.innerHTML = `
        <strong>${this.escapeHtml(data.student_summary.title)}</strong><br>
        ${this.escapeHtml(data.student_summary.cohort_attendance_note)}<br>
        <em>${this.escapeHtml(data.student_summary.dynamic_summary)}</em><br>
        <span style="font-size:0.72rem; color:#64748b; margin-top:4px; display:inline-block;">
          ${this.escapeHtml(data.student_summary.ethical_notice)}
        </span>
      `;
    }
  }

  renderAttendanceTable(records) {
    this.attendanceTableBody.innerHTML = '';
    if (records.length === 0) {
      this.attendanceTableBody.innerHTML = `
        <tr><td colspan="6" style="text-align:center; color:#64748b; padding:1.5rem;">
          No participant tracks recorded. Process a video or run the Interactive Demo.
        </td></tr>
      `;
      return;
    }

    records.forEach(r => {
      const tr = document.createElement('tr');
      const badgeClass = r.sustained_presence_status === 'present'
        ? 'badge-present'
        : (r.sustained_presence_status === 'partial' ? 'badge-partial' : 'badge-insufficient');

      const displayName = r.student_name ? `<strong>${this.escapeHtml(r.student_name)}</strong>` : '<em style="color:#64748b;">Unmapped</em>';

      tr.innerHTML = `
        <td><span class="badge badge-mode">Track #${r.track_id}</span></td>
        <td>${displayName}</td>
        <td><span class="badge ${badgeClass}">${r.sustained_presence_status}</span></td>
        <td>
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width:${Math.min(100, r.presence_percentage)}%;"></div>
            </div>
            <span>${r.presence_duration_seconds}s (${r.presence_percentage}%)</span>
          </div>
        </td>
        <td>Seen: ${r.first_seen_seconds}s - ${r.last_seen_seconds}s</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="window.app.openMappingModal(${r.track_id}, '${this.escapeHtml(r.student_name || '')}', '${this.escapeHtml(r.notes || '')}')">
            Review / Map
          </button>
        </td>
      `;
      this.attendanceTableBody.appendChild(tr);
    });
  }

  renderRecommendations(recs) {
    this.recommendationsContainer.innerHTML = '';
    if (recs.length === 0) {
      this.recommendationsContainer.innerHTML = '<div style="color:#64748b; font-size:0.85rem;">No pedagogical alerts for this session.</div>';
      return;
    }

    recs.forEach(rec => {
      const card = document.createElement('div');
      card.className = `rec-card ${rec.priority}`;
      card.innerHTML = `
        <div class="rec-header">
          <span class="rec-category">${rec.category} • ${rec.timestamp_reference || 'Session'}</span>
          <span class="badge ${rec.priority === 'high' ? 'badge-insufficient' : (rec.priority === 'medium' ? 'badge-partial' : 'badge-mode')}">${rec.priority.toUpperCase()}</span>
        </div>
        <div class="rec-suggestion">${this.escapeHtml(rec.suggestion_text)}</div>
        <div class="rec-evidence"><strong>Evidence:</strong> ${this.escapeHtml(rec.evidence_text)}</div>
      `;
      this.recommendationsContainer.appendChild(card);
    });
  }

  renderUnprocessedSession(sess) {
    this.emptyStateEl.style.display = 'block';
    this.mainContentEl.style.display = 'none';
    this.emptyStateEl.innerHTML = `
      <div class="empty-state-icon">📹</div>
      <h3>${this.escapeHtml(sess.title)}</h3>
      <p style="margin-top:0.5rem; font-size:0.85rem;">Status: <strong>${sess.status}</strong>. Please upload video/audio media or click "Launch Demo Session".</p>
    `;
  }

  // Teacher Review & Name Mapping Modal
  openMappingModal(trackId, currentName, currentNotes) {
    this.modalTrackIdInput.value = trackId;
    this.modalStudentNameInput.value = currentName === 'null' ? '' : currentName;
    this.modalNotesInput.value = currentNotes === 'null' ? '' : currentNotes;
    this.mappingModal.classList.add('active');
  }

  closeMappingModal() {
    this.mappingModal.classList.remove('active');
  }

  async handleSaveMapping() {
    const trackId = this.modalTrackIdInput.value;
    const studentName = this.modalStudentNameInput.value.trim();
    const notes = this.modalNotesInput.value.trim();

    if (!studentName) {
      alert('Please provide a student name.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/sessions/${this.currentSessionId}/attendance/${trackId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_name: studentName, notes: notes })
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.closeMappingModal();
        this.selectSession(this.currentSessionId);
      } else {
        alert('Failed to update student identity: ' + data.message);
      }
    } catch (err) {
      alert('Error updating mapping: ' + err.message);
    }
  }

  // Helper Utilities
  modeCounts(modes) {
    const counts = {};
    modes.forEach(m => counts[m] = (counts[m] || 0) + 1);
    return Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
  }

  computeModeDistribution(modes) {
    const counts = {};
    modes.forEach(m => counts[m] = (counts[m] || 0) + 1);
    const total = modes.length || 1;
    const dist = {};
    Object.keys(counts).forEach(k => {
      dist[k] = Math.round((counts[k] / total) * 100);
    });
    return dist;
  }

  showLoading(show, message = 'Processing...') {
    if (show) {
      this.loadingIndicator.style.display = 'flex';
      this.loadingIndicator.querySelector('.loading-msg').textContent = message;
    } else {
      this.loadingIndicator.style.display = 'none';
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new DashboardApp();
});
