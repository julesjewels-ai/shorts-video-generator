// Dance Loop Gen - Frontend Controller

class DanceLoopApp {
    constructor() {
        this.selectedPoseIndex = 0;
        this.currentMode = 'single';
        this.socket = null;
        this.init();
    }

    async init() {
        this.cacheDOM();
        this.bindEvents();
        await this.loadConfig();
        this.connectWS();
    }

    cacheDOM() {
        // Inputs
        this.leaderOutfit = document.getElementById('leader-outfit');
        this.followerOutfit = document.getElementById('follower-outfit');
        this.settingDesc = document.getElementById('setting-desc');
        this.sceneVariety = document.getElementById('scene-variety');
        this.varietyValue = document.getElementById('variety-value');
        this.poseGrid = document.getElementById('reference-pose-grid');
        
        // Navigation / Actions
        this.btnGenerate = document.getElementById('btn-generate');
        this.btnSaveConfig = document.getElementById('save-config');
        this.modeSingle = document.getElementById('mode-single');
        this.modeBatch = document.getElementById('mode-batch');
        this.btnBackToGen = document.getElementById('btn-back-to-gen');

        // Views
        this.viewIdle = document.getElementById('view-idle');
        this.viewProgress = document.getElementById('view-progress');
        this.viewResults = document.getElementById('view-results');

        // Progress elements
        this.progStatus = document.getElementById('progress-status');
        this.progPercentText = document.getElementById('progress-percent');
        this.progBarFill = document.getElementById('progress-bar-fill');
        this.logTerminal = document.getElementById('log-terminal');
        
        // Result elements
        this.resultTitle = document.getElementById('result-title');
        this.mainResultImg = document.getElementById('main-result-img');
        this.resultThumbnails = document.getElementById('result-thumbnails');
        this.metadataDisplay = document.getElementById('metadata-display');
        this.sceneCardsContainer = document.getElementById('scene-cards-container');
    }

    bindEvents() {
        this.btnGenerate.addEventListener('click', () => this.startGeneration());
        this.btnSaveConfig.addEventListener('click', () => this.saveConfig());
        this.sceneVariety.addEventListener('input', (e) => this.varietyValue.textContent = e.target.value);
        
        this.modeSingle.addEventListener('click', () => this.switchMode('single'));
        this.modeBatch.addEventListener('click', () => this.switchMode('batch'));
        
        this.btnBackToGen.addEventListener('click', () => this.switchView('idle'));
    }

    async loadConfig() {
        try {
            const resp = await fetch('/api/config');
            const config = await resp.json();
            
            this.leaderOutfit.value = config.leader_outfit;
            this.followerOutfit.value = config.follower_outfit;
            this.settingDesc.value = config.setting;
            this.sceneVariety.value = config.scene_variety;
            this.varietyValue.textContent = config.scene_variety;
            
            this.renderPoseGrid(config.reference_poses);
        } catch (err) {
            this.notify('Failed to load configuration', 'error');
        }
    }

    renderPoseGrid(poses) {
        this.poseGrid.innerHTML = '';
        poses.forEach((pose, index) => {
            const div = document.createElement('div');
            div.className = `pose-thumb ${index === this.selectedPoseIndex ? 'selected' : ''}`;
            div.setAttribute('tabindex', '0');
            div.setAttribute('role', 'button');
            div.setAttribute('aria-label', `Select pose ${index + 1}`);
            div.innerHTML = `<img src="/api/prompts/file/${pose}" alt="Pose ${index + 1}">`;
            
            const select = () => {
                this.selectedPoseIndex = index;
                document.querySelectorAll('.pose-thumb').forEach(t => t.classList.remove('selected'));
                div.classList.add('selected');
            };
            
            div.onclick = select;
            div.onkeydown = (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    select();
                }
            };
            this.poseGrid.appendChild(div);
        });
    }

    async saveConfig() {
        const config = {
            leader_outfit: this.leaderOutfit.value,
            follower_outfit: this.followerOutfit.value,
            setting: this.settingDesc.value,
            scene_variety: parseInt(this.sceneVariety.value)
        };
        
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            this.notify('Configuration saved successfully');
        } catch (err) {
            this.notify('Failed to save configuration', 'error');
        }
    }

    switchMode(mode) {
        this.currentMode = mode;
        this.modeSingle.classList.toggle('active', mode === 'single');
        this.modeBatch.classList.toggle('active', mode === 'batch');
        
        if (mode === 'batch') {
            this.notify('Batch mode coming soon in UI - Use Single for now!', 'info');
        }
    }

    switchView(viewId) {
        [this.viewIdle, this.viewProgress, this.viewResults].forEach(v => v.classList.add('hidden'));
        document.getElementById(`view-${viewId}`).classList.remove('hidden');
    }

    connectWS() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.socket = new WebSocket(`${protocol}//${window.location.host}/ws/progress`);
        
        this.socket.onmessage = (event) => {
            const progress = JSON.parse(event.data);
            this.updateProgressUI(progress);
        };

        this.socket.onclose = () => {
            setTimeout(() => this.connectWS(), 2000); // Reconnect
        };
    }

    async startGeneration() {
        this.switchView('progress');
        this.clearProgressUI();
        
        try {
            await fetch('/api/generate/single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    reference_pose_index: this.selectedPoseIndex,
                    scene_variety: parseInt(this.sceneVariety.value)
                })
            });
        } catch (err) {
            this.notify('Failed to start generation', 'error');
        }
    }

    updateProgressUI(progress) {
        if (progress.status === 'idle' && this.viewProgress.classList.contains('hidden')) return;

        this.progStatus.textContent = progress.message;
        this.progPercentText.textContent = `${progress.progress_percent}%`;
        this.progBarFill.style.width = `${progress.progress_percent}%`;
        
        // Add log entry
        const logEntry = document.createElement('div');
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${progress.message}`;
        this.logTerminal.appendChild(logEntry);
        this.logTerminal.scrollTop = this.logTerminal.scrollHeight;

        // Highlight pipeline nodes
        document.querySelectorAll('.stage-node').forEach(node => {
            const stage = node.dataset.stage;
            if (stage === progress.current_stage) {
                node.classList.add('active');
                node.classList.remove('complete');
            } else if (this.isStageBefore(stage, progress.current_stage)) {
                node.classList.add('complete');
                node.classList.remove('active');
            }
        });

        // Show keyframes if any
        if (progress.keyframes && progress.keyframes.length > 0) {
            progress.keyframes.forEach(kf => {
                const img = document.getElementById(`stream-img-${kf.scene.toLowerCase()}`);
                if (img) {
                    img.src = kf.url;
                    img.classList.remove('hidden');
                    img.previousElementSibling.classList.add('hidden'); // hide placeholder
                }
            });
        }

        if (progress.status === 'complete') {
            this.notify('Generation complete!', 'success');
            // Wait a bit before showing results so user can see 100%
            setTimeout(() => this.showResults(progress), 2000);
        }
    }

    isStageBefore(stage, currentStage) {
        const order = ['Planning', 'Generating Assets', 'Creating Veo', 'Generating SEO', 'Complete'];
        return order.indexOf(stage) < order.indexOf(currentStage);
    }

    clearProgressUI() {
        this.progBarFill.style.width = '0%';
        this.logTerminal.innerHTML = '';
        document.querySelectorAll('.stage-node').forEach(n => {
            n.classList.remove('active');
            n.classList.remove('complete');
        });
        document.querySelectorAll('.keyframe-streaming-grid img').forEach(img => {
            img.classList.add('hidden');
            img.previousElementSibling.classList.remove('hidden');
        });
    }

    showResults(progress) {
        this.switchView('results');
        this.resultTitle.textContent = progress.plan_title.replace(/_/g, ' ').toUpperCase();
        
        if (progress.keyframes.length > 0) {
            this.mainResultImg.src = progress.keyframes[0].url;
            this.renderThumbnails(progress.keyframes);
        }
        
        // In a real app, we'd fetch the full detail here
        // For V1 V0, we'll just show what we have from progress
    }

    renderThumbnails(keyframes) {
        this.resultThumbnails.innerHTML = '';
        keyframes.forEach((kf, i) => {
            const div = document.createElement('div');
            div.className = `thumb-item ${i === 0 ? 'active' : ''}`;
            div.innerHTML = `<img src="${kf.url}">`;
            div.onclick = () => {
                this.mainResultImg.src = kf.url;
                document.querySelectorAll('.thumb-item').forEach(t => t.classList.remove('active'));
                div.classList.add('active');
            };
            this.resultThumbnails.appendChild(div);
        });
    }

    notify(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        const container = document.getElementById('toast-container');
        if (!container) {
            const c = document.createElement('div');
            c.id = 'toast-container';
            c.style.position = 'fixed';
            c.style.bottom = '20px';
            c.style.right = '20px';
            c.style.zIndex = '1000';
            document.body.appendChild(c);
        }
        
        document.getElementById('toast-container').appendChild(toast);
        
        setTimeout(() => toast.remove(), 4000);
    }
}

// Global Styles for Toast
const style = document.createElement('style');
style.textContent = `
    .toast {
        padding: 12px 24px;
        border-radius: 8px;
        margin-top: 10px;
        color: white;
        font-weight: 500;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .toast-success { background: #4caf50; }
    .toast-error { background: #ff5252; }
    .toast-info { background: #2196f3; }
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

// Start app
window.onload = () => new DanceLoopApp();
