/**
 * ExcelPlorer — Export Tab Controller
 */

const ExportController = {
    init() {
        this.cacheDOM();
        this.bindEvents();
    },

    cacheDOM() {
        this.btnDownload = document.getElementById('btn-download-excel');
        
        // Modal elements
        this.modal = document.getElementById('modal-missing-sku');
        this.missingSkuList = document.getElementById('missing-sku-list');
        this.btnCancel = document.getElementById('btn-modal-cancel');
        this.btnPreview = document.getElementById('btn-modal-preview');
        this.btnSkip = document.getElementById('btn-modal-skip');
    },

    bindEvents() {
        if (!this.btnDownload) return;

        this.btnDownload.addEventListener('click', () => this.handleExport(false));

        if (this.modal) {
            this.btnCancel.addEventListener('click', () => this.hideModal());
            this.btnPreview.addEventListener('click', () => {
                this.hideModal();
                App.navigateTo('preview');
            });
            this.btnSkip.addEventListener('click', () => {
                this.hideModal();
                this.handleExport(true);
            });
        }
    },

    async handleExport(skipMissing) {
        if (!App.state.sessionId) {
            Utils.showToast('No active session.', 'error');
            return;
        }

        const originalText = this.btnDownload.innerHTML;
        this.btnDownload.innerHTML = 'Downloading...';
        this.btnDownload.disabled = true;

        try {
            const { blob, filename } = await API.downloadExport(App.state.sessionId, skipMissing);
            
            // Trigger native download
            const objectUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = objectUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(objectUrl);
            document.body.removeChild(a);

            Utils.showToast('Download started', 'success');
            App.updateNavStatus('export', 'complete');
            
        } catch (error) {
            if (error.status === 409 && error.data && error.data.missing_skus) {
                this.showModal(error.data.missing_skus);
            } else if (error.data && error.data.error) {
                Utils.showToast(error.data.error, 'error');
            } else {
                Utils.showToast('Failed to generate export file.', 'error');
            }
        } finally {
            this.btnDownload.innerHTML = originalText;
            this.btnDownload.disabled = false;
        }
    },

    showModal(missingSkus) {
        if (!this.modal) return;
        this.missingSkuList.innerHTML = missingSkus.map(sku => `<div>• ${sku}</div>`).join('');
        this.modal.style.display = 'flex';
    },

    hideModal() {
        if (!this.modal) return;
        this.modal.style.display = 'none';
    }
};

document.addEventListener('app:ready', () => ExportController.init());
