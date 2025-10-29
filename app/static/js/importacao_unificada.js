// Sistema de Importação Unificada
// Detecta automaticamente o tipo de dados do arquivo Excel

let selectedFile = null;
let analysisResult = null;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setupFileInput();
});

// Configuração do drag and drop
function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    // Eventos de drag and drop
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('border-blue-400', 'bg-blue-50');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('border-blue-400', 'bg-blue-50');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('border-blue-400', 'bg-blue-50');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // Evento de clique na zona
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });
}

// Configuração do input de arquivo
function setupFileInput() {
    const fileInput = document.getElementById('file-input');

    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

// Manipulação da seleção de arquivo
function handleFileSelection(file) {
    // Verificar extensão
    const allowedExtensions = ['.xlsx', '.xls'];
    const fileName = file.name.toLowerCase();
    const isValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));

    if (!isValidExtension) {
        showError('Por favor, selecione um arquivo Excel (.xlsx ou .xls)');
        return;
    }

    // Verificar tamanho (máximo 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError('Arquivo muito grande. Máximo permitido: 10MB');
        return;
    }

    selectedFile = file;
    updateFileDisplay();
    hideAnalysisResult();
}

// Atualizar exibição do arquivo selecionado
function updateFileDisplay() {
    const fileSelected = document.getElementById('file-selected');
    const selectedFilename = document.getElementById('selected-filename');
    const selectedSize = document.getElementById('selected-size');

    selectedFilename.textContent = selectedFile.name;
    selectedSize.textContent = formatFileSize(selectedFile.size);

    fileSelected.classList.remove('hidden');
}

// Formatar tamanho do arquivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Limpar arquivo selecionado
function clearFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-selected').classList.add('hidden');
    hideAnalysisResult();
}

// Esconder resultado da análise
function hideAnalysisResult() {
    const analysisResult = document.getElementById('analysis-result');
    const actionButtons = document.getElementById('action-buttons');

    analysisResult.classList.add('hidden');
    actionButtons.classList.add('hidden');
    analysisResult = null;
}

// Analisar arquivo automaticamente
async function analyzeFile() {
    if (!selectedFile) {
        showError('Por favor, selecione um arquivo primeiro');
        return;
    }

    try {
        showLoading('Analisando arquivo...');

        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro na análise do arquivo');
        }

        const result = await response.json();
        analysisResult = result;

        displayAnalysisResult(result);

    } catch (error) {
        console.error('Erro na análise:', error);
        showError(error.message || 'Erro ao analisar o arquivo');
    } finally {
        hideLoading();
    }
}

// Exibir resultado da análise
function displayAnalysisResult(result) {
    const analysisResultDiv = document.getElementById('analysis-result');
    const analysisContent = document.getElementById('analysis-content');
    const actionButtons = document.getElementById('action-buttons');

    let content = '';

    if (result.success) {
        content += `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span class="text-green-800 font-medium">Arquivo válido detectado!</span>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 class="font-semibold text-blue-900 mb-2">Tipo Detectado</h4>
                    <p class="text-blue-800">${getTypeDisplayName(result.tipo)}</p>
                </div>

                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <h4 class="font-semibold text-purple-900 mb-2">Registros Encontrados</h4>
                    <p class="text-purple-800">${result.total_registros} registros</p>
                </div>
            </div>
        `;

        // Mostrar preview dos dados se disponível
        if (result.preview && result.preview.length > 0) {
            content += `
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-900 mb-2">Preview dos Dados</h4>
                    <div class="overflow-x-auto">
                        <table class="min-w-full text-sm">
                            <thead>
                                <tr class="border-b border-gray-200">
                                    ${Object.keys(result.preview[0]).map(key =>
                                        `<th class="text-left py-2 px-3 font-medium text-gray-700">${key}</th>`
                                    ).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${result.preview.slice(0, 3).map(row => `
                                    <tr class="border-b border-gray-100">
                                        ${Object.values(row).map(value =>
                                            `<td class="py-2 px-3 text-gray-600">${value || '-'}</td>`
                                        ).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        ${result.preview.length > 3 ? `<p class="text-sm text-gray-500 mt-2">... e mais ${result.total_registros - 3} registros</p>` : ''}
                    </div>
                </div>
            `;
        }

        // Mostrar avisos se houver
        if (result.warnings && result.warnings.length > 0) {
            content += `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 class="font-semibold text-yellow-900 mb-2 flex items-center">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                        </svg>
                        Avisos
                    </h4>
                    <ul class="list-disc list-inside text-yellow-800 text-sm">
                        ${result.warnings.map(warning => `<li>${warning}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        actionButtons.classList.remove('hidden');

    } else {
        content += `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span class="text-red-800 font-medium">Erro na análise do arquivo</span>
                </div>
                <p class="text-red-700 mt-2">${result.error}</p>
            </div>
        `;
    }

    analysisContent.innerHTML = content;
    analysisResultDiv.classList.remove('hidden');
}

// Obter nome de exibição do tipo
function getTypeDisplayName(tipo) {
    const tipos = {
        'proprietarios': 'Proprietários',
        'imoveis': 'Imóveis',
        'participacoes': 'Participações',
        'alugueis': 'Aluguéis'
    };
    return tipos[tipo] || tipo;
}

// Prosseguir com a importação
async function proceedWithImport() {
    if (!analysisResult || !analysisResult.success) {
        showError('Análise do arquivo necessária antes da importação');
        return;
    }

    try {
        showLoading('Importando dados...');

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('tipo', analysisResult.tipo);

        const response = await fetch('/importar', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${getAuthToken()}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro na importação');
        }

        const result = await response.json();

        if (result.success) {
            showSuccess(`Importação concluída! ${result.importados} registros importados com sucesso.`);
            clearFile();
        } else {
            showError(result.error || 'Erro na importação');
        }

    } catch (error) {
        console.error('Erro na importação:', error);
        showError(error.message || 'Erro ao importar os dados');
    } finally {
        hideLoading();
    }
}

// Cancelar importação
function cancelImport() {
    hideAnalysisResult();
}

// Obter token de autenticação
function getAuthToken() {
    return sessionStorage.getItem('auth_token') || localStorage.getItem('auth_token');
}

// Utilitários de UI
function showLoading(message) {
    // Criar overlay de loading se não existir
    let loadingOverlay = document.getElementById('loading-overlay');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        loadingOverlay.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex items-center space-x-4">
                <svg class="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-gray-700" id="loading-message">${message}</span>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    } else {
        document.getElementById('loading-message').textContent = message;
        loadingOverlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('hidden');
    }
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error');
}

function showToast(message, type) {
    // Remover toast existente
    const existingToast = document.getElementById('toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    // Criar novo toast
    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white`;

    toast.innerHTML = `
        <div class="flex items-center">
            <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${type === 'success'
                    ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
                    : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
                }
            </svg>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto-remover após 5 segundos
    setTimeout(() => {
        toast.remove();
    }, 5000);
}