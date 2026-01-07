// 遊戲邏輯類
class IdiomGame {
    constructor(idiomManager, pictureGenerator = null) {
        this.idiomManager = idiomManager;
        this.pictureGenerator = pictureGenerator;
        this.currentMode = null;
        this.currentQuestion = null;
        this.score = 0;
        this.correctCount = 0;
        this.wrongCount = 0;
        this.currentHint = 0;
    }

    // 開始遊戲
    startGame(mode) {
        this.currentMode = mode;
        this.score = 0;
        this.correctCount = 0;
        this.wrongCount = 0;
        this.currentHint = 0;
        this.updateScore();
        this.generateQuestion();
    }

    // 生成題目
    generateQuestion() {
        this.currentHint = 0;
        
        switch (this.currentMode) {
            case 'picture-guess':
                this.generatePictureGuessQuestion();
                break;
            case 'fill-blank':
                this.generateFillBlankQuestion();
                break;
            case 'guess-meaning':
                this.generateGuessMeaningQuestion();
                break;
            case 'word-chain':
                this.generateWordChainQuestion();
                break;
            case 'find-idiom':
                this.generateFindIdiomQuestion();
                break;
        }
    }

    // 生成看圖猜成語題（暫時改為顯示解釋猜成語）
    async generatePictureGuessQuestion() {
        try {
            const idiom = this.idiomManager.getRandomIdiom();
            const wrongOptions = this.idiomManager.getAllIdioms()
                .filter(item => item.idiom !== idiom.idiom)
                .map(item => item.idiom)
                .sort(() => Math.random() - 0.5)
                .slice(0, 3);

            const allOptions = [idiom.idiom, ...wrongOptions];
            
            // 打亂選項順序
            for (let i = allOptions.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [allOptions[i], allOptions[j]] = [allOptions[j], allOptions[i]];
            }

            this.currentQuestion = {
                type: 'picture-guess',
                idiom: idiom.idiom,
                correctAnswer: idiom.idiom,
                options: allOptions,
                meaning: idiom.meaning,
                pinyin: idiom.pinyin,
                example: idiom.example
            };

            this.renderPictureGuess();
        } catch (error) {
            console.error('生成看圖猜成語題失敗:', error);
            const container = document.getElementById('gameContent');
            container.innerHTML = `
                <div style="text-align: center; padding: 50px;">
                    <p style="color: red;">生成題目失敗: ${error.message}</p>
                    <p>請刷新頁面重試</p>
                </div>
            `;
        }
    }

    // 生成填空題
    generateFillBlankQuestion() {
        const idiom = this.idiomManager.getRandomIdiom();
        const fillBlank = this.idiomManager.generateFillBlank(idiom.idiom);
        
        this.currentQuestion = {
            type: 'fill-blank',
            idiom: idiom.idiom,
            display: fillBlank.display,
            answers: fillBlank.answers,
            hint: idiom.meaning,
            pinyin: idiom.pinyin
        };

        this.renderFillBlank();
    }

    // 生成猜意思題
    generateGuessMeaningQuestion() {
        const idiom = this.idiomManager.getRandomIdiom();
        const wrongOptions = this.idiomManager.generateWrongOptions(idiom.meaning, 3);
        const allOptions = [idiom.meaning, ...wrongOptions];
        
        // 打亂選項順序
        for (let i = allOptions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [allOptions[i], allOptions[j]] = [allOptions[j], allOptions[i]];
        }

        this.currentQuestion = {
            type: 'guess-meaning',
            idiom: idiom.idiom,
            correctAnswer: idiom.meaning,
            options: allOptions,
            pinyin: idiom.pinyin
        };

        this.renderGuessMeaning();
    }

    // 生成接龍題
    generateWordChainQuestion() {
        const previousIdiom = this.idiomManager.getRandomIdiom();
        const lastChar = previousIdiom.idiom[previousIdiom.idiom.length - 1];
        const chainIdioms = this.idiomManager.getChainIdioms(lastChar);
        
        if (chainIdioms.length === 0) {
            // 如果沒有可接的，重新生成
            this.generateWordChainQuestion();
            return;
        }

        const correctIdiom = chainIdioms[Math.floor(Math.random() * chainIdioms.length)];
        const wrongOptions = this.idiomManager.getAllIdioms()
            .filter(item => item.idiom !== correctIdiom.idiom && item.idiom[0] !== lastChar)
            .slice(0, 3)
            .map(item => item.idiom);

        const allOptions = [correctIdiom.idiom, ...wrongOptions];
        
        // 打亂選項順序
        for (let i = allOptions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [allOptions[i], allOptions[j]] = [allOptions[j], allOptions[i]];
        }

        this.currentQuestion = {
            type: 'word-chain',
            previousIdiom: previousIdiom.idiom,
            lastChar: lastChar,
            correctAnswer: correctIdiom.idiom,
            options: allOptions
        };

        this.renderWordChain();
    }

    // 生成找成語題（簡化版）
    generateFindIdiomQuestion() {
        const idiom = this.idiomManager.getRandomIdiom();
        
        // 生成包含成語的文字（簡化版）
        const text = `在這段文字中，有一個成語：${idiom.idiom}，請找出它。`;
        
        this.currentQuestion = {
            type: 'find-idiom',
            text: text,
            correctAnswer: idiom.idiom,
            idiom: idiom.idiom
        };

        this.renderFindIdiom();
    }

    // 檢查答案
    checkAnswer(userAnswer) {
        let isCorrect = false;

        switch (this.currentQuestion.type) {
            case 'picture-guess':
                isCorrect = userAnswer === this.currentQuestion.correctAnswer;
                break;
            case 'fill-blank':
                isCorrect = this.checkFillBlank(userAnswer);
                break;
            case 'guess-meaning':
                isCorrect = userAnswer === this.currentQuestion.correctAnswer;
                break;
            case 'word-chain':
                isCorrect = userAnswer === this.currentQuestion.correctAnswer;
                break;
            case 'find-idiom':
                isCorrect = userAnswer === this.currentQuestion.correctAnswer;
                break;
        }

        if (isCorrect) {
            this.correctCount++;
            this.score += 10;
            this.showResult(true);
        } else {
            this.wrongCount++;
            this.score = Math.max(0, this.score - 5);
            this.showResult(false);
        }

        this.updateScore();

        // 1秒後生成新題目
        setTimeout(() => {
            this.generateQuestion();
        }, 2000);
    }

    // 檢查填空答案
    checkFillBlank(userAnswers) {
        if (!Array.isArray(userAnswers) || userAnswers.length !== this.currentQuestion.answers.length) {
            return false;
        }
        
        return userAnswers.every((answer, index) => 
            answer.trim() === this.currentQuestion.answers[index]
        );
    }

    // 顯示提示
    showHint() {
        if (!this.currentQuestion) return;

        this.currentHint++;
        
        switch (this.currentQuestion.type) {
            case 'fill-blank':
                if (this.currentHint === 1) {
                    alert(`提示：拼音是 ${this.currentQuestion.pinyin}`);
                } else if (this.currentHint === 2) {
                    alert(`提示：意思是「${this.currentQuestion.hint}」`);
                }
                break;
            case 'guess-meaning':
                if (this.currentHint === 1) {
                    alert(`提示：拼音是 ${this.currentQuestion.pinyin}`);
                }
                break;
            default:
                alert('這個模式暫時沒有提示');
        }
    }

    // 跳過題目
    skipQuestion() {
        this.wrongCount++;
        this.score = Math.max(0, this.score - 3);
        this.updateScore();
        this.generateQuestion();
    }

    // 更新分數
    updateScore() {
        document.getElementById('score').textContent = this.score;
        document.getElementById('correctCount').textContent = this.correctCount;
        document.getElementById('wrongCount').textContent = this.wrongCount;
    }

    // 顯示結果
    showResult(isCorrect) {
        const message = isCorrect ? '✅ 正確！' : '❌ 錯誤！';
        const correctAnswer = this.getCorrectAnswerText();
        
        // 顯示結果提示
        const resultDiv = document.createElement('div');
        resultDiv.className = `result-message ${isCorrect ? 'correct' : 'wrong'}`;
        resultDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: ${isCorrect ? '#28a745' : '#dc3545'};
            color: white;
            padding: 30px 50px;
            border-radius: 12px;
            font-size: 24px;
            z-index: 2000;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        `;
        resultDiv.textContent = `${message} ${correctAnswer}`;
        document.body.appendChild(resultDiv);

        setTimeout(() => {
            document.body.removeChild(resultDiv);
        }, 1500);
    }

    // 獲取正確答案文字
    getCorrectAnswerText() {
        switch (this.currentQuestion.type) {
            case 'picture-guess':
                return `正確答案是：${this.currentQuestion.correctAnswer}`;
            case 'fill-blank':
                return `正確答案是：${this.currentQuestion.idiom}`;
            case 'guess-meaning':
                return `正確答案是：${this.currentQuestion.correctAnswer}`;
            case 'word-chain':
                return `正確答案是：${this.currentQuestion.correctAnswer}`;
            case 'find-idiom':
                return `正確答案是：${this.currentQuestion.correctAnswer}`;
            default:
                return '';
        }
    }

    // 結束遊戲
    endGame() {
        const totalQuestions = this.correctCount + this.wrongCount;
        const correctRate = totalQuestions > 0 
            ? Math.round((this.correctCount / totalQuestions) * 100) 
            : 0;

        document.getElementById('finalScore').textContent = this.score;
        document.getElementById('finalCorrect').textContent = this.correctCount;
        document.getElementById('finalWrong').textContent = this.wrongCount;
        document.getElementById('finalRate').textContent = correctRate + '%';

        document.getElementById('gameArea').classList.add('hidden');
        document.getElementById('resultScreen').classList.remove('hidden');
    }

    // 渲染填空題
    renderFillBlank() {
        const container = document.getElementById('gameContent');
        const display = this.currentQuestion.display;
        const blankCount = (display.match(/_/g) || []).length;

        let html = '<div class="fill-blank-container">';
        html += '<div class="question-text">';
        
        // 將顯示文字轉換為輸入框
        let inputIndex = 0;
        display.split('').forEach(char => {
            if (char === '_') {
                html += `<input type="text" class="blank-input" maxlength="1" data-index="${inputIndex}" />`;
                inputIndex++;
            } else {
                html += `<span style="margin: 0 5px; font-size: 48px;">${char}</span>`;
            }
        });
        
        html += '</div>';
        html += '<button class="btn btn-success submit-btn" id="submitAnswer">提交答案</button>';
        html += '</div>';

        container.innerHTML = html;

        // 添加提交事件
        document.getElementById('submitAnswer').addEventListener('click', () => {
            const inputs = container.querySelectorAll('.blank-input');
            const answers = Array.from(inputs).map(input => input.value);
            this.checkAnswer(answers);
        });

        // 輸入框自動跳轉
        const inputs = container.querySelectorAll('.blank-input');
        inputs.forEach((input, index) => {
            input.addEventListener('input', () => {
                if (input.value && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            });
        });

        // 聚焦第一個輸入框
        if (inputs.length > 0) {
            inputs[0].focus();
        }
    }

    // 渲染猜意思題
    renderGuessMeaning() {
        const container = document.getElementById('gameContent');
        
        let html = '<div class="guess-meaning-container">';
        html += `<div class="idiom-display">${this.currentQuestion.idiom}</div>`;
        html += '<div class="options-list">';
        
        this.currentQuestion.options.forEach(option => {
            html += `<button class="option-btn" data-answer="${option}">${option}</button>`;
        });
        
        html += '</div>';
        html += '</div>';

        container.innerHTML = html;

        // 添加選項點擊事件
        container.querySelectorAll('.option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const answer = btn.getAttribute('data-answer');
                this.checkAnswer(answer);
                
                // 顯示正確/錯誤狀態
                container.querySelectorAll('.option-btn').forEach(b => {
                    if (b.getAttribute('data-answer') === this.currentQuestion.correctAnswer) {
                        b.classList.add('correct');
                    } else if (b.getAttribute('data-answer') === answer && answer !== this.currentQuestion.correctAnswer) {
                        b.classList.add('wrong');
                    }
                    b.disabled = true;
                });
            });
        });
    }

    // 渲染接龍題
    renderWordChain() {
        const container = document.getElementById('gameContent');
        
        let html = '<div class="guess-meaning-container">';
        html += `<div class="idiom-display">${this.currentQuestion.previousIdiom}</div>`;
        html += `<p style="text-align: center; font-size: 20px; margin-bottom: 30px;">請接上一個成語的最後一個字「${this.currentQuestion.lastChar}」</p>`;
        html += '<div class="options-list">';
        
        this.currentQuestion.options.forEach(option => {
            html += `<button class="option-btn" data-answer="${option}">${option}</button>`;
        });
        
        html += '</div>';
        html += '</div>';

        container.innerHTML = html;

        // 添加選項點擊事件
        container.querySelectorAll('.option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const answer = btn.getAttribute('data-answer');
                this.checkAnswer(answer);
                
                // 顯示正確/錯誤狀態
                container.querySelectorAll('.option-btn').forEach(b => {
                    if (b.getAttribute('data-answer') === this.currentQuestion.correctAnswer) {
                        b.classList.add('correct');
                    } else if (b.getAttribute('data-answer') === answer && answer !== this.currentQuestion.correctAnswer) {
                        b.classList.add('wrong');
                    }
                    b.disabled = true;
                });
            });
        });
    }

    // 渲染看圖猜成語題（暫時改為顯示解釋猜成語）
    renderPictureGuess() {
        const container = document.getElementById('gameContent');
        
        // 確保有題目數據
        if (!this.currentQuestion || !this.currentQuestion.meaning) {
            console.error('❌ 沒有題目數據！', this.currentQuestion);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: red;">錯誤：題目數據缺失，請刷新頁面重試</div>';
            return;
        }
        
        // 顯示成語解釋，讓用戶猜成語
        let html = '<div class="picture-guess-container">';
        html += '<div class="meaning-display">';
        html += '<div class="meaning-title">成語解釋</div>';
        html += `<div class="meaning-text">${this.currentQuestion.meaning}</div>`;
        
        // 如果有例句，也顯示
        if (this.currentQuestion.example) {
            html += '<div class="example-title" style="margin-top: 30px; font-size: 18px; color: #666; font-weight: bold;">例句：</div>';
            html += `<div class="example-text" style="margin-top: 10px; font-size: 16px; color: #888; font-style: italic;">${this.currentQuestion.example}</div>`;
        }
        
        html += '</div>';
        html += '<div class="options-panel">';
        html += '<h3 style="text-align: center; margin-bottom: 20px; color: #667eea; font-size: 20px;">請根據解釋選擇正確的成語：</h3>';
        html += '<div class="options-list">';
        
        this.currentQuestion.options.forEach(option => {
            html += `<button class="option-btn idiom-option-btn" data-answer="${option}">${option}</button>`;
        });
        
        html += '</div>';
        html += '</div>';
        html += '</div>';

        container.innerHTML = html;

        // 添加選項點擊事件
        container.querySelectorAll('.idiom-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const answer = btn.getAttribute('data-answer');
                this.checkAnswer(answer);
                
                // 顯示正確/錯誤狀態
                container.querySelectorAll('.idiom-option-btn').forEach(b => {
                    if (b.getAttribute('data-answer') === this.currentQuestion.correctAnswer) {
                        b.classList.add('correct');
                    } else if (b.getAttribute('data-answer') === answer && answer !== this.currentQuestion.correctAnswer) {
                        b.classList.add('wrong');
                    }
                    b.disabled = true;
                });
            });
        });
    }

    // 渲染找成語題
    renderFindIdiom() {
        const container = document.getElementById('gameContent');
        
        let html = '<div class="guess-meaning-container">';
        html += `<div style="font-size: 24px; line-height: 1.8; margin-bottom: 30px; text-align: center;">${this.currentQuestion.text}</div>`;
        html += '<input type="text" id="idiomInput" placeholder="請輸入找到的成語" style="width: 100%; padding: 15px; font-size: 20px; border: 2px solid #667eea; border-radius: 8px; margin-bottom: 20px;">';
        html += '<button class="btn btn-success submit-btn" id="submitIdiom">提交答案</button>';
        html += '</div>';

        container.innerHTML = html;

        // 添加提交事件
        document.getElementById('submitIdiom').addEventListener('click', () => {
            const answer = document.getElementById('idiomInput').value.trim();
            if (answer) {
                this.checkAnswer(answer);
            }
        });

        // Enter 鍵提交
        document.getElementById('idiomInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('submitIdiom').click();
            }
        });

        document.getElementById('idiomInput').focus();
    }
}

