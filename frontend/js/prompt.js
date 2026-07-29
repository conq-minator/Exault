/**
 * ExcelPlorer — Prompt Tab Controller
 */

const PromptController = {
    init() {
        document.getElementById('btn-copy-rules-prompt').addEventListener('click', () => {
            const textarea = document.getElementById('rules-prompt-textarea');
            if (textarea.value) {
                Utils.copyToClipboard(textarea.value);
            }
        });
        
        document.getElementById('btn-copy-prompt').addEventListener('click', () => {
            const textarea = document.getElementById('prompt-textarea');
            if (textarea.value) {
                Utils.copyToClipboard(textarea.value);
            }
        });
    },

    async load() {
        if (!App.state.sessionId) return;
        
        const textareaRules = document.getElementById('rules-prompt-textarea');
        const statsRules = document.getElementById('rules-prompt-stats');
        const textareaData = document.getElementById('prompt-textarea');
        const statsData = document.getElementById('prompt-stats');
        
        textareaRules.value = "Generating rules prompt...";
        textareaData.value = "Generating data prompt...";
        
        try {
            const data = await API.generatePrompt(App.state.sessionId);
            App.state.prompt = data;
            
            textareaRules.value = data.rules_prompt;
            statsRules.textContent = `${data.rules_word_count} words | ~${data.rules_token_count} tokens`;
            
            textareaData.value = data.prompt;
            statsData.textContent = `${data.word_count} words | ~${data.token_count} tokens`;
            
            App.updateNavStatus('prompt', 'complete');
        } catch (error) {
            textareaRules.value = `Error: ${error.message}`;
            textareaData.value = `Error: ${error.message}`;
            App.updateNavStatus('prompt', 'error');
        }
    }
};

document.addEventListener('app:ready', () => PromptController.init());
document.addEventListener('tab:changed', (e) => {
    if (e.detail.target === 'prompt' && App.state.sessionId && !App.state.prompt) {
        PromptController.load();
    }
});
