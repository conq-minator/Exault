/**
 * ExcelPlorer — Validator Tab Controller
 */

const ValidatorController = {
    render() {
        const report = App.state.validationReport;
        const container = document.getElementById('validator-content');
        
        if (!report) {
            container.innerHTML = '<div style="color:var(--text-secondary);">No validation data. Please input JSON first.</div>';
            return;
        }
        
        if (report.is_valid && report.issues.length === 0) {
            container.innerHTML = `
                <div class="glass-panel" style="padding: 2rem; text-align: center; border-color: var(--status-success);">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--status-success)" stroke-width="2" style="margin-bottom:1rem;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    <h3 style="color: var(--status-success);">Perfect Validation!</h3>
                    <p style="color: var(--text-secondary); margin-top: 0.5rem;">No errors, warnings, or corrections were needed.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        // Group issues by severity
        const errors = report.issues.filter(i => i.severity === 'ERROR');
        const warnings = report.issues.filter(i => i.severity === 'WARNING');
        const infos = report.issues.filter(i => i.severity === 'INFO');
        
        const renderSection = (title, issues, colorClass) => {
            if (issues.length === 0) return '';
            
            let html = `
                <div class="glass-panel" style="margin-bottom: 2rem; border-color: var(--status-${colorClass});">
                    <div style="padding: 1rem 1.5rem; background: var(--status-${colorClass}-bg); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between;">
                        <h3 style="color: var(--status-${colorClass}); margin: 0;">${title} (${issues.length})</h3>
                    </div>
                    <div style="padding: 1rem 1.5rem;">
                        <ul style="display: flex; flex-direction: column; gap: 0.75rem;">
            `;
            
            issues.forEach(issue => {
                let productTitle = `Row ${issue.item_index + 1}`;
                if (report.indexToProductId && report.productsInfo) {
                    const prodId = report.indexToProductId[issue.item_index];
                    const prodInfo = report.productsInfo.find(p => p.id === prodId);
                    if (prodInfo) {
                        productTitle = prodInfo.title;
                    }
                }
                
                html += `
                    <li style="display: flex; gap: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <div style="min-width: 120px; font-weight: 500;">${productTitle}</div>
                        <div style="min-width: 150px; color: var(--text-secondary);">${issue.field}</div>
                        <div style="flex: 1;">${issue.message}</div>
                    </li>
                `;
            });
            
            html += `</ul></div></div>`;
            return html;
        };
        
        html += renderSection('Errors', errors, 'error');
        html += renderSection('Warnings', warnings, 'warning');
        html += renderSection('Auto-Corrections', infos, 'info');
        
        container.innerHTML = html;
    }
};

document.addEventListener('tab:changed', (e) => {
    if (e.detail.target === 'validator') {
        ValidatorController.render();
    }
});
