// 错误提示功能
function showError(message, duration = 3000) {
    const toast = document.getElementById('errorToast');
    const messageEl = document.getElementById('errorMessage');
    messageEl.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        hideError();
    }, duration);
}

function hideError() {
    document.getElementById('errorToast').classList.add('hidden');
}

// 加载状态控制
function showLoading(message = '加载中...') {
    const overlay = document.getElementById('loadingOverlay');
    const messageEl = document.getElementById('loadingMessage');
    messageEl.textContent = message;
    overlay.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

// 确认对话框
let confirmCallback = null;

function showConfirm(title, message, callback) {
    const dialog = document.getElementById('confirmDialog');
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    confirmCallback = callback;
    dialog.classList.remove('hidden');
}

function confirmAction() {
    if (confirmCallback) {
        confirmCallback();
    }
    cancelConfirm();
}

function cancelConfirm() {
    const dialog = document.getElementById('confirmDialog');
    dialog.classList.add('hidden');
    confirmCallback = null;
}

// API请求封装
async function apiRequest(url, options = {}) {
    try {
        showLoading();
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }
        
        return data;
    } catch (error) {
        showError(error.message);
        throw error;
    } finally {
        hideLoading();
    }
}

// 工具函数
function formatFileSize(bytes) {
    if (!bytes) return '未知';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function formatDuration(seconds) {
    if (!seconds) return '未知';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    return [hours, minutes, remainingSeconds]
        .map(v => v.toString().padStart(2, '0'))
        .join(':');
} 