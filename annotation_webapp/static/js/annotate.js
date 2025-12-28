// Annotation Interface JavaScript
let allData = [];
let currentUtteranceIndex = 0;
let currentErrorKey = null;
let userAnnotations = {};
let modelName = null;

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
    
    document.getElementById('utteranceSelect').addEventListener('change', function() {
        loadUtterance(parseInt(this.value));
    });
    
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) prevBtn.addEventListener('click', () => navigateUtterance(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => navigateUtterance(1));
    
    document.getElementById('exportBtn').addEventListener('click', exportAnnotations);
    document.getElementById('severitySlider').addEventListener('input', updateSeverityDisplay);
    document.getElementById('annotationForm').addEventListener('submit', handleAnnotationSubmit);
});

function navigateUtterance(direction) {
    const newIndex = currentUtteranceIndex + direction;
    if (newIndex >= 0 && newIndex < allData.length) {
        loadUtterance(newIndex);
        document.getElementById('utteranceSelect').value = newIndex;
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
        
        populateUtteranceSelect();
        document.getElementById('transcriptsContainer').style.display = 'grid';
        loadUtterance(0);
        loadStats();
    } catch (error) {
        console.error('Error loading utterances:', error);
    }
}

function populateUtteranceSelect() {
    const select = document.getElementById('utteranceSelect');
    select.innerHTML = '';
    
    allData.forEach((utt, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${index + 1}. ${utt.utterance_id.substring(0, 40)}...`;
        select.appendChild(option);
    });
}

function loadUtterance(index) {
    if (index < 0 || index >= allData.length) return;
    
    currentUtteranceIndex = index;
    const utterance = allData[index];
    
    document.getElementById('humanTranscript').textContent = utterance.human_transcript;
    document.getElementById('asrTranscript').innerHTML = highlightErrors(utterance.asr_reconstructed, utterance.utterance_id);
    document.getElementById('utteranceSelect').value = index;
}

function highlightErrors(text, utteranceId) {
    const patterns = [
        { regex: /\[DEL:([^\]]+)\]/g, type: 'DEL', class: 'del-error' },
        { regex: /\[SUB:([^\]]+)\]/g, type: 'SUB', class: 'sub-error' },
        { regex: /\[INS:([^\]]+)\]/g, type: 'INS', class: 'ins-error' }
    ];
    
    let html = text;
    let offset = 0;
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
                `onclick="openAnnotationModal('${escapeHtml(pattern.type)}', '${escapeHtml(fullMatch)}', '${escapeHtml(content)}')">` +
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

function openAnnotationModal(errorType, fullMatch, errorText) {
    const utterance = allData[currentUtteranceIndex];
    currentErrorKey = `${utterance.utterance_id}_${errorType}_${fullMatch}`;
    
    document.getElementById('errorContext').innerHTML = `
        <strong>Error Type:</strong> ${errorType}<br>
        <strong>Error Text:</strong> "${errorText}"<br>
        <strong>Utterance:</strong> ${utterance.utterance_id}
    `;
    
    // Reset form
    document.getElementById('annotationForm').reset();
    document.getElementById('severitySlider').value = 0;
    updateSeverityDisplay();
    
    // Load existing annotation if present
    const existing = userAnnotations[currentErrorKey];
    if (existing) {
        existing.taxonomy.forEach(tax => {
            const checkbox = document.getElementById(`tax-${tax}`);
            if (checkbox) checkbox.checked = true;
        });
        document.getElementById('severitySlider').value = existing.severity;
        updateSeverityDisplay();
    }
    
    document.getElementById('annotationModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('annotationModal').style.display = 'none';
    currentErrorKey = null;
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
    
    if (selectedTaxonomy.length === 0) {
        alert('Please select at least one taxonomy category');
        return;
    }
    
    const severity = parseInt(document.getElementById('severitySlider').value);
    const utterance = allData[currentUtteranceIndex];
    const [uttId, errType, errMatch] = currentErrorKey.split('_', 3);
    
    const payload = {
        utteranceId: utterance.utterance_id,
        errorType: errType,
        errorMatch: errMatch,
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
            // Update local cache
            userAnnotations[currentErrorKey] = {
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
        
        // Build local cache
        userAnnotations = {};
        annotations.forEach(ann => {
            const key = `${ann.utteranceId}_${ann.errorType}_${ann.errorMatch}`;
            userAnnotations[key] = {
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
        const response = await fetch(`/api/stats/${modelName}`);
        const stats = await response.json();
        
        document.getElementById('totalUtterances').textContent = stats.totalUtterances;
        document.getElementById('totalErrors').textContent = stats.totalErrors;
        document.getElementById('totalAnnotations').textContent = stats.totalAnnotations;
        document.getElementById('progressPercent').textContent = stats.progress + '%';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function exportAnnotations() {
    try {
        const response = await fetch(`/api/export?model=${modelName}`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `annotations_${modelName}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('Error exporting annotations: ' + error.message);
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
