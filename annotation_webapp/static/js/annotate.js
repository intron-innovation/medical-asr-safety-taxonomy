// Annotation Interface JavaScript
let allData = [];
let randomizedIndices = [];  // Randomized session order
let currentPositionInRandomized = 0;  // Current position in randomized array
let currentErrorId = null;  // Changed: now using error_id instead of error key
let userAnnotations = {};
let modelName = null;
let errorIdMap = {};  // Map from error_id to annotation data

// Shuffle function to randomize session order
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

// Initialize on page load
window.addEventListener('load', function() {
    // Get model name from data attribute
    const interfaceDiv = document.querySelector('.annotation-interface');
    modelName = interfaceDiv ? interfaceDiv.dataset.modelName : null;
    
    if (!modelName) {
        alert('Model name not found. Please select a model.');
        window.location.href = '/select_model';
        return;
    }
    
    loadUtterances();
    loadAnnotations();
    loadStats();
    
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) prevBtn.addEventListener('click', () => navigateUtterance(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => navigateUtterance(1));
    
    document.getElementById('severitySlider').addEventListener('input', updateSeverityDisplay);
    document.getElementById('annotationForm').addEventListener('submit', handleAnnotationSubmit);
});

function navigateUtterance(direction) {
    const newPosition = currentPositionInRandomized + direction;
    if (newPosition >= 0 && newPosition < randomizedIndices.length) {
        currentPositionInRandomized = newPosition;
        const actualIndex = randomizedIndices[currentPositionInRandomized];
        loadUtterance(actualIndex);
        updateSessionCounter();
        loadStats();
    }
}

async function loadUtterances() {
    try {
        const response = await fetch(`/api/utterances/${modelName}`);
        allData = await response.json();
        
        if (allData.length === 0) {
            document.getElementById('loadStatus').textContent = 
                '⚠️ No data loaded. Please upload a JSON file.';
            return;
        }
        
        // Create randomized order of sessions
        randomizedIndices = shuffleArray(Array.from({length: allData.length}, (_, i) => i));
        currentPositionInRandomized = 0;
        
        document.getElementById('transcriptsContainer').style.display = 'grid';
        loadUtterance(randomizedIndices[currentPositionInRandomized]);
        updateSessionCounter();
        loadStats();
    } catch (error) {
        console.error('Error loading utterances:', error);
    }
}

function updateSessionCounter() {
    const totalSessions = allData.length;
    const currentSessionNum = currentPositionInRandomized + 1;
    const utteranceId = allData[randomizedIndices[currentPositionInRandomized]].utterance_id;
    document.getElementById('sessionCounter').textContent = 
        `Session ${currentSessionNum} of ${totalSessions} - ${utteranceId}`;
}

function loadUtterance(index) {
    if (index < 0 || index >= allData.length) return;
    
    currentUtteranceIndex = index;
    const utterance = allData[index];
    
    document.getElementById('humanTranscript').textContent = utterance.human_transcript;
    document.getElementById('asrTranscript').innerHTML = highlightErrors(utterance.asr_reconstructed, utterance.utterance_id);
}

function highlightErrors(text, utteranceId) {
    const utterance = allData[currentUtteranceIndex];
    const errors = utterance.metadata?.errors || [];
    
    if (errors.length === 0) {
        // Fallback to old method if no errors in metadata
        return highlightErrorsLegacy(text, utteranceId);
    }
    
    let html = text;
    const replacements = [];
    
    // Use the start_idx and end_idx from error data for accurate positioning
    errors.forEach((error) => {
        const fullMatch = error.error_match;
        const content = error.error_text;
        const errorId = error.error_id;
        const errorType = error.error_type;
        const isAnnotated = userAnnotations[errorId] ? 'annotated' : 'unannotated';
        
        // Use start_idx and end_idx if available, otherwise fall back to search
        let startIdx = error.start_idx;
        let endIdx = error.end_idx;
        
        if (startIdx !== undefined && endIdx !== undefined) {
            const errorClass = errorType === 'DEL' ? 'del-error' : errorType === 'INS' ? 'ins-error' : 'sub-error';
            const replacement = `<span class="error-highlight ${errorClass} ${isAnnotated}" ` +
                `onclick="openAnnotationModal('${escapeHtml(errorId)}', '${escapeHtml(errorType)}', '${escapeHtml(fullMatch)}', '${escapeHtml(content)}')">` +
                `<span class="error-status-indicator"></span>${escapeHtml(fullMatch)}</span>`;
            
            replacements.push({
                start: startIdx,
                end: endIdx,
                replacement: replacement,
                errorId: errorId
            });
        }
    });
    
    // Sort by position (descending) and apply replacements
    replacements.sort((a, b) => b.start - a.start);
    replacements.forEach(r => {
        html = html.substring(0, r.start) + r.replacement + html.substring(r.end);
    });
    
    return html;
}

function highlightErrorsLegacy(text, utteranceId) {
    // Fallback for backward compatibility
    const patterns = [
        { regex: /\[DEL:([^\]]+)\]/g, type: 'DEL', class: 'del-error' },
        { regex: /\[SUB:([^\]]+)\]/g, type: 'SUB', class: 'sub-error' },
        { regex: /\[INS:([^\]]+)\]/g, type: 'INS', class: 'ins-error' }
    ];
    
    let html = text;
    const replacements = [];
    
    patterns.forEach(pattern => {
        let match;
        const regex = new RegExp(pattern.regex);
        while ((match = regex.exec(text)) !== null) {
            const fullMatch = match[0];
            const content = match[1];
            const key = `${utteranceId}_${pattern.type}_${fullMatch}`;
            const isAnnotated = userAnnotations[key] ? 'annotated' : 'unannotated';
            
            const replacement = `<span class="error-highlight ${pattern.class} ${isAnnotated}" ` +
                `onclick="openAnnotationModalLegacy('${escapeHtml(pattern.type)}', '${escapeHtml(fullMatch)}', '${escapeHtml(content)}')">` +
                `<span class="error-status-indicator"></span>${escapeHtml(fullMatch)}</span>`;
            
            replacements.push({
                start: match.index,
                end: match.index + fullMatch.length,
                replacement: replacement
            });
        }
    });
    
    // Sort by position (descending) and apply replacements
    replacements.sort((a, b) => b.start - a.start);
    replacements.forEach(r => {
        html = html.substring(0, r.start) + r.replacement + html.substring(r.end);
    });
    
    return html;
}

function openAnnotationModal(errorId, errorType, fullMatch, errorText) {
    const utterance = allData[currentUtteranceIndex];
    currentErrorId = errorId;  // Store the error_id
    
    document.getElementById('errorContext').innerHTML = `
        <strong>Error Type:</strong> ${errorType}<br>
        <strong>Error Text:</strong> "${errorText}"<br>
        <strong>Utterance:</strong> ${utterance.utterance_id}<br>
        <strong>Error ID:</strong> <code style="font-size: 0.9em;">${errorId}</code>
    `;
    
    // Reset form
    document.getElementById('annotationForm').reset();
    document.getElementById('severitySlider').value = 0;
    document.getElementById('customTaxonomy').value = '';
    updateSeverityDisplay();
    
    // Load existing annotation if present
    const existing = userAnnotations[errorId];
    if (existing) {
        existing.taxonomy.forEach(tax => {
            if (tax.startsWith('custom:')) {
                // Extract custom taxonomy value
                document.getElementById('customTaxonomy').value = tax.substring(7);
            } else {
                const checkbox = document.getElementById(`tax-${tax}`);
                if (checkbox) checkbox.checked = true;
            }
        });
        document.getElementById('severitySlider').value = existing.severity;
        updateSeverityDisplay();
    }
    
    document.getElementById('annotationModal').style.display = 'block';
}

function openAnnotationModalLegacy(errorType, fullMatch, errorText) {
    // Fallback for backward compatibility
    const utterance = allData[currentUtteranceIndex];
    currentErrorId = `${utterance.utterance_id}_${errorType}_${fullMatch}`;  // Legacy key format
    
    document.getElementById('errorContext').innerHTML = `
        <strong>Error Type:</strong> ${errorType}<br>
        <strong>Error Text:</strong> "${errorText}"<br>
        <strong>Utterance:</strong> ${utterance.utterance_id}
    `;
    
    // Reset form
    document.getElementById('annotationForm').reset();
    document.getElementById('severitySlider').value = 0;
    document.getElementById('customTaxonomy').value = '';
    updateSeverityDisplay();
    
    // Load existing annotation if present
    const existing = userAnnotations[currentErrorId];
    if (existing) {
        existing.taxonomy.forEach(tax => {
            if (tax.startsWith('custom:')) {
                // Extract custom taxonomy value
                document.getElementById('customTaxonomy').value = tax.substring(7);
            } else {
                const checkbox = document.getElementById(`tax-${tax}`);
                if (checkbox) checkbox.checked = true;
            }
        });
        document.getElementById('severitySlider').value = existing.severity;
        updateSeverityDisplay();
    }
    
    document.getElementById('annotationModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('annotationModal').style.display = 'none';
    currentErrorId = null;
}

function updateSeverityDisplay() {
    const value = document.getElementById('severitySlider').value;
    const labels = ['None (0)', 'Minor (1)', 'Low (2)', 'Medium (3)', 'High (4)', 'Critical (5)'];
    document.getElementById('severityDisplay').textContent = `Severity: ${labels[value]}`;
}

async function handleAnnotationSubmit(e) {
    e.preventDefault();
    
    const selectedTaxonomy = Array.from(document.querySelectorAll('input[name="taxonomy"]:checked'))
        .map(el => el.value);
    
    // Add custom taxonomy if provided
    const customTaxonomy = document.getElementById('customTaxonomy').value.trim();
    if (customTaxonomy) {
        selectedTaxonomy.push(`custom:${customTaxonomy}`);
    }
    
    if (selectedTaxonomy.length === 0) {
        alert('Please select at least one taxonomy category or enter a custom category');
        return;
    }
    
    const severity = parseInt(document.getElementById('severitySlider').value);
    const utterance = allData[currentUtteranceIndex];
    const errors = utterance.metadata?.errors || [];
    
    // Find error metadata by error_id
    const errorData = errors.find(e => e.error_id === currentErrorId);
    if (!errorData) {
        alert('Error: Could not find error data');
        return;
    }
    
    const payload = {
        errorId: currentErrorId,
        utteranceId: utterance.utterance_id,
        errorType: errorData.error_type,
        errorMatch: errorData.error_match,
        taxonomy: selectedTaxonomy,
        severity: severity,
        utteranceIndex: currentUtteranceIndex,
        humanTranscript: utterance.human_transcript,
        asrReconstructed: utterance.asr_reconstructed
    };
    
    try {
        const response = await fetch(`/api/annotations/${modelName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        if (result.success) {
            // Update local cache with error_id as key
            userAnnotations[currentErrorId] = {
                taxonomy: selectedTaxonomy,
                severity: severity
            };
            
            closeModal();
            loadUtterance(currentUtteranceIndex); // Refresh to show updated status
            loadStats();
        } else {
            alert('Error saving annotation: ' + result.error);
        }
    } catch (error) {
        alert('Error saving annotation: ' + error.message);
    }
}

async function loadAnnotations() {
    try {
        const response = await fetch(`/api/annotations/${modelName}`);
        const annotations = await response.json();
        
        // Build local cache indexed by error_id
        userAnnotations = {};
        annotations.forEach(ann => {
            userAnnotations[ann.errorId] = {
                taxonomy: ann.taxonomy,
                severity: ann.severity
            };
            
            // Also maintain legacy keys for backward compatibility
            const legacyKey = `${ann.utteranceId}_${ann.errorType}_${ann.errorMatch}`;
            userAnnotations[legacyKey] = {
                taxonomy: ann.taxonomy,
                severity: ann.severity
            };
        });
    } catch (error) {
        console.error('Error loading annotations:', error);
    }
}

async function loadStats() {
    try {
        // Get current session data
        const actualIndex = randomizedIndices[currentPositionInRandomized];
        const currentUtterance = allData[actualIndex];
        
        // Get total sessions (all utterances)
        const totalSessions = allData.length;
        
        // Get errors in current session
        const errors = currentUtterance.metadata?.errors || [];
        const totalErrorsInSession = errors.length;
        
        // Get annotated errors in current session
        const annotatedInSession = errors.filter(e => userAnnotations[e.error_id]).length;
        
        // Calculate progress percentage
        const progressPercent = totalErrorsInSession > 0 
            ? Math.round((annotatedInSession / totalErrorsInSession) * 100)
            : 0;
        
        // Update UI
        document.getElementById('totalUtterances').textContent = totalSessions;
        document.getElementById('totalErrors').textContent = totalErrorsInSession;
        document.getElementById('totalAnnotations').textContent = annotatedInSession;
        document.getElementById('progressPercent').textContent = progressPercent + '%';
    } catch (error) {
        console.error('Error loading stats:', error);
        // Set default values on error
        document.getElementById('totalErrors').textContent = '0';
        document.getElementById('totalAnnotations').textContent = '0';
        document.getElementById('progressPercent').textContent = '0%';
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
});

// Close modal on outside click
window.addEventListener('click', function(e) {
    const modal = document.getElementById('annotationModal');
    if (e.target === modal) closeModal();
});
