import * as pdfjsLib from './node_modules/pdfjs-dist/build/pdf.mjs';

const { ipcRenderer } = window.electron || {};

let words = [];
let currentIndex = 0;
let isPlaying = false;
let intervalId = null;

pdfjsLib.GlobalWorkerOptions.workerSrc = './node_modules/pdfjs-dist/build/pdf.worker.mjs';

const display = document.getElementById('display');
const startButton = document.getElementById('start');
const pauseButton = document.getElementById('pause');
const resetButton = document.getElementById('reset');
const inputArea = document.getElementById('input-area');
const fileInput = document.getElementById('file-input');
const wordsPerDisplay = document.getElementById('words-per-display');
const speedInput = document.getElementById('speed');
const clearButton = document.getElementById('clear-text');
const linesToDisplay = document.getElementById('lines-to-display');
const urlInput = document.getElementById('url-input');
const fetchUrlButton = document.getElementById('fetch-url');

function splitIntoWords(text) {
    return text.trim().split(/\s+/);
}

function calculateTextLines(text, containerWidth) {
    const temp = document.createElement('div');
    temp.style.position = 'absolute';
    temp.style.width = `${containerWidth}px`;
    temp.style.fontSize = window.getComputedStyle(display).fontSize;
    temp.style.lineHeight = window.getComputedStyle(display).lineHeight;
    temp.style.visibility = 'hidden';
    temp.textContent = text;
    document.body.appendChild(temp);
    
    const height = temp.offsetHeight;
    const lineHeight = parseInt(window.getComputedStyle(temp).lineHeight);
    document.body.removeChild(temp);
    
    return Math.ceil(height / lineHeight);
}

function displayWords() {
    const numWords = parseInt(wordsPerDisplay.value);
    const maxLines = parseInt(linesToDisplay.value);
    const displayWidth = display.offsetWidth - 40;
    
    let tempWords = words.slice(currentIndex, currentIndex + numWords);
    let tempText = tempWords.join(' ');
    
    // Adjust timing if we had to reduce words to fit lines
    if (tempWords.length < numWords) {
        const speed = parseInt(speedInput.value);
        const newInterval = (60 / speed) * 1000 * tempWords.length;
        
        // Reset interval with new timing if it changed
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = setInterval(displayWords, newInterval);
        }
    }
    
    while (calculateTextLines(tempText, displayWidth) > maxLines && tempWords.length > 1) {
        tempWords.pop();
        tempText = tempWords.join(' ');
    }
    
    display.textContent = tempText;
    currentIndex += tempWords.length;

    // Stop at the end
    if (currentIndex >= words.length) {
        stopReading();
    }
}

function startReading() {
    if (!words.length) return;
    
    // If we're at the end, start from beginning
    if (currentIndex >= words.length) {
        currentIndex = 0;
    }
    
    isPlaying = true;
    const speed = parseInt(speedInput.value);
    const wordsPerBatch = parseInt(wordsPerDisplay.value);
    const interval = (60 / speed) * 1000 * wordsPerBatch;
    
    intervalId = setInterval(displayWords, interval);
    startButton.disabled = true;
    pauseButton.disabled = false;
}

function stopReading() {
    isPlaying = false;
    clearInterval(intervalId);
    startButton.disabled = false;
    pauseButton.disabled = true;
}

function resetReading() {
    stopReading();
    currentIndex = 0;
    display.textContent = 'Words will appear here';
}

function clearText() {
    inputArea.value = '';
    words = [];
    resetReading();
}

async function fetchWebPage(url) {
    fetchUrlButton.disabled = true;
    try {
        const response = await fetch(url);
        const html = await response.text();
        
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        const elementsToRemove = doc.querySelectorAll('script, style, header, footer, nav, aside, iframe, img');
        elementsToRemove.forEach(element => element.remove());
        
        const content = doc.body.textContent
            .replace(/\s+/g, ' ')
            .trim();
        
        inputArea.value = content;
        words = splitIntoWords(content);
        resetReading();
    } catch (error) {
        alert('Error fetching webpage: ' + error.message);
    } finally {
        fetchUrlButton.disabled = false;
    }
}

function updateReadingInterval() {
    if (!isPlaying) return;
    
    const speed = parseInt(speedInput.value);
    const wordsPerBatch = parseInt(wordsPerDisplay.value);
    const interval = (60 / speed) * 1000 * wordsPerBatch;
    
    clearInterval(intervalId);
    intervalId = setInterval(displayWords, interval);
}

// Event Listeners
startButton.addEventListener('click', startReading);
pauseButton.addEventListener('click', stopReading);
resetButton.addEventListener('click', resetReading);
clearButton.addEventListener('click', clearText);

inputArea.addEventListener('input', (e) => {
    words = splitIntoWords(e.target.value);
    resetReading();
});

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
        let text;
        if (file.type === 'application/pdf') {
            display.textContent = 'Loading PDF...';
            
            if (!pdfjsLib) {
                throw new Error('PDF.js library not loaded properly');
            }
            
            text = await readPdfFile(file);
        } else {
            text = await file.text();
        }
        
        inputArea.value = text;
        words = splitIntoWords(text);
        resetReading();
    } catch (error) {
        alert('Error reading file: ' + error.message);
    }
});

linesToDisplay.addEventListener('input', (e) => {
    if (e.target.value < 1) e.target.value = 1;
    if (e.target.value > 3) e.target.value = 3;
    // Force refresh of current display
    if (isPlaying) {
        displayWords();
    }
});

wordsPerDisplay.addEventListener('input', (e) => {
    if (e.target.value < 1) e.target.value = 1;
    updateReadingInterval();
});

fetchUrlButton.addEventListener('click', () => {
    const url = urlInput.value.trim();
    if (!url) {
        alert('Please enter a URL');
        return;
    }
    
    try {
        new URL(url); // Validate URL format
        fetchWebPage(url);
    } catch {
        alert('Please enter a valid URL');
    }
});

speedInput.addEventListener('input', (e) => {
    if (e.target.value < 60) e.target.value = 60;
    if (e.target.value > 1000) e.target.value = 1000;
    updateReadingInterval();
});

// Initialize
pauseButton.disabled = true; 

async function readPdfFile(file) {
    try {
        const fileUrl = URL.createObjectURL(file);
        const loadingTask = pdfjsLib.getDocument(fileUrl);
        const pdf = await loadingTask.promise;
        
        let fullText = '';
        
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const textItems = textContent.items;
            const lines = {};
            
            textItems.forEach(item => {
                const y = Math.round(item.transform[5]);
                if (!lines[y]) {
                    lines[y] = [];
                }
                lines[y].push(item.str);
            });
            
            const sortedLines = Object.keys(lines)
                .sort((a, b) => b - a)
                .map(y => lines[y].join(' '));
            
            fullText += sortedLines.join('\n') + '\n\n';
        }
        
        URL.revokeObjectURL(fileUrl);
        
        return fullText
            .replace(/\n\s*\n/g, '\n\n')
            .replace(/\s+/g, ' ')
            .trim();
    } catch (error) {
        throw new Error('Failed to read PDF: ' + error.message);
    }
}
