// Annotation Interface JavaScript
let allData = [];
let randomizedIndices = [];  // Randomized session order
let currentPositionInRandomized = 0;  // Current position in randomized array
let currentErrorId = null;  // Changed: now using error_id instead of error key
let userAnnotations = {};
let modelName = null;
let errorIdMap = {};  // Map from error_id to annotation data
let manualSpansByUtterance = {};  // utterance_id -> [manual span objects]
let pendingManualSpan = null;  // Manual span awaiting save (from a fresh selection)

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
    
    // Load utterances, then annotations, then re-render so manual spans and
    // annotated states are reflected on first paint.
    loadUtterances().then(() => loadAnnotations()).then(() => {
        if (randomizedIndices.length) {
            loadUtterance(randomizedIndices[currentPositionInRandomized]);
        }
        loadStats();
    });
    
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) prevBtn.addEventListener('click', () => navigateUtterance(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => navigateUtterance(1));
    
    document.getElementById('annotationForm').addEventListener('submit', handleAnnotationSubmit);

    // "Not an Error" is mutually exclusive with the other ASR Error Class options -
    // checking it clears the rest and vice versa, since they're contradictory.
    document.querySelectorAll('input[name="errorClass"]').forEach(cb => {
        cb.addEventListener('change', function() {
            if (this.value === 'not_an_error' && this.checked) {
                document.querySelectorAll('input[name="errorClass"]').forEach(other => {
                    if (other.value !== 'not_an_error') other.checked = false;
                });
            } else if (this.value !== 'not_an_error' && this.checked) {
                const notAnError = document.getElementById('ec-not_an_error');
                if (notAnError) notAnError.checked = false;
            }
        });
    });

    // Click-anywhere seek + text-selection manual annotation on the ASR Reconstructed box
    const asrRecEl = document.getElementById('asrReconstructed');
    if (asrRecEl) {
        asrRecEl.addEventListener('click', handleSeekClick);
        asrRecEl.addEventListener('mouseup', handleTextSelection);
    }
});

// Returns { total, annotated, complete } for the auto-detected errors in a session.
// Manual (annotator-added) spans are always annotated at creation time, so only
// the auto-detected flagged errors need to be checked for completion.
function getSessionCompletion(utterance) {
    const autoErrors = (utterance && utterance.metadata && utterance.metadata.errors) || [];
    const annotated = autoErrors.filter(e => userAnnotations[e.error_id]).length;
    return { total: autoErrors.length, annotated, complete: annotated === autoErrors.length };
}

function navigateUtterance(direction) {
    if (direction > 0) {
        const currentUtterance = allData[randomizedIndices[currentPositionInRandomized]];
        const status = getSessionCompletion(currentUtterance);
        if (!status.complete) {
            alert(
                `This session is INCOMPLETE: ${status.total - status.annotated} of ${status.total} ` +
                `flagged error(s) still need to be annotated before moving to the next session.`
            );
            return;
        }
    }
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
    
    // Debug: Log the utterance structure
    console.log('Loaded utterance index:', index);
    console.log('Utterance keys:', Object.keys(utterance));
    console.log('Metadata exists:', !!utterance.metadata);
    if (utterance.metadata) {
        console.log('Metadata keys:', Object.keys(utterance.metadata));
        console.log('Errors found:', utterance.metadata.errors?.length || 0);
    }
    
    const humanEl = document.getElementById('humanTranscript');
    if (humanEl) humanEl.textContent = utterance.human_transcript || '';

    const humanNerEl = document.getElementById('humanTranscriptNER');
    // Resolve NER text from several possible locations (top-level or metadata)
    const humanNerText = utterance.human_transcript_ner || utterance.humanTranscriptNER ||
        utterance.metadata?.human_transcript_ner || utterance.metadata?.humanTranscriptNER || '';
    if (humanNerEl) humanNerEl.textContent = humanNerText;

    const asrEl = document.getElementById('asrTranscript');
    if (asrEl) asrEl.textContent = utterance.asr_transcript || '';

    const asrRecEl = document.getElementById('asrReconstructed');
    if (asrRecEl) asrRecEl.innerHTML = highlightErrors(utterance.asr_reconstructed, utterance.utterance_id);

    loadSessionAudio(utterance);
}

function loadSessionAudio(utterance) {
    const audioEl = document.getElementById('sessionAudio');
    const unavailableEl = document.getElementById('audioUnavailable');
    if (!audioEl) return;

    const audioFile = utterance.audio_file || utterance.metadata?.audio_file || '';

    // Stop any audio from the previous session before swapping sources
    audioEl.pause();

    if (audioFile) {
        const src = audioFile.startsWith('http')
            ? audioFile
            : `/api/audio?path=${encodeURIComponent(audioFile)}`;
        audioEl.src = src;
        audioEl.load();
        audioEl.style.display = '';
        if (unavailableEl) unavailableEl.style.display = 'none';
    } else {
        audioEl.removeAttribute('src');
        audioEl.load();
        audioEl.style.display = 'none';
        if (unavailableEl) unavailableEl.style.display = '';
    }
}

// Map a DOM position (node, offset) to a raw character index in asr_reconstructed.
// Works because highlightErrors only wraps substrings, never alters characters.
function domPointToCharIdx(container, node, offset) {
    const r = document.createRange();
    r.setStart(container, 0);
    r.setEnd(node, offset);
    return r.toString().length;
}

// Proportionally seek the session audio to a character position in the text.
function seekToPosition(charIdx) {
    const audio = document.getElementById('sessionAudio');
    if (!audio || !isFinite(audio.duration) || audio.duration <= 0) return;
    const text = allData[currentUtteranceIndex]?.asr_reconstructed || '';
    if (!text.length || charIdx === undefined || charIdx === null) return;
    const frac = Math.min(1, Math.max(0, charIdx / text.length));
    audio.currentTime = Math.max(0, frac * audio.duration - 0.25); // small lead-in
    audio.play().catch(() => {}); // ignore browser autoplay rejection
}

function seekToError(error) {
    if (!error) return;
    // Prefer real timestamps if a future alignment pass adds them
    if (typeof error.start_time === 'number') {
        const audio = document.getElementById('sessionAudio');
        if (!audio) return;
        audio.currentTime = Math.max(0, error.start_time - 0.25);
        audio.play().catch(() => {});
        return;
    }
    seekToPosition(error.start_idx);
}

// Click on empty (non-span) text seeks the audio to that approximate position.
function handleSeekClick(e) {
    const container = document.getElementById('asrReconstructed');
    if (!container) return;
    if (e.target.closest('.error-highlight')) return; // span handles its own seek
    const sel = window.getSelection();
    if (sel && !sel.isCollapsed) return; // user is selecting text, not seeking

    let node = null, offset = 0;
    if (document.caretPositionFromPoint) {
        const cp = document.caretPositionFromPoint(e.clientX, e.clientY);
        if (cp) { node = cp.offsetNode; offset = cp.offset; }
    } else if (document.caretRangeFromPoint) {
        const cr = document.caretRangeFromPoint(e.clientX, e.clientY);
        if (cr) { node = cr.startContainer; offset = cr.startOffset; }
    }
    if (node && container.contains(node)) {
        seekToPosition(domPointToCharIdx(container, node, offset));
    }
}

// Manual span helpers -------------------------------------------------------

function getManualSpans(utteranceId) {
    return manualSpansByUtterance[utteranceId] || [];
}

// Resolve a span (auto error, saved manual span, or pending selection) by id.
function getErrorById(utterance, errorId) {
    const auto = (utterance.metadata?.errors || []).find(e => e.error_id === errorId);
    if (auto) return auto;
    const manual = getManualSpans(utterance.utterance_id).find(e => e.error_id === errorId);
    if (manual) return manual;
    if (pendingManualSpan && pendingManualSpan.error_id === errorId) return pendingManualSpan;
    return null;
}

// Read the current selection within the container as raw character offsets.
function getSelectionOffsets(container) {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return null;
    const range = sel.getRangeAt(0);
    if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) return null;
    const text = sel.toString();
    if (!text.trim()) return null;
    const startIdx = domPointToCharIdx(container, range.startContainer, range.startOffset);
    return { startIdx, endIdx: startIdx + text.length, text };
}

// True if [startIdx, endIdx) overlaps any existing auto error or manual span.
function spanOverlaps(startIdx, endIdx, utterance) {
    const spans = [
        ...(utterance.metadata?.errors || []),
        ...getManualSpans(utterance.utterance_id)
    ];
    return spans.some(s => s.start_idx !== undefined && s.end_idx !== undefined &&
        startIdx < s.end_idx && s.start_idx < endIdx);
}

// On text selection in the ASR Reconstructed box, open the modal for a MANUAL span.
function handleTextSelection() {
    const container = document.getElementById('asrReconstructed');
    if (!container) return;
    const offsets = getSelectionOffsets(container);
    if (!offsets) return;

    const utterance = allData[currentUtteranceIndex];
    if (!utterance) return;

    if (spanOverlaps(offsets.startIdx, offsets.endIdx, utterance)) {
        alert('This selection overlaps an existing highlighted span. Please select text outside existing spans.');
        window.getSelection().removeAllRanges();
        return;
    }

    const text = offsets.text.trim();
    pendingManualSpan = {
        error_id: (crypto.randomUUID ? crypto.randomUUID() : `manual_${Date.now()}_${Math.random().toString(36).slice(2)}`),
        error_type: 'MANUAL',
        error_match: text,
        error_text: text,
        start_idx: offsets.startIdx,
        end_idx: offsets.endIdx,
        source: 'manual'
    };
    window.getSelection().removeAllRanges();
    openAnnotationModal(pendingManualSpan.error_id, 'MANUAL', text, text);
}

function highlightErrors(text, utteranceId) {
    const utterance = allData[currentUtteranceIndex];
    const autoErrors = utterance.metadata?.errors || [];
    const manualSpans = getManualSpans(utterance.utterance_id);
    const errors = [...autoErrors, ...manualSpans];
    
    if (errors.length === 0) {
        // Fallback to old method if no errors in metadata and no manual spans
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
            const errorClass = errorType === 'MANUAL' ? 'manual-error'
                : errorType === 'DEL' ? 'del-error'
                : errorType === 'INS' ? 'ins-error' : 'sub-error';
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

    // Seek the session audio to the approximate location of this error
    const errorData = getErrorById(utterance, errorId);
    if (errorData) seekToError(errorData);
    
    document.getElementById('errorContext').innerHTML = `
        <strong>Error Type:</strong> ${errorType}<br>
        <strong>Error Text:</strong> "${errorText}"<br>
        <strong>Utterance:</strong> ${utterance.utterance_id}<br>
        <strong>Error ID:</strong> <code style="font-size: 0.9em;">${errorId}</code>
    `;
    
    // Reset form
    document.getElementById('annotationForm').reset();
    clearSeveritySelection();
    
    // Load existing annotation if present
    const existing = userAnnotations[errorId];
    if (existing) {
        (existing.taxonomy || []).forEach(tax => {
            if (!tax.startsWith('custom:')) {
                const checkbox = document.getElementById(`tax-${tax}`);
                if (checkbox) checkbox.checked = true;
            }
        });
        (existing.errorClass || []).forEach(cls => {
            const checkbox = document.getElementById(`ec-${cls}`);
            if (checkbox) checkbox.checked = true;
        });
        selectSeverity(existing.severity);
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
    clearSeveritySelection();
    
    // Load existing annotation if present
    const existing = userAnnotations[currentErrorId];
    if (existing) {
        (existing.taxonomy || []).forEach(tax => {
            if (!tax.startsWith('custom:')) {
                const checkbox = document.getElementById(`tax-${tax}`);
                if (checkbox) checkbox.checked = true;
            }
        });
        (existing.errorClass || []).forEach(cls => {
            const checkbox = document.getElementById(`ec-${cls}`);
            if (checkbox) checkbox.checked = true;
        });
        selectSeverity(existing.severity);
    }
    
    document.getElementById('annotationModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('annotationModal').style.display = 'none';
    currentErrorId = null;
    pendingManualSpan = null;
}

const SEVERITY_LABELS = { 1: 'Minor', 2: 'Moderate', 3: 'Severe' };

// Select a severity level (1-3) via the button group and update the hidden
// input + display text used elsewhere (submit handler, loadStats, etc).
function selectSeverity(value) {
    value = parseInt(value, 10);
    document.getElementById('severitySlider').value = value;
    document.querySelectorAll('.severity-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.value, 10) === value);
    });
    updateSeverityDisplay();
}

// Clear the severity selection so the annotator must explicitly click a level -
// no default is pre-selected, so severity can no longer be silently skipped.
function clearSeveritySelection() {
    document.getElementById('severitySlider').value = '';
    document.querySelectorAll('.severity-btn').forEach(btn => btn.classList.remove('active'));
    updateSeverityDisplay();
}

function updateSeverityDisplay() {
    const raw = document.getElementById('severitySlider').value;
    if (raw === '' || raw === null) {
        document.getElementById('severityDisplay').textContent = 'Severity: not yet selected';
        return;
    }
    const value = parseInt(raw, 10);
    const label = SEVERITY_LABELS[value] ? `${value} (${SEVERITY_LABELS[value]})` : `${value}`;
    document.getElementById('severityDisplay').textContent = `Severity: ${label}`;
}

async function handleAnnotationSubmit(e) {
    e.preventDefault();
    
    // Clinical taxonomy is deprecated (commented out of the form) - classification
    // is now driven entirely by ASR Error Class. selectedTaxonomy will be empty
    // since no `taxonomy` checkboxes exist in the DOM anymore; kept for payload
    // shape / backward compatibility with the Annotation.taxonomy column.
    const selectedTaxonomy = Array.from(document.querySelectorAll('input[name="taxonomy"]:checked'))
        .map(el => el.value);
    
    const selectedErrorClass = Array.from(document.querySelectorAll('input[name="errorClass"]:checked'))
        .map(el => el.value);
    
    if (selectedErrorClass.length === 0) {
        alert('Please select at least one ASR Error Class (or "Not an Error")');
        return;
    }
    
    const severityRaw = document.getElementById('severitySlider').value;
    if (severityRaw === '' || severityRaw === null) {
        alert('Please select a severity rating (Minor / Moderate / Severe)');
        return;
    }
    const severity = parseInt(severityRaw, 10);
    const utterance = allData[currentUtteranceIndex];
    
    // Resolve the span: auto error, saved manual span, or pending selection
    const errorData = getErrorById(utterance, currentErrorId);
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
        errorClass: selectedErrorClass,
        severity: severity,
        utteranceIndex: currentUtteranceIndex,
        humanTranscript: utterance.human_transcript,
        humanTranscriptNER: utterance.human_transcript_ner
            || utterance.metadata?.human_transcript_ner
            || '',
        asrReconstructed: utterance.asr_reconstructed,
        startIdx: errorData.start_idx,
        endIdx: errorData.end_idx,
        source: errorData.source || 'auto'
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
                errorClass: selectedErrorClass,
                severity: severity
            };

            // Persist newly created manual spans so they render immediately
            if ((errorData.source || 'auto') === 'manual') {
                const uid = utterance.utterance_id;
                manualSpansByUtterance[uid] = manualSpansByUtterance[uid] || [];
                if (!manualSpansByUtterance[uid].some(s => s.error_id === currentErrorId)) {
                    manualSpansByUtterance[uid].push({
                        error_id: currentErrorId,
                        error_type: 'MANUAL',
                        error_match: errorData.error_match,
                        error_text: errorData.error_text || errorData.error_match,
                        start_idx: errorData.start_idx,
                        end_idx: errorData.end_idx,
                        source: 'manual'
                    });
                }
            }
            pendingManualSpan = null;

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
        manualSpansByUtterance = {};
        annotations.forEach(ann => {
            userAnnotations[ann.errorId] = {
                taxonomy: ann.taxonomy,
                errorClass: ann.errorClass,
                severity: ann.severity
            };
            
            // Also maintain legacy keys for backward compatibility
            const legacyKey = `${ann.utteranceId}_${ann.errorType}_${ann.errorMatch}`;
            userAnnotations[legacyKey] = {
                taxonomy: ann.taxonomy,
                errorClass: ann.errorClass,
                severity: ann.severity
            };

            // Collect manual spans so they can be re-rendered as highlights
            if (ann.source === 'manual' && ann.startIdx !== null && ann.startIdx !== undefined) {
                const uid = ann.utteranceId;
                manualSpansByUtterance[uid] = manualSpansByUtterance[uid] || [];
                manualSpansByUtterance[uid].push({
                    error_id: ann.errorId,
                    error_type: 'MANUAL',
                    error_match: ann.errorMatch,
                    error_text: ann.errorMatch,
                    start_idx: ann.startIdx,
                    end_idx: ann.endIdx,
                    source: 'manual'
                });
            }
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
        
        // Safety check - if no current utterance, set defaults
        if (!currentUtterance) {
            console.warn('No current utterance available for stats');
            document.getElementById('totalErrors').textContent = '0';
            document.getElementById('totalAnnotations').textContent = '0';
            document.getElementById('progressPercent').textContent = '0%';
            return;
        }
        
        // Get total sessions (all utterances)
        const totalSessions = allData.length;
        
        // Get errors in current session (auto-detected + manual spans)
        const autoErrors = currentUtterance.metadata?.errors || [];
        const manualSpans = getManualSpans(currentUtterance.utterance_id);
        const errors = [...autoErrors, ...manualSpans];
        const totalErrorsInSession = errors.length;
        
        // Get annotated errors in current session (manual spans are always annotated)
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
        
        // Session completion badge + gate the Next button (auto-detected errors only)
        const status = getSessionCompletion(currentUtterance);
        const badge = document.getElementById('sessionStatusBadge');
        const tracker = document.getElementById('sessionTracker');
        const nextBtn = document.getElementById('nextBtn');
        if (tracker) {
            tracker.textContent = `${status.annotated} / ${status.total} errors annotated`;
        }
        if (badge) {
            if (status.complete) {
                badge.textContent = 'COMPLETE';
                badge.classList.remove('incomplete');
                badge.classList.add('complete');
            } else {
                badge.textContent = `INCOMPLETE (${status.total - status.annotated} left)`;
                badge.classList.remove('complete');
                badge.classList.add('incomplete');
            }
        }
        if (nextBtn) nextBtn.disabled = !status.complete;
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
