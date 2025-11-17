// API Base URL
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentUserId = null;
let currentSessionId = null;

// Status bar helper
function showStatus(message, type = 'info') {
    const statusBar = document.getElementById('statusBar');
    statusBar.textContent = message;
    statusBar.className = `status-bar show ${type}`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusBar.className = 'status-bar';
    }, 5000);
}

// Student Registration
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const userId = document.getElementById('userId').value.trim();
    const userName = document.getElementById('userName').value.trim();
    const userEmail = document.getElementById('userEmail').value.trim();
    const background = document.getElementById('background').value.trim();
    const learningGoals = document.getElementById('learningGoals').value.trim();
    const learningPace = document.getElementById('learningPace').value;

    try {
        const response = await fetch(`${API_BASE_URL}/api/student/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                name: userName,
                email: userEmail,
                background: background || null,
                learning_goals: learningGoals || null,
                learning_pace: learningPace
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentUserId = userId;
            showStatus(`✅ Student registered successfully: ${userName}`, 'success');

            // Show next section
            document.getElementById('sessionSection').style.display = 'block';
            document.getElementById('progressSection').style.display = 'block';

            // Scroll to session section
            document.getElementById('sessionSection').scrollIntoView({ behavior: 'smooth' });
        } else {
            showStatus(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Network error: ${error.message}`, 'error');
        console.error('Error:', error);
    }
});

// Session Start
document.getElementById('sessionForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!currentUserId) {
        showStatus('❌ Please register first', 'error');
        return;
    }

    const topicId = document.getElementById('topicId').value;
    const sessionGoal = document.getElementById('sessionGoal').value.trim();

    try {
        const response = await fetch(`${API_BASE_URL}/api/session/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUserId,
                topic_id: topicId,
                session_type: 'learning',
                goal: sessionGoal || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentSessionId = data.session_id;
            showStatus(`✅ Session started: ${topicId}`, 'success');

            // Show chat section
            document.getElementById('chatSection').style.display = 'block';

            // Add welcome message
            addMessageToChat('assistant', 'Hello! I\'m your Socratic tutor. I\'ll help you learn through questions, not direct explanations. What would you like to explore about this topic?', 'orchestrator');

            // Scroll to chat section
            document.getElementById('chatSection').scrollIntoView({ behavior: 'smooth' });
        } else {
            showStatus(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Network error: ${error.message}`, 'error');
        console.error('Error:', error);
    }
});

// Chat Message
document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!currentUserId || !currentSessionId) {
        showStatus('❌ Please start a session first', 'error');
        return;
    }

    const messageInput = document.getElementById('chatMessage');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    messageInput.value = '';

    // Disable input while processing
    messageInput.disabled = true;
    document.querySelector('#chatForm button').disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUserId,
                session_id: currentSessionId,
                message: message
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Add assistant response to chat
            addMessageToChat('assistant', data.message, data.agent_type);

            // Update chat info
            document.getElementById('teachingStage').textContent = data.teaching_stage || '-';
            document.getElementById('understandingScore').textContent =
                data.understanding_score !== null ? data.understanding_score.toFixed(2) : '-';
            document.getElementById('currentAgent').textContent = data.agent_type || '-';
        } else {
            showStatus(`❌ Error: ${data.detail}`, 'error');
            addMessageToChat('assistant', `Sorry, I encountered an error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(`❌ Network error: ${error.message}`, 'error');
        addMessageToChat('assistant', 'Sorry, I encountered a network error. Please try again.', 'error');
        console.error('Error:', error);
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        document.querySelector('#chatForm button').disabled = false;
        messageInput.focus();
    }
});

// Helper to add message to chat
function addMessageToChat(role, content, agentType = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    let html = `
        <div class="role">${role === 'user' ? 'You' : 'Tutor'}</div>
        <div class="content">${content}</div>
    `;

    if (agentType) {
        html += `<div class="agent-type">Agent: ${agentType}</div>`;
    }

    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Refresh Progress
document.getElementById('refreshProgress').addEventListener('click', async () => {
    if (!currentUserId) {
        showStatus('❌ Please register first', 'error');
        return;
    }

    const progressDisplay = document.getElementById('progressDisplay');
    progressDisplay.innerHTML = '<div class="loading">Loading progress...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/student/${currentUserId}/progress`);
        const data = await response.json();

        if (response.ok) {
            progressDisplay.innerHTML = `
                <div class="progress-stats">
                    <div class="stat-box">
                        <div class="value">${data.total_topics}</div>
                        <div class="label">Total Topics</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${data.mastered_count}</div>
                        <div class="label">Mastered</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${data.learning_count}</div>
                        <div class="label">Learning</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${data.struggling_count}</div>
                        <div class="label">Struggling</div>
                    </div>
                    <div class="stat-box">
                        <div class="value">${(data.overall_understanding * 100).toFixed(0)}%</div>
                        <div class="label">Overall Understanding</div>
                    </div>
                </div>
                ${data.mastered_topics.length > 0 ? `
                    <div style="margin-top: 20px;">
                        <h4>Mastered Topics:</h4>
                        <p style="color: #28a745; font-weight: 600; margin-top: 10px;">
                            ${data.mastered_topics.join(', ')}
                        </p>
                    </div>
                ` : '<p style="margin-top: 15px; color: #666;">No topics mastered yet. Keep learning!</p>'}
            `;

            showStatus('✅ Progress updated', 'success');
        } else {
            progressDisplay.innerHTML = '<p style="color: #dc3545;">Failed to load progress</p>';
            showStatus(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        progressDisplay.innerHTML = '<p style="color: #dc3545;">Network error</p>';
        showStatus(`❌ Network error: ${error.message}`, 'error');
        console.error('Error:', error);
    }
});

// Load Curriculum
document.getElementById('loadCurriculum').addEventListener('click', async () => {
    const curriculumDisplay = document.getElementById('curriculumDisplay');
    curriculumDisplay.innerHTML = '<div class="loading">Loading curriculum...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/curriculum/graph`);
        const data = await response.json();

        if (response.ok) {
            if (data.topics.length === 0) {
                curriculumDisplay.innerHTML = '<p style="color: #666;">No topics found in curriculum</p>';
                return;
            }

            let html = '<ul class="topic-list">';

            data.topics.forEach(topic => {
                const difficultyLabel = `Difficulty ${topic.difficulty}`;
                const prereqText = topic.prerequisites && topic.prerequisites.length > 0
                    ? `Prerequisites: ${topic.prerequisites.join(', ')}`
                    : 'No prerequisites';

                html += `
                    <li class="topic-item">
                        <h4>${topic.title}</h4>
                        <div>
                            <span class="difficulty">${difficultyLabel}</span>
                            <span style="color: #666; font-size: 12px;">${topic.category}</span>
                        </div>
                        <p style="margin-top: 8px; color: #666; font-size: 14px;">${topic.description || 'No description'}</p>
                        <p class="prerequisites">${prereqText}</p>
                        ${topic.estimated_time_hours ? `<p style="font-size: 12px; color: #999; margin-top: 5px;">⏱️ ${topic.estimated_time_hours} hours</p>` : ''}
                    </li>
                `;
            });

            html += '</ul>';
            html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Total topics: ${data.topics.length} | Total prerequisites: ${data.prerequisites.length}</p>`;

            curriculumDisplay.innerHTML = html;
            showStatus('✅ Curriculum loaded', 'success');
        } else {
            curriculumDisplay.innerHTML = '<p style="color: #dc3545;">Failed to load curriculum</p>';
            showStatus(`❌ Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        curriculumDisplay.innerHTML = '<p style="color: #dc3545;">Network error</p>';
        showStatus(`❌ Network error: ${error.message}`, 'error');
        console.error('Error:', error);
    }
});

// Initialize - check API health
fetch(`${API_BASE_URL}/health`)
    .then(response => response.json())
    .then(data => {
        console.log('API Health:', data);
        showStatus(`✅ API Connected - Version ${data.version}`, 'success');
    })
    .catch(error => {
        console.error('API Health Check Failed:', error);
        showStatus('⚠️ Warning: Cannot connect to API. Make sure the backend is running on http://localhost:8000', 'error');
    });
