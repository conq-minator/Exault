/**
 * ExcelPlorer — Main App Controller
 */

const App = {
    state: {
        sessionId: null,
        schema: null,
        prompt: null,
        validationReport: null,
        previewData: null
    },
    
    init() {
        console.log("ExcelPlorer App Initialized.");
        this.setupNavigation();
        
        // Dispatch custom event to notify tabs to initialize
        document.dispatchEvent(new Event('app:ready'));
    },
    
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                // Remove active from all
                navItems.forEach(nav => nav.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Add active to clicked
                item.classList.add('active');
                const targetId = `tab-${item.dataset.target}`;
                document.getElementById(targetId).classList.add('active');
                
                // Dispatch event so tabs can refresh if needed
                document.dispatchEvent(new CustomEvent('tab:changed', { 
                    detail: { target: item.dataset.target } 
                }));
            });
        });
    },
    
    setSessionId(id) {
        this.state.sessionId = id;
        console.log(`Session ID set to ${id}`);
        // Refresh history
        if (window.HistoryController) {
            window.HistoryController.loadHistory();
        }
    },
    
    navigateTo(tabName) {
        const item = document.querySelector(`.nav-item[data-target="${tabName}"]`);
        if (item) item.click();
    },
    
    updateNavStatus(tabName, statusClass) {
        const el = document.getElementById(`status-${tabName}`);
        if (el) {
            el.className = `nav-status ${statusClass}`;
        }
    }
};

window.App = App;

// Start app on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
