/**
 * BlockJournal Main JavaScript
 * Handles UI interactions, animations, and user experience
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme setting
    initializeThemeToggle();
    
    // Initialize automatic session timeout
    initializeSessionTimeout();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize flash message auto-hide
    initializeFlashMessages();
    
    // Post interactions
    initializePostInteractions();
});

/**
 * Theme Toggle Functionality
 */
function initializeThemeToggle() {
    // Check if theme toggle exists in the settings page
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Get current theme from localStorage
        const currentTheme = localStorage.getItem('theme') || 'light';
        themeToggle.checked = currentTheme === 'dark';
        
        // Apply theme on toggle change
        themeToggle.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
}

/**
 * Initialize automatic session timeout
 */
function initializeSessionTimeout() {
    let lastActivity = Date.now();
    const sessionTimeoutElement = document.getElementById('session-countdown');
    
    // If there's no session countdown element, return early
    if (!sessionTimeoutElement) return;
    
    // Get timeout in minutes from the element's data attribute or default to 30
    const timeoutMinutes = parseInt(sessionTimeoutElement.dataset.timeout || '30');
    let remainingSeconds = timeoutMinutes * 60;
    
    // Update the countdown timer
    function updateCountdown() {
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        sessionTimeoutElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        if (remainingSeconds <= 0) {
            // Session expired, redirect to logout
            window.location.href = '/logout';
            return;
        }
        
        remainingSeconds--;
    }
    
    // Set up auto logout after inactivity
    function resetTimer() {
        lastActivity = Date.now();
    }
    
    // Activity events to track user interaction
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
        document.addEventListener(event, resetTimer, true);
    });
    
    // Start the countdown timer
    const countdownInterval = setInterval(updateCountdown, 1000);
    
    // Check for inactivity every 5 seconds
    setInterval(function() {
        const idleTime = Date.now() - lastActivity;
        // If idle for more than timeout minutes, logout
        if (idleTime >= timeoutMinutes * 60 * 1000) {
            clearInterval(countdownInterval);
            window.location.href = '/logout';
        }
    }, 5000);
}

/**
 * Initialize tooltips for icons and elements
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[title]');
    
    tooltipElements.forEach(element => {
        const tooltipText = element.getAttribute('title');
        if (!tooltipText) return;
        
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        // Remove the title attribute to prevent default browser tooltip
        element.removeAttribute('title');
        element.dataset.tooltip = tooltipText;
        
        // Position tooltip on hover
        element.addEventListener('mouseenter', function(e) {
            document.body.appendChild(tooltip);
            
            const rect = element.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            // Position the tooltip centered above the element
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltipRect.width / 2) + 'px';
            tooltip.style.top = rect.top - tooltipRect.height - 10 + 'px';
            
            // Add visible class for animation
            setTimeout(() => tooltip.classList.add('visible'), 10);
        });
        
        // Remove tooltip on mouse leave
        element.addEventListener('mouseleave', function() {
            tooltip.classList.remove('visible');
            
            // Remove after animation completes
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 200);
        });
    });
}

/**
 * Initialize auto-hide for flash messages
 */
function initializeFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        // Auto-hide after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 300);
        }, 5000);
    });
}

/**
 * Initialize post interactions (likes, comments, etc.)
 */
function initializePostInteractions() {
    // Toggle comment section
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const postCard = this.closest('.post-card');
            const commentsSection = postCard.querySelector('.post-comments');
            commentsSection.classList.toggle('hidden');
        });
    });
    
    // Submit comment form
    document.querySelectorAll('.submit-comment').forEach(btn => {
        btn.addEventListener('click', async function() {
            const commentForm = this.closest('.comment-form');
            const textarea = commentForm.querySelector('textarea');
            const comment = textarea.value.trim();
            
            if (!comment) return;
            
            const postCard = this.closest('.post-card');
            const postId = postCard.dataset.postId;
            
            try {
                // Simulate API call (replace with actual fetch when backend is ready)
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Clear textarea
                textarea.value = '';
                
                // Update UI with new comment
                addCommentToUI(postCard, {
                    author: 'Current User', // Replace with actual user data
                    content: comment,
                    timestamp: 'Gerade eben'
                });
                
                // Update comment count
                updateCommentCount(postCard, 1);
            } catch (error) {
                console.error('Error posting comment:', error);
                showErrorMessage('Kommentar konnte nicht gesendet werden.');
            }
        });
    });
    
    // Handle reactions (likes, etc)
    document.querySelectorAll('.reaction-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const postId = this.closest('.post-card').dataset.postId;
            const reactionType = this.dataset.reaction;
            const icon = this.querySelector('i');
            
            // Toggle the reaction state
            if (icon.classList.contains('far')) {
                // Add reaction
                try {
                    // Simulate API call (replace with actual fetch when backend is ready)
                    await new Promise(resolve => setTimeout(resolve, 300));
                    
                    // Update UI
                    icon.classList.replace('far', 'fas');
                    incrementCounter(this.querySelector('.count'));
                } catch (error) {
                    console.error('Error adding reaction:', error);
                }
            } else {
                // Remove reaction
                try {
                    // Simulate API call (replace with actual fetch when backend is ready)
                    await new Promise(resolve => setTimeout(resolve, 300));
                    
                    // Update UI
                    icon.classList.replace('fas', 'far');
                    decrementCounter(this.querySelector('.count'));
                } catch (error) {
                    console.error('Error removing reaction:', error);
                }
            }
        });
    });
}

/**
 * Helper function to add a new comment to the UI
 */
function addCommentToUI(postCard, comment) {
    const commentsList = postCard.querySelector('.comments-list');
    const commentElement = document.createElement('div');
    commentElement.className = 'comment';
    
    commentElement.innerHTML = `
        <div class="comment-header">
            <div class="comment-author">
                <div class="author-avatar">
                    <div class="default-avatar extra-small">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
                <div class="author-info">
                    <h5 class="author-name">${comment.author}</h5>
                    <span class="comment-time">${comment.timestamp}</span>
                </div>
            </div>
        </div>
        <div class="comment-content">
            <p>${escapeHTML(comment.content)}</p>
        </div>
    `;
    
    commentsList.appendChild(commentElement);
}

/**
 * Update comment count in UI
 */
function updateCommentCount(postCard, increment) {
    const countEl = postCard.querySelector('.comment-btn .count');
    let count = parseInt(countEl.textContent) || 0;
    count += increment;
    countEl.textContent = count.toString();
}

/**
 * Increment a counter element
 */
function incrementCounter(countElement) {
    const count = parseInt(countElement.textContent) || 0;
    countElement.textContent = (count + 1).toString();
}

/**
 * Decrement a counter element
 */
function decrementCounter(countElement) {
    const count = parseInt(countElement.textContent) || 0;
    if (count > 0) {
        countElement.textContent = (count - 1).toString();
    }
}

/**
 * Show an error message to the user
 */
function showErrorMessage(message) {
    const flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) return;
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.innerHTML = `
        ${message}
        <span class="close-btn" onclick="this.parentElement.style.display='none';">&times;</span>
    `;
    
    flashContainer.appendChild(alert);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 300);
    }, 5000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
