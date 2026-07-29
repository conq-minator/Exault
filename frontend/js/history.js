/**
 * ExcelPlorer — Session History Controller
 */

const HistoryController = {
    async loadHistory() {
        const container = document.getElementById('history-list');
        if (!container) return;
        
        try {
            const data = await API.getSessions();
            this.render(data.sessions);
        } catch (error) {
            container.innerHTML = `<div style="padding:1rem; color:var(--status-error); font-size:0.875rem;">Failed to load history</div>`;
        }
    },
    
    render(sessions) {
        const container = document.getElementById('history-list');
        
        if (!sessions || sessions.length === 0) {
            container.innerHTML = `<div style="padding:1rem; color:var(--text-muted); font-size:0.875rem;">No previous sessions</div>`;
            return;
        }
        
        // Sort by created_at descending
        sessions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        let html = '';
        sessions.forEach(session => {
            const date = new Date(session.created_at).toLocaleString(undefined, { 
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
            });
            
            const isActive = session.session_id === App.state.sessionId;
            
            html += `
                <div class="nav-item ${isActive ? 'active' : ''}" 
                     style="flex-direction: column; align-items: flex-start; gap: 0.25rem; font-size: 0.875rem;"
                     onclick="HistoryController.resumeSession('${session.session_id}')">
                    <div style="font-weight: 500; color: ${isActive ? 'var(--accent-primary)' : 'var(--text-primary)'}; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        ${session.original_filename || 'Unknown File'}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">
                        ${date}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    },
    
    resumeSession(sessionId) {
        if (sessionId === App.state.sessionId) return; // Already active
        
        // Quick local state reset
        App.state.schema = null;
        App.state.prompt = null;
        App.state.validationReport = null;
        App.state.previewData = null;
        
        // Set new session ID
        App.setSessionId(sessionId);
        
        // Navigate to Analysis to kick off reloading
        App.navigateTo('analysis');
        
        Utils.showToast(`Resumed session: ${sessionId.substring(0,8)}...`, 'info');
    }
};

window.HistoryController = HistoryController;

// Load history on startup
document.addEventListener('app:ready', () => {
    HistoryController.loadHistory();
});
