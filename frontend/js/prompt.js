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

        // Custom notes logic
        this.loadNotesList();

        const customNotesTextarea = document.getElementById('custom-notes-textarea');
        const notesDropdown = document.getElementById('notes-dropdown');
        const btnLoadNote = document.getElementById('btn-load-note');
        const btnDeleteNote = document.getElementById('btn-delete-note');
        const btnSaveNote = document.getElementById('btn-save-note');

        if (notesDropdown) {
            notesDropdown.addEventListener('change', () => {
                btnDeleteNote.style.display = notesDropdown.value ? 'block' : 'none';
            });

            btnLoadNote.addEventListener('click', async () => {
                const name = notesDropdown.value;
                if (!name) return Utils.showToast('Please select a note profile to load', 'warning');

                try {
                    const note = await API.getNote(name);
                    customNotesTextarea.value = note.content;
                    Utils.showToast(`Loaded ${name}`, 'success');
                } catch (e) {
                    Utils.showToast('Failed to load note', 'error');
                }
            });

            btnDeleteNote.addEventListener('click', async () => {
                const name = notesDropdown.value;
                if (!name) return;

                const confirmed = await Utils.showConfirm('Delete Note Profile', `Are you sure you want to delete the note profile "${name}"?`);
                if (confirmed) {
                    try {
                        await API.deleteNote(name);
                        Utils.showToast(`Deleted ${name}`, 'success');
                        customNotesTextarea.value = '';
                        await this.loadNotesList();
                    } catch (e) {
                        Utils.showToast('Failed to delete note', 'error');
                    }
                }
            });

            btnSaveNote.addEventListener('click', async () => {
                const content = customNotesTextarea.value.trim();
                if (!content) return Utils.showToast('Cannot save empty notes', 'warning');

                const currentName = notesDropdown.value;
                const name = await Utils.showPrompt('Save Note Profile As:', currentName || 'New Note');
                if (!name) return;

                try {
                    await API.saveNote(name, content, true);
                    Utils.showToast(`Saved note profile "${name}"`, 'success');
                    await this.loadNotesList();
                    notesDropdown.value = name;
                    btnDeleteNote.style.display = 'block';
                } catch (e) {
                    Utils.showToast('Failed to save note: ' + (e.data?.error || e.message), 'error');
                }
            });
        }

        if (customNotesTextarea) {
            document.getElementById('btn-add-notes-rules').addEventListener('click', () => {
                const rulesTextarea = document.getElementById('rules-prompt-textarea');
                const notes = customNotesTextarea.value.trim();
                if (notes && !rulesTextarea.value.includes(notes)) {
                    rulesTextarea.value = rulesTextarea.value + '\n\n--- CUSTOM NOTES ---\n' + notes;
                    Utils.showToast('Custom notes attached to Prompt 1', 'success');
                } else if (!notes) {
                    Utils.showToast('Custom notes are empty', 'warning');
                }
            });

            document.getElementById('btn-add-notes-data').addEventListener('click', () => {
                const dataTextarea = document.getElementById('prompt-textarea');
                const notes = customNotesTextarea.value.trim();
                if (notes && !dataTextarea.value.includes(notes)) {
                    dataTextarea.value = dataTextarea.value + '\n\n--- CUSTOM NOTES ---\n' + notes;
                    Utils.showToast('Custom notes attached to Prompt 2', 'success');
                } else if (!notes) {
                    Utils.showToast('Custom notes are empty', 'warning');
                }
            });
        }
    },

    async loadNotesList() {
        try {
            const notes = await API.getNotes();
            const dropdown = document.getElementById('notes-dropdown');
            const currentValue = dropdown.value;

            dropdown.innerHTML = '<option value="">-- Load a saved note profile --</option>';
            notes.forEach(note => {
                const option = document.createElement('option');
                option.value = note.name;
                option.textContent = note.name;
                dropdown.appendChild(option);
            });

            if (notes.some(n => n.name === currentValue)) {
                dropdown.value = currentValue;
            }

            document.getElementById('btn-delete-note').style.display = dropdown.value ? 'block' : 'none';
        } catch (e) {
            console.error('Failed to load notes list:', e);
        }
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
