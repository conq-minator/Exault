/**
 * ExcelPlorer — JSON Input Tab Controller
 */

const JsonInputController = {
    products: [],
    activeProductId: null,
    nextId: 1,

    init() {
        this.cacheDOM();
        this.bindEvents();
        
        // Listen for tab changed to reset/init if needed
        document.addEventListener('tab:changed', (e) => {
            if (e.detail.target === 'json-input' && this.products.length === 0) {
                this.addProduct();
            }
        });
    },

    cacheDOM() {
        this.btnAddProduct = document.getElementById('btn-add-product');
        this.btnLoadProduct = document.getElementById('btn-load-product');
        this.productList = document.getElementById('product-list');
        this.textarea = document.getElementById('json-textarea');
        this.btnValidate = document.getElementById('btn-validate-json');
        this.btnDelete = document.getElementById('btn-delete-product');
        this.btnSave = document.getElementById('btn-save-product');
        this.titleEl = document.getElementById('current-product-title');
        this.statusEl = document.getElementById('current-product-status');
        
        // Modals
        this.modalLibrary = document.getElementById('modal-library');
        this.libraryList = document.getElementById('library-list');
        this.btnLibraryClose = document.getElementById('btn-library-close');
        
        this.modalConflict = document.getElementById('modal-conflict');
        this.conflictMessage = document.getElementById('conflict-message');
        this.btnConflictCancel = document.getElementById('btn-conflict-cancel');
        this.btnConflictOverwrite = document.getElementById('btn-conflict-overwrite');
        
        // State for conflict resolution
        this.pendingSaveSku = null;
        this.pendingSaveData = null;
    },

    bindEvents() {
        if (!this.btnAddProduct) return;
        
        this.btnAddProduct.addEventListener('click', () => this.addProduct());
        if (this.btnLoadProduct) {
            this.btnLoadProduct.addEventListener('click', () => this.openLibraryModal());
        }
        
        this.btnDelete.addEventListener('click', () => this.deleteActiveProduct());
        if (this.btnSave) {
            this.btnSave.addEventListener('click', () => this.saveActiveProduct());
        }
        
        if (this.btnLibraryClose) {
            this.btnLibraryClose.addEventListener('click', () => {
                this.modalLibrary.style.display = 'none';
            });
        }
        
        if (this.btnConflictCancel) {
            this.btnConflictCancel.addEventListener('click', () => {
                this.modalConflict.style.display = 'none';
                this.pendingSaveSku = null;
                this.pendingSaveData = null;
            });
        }
        
        if (this.btnConflictOverwrite) {
            this.btnConflictOverwrite.addEventListener('click', () => {
                if (this.pendingSaveSku && this.pendingSaveData) {
                    this.executeSaveProduct(this.pendingSaveSku, this.pendingSaveData, true);
                }
                this.modalConflict.style.display = 'none';
            });
        }
        
        this.saveTimeout = null;
        this.textarea.addEventListener('input', (e) => {
            if (this.activeProductId) {
                const product = this.products.find(p => p.id === this.activeProductId);
                if (product) {
                    product.rawJson = e.target.value;
                    product.status = 'Draft';
                    this.updateProductListUI();
                    this.updateEditorUI();
                    
                    clearTimeout(this.saveTimeout);
                    this.saveTimeout = setTimeout(() => {
                        this.saveActiveProduct(true);
                    }, 1000);
                }
            }
            this.checkValidationReady();
        });
        
        this.btnValidate.addEventListener('click', () => this.validateAll());
    },

    addProduct() {
        const product = {
            id: this.nextId++,
            rawJson: '',
            status: 'Draft'
        };
        this.products.push(product);
        this.selectProduct(product.id);
        this.updateProductListUI();
        this.checkValidationReady();
    },

    async deleteActiveProduct() {
        if (!this.activeProductId) return;
        
        const product = this.products.find(p => p.id === this.activeProductId);
        if (product) {
            const sku = this.getSkuFromName(product.rawJson);
            if (sku) {
                try {
                    await API.deleteProduct(sku);
                    Utils.showToast(`Deleted SKU ${sku} from library`, 'success');
                } catch(e) {
                    console.error("Failed to delete from library:", e);
                }
            }
        }
        
        this.products = this.products.filter(p => p.id !== this.activeProductId);
        
        if (this.products.length > 0) {
            this.selectProduct(this.products[0].id);
        } else {
            this.activeProductId = null;
            this.updateEditorUI();
        }
        
        this.updateProductListUI();
        this.checkValidationReady();
    },

    selectProduct(id) {
        this.activeProductId = id;
        this.updateProductListUI();
        this.updateEditorUI();
    },
    
    getSkuFromName(jsonStr) {
        try {
            // Clean up potentially bad markdown wrapping from LLMs
            let cleanJson = jsonStr.trim();
            if (cleanJson.startsWith('```json')) cleanJson = cleanJson.substring(7);
            else if (cleanJson.startsWith('```')) cleanJson = cleanJson.substring(3);
            if (cleanJson.endsWith('```')) cleanJson = cleanJson.substring(0, cleanJson.length - 3);
            
            const data = JSON.parse(cleanJson);
            // Handle if it's an array with one item or just an object
            const item = Array.isArray(data) ? data[0] : data;
            
            if (item) {
                const skuKeys = ["seller sku id", "sku", "item_sku", "seller sku"];
                for (const key of Object.keys(item)) {
                    if (skuKeys.includes(key.toLowerCase())) {
                        return item[key];
                    }
                }
            }
        } catch(e) {
            return null;
        }
        return null;
    },

    updateProductListUI() {
        if (!this.productList) return;
        this.productList.innerHTML = '';
        
        this.products.forEach(product => {
            const sku = this.getSkuFromName(product.rawJson);
            const title = sku ? `SKU: ${sku}` : `Product ${product.id} (Untitled)`;
            
            const el = document.createElement('div');
            el.className = `product-list-item ${product.id === this.activeProductId ? 'active' : ''}`;
            el.style.padding = '0.75rem';
            el.style.borderRadius = 'var(--border-radius-md)';
            el.style.cursor = 'pointer';
            el.style.display = 'flex';
            el.style.justifyContent = 'space-between';
            el.style.alignItems = 'center';
            el.style.border = product.id === this.activeProductId ? '1px solid var(--accent-primary)' : '1px solid transparent';
            el.style.background = product.id === this.activeProductId ? 'rgba(var(--accent-primary-rgb), 0.1)' : 'rgba(255,255,255,0.03)';
            el.style.marginBottom = '0.5rem';
            
            let statusColor = 'var(--text-secondary)';
            if (product.status === 'Valid') statusColor = 'var(--status-success)';
            if (product.status === 'Invalid') statusColor = 'var(--status-error)';
            
            el.innerHTML = `
                <span style="font-weight: 500; font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px;">${title}</span>
                <span style="font-size: 0.75rem; padding: 0.15rem 0.4rem; border-radius: 4px; background: rgba(255,255,255,0.1); color: ${statusColor};">${product.status}</span>
            `;
            
            el.addEventListener('click', () => this.selectProduct(product.id));
            this.productList.appendChild(el);
        });
    },

    updateEditorUI() {
        if (!this.activeProductId) {
            this.titleEl.textContent = 'No product selected';
            this.statusEl.textContent = '';
            this.textarea.value = '';
            this.textarea.disabled = true;
            this.btnDelete.style.display = 'none';
            if (this.btnSave) this.btnSave.style.display = 'none';
            return;
        }

        const product = this.products.find(p => p.id === this.activeProductId);
        if (!product) return;

        const sku = this.getSkuFromName(product.rawJson);
        this.titleEl.textContent = sku ? `SKU: ${sku}` : `Product ${product.id} (Untitled)`;
        
        let statusColor = 'var(--text-secondary)';
        if (product.status === 'Valid') statusColor = 'var(--status-success)';
        if (product.status === 'Invalid') statusColor = 'var(--status-error)';
        
        this.statusEl.textContent = product.status;
        this.statusEl.style.color = statusColor;
        
        this.textarea.value = product.rawJson;
        this.textarea.disabled = false;
        this.btnDelete.style.display = 'block';
        if (this.btnSave) this.btnSave.style.display = 'block';
    },
    
    // --- Library Integration ---
    
    async openLibraryModal() {
        try {
            const skus = await API.getProducts();
            this.libraryList.innerHTML = '';
            
            if (skus.length === 0) {
                this.libraryList.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 2rem;">No products saved in library yet.</div>';
            } else {
                skus.forEach(item => {
                    const el = document.createElement('div');
                    el.className = 'product-list-item';
                    el.style.padding = '1rem';
                    el.style.borderRadius = 'var(--border-radius-md)';
                    el.style.cursor = 'pointer';
                    el.style.background = 'rgba(255,255,255,0.05)';
                    el.style.border = '1px solid rgba(255,255,255,0.1)';
                    el.innerHTML = `<strong>SKU: ${item.sku}</strong><br><span style="font-size: 0.85rem; color: var(--text-secondary);">${item.title !== item.sku ? item.title : 'No title'}</span>`;
                    
                    el.addEventListener('click', async () => {
                        await this.loadProductFromLibrary(item.sku);
                        this.modalLibrary.style.display = 'none';
                    });
                    
                    this.libraryList.appendChild(el);
                });
            }
            
            this.modalLibrary.style.display = 'flex';
        } catch (e) {
            Utils.showToast('Failed to load library: ' + e.message, 'error');
        }
    },
    
    async loadProductFromLibrary(sku) {
        try {
            const data = await API.getProduct(sku);
            const product = {
                id: this.nextId++,
                rawJson: JSON.stringify(data, null, 2),
                status: 'Draft'
            };
            this.products.push(product);
            this.selectProduct(product.id);
            this.checkValidationReady();
            Utils.showToast(`Loaded SKU ${sku} from library`, 'success');
        } catch (e) {
            Utils.showToast('Failed to load product: ' + e.message, 'error');
        }
    },
    
    async saveActiveProduct(isAutoSave = true) {
        if (!this.activeProductId) return;
        const product = this.products.find(p => p.id === this.activeProductId);
        if (!product) return;
        
        const sku = this.getSkuFromName(product.rawJson);
        if (!sku) {
            if (!isAutoSave) Utils.showToast('Cannot save to library: No valid SKU ID found in the JSON data.', 'error');
            return;
        }
        
        let cleanJson = product.rawJson.trim();
        if (cleanJson.startsWith('```json')) cleanJson = cleanJson.substring(7);
        else if (cleanJson.startsWith('```')) cleanJson = cleanJson.substring(3);
        if (cleanJson.endsWith('```')) cleanJson = cleanJson.substring(0, cleanJson.length - 3);
        
        let data;
        try {
            data = JSON.parse(cleanJson);
        } catch(e) {
            if (!isAutoSave) Utils.showToast('Cannot save to library: JSON is invalid.', 'error');
            return;
        }
        
        // If it's an array, save the first item or let backend handle it, but library expects an object.
        const itemData = Array.isArray(data) ? data[0] : data;
        this.executeSaveProduct(sku, itemData, true, isAutoSave);
    },
    
    async executeSaveProduct(sku, data, overwrite, isAutoSave = true) {
        try {
            await API.saveProduct(sku, data, overwrite);
            if (!isAutoSave) Utils.showToast(`Saved SKU ${sku} to library!`, 'success');
            this.pendingSaveSku = null;
            this.pendingSaveData = null;
        } catch (err) {
            if (err.status === 409 && !isAutoSave) {
                this.pendingSaveSku = sku;
                this.pendingSaveData = data;
                this.conflictMessage.textContent = `A product with SKU '${sku}' already exists in your library. Do you want to overwrite it?`;
                this.modalConflict.style.display = 'flex';
            } else if (!isAutoSave) {
                Utils.showToast('Failed to save to library: ' + (err.data?.error || 'Unknown error'), 'error');
            }
        }
    },
    
    checkValidationReady() {
        // Can validate if we have at least one product with some text
        const hasContent = this.products.some(p => p.rawJson.trim().length > 0);
        this.btnValidate.disabled = !hasContent;
    },

    async validateAll() {
        if (!App.state.sessionId) {
            Utils.showToast('No active session. Please upload a template first.', 'error');
            return;
        }

        if (this.products.length === 0) return;

        const combinedData = [];
        const indexToProductId = []; // Maps JSON array index to product ID

        for (const product of this.products) {
            const rawText = product.rawJson.trim();
            if (!rawText) continue;

            // Clean up potentially bad markdown wrapping from LLMs
            let cleanJson = rawText;
            if (cleanJson.startsWith('```json')) cleanJson = cleanJson.substring(7);
            else if (cleanJson.startsWith('```')) cleanJson = cleanJson.substring(3);
            if (cleanJson.endsWith('```')) cleanJson = cleanJson.substring(0, cleanJson.length - 3);

            try {
                const parsedData = JSON.parse(cleanJson);
                // Handle if user pasted array instead of object
                if (Array.isArray(parsedData)) {
                    for (const item of parsedData) {
                        combinedData.push(item);
                        indexToProductId.push(product.id);
                    }
                } else {
                    combinedData.push(parsedData);
                    indexToProductId.push(product.id);
                }
            } catch (e) {
                Utils.showToast(`Invalid JSON format in Product ${product.id}.`, 'error');
                product.status = 'Invalid (JSON Error)';
                this.updateProductListUI();
                this.updateEditorUI();
                return;
            }
        }

        if (combinedData.length === 0) {
            Utils.showToast('No JSON data to validate.', 'warning');
            return;
        }

        const originalText = this.btnValidate.textContent;
        this.btnValidate.textContent = "Validating...";
        this.btnValidate.disabled = true;

        try {
            const report = await API.validateJson(App.state.sessionId, combinedData);
            
            // Map item_statuses back to products
            // A product is valid if all its items (usually just 1) are valid
            const productValidMap = {};
            indexToProductId.forEach((prodId, idx) => {
                if (productValidMap[prodId] === undefined) {
                    productValidMap[prodId] = true;
                }
                if (report.report && report.report.item_statuses && report.report.item_statuses[idx] && !report.report.item_statuses[idx].is_valid) {
                    productValidMap[prodId] = false;
                }
            });
            
            this.products.forEach(p => {
                if (productValidMap[p.id] !== undefined) {
                    p.status = productValidMap[p.id] ? 'Valid' : 'Invalid';
                }
            });
            
            // Re-format textarea for active product if it's valid JSON
            if (this.activeProductId) {
                const activeProd = this.products.find(p => p.id === this.activeProductId);
                if (activeProd) {
                    try {
                        let cleanJson = activeProd.rawJson.trim();
                        if (cleanJson.startsWith('```json')) cleanJson = cleanJson.substring(7);
                        else if (cleanJson.startsWith('```')) cleanJson = cleanJson.substring(3);
                        if (cleanJson.endsWith('```')) cleanJson = cleanJson.substring(0, cleanJson.length - 3);
                        activeProd.rawJson = JSON.stringify(JSON.parse(cleanJson), null, 2);
                    } catch(e) {}
                }
            }
            
            // Add indexToProductId to report for validator tab
            report.report.indexToProductId = indexToProductId;
            // Also store products array for title lookup
            report.report.productsInfo = this.products.map(p => ({
                id: p.id,
                title: this.getSkuFromName(p.rawJson) ? `SKU: ${this.getSkuFromName(p.rawJson)}` : `Product ${p.id}`
            }));

            App.state.validationReport = report.report;
            
            this.updateProductListUI();
            this.updateEditorUI();
            
            App.updateNavStatus('json-input', 'complete');
            
            // Valid if ANY item is valid (so we can proceed to export)
            const hasValidItems = report.report.item_statuses && report.report.item_statuses.some(s => s.is_valid);
            
            if (hasValidItems) {
                App.updateNavStatus('validator', report.report.is_valid ? 'complete' : 'warning');
                Utils.showToast(report.message, report.report.is_valid ? 'success' : 'warning');
            } else {
                App.updateNavStatus('validator', 'error');
                Utils.showToast('All products failed validation.', 'error');
            }
            
            // Switch to validator tab
            App.navigateTo('validator');
        } catch (error) {
            App.updateNavStatus('json-input', 'error');
            Utils.showToast('Validation failed to reach server.', 'error');
        } finally {
            this.btnValidate.textContent = originalText;
            this.btnValidate.disabled = false;
        }
    }
};

document.addEventListener('app:ready', () => JsonInputController.init());
