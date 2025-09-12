const fileInput = document.getElementById('fileInput');
const span = document.getElementById('span');

fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    
    if (!file?.name.endsWith('.txt')) {
        console.error('Invalid file type. Please upload .txt file');
        alert('Invalid file type. Please upload .txt file');
        return;
    }

    try {
        const text = await readFile(file);
        const lineCount = countLines(text);
        span.value = lineCount;
        // Вывод в консоль
//        console.log('------ File Analysis ------');
//        console.log('File Name:', file.name);
//        console.log('File Size:', (file.size / 1024).toFixed(2), 'KB');
//        console.log('Content:\n', text);
//        console.log('Total Lines:', lineCount);
//        console.log('Total Characters:', text.length);
//        console.log('---------------------------');
    } catch (error) {
        console.error('Error reading file:', error);
    }
});

async function readFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e.target.error);
        reader.readAsText(file);
    });
}

function countLines(text) {
    return text.split(/\r\n|\n|\r/).filter(line => line.trim() !== '').length;
}
