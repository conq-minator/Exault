/**
 * ExcelPlorer — Report Tab Controller
 */

const ReportController = {
    load() {
        if (!App.state.sessionId) return;
        
        const iframe = document.getElementById('report-frame');
        if (!iframe) return;
        
        // Point iframe to the HTML report endpoint
        const url = API.getReportUrl(App.state.sessionId, 'html');
        iframe.src = url;
        
        App.updateNavStatus('report', 'complete');
    }
};

document.addEventListener('tab:changed', (e) => {
    if (e.detail.target === 'report' && App.state.sessionId) {
        ReportController.load();
    }
});
