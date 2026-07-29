/**
 * ExcelPlorer — Upload Tab Controller
 */

const UploadController = {
    init() {
        this.dropzone = document.getElementById('upload-dropzone');
        this.input = document.getElementById('upload-input');
        
        if (!this.dropzone) return;

        this.dropzone.addEventListener('click', () => this.input.click());
        
        this.dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropzone.classList.add('dragover');
        });
        
        this.dropzone.addEventListener('dragleave', () => {
            this.dropzone.classList.remove('dragover');
        });
        
        this.dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropzone.classList.remove('dragover');
            
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });
        
        this.input.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
    },
    
    async handleFile(file) {
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            Utils.showToast('Only .xlsx and .xls files are supported.', 'error');
            return;
        }
        
        document.getElementById('upload-status').style.display = 'block';
        document.getElementById('upload-filename').textContent = `Uploading: ${file.name} (${Utils.formatBytes(file.size)})`;
        document.getElementById('upload-progress-bar').style.width = '30%';
        
        try {
            const result = await API.uploadTemplate(file);
            document.getElementById('upload-progress-bar').style.width = '100%';
            
            Utils.showToast(`Uploaded successfully! Session: ${result.session_id}`, 'success');
            App.setSessionId(result.session_id);
            App.updateNavStatus('upload', 'complete');
            
            // Wait a sec for the progress bar animation
            setTimeout(() => {
                App.navigateTo('analysis');
                document.getElementById('upload-progress-bar').style.width = '0%';
                document.getElementById('upload-status').style.display = 'none';
            }, 800);
            
        } catch (error) {
            document.getElementById('upload-progress-bar').style.backgroundColor = 'var(--status-error)';
            App.updateNavStatus('upload', 'error');
        }
    }
};

document.addEventListener('app:ready', () => UploadController.init());
