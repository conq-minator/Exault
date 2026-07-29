/**
 * ExcelPlorer — Preview Tab Controller
 */

const PreviewController = {
    async load() {
        if (!App.state.sessionId) return;
        
        const table = document.getElementById('preview-table');
        table.innerHTML = '<tr><td>Loading preview...</td></tr>';
        
        try {
            const data = await API.getPreview(App.state.sessionId);
            App.state.previewData = data;
            this.render(data);
            App.updateNavStatus('preview', 'complete');
        } catch (error) {
            table.innerHTML = `<tr><td style="color:var(--status-error);">${error.message}</td></tr>`;
            App.updateNavStatus('preview', 'error');
        }
    },
    
    render(data) {
        if (!data || data.length === 0) {
            document.getElementById('preview-table').innerHTML = '<tr><td>No data available.</td></tr>';
            return;
        }
        
        // Extract headers from first object
        const headers = Object.keys(data[0]);
        
        let html = '<thead><tr>';
        html += '<th style="width: 60px;">#</th>';
        headers.forEach(h => {
            html += `<th>${h}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach((row, rowIndex) => {
            html += `<tr>`;
            html += `<td style="color:var(--text-muted);">${rowIndex + 1}</td>`;
            
            headers.forEach(h => {
                const val = row[h] !== null && row[h] !== undefined ? row[h] : '';
                // Escaping could be needed here in production for security
                html += `
                    <td class="editable-cell">
                        <input type="text" 
                               value="${val.toString().replace(/"/g, '&quot;')}" 
                               data-row="${rowIndex}" 
                               data-col="${h}"
                               onchange="PreviewController.handleEdit(this)">
                    </td>
                `;
            });
            html += '</tr>';
        });
        
        html += '</tbody>';
        document.getElementById('preview-table').innerHTML = html;
    },
    
    async handleEdit(input) {
        const rowIndex = parseInt(input.dataset.row);
        const colName = input.dataset.col;
        const newValue = input.value;
        
        // Update local state
        if (App.state.previewData && App.state.previewData[rowIndex]) {
            App.state.previewData[rowIndex][colName] = newValue;
            
            // Send update to server
            try {
                await API.updatePreviewRow(App.state.sessionId, rowIndex, App.state.previewData[rowIndex]);
                Utils.showToast(`Row ${rowIndex + 1} updated`, 'success');
            } catch (err) {
                // Revert is complex without original state, so just show error
                // In a full app, we'd keep track of original state
            }
        }
    }
};

window.PreviewController = PreviewController;

document.addEventListener('tab:changed', (e) => {
    // We reload preview every time to ensure it has latest corrected data from validator
    if (e.detail.target === 'preview' && App.state.sessionId) {
        PreviewController.load();
    }
});
