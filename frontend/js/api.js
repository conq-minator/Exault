/**
 * ExcelPlorer — API Client
 */

const API_BASE = 'http://127.0.0.1:5000/api';

const API = {
    /**
     * Helper to handle JSON responses and errors.
     */
    async _fetch(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, options);
            if (!response.ok) {
                let errMessage = `HTTP Error ${response.status}`;
                try {
                    const errData = await response.json();
                    errMessage = errData.message || errMessage;
                } catch (e) {
                    // response is not json
                }
                throw new Error(errMessage);
            }
            // For downloads (like export), we might return a blob, but let's handle that separately if needed.
            return await response.json();
        } catch (error) {
            Utils.showToast(error.message, 'error');
            throw error;
        }
    },

    async uploadTemplate(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this._fetch('/upload', {
            method: 'POST',
            body: formData
        });
    },

    async getAnalysis(sessionId) {
        return this._fetch(`/analysis/${sessionId}`);
    },

    async generatePrompt(sessionId) {
        return this._fetch(`/prompt/${sessionId}`);
    },

    async validateJson(sessionId, jsonData) {
        return this._fetch(`/validate/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                raw_json: typeof jsonData === 'string' ? jsonData : JSON.stringify(jsonData, null, 2)
            })
        });
    },

    async getPreview(sessionId) {
        return this._fetch(`/preview/${sessionId}`);
    },

    async updatePreviewRow(sessionId, rowIndex, rowData) {
        return this._fetch(`/preview/${sessionId}/row/${rowIndex}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rowData)
        });
    },

    getExportUrl(sessionId) {
        return `${API_BASE}/export/${sessionId}`;
    },

    async downloadExport(sessionId, skipMissing = false) {
        const url = `${API_BASE}/export/${sessionId}${skipMissing ? '?skip_missing=true' : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
            let errData = {};
            try { errData = await response.json(); } catch (e) { }
            // We throw an object so export.js can check the status code
            throw { status: response.status, data: errData };
        }

        // Extract filename from Content-Disposition if present
        let filename = `output.xlsx`;
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('attachment') !== -1) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        const blob = await response.blob();
        return { blob, filename };
    },

    getReportUrl(sessionId, format = 'html') {
        return `${API_BASE}/report/${sessionId}?format=${format}`;
    },

    async getSessions() {
        return this._fetch('/sessions');
    },

    // --- Product Library API --- //

    async getProducts() {
        return this._fetch('/products');
    },

    async getProduct(sku) {
        return this._fetch(`/products/${encodeURIComponent(sku)}`);
    },

    async deleteProduct(sku) {
        return this._fetch(`/products/${encodeURIComponent(sku)}`, {
            method: 'DELETE'
        });
    },

    async saveProduct(sku, data, overwrite = false) {
        // Use full fetch for status check since 409 means conflict
        const url = `${API_BASE}/products/${encodeURIComponent(sku)}${overwrite ? '?overwrite=true' : ''}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            let errData = {};
            try { errData = await response.json(); } catch (e) { }
            throw { status: response.status, data: errData };
        }
        return await response.json();
    },

    // --- Notes API ---
    async getNotes() {
        return this._fetch(`/notes`);
    },

    async getNote(name) {
        return this._fetch(`/notes/${encodeURIComponent(name)}`);
    },

    async saveNote(name, content, overwrite = false) {
        const url = `${API_BASE}/notes/${encodeURIComponent(name)}${overwrite ? '?overwrite=true' : ''}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        if (!response.ok) {
            let errData = {};
            try { errData = await response.json(); } catch (e) { }
            throw { status: response.status, data: errData };
        }
        return await response.json();
    },

    async deleteNote(name) {
        return this._fetch(`/notes/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
    }
};

window.API = API;
