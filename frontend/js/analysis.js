/**
 * ExcelPlorer — Analysis Tab Controller
 */

const AnalysisController = {
    async load() {
        if (!App.state.sessionId) return;
        
        const container = document.getElementById('analysis-content');
        container.innerHTML = '<div class="spin" style="width:30px; height:30px; border:3px solid var(--border-color); border-top-color:var(--accent-primary); border-radius:50%; margin:2rem auto;"></div>';
        
        try {
            const data = await API.getAnalysis(App.state.sessionId);
            App.state.schema = data.schema;
            this.render(data);
            App.updateNavStatus('analysis', 'complete');
        } catch (error) {
            container.innerHTML = `<div style="color:var(--status-error);">${error.message}</div>`;
            App.updateNavStatus('analysis', 'error');
        }
    },
    
    render(data) {
        const schema = data.schema;
        const container = document.getElementById('analysis-content');
        
        let html = `
            <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 2rem;">
                <h3 style="margin-bottom: 1rem; color: var(--accent-primary);">${schema.filename}</h3>
                <div style="display: flex; gap: 2rem; color: var(--text-secondary); font-size: 0.875rem;">
                    <div><strong>Detected Marketplace:</strong> ${schema.detected_marketplace || 'Generic / None'}</div>
                    <div><strong>Sheets:</strong> ${schema.sheet_count}</div>
                    <div><strong>Size:</strong> ${Utils.formatBytes(schema.file_size)}</div>
                    <div><strong>Analysis Time:</strong> ${data.duration_ms.toFixed(0)}ms</div>
                </div>
            </div>
        `;
        
        if (data.warnings && data.warnings.length > 0) {
            html += `
                <div class="glass-panel" style="padding: 1rem; border-color: var(--status-warning); margin-bottom: 2rem;">
                    <h4 style="color: var(--status-warning); margin-bottom: 0.5rem;">Warnings</h4>
                    <ul style="font-size: 0.875rem; padding-left: 1rem;">
                        ${data.warnings.map(w => `<li style="list-style-type:disc;">${w}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        schema.sheets.forEach(sheet => {
            if (!sheet.is_data_sheet || sheet.columns.length === 0) return;
            
            html += `
                <h3 style="margin: 2rem 0 1rem 0;">Sheet: ${sheet.name}</h3>
                <div class="card-grid">
            `;
            
            sheet.columns.forEach(col => {
                if (col.is_hidden) return;
                
                const reqBadge = col.is_required ? '<span class="badge req">Required</span>' : '<span class="badge opt">Optional</span>';
                const typeBadge = `<span class="badge type">${col.data_type}</span>`;
                
                html += `
                    <div class="card glass-panel-light">
                        <div class="card-header">
                            <strong style="font-size: 0.875rem; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${col.name}">${col.name}</strong>
                            <div style="display:flex; gap:0.5rem; flex-shrink:0;">${typeBadge}${reqBadge}</div>
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">
                            <div><strong>Index:</strong> ${col.letter}</div>
                            ${col.max_length ? `<div><strong>Max Length:</strong> ${col.max_length}</div>` : ''}
                            ${col.allowed_values && col.allowed_values.length > 0 ? `
                                <div style="margin-top:0.5rem;">
                                    <strong>Allowed Values:</strong>
                                    <div style="margin-top:0.25rem; max-height:60px; overflow-y:auto; background:rgba(0,0,0,0.2); padding:0.25rem; border-radius:4px;">
                                        ${col.allowed_values.join(', ')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
        });
        
        container.innerHTML = html;
    }
};

document.addEventListener('tab:changed', (e) => {
    if (e.detail.target === 'analysis' && App.state.sessionId && !App.state.schema) {
        AnalysisController.load();
    }
});
